import sounddevice as sd
import soundfile as sf
import os, sys
import threading
import subprocess
from tkinter import messagebox
import numpy as np

try:
    from libs import macvolume
except ImportError:
    import macvolume

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Soundpad', 'audio')


def list_devices():
    """Return list of (idx, name, has_input, has_output)."""
    result = []
    for i, d in enumerate(sd.query_devices()):
        result.append({
            "idx": i,
            "name": d["name"],
            "inputs": d["max_input_channels"],
            "outputs": d["max_output_channels"],
        })
    return result


MIN_CABLE_VOLUME = 0.99


def ensure_cable_volume(name, restore=True):
    """Проверить громкость виртуального кабеля и при необходимости поднять её.

    У BlackHole есть собственный регулятор громкости, и macOS запоминает его
    между запусками. Драйвер применяет его по кубической кривой, поэтому
    ползунок на 11% душит весь тракт примерно на -57 дБ: Discord получает
    почти тишину, и ни его настройки, ни громкость саундпада этого не вернут.
    Возвращает (было, стало) либо (None, None), если у устройства нет регулятора.
    """
    if not name:
        return (None, None)
    before = macvolume.get_volume(name)
    if before is None:
        return (None, None)
    if before >= MIN_CABLE_VOLUME:
        return (before, before)
    print(f"Громкость '{name}' = {before:.3f} — сигнал в Discord будет тихим.")
    if restore and macvolume.set_volume(name, 1.0):
        after = macvolume.get_volume(name)
        print(f"Громкость '{name}' поднята до {after:.3f}.")
        return (before, after)
    return (before, before)


class AudioInjector:
    def __init__(self, vb_name=None, monitor_name=None):
        if os.path.exists(AUDIO_DIR):
            self.path = os.listdir(AUDIO_DIR)
            self.clean()
        else:
            os.mkdir(AUDIO_DIR)
            self.path = []
        self.file = None
        self.data = None
        self.samplerate = None
        self.stream = None
        self.stream2 = None      # monitor stream
        self.data_index = 0
        self.data_index2 = 0     # separate index for monitor stream
        self.playing = False
        self.play_thread = None
        self.active = True
        self.vbidx = None
        self.monitor_idx = None
        self.vb_channels_out = 2
        self.monitor_channels_out = 2
        self.on_finish_callback = None
        self.volume = 1.0
        self._vb_name = vb_name
        self._monitor_name = monitor_name
        self.idx()

    def set_devices(self, vb_name, monitor_name):
        """Update device names and re-index."""
        self._vb_name = vb_name
        self._monitor_name = monitor_name
        self.vbidx = None
        self.monitor_idx = None
        self.idx()

    def clean(self):
        try:
            for i, file in enumerate(self.path):
                if isinstance(file, str) and file.endswith('.mp3'):
                    wav_filename = file.replace('.mp3', '.wav')
                    subprocess.run(['ffmpeg', '-i', os.path.join(AUDIO_DIR, file),
                                    os.path.join(AUDIO_DIR, wav_filename), '-y'],
                                   capture_output=True)
                    self.path[i] = wav_filename
                    os.remove(os.path.join(AUDIO_DIR, file))
        except Exception as e:
            print(e)

    def load_wav(self):
        try:
            self.data, self.samplerate = sf.read(self.file)
            if len(self.data.shape) == 1:
                self.data = self.data.reshape(-1, 1)
            # Resample to 48000 Hz (Discord/BlackHole standard)
            if int(self.samplerate) != 48000:
                self.data = self._resample(self.data, int(self.samplerate), 48000)
                self.samplerate = 48000
            # Normalize volume so audio always plays loud and clear
            peak = np.max(np.abs(self.data))
            if peak > 0.01:
                self.data = (self.data / peak * 0.95).astype(np.float32)
        except Exception as e:
            print(f"Error loading WAV file: {e}")
            return False
        return True

    @staticmethod
    def _lowpass(data, cutoff_norm, taps=127):
        """Фильтр нижних частот на окне Блэкмана.

        cutoff_norm — частота среза в долях исходной частоты дискретизации
        (0.5 = Найквист). Края сигнала дополняются крайними значениями, чтобы
        свёртка не вносила щелчок в начале и конце файла.
        """
        if cutoff_norm >= 0.5 or len(data) < taps:
            return data
        n = np.arange(taps) - (taps - 1) / 2.0
        h = 2 * cutoff_norm * np.sinc(2 * cutoff_norm * n) * np.blackman(taps)
        h /= h.sum()
        pad = taps // 2
        out = np.empty_like(data, dtype=np.float32)
        for ch in range(data.shape[1]):
            col = data[:, ch]
            padded = np.concatenate([np.full(pad, col[0]), col, np.full(pad, col[-1])])
            out[:, ch] = np.convolve(padded, h, mode='same')[pad:len(padded) - pad]
        return out

    @staticmethod
    def _resample(data, src_sr, dst_sr):
        if src_sr == dst_sr:
            return data
        # При понижении частоты всё, что выше новой частоты Найквиста, при
        # прореживании заворачивается вниз и звучит как металлический призвук.
        # Поэтому сначала срезаем эти частоты, и только потом интерполируем.
        if dst_sr < src_sr:
            data = AudioInjector._lowpass(data, 0.45 * dst_sr / src_sr)
        new_len = int(len(data) * dst_sr / src_sr)
        old_idx = np.linspace(0, len(data) - 1, new_len)
        resampled = np.zeros((new_len, data.shape[1]), dtype=np.float32)
        for ch in range(data.shape[1]):
            resampled[:, ch] = np.interp(old_idx, np.arange(len(data)), data[:, ch])
        return resampled

    def _make_callback(self, index_attr):
        """Return a callback that reads from the given index attribute."""
        def callback(outdata, frames, time, status):
            try:
                idx = getattr(self, index_attr)
                if idx is None:
                    outdata[:] = 0
                    return
                ch_out = outdata.shape[1]
                ch_data = self.data.shape[1]
                end = idx + frames
                if end <= len(self.data):
                    chunk = self.data[idx:end]
                else:
                    chunk = self.data[idx:]
                    remaining = frames - len(chunk)
                    chunk = np.vstack([chunk, np.zeros((remaining, ch_data))])

                # Match channel count and apply volume
                if ch_data >= ch_out:
                    outdata[:] = chunk[:, :ch_out] * self.volume
                else:
                    outdata[:, :ch_data] = chunk * self.volume
                    outdata[:, ch_data:] = 0

                new_idx = min(idx + frames, len(self.data))
                setattr(self, index_attr, new_idx)

                if new_idx >= len(self.data):
                    self.playing = False
            except Exception as e:
                print(e)
                outdata[:] = 0
        return callback

    def idx(self):
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                name = device['name']
                if self._vb_name and self._vb_name == name:
                    self.vbidx = i
                    self.vb_channels_out = max(1, device['max_output_channels'])
                if self._monitor_name and self._monitor_name == name:
                    self.monitor_idx = i
                    self.monitor_channels_out = max(1, device['max_output_channels'])
            if self.vbidx is not None:
                print(f"VB device: {self.vbidx} ({self._vb_name}), ch={self.vb_channels_out}")
            if self.monitor_idx is not None:
                print(f"Monitor device: {self.monitor_idx} ({self._monitor_name}), ch={self.monitor_channels_out}")
            return True
        except Exception as e:
            print(e)
            return False

    def play_by_filename(self, filename):
        if self.active:
            self.file = os.path.join(AUDIO_DIR, filename)
            if self.playing:
                try:
                    if self.stream:  self.stream.stop()
                    if self.stream2: self.stream2.stop()
                except Exception:
                    pass
            self.playing = True
            self.data_index = 0
            self.data_index2 = 0
            threading.Thread(target=self._play_file, daemon=True).start()

    def _play_file(self):
        try:
            if not self.load_wav():
                self.playing = False
                return
            sr = int(self.samplerate)
            self.data_index = 0
            self.data_index2 = 0
            total_ms = int(len(self.data) / sr * 1000) + 200

            threads = []

            # Stream 1: virtual cable (Discord)
            if self.vbidx is not None:
                def run_vb():
                    try:
                        ch = min(self.data.shape[1], self.vb_channels_out)
                        with sd.OutputStream(callback=self._make_callback('data_index'),
                                             channels=ch, samplerate=sr,
                                             blocksize=4096,
                                             device=self.vbidx) as st:
                            self.stream = st
                            while self.playing and self.data_index < len(self.data):
                                sd.sleep(50)
                    except Exception as e:
                        print(f"VB stream error: {e}")
                t1 = threading.Thread(target=run_vb, daemon=True)
                threads.append(t1)
                t1.start()

            # Stream 2: monitor (headphones/speakers)
            if self.monitor_idx is not None and self.monitor_idx != self.vbidx:
                def run_monitor():
                    try:
                        ch = min(self.data.shape[1], self.monitor_channels_out)
                        with sd.OutputStream(callback=self._make_callback('data_index2'),
                                             channels=ch, samplerate=sr,
                                             blocksize=4096,
                                             device=self.monitor_idx) as st:
                            self.stream2 = st
                            while self.playing and self.data_index2 < len(self.data):
                                sd.sleep(50)
                    except Exception as e:
                        print(f"Monitor stream error: {e}")
                t2 = threading.Thread(target=run_monitor, daemon=True)
                threads.append(t2)
                t2.start()

            # If no specific devices, fall back to default output
            if not threads:
                def run_default():
                    try:
                        ch = self.data.shape[1]
                        with sd.OutputStream(callback=self._make_callback('data_index'),
                                             channels=ch, samplerate=sr,
                                             blocksize=4096) as st:
                            self.stream = st
                            while self.playing and self.data_index < len(self.data):
                                sd.sleep(50)
                    except Exception as e:
                        print(f"Default stream error: {e}")
                t = threading.Thread(target=run_default, daemon=True)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

        except Exception as e:
            print(f"Error during audio streaming: {e}")
        finally:
            natural_finish = self.data is not None and (
                self.data_index >= len(self.data) or
                self.data_index2 >= len(self.data)
            )
            self.playing = False
            if self.on_finish_callback and natural_finish:
                self.on_finish_callback()

    def pause(self):
        self.playing = False
        try:
            if self.stream:  self.stream.stop()
            if self.stream2: self.stream2.stop()
        except Exception:
            pass

    def resume(self):
        if self.data is None or self.file is None:
            return
        self.playing = True
        threading.Thread(target=self._resume_play, daemon=True).start()

    def _resume_play(self):
        try:
            sr = int(self.samplerate)
            remaining = max(0, len(self.data) - self.data_index)
            total_ms = int(remaining / sr * 1000) + 200

            threads = []
            if self.vbidx is not None:
                def run_vb():
                    try:
                        ch = min(self.data.shape[1], self.vb_channels_out)
                        with sd.OutputStream(callback=self._make_callback('data_index'),
                                             channels=ch, samplerate=sr,
                                             blocksize=4096,
                                             device=self.vbidx) as st:
                            self.stream = st
                            while self.playing and self.data_index < len(self.data):
                                sd.sleep(50)
                    except Exception as e:
                        print(f"VB resume error: {e}")
                t1 = threading.Thread(target=run_vb, daemon=True)
                threads.append(t1)
                t1.start()

            if self.monitor_idx is not None and self.monitor_idx != self.vbidx:
                def run_monitor():
                    try:
                        ch = min(self.data.shape[1], self.monitor_channels_out)
                        with sd.OutputStream(callback=self._make_callback('data_index2'),
                                             channels=ch, samplerate=sr,
                                             blocksize=4096,
                                             device=self.monitor_idx) as st:
                            self.stream2 = st
                            while self.playing and self.data_index2 < len(self.data):
                                sd.sleep(50)
                    except Exception as e:
                        print(f"Monitor resume error: {e}")
                t2 = threading.Thread(target=run_monitor, daemon=True)
                threads.append(t2)
                t2.start()

            for t in threads:
                t.join()
        except Exception as e:
            print(f"Error resuming: {e}")
        finally:
            natural_finish = self.data is not None and (
                self.data_index >= len(self.data) or
                self.data_index2 >= len(self.data)
            )
            self.playing = False
            if self.on_finish_callback and natural_finish:
                self.on_finish_callback()

    def get_progress(self):
        try:
            if self.data is not None and self.samplerate:
                return (self.data_index or 0, len(self.data))
        except Exception:
            pass
        return (0, 0)

    def seek(self, frac):
        try:
            if self.data is not None:
                pos = int(max(0.0, min(1.0, frac)) * len(self.data))
                self.data_index = pos
                self.data_index2 = pos
        except Exception:
            pass

    def stop_current(self):
        self.playing = False
        self.data_index = 0
        self.data_index2 = 0
        try:
            if self.stream:  self.stream.stop()
            if self.stream2: self.stream2.stop()
        except Exception:
            pass

    def reload_audio(self):
        if os.path.exists(AUDIO_DIR):
            self.path = os.listdir(AUDIO_DIR)
            self.clean()

    def stop(self):
        if self.stream is not None:
            self.stream.abort()
        if self.stream2 is not None:
            self.stream2.abort()


class Mic:
    def __init__(self, vbname, micname, gain=5.0):
        self.vbname = vbname
        self.micname = micname
        self.vbidx = None
        self.micidx = None
        self.running = False
        self.streamobj = None
        self.gain = gain
        self.last_error = None
        # Реальное состояние тракта микрофон → кабель: True только пока поток
        # действительно открыт. `running` — лишь «хотим работать», по нему о
        # маршруте судить нельзя (устройство могло не найтись или поток упасть).
        self.streaming = False
        self._gen = 0   # поколение запуска: старый поток не трогает статус нового
        self.vb_channels_out = 0
        self.mic_channels_in = 0

    def set_devices(self, vbname, micname):
        self.vbname = vbname
        self.micname = micname
        self.vbidx = None
        self.micidx = None

    def idx(self):
        self.last_error = None
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if self.vbname and self.vbname == device['name']:
                    self.vbidx = i
                    self.vb_channels_out = device['max_output_channels']
                if self.micname and self.micname == device['name']:
                    self.micidx = i
                    self.mic_channels_in = device['max_input_channels']

            if self.vbidx is None or self.micidx is None:
                missing = []
                if self.vbidx is None: missing.append(f"VB '{self.vbname}'")
                if self.micidx is None: missing.append(f"Mic '{self.micname}'")
                raise ValueError(f"Device not found: {', '.join(missing)}")

            # Защита от петли: если микрофон и виртуальный кабель — одно и то же
            # устройство, поток читает собственный выход и усиливает его на каждом проходе.
            # При gain > 1 это за доли секунды насыщает кабель до предела.
            if self.micidx == self.vbidx or self.micname == self.vbname:
                raise ValueError(
                    f"Петля обратной связи: микрофон и виртуальный кабель — "
                    f"одно устройство ('{self.micname}'). "
                    f"В настройках выбери реальный микрофон."
                )

            print(f"Mic routing: {self.micname} → {self.vbname}")
            return True
        except Exception as e:
            self.last_error = str(e)
            print(f"Mic idx error: {e}")
            return False

    def _apply_gain(self, indata):
        """Поднять уровень микрофона до величины, которую ждёт Discord.

        Сейчас здесь жёсткое ограничение: всё, что вылезло за +-1.0, срезается
        прямо по краю. Это гарантирует отсутствие переполнения, но на пиках
        голоса звучит как треск, а при gain=6 в эти пики упирается почти каждое
        произнесённое слово.

        TODO: заменить на мягкое ограничение — см. пояснение в ответе.
        """
        return np.clip(indata * self.gain, -1.0, 1.0)

    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        boosted = self._apply_gain(indata)
        ch_in = boosted.shape[1]
        ch_out = outdata.shape[1]
        if ch_in <= ch_out:
            outdata[:, :ch_in] = boosted
            outdata[:, ch_in:] = 0
        else:
            outdata[:] = boosted[:, :ch_out]

    def start(self):
        self._gen += 1
        gen = self._gen
        self.streaming = False
        if self.idx():
            self.running = True
            try:
                ch = min(self.mic_channels_in, self.vb_channels_out)
                with sd.Stream(device=(int(self.micidx), int(self.vbidx)),
                               channels=ch,
                               callback=self.audio_callback) as stream:
                    self.streamobj = stream
                    stream.start()
                    if gen == self._gen:
                        self.streaming = True
                    print("Mic routing started.")
                    while self.running and gen == self._gen:
                        sd.sleep(1000)
            except Exception as e:
                if gen == self._gen:
                    self.last_error = str(e)
                print(f"Mic stream error: {e}")
            finally:
                if gen == self._gen:
                    self.streaming = False
        else:
            print("Mic routing skipped — devices not found.")

    def stop(self):
        self.running = False
        self.streaming = False
        if self.streamobj:
            try:
                self.streamobj.stop()
                self.streamobj.close()
            except Exception:
                pass
