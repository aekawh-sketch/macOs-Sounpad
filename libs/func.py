import sounddevice as sd
import soundfile as sf
import os, sys
import threading
import subprocess
from tkinter import messagebox
import numpy as np

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
        except Exception as e:
            print(f"Error loading WAV file: {e}")
            return False
        return True

    @staticmethod
    def _resample(data, src_sr, dst_sr):
        if src_sr == dst_sr:
            return data
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

                # Match channel count
                if ch_data >= ch_out:
                    outdata[:] = chunk[:, :ch_out]
                else:
                    outdata[:, :ch_data] = chunk
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
                            sd.sleep(total_ms)
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
                            sd.sleep(total_ms)
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
                            sd.sleep(total_ms)
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
            self.playing = False
            if self.on_finish_callback:
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
                            sd.sleep(total_ms)
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
                            sd.sleep(total_ms)
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
            self.playing = False
            if self.on_finish_callback:
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
    def __init__(self, vbname, micname):
        self.vbname = vbname
        self.micname = micname
        self.vbidx = None
        self.micidx = None
        self.running = False
        self.streamobj = None

    def set_devices(self, vbname, micname):
        self.vbname = vbname
        self.micname = micname
        self.vbidx = None
        self.micidx = None

    def idx(self):
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

            print(f"Mic routing: {self.micname} → {self.vbname}")
            return True
        except Exception as e:
            print(f"Mic idx error: {e}")
            return False

    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        ch_in = indata.shape[1]
        ch_out = outdata.shape[1]
        if ch_in <= ch_out:
            outdata[:, :ch_in] = indata
            outdata[:, ch_in:] = 0
        else:
            outdata[:] = indata[:, :ch_out]

    def start(self):
        if self.idx():
            self.running = True
            try:
                ch = min(self.mic_channels_in, self.vb_channels_out)
                with sd.Stream(device=(int(self.micidx), int(self.vbidx)),
                               channels=ch,
                               callback=self.audio_callback) as stream:
                    self.streamobj = stream
                    stream.start()
                    print("Mic routing started.")
                    while self.running:
                        sd.sleep(1000)
            except Exception as e:
                print(f"Mic stream error: {e}")
        else:
            print("Mic routing skipped — devices not found.")

    def stop(self):
        self.running = False
        if self.streamobj:
            self.streamobj.stop()
            self.streamobj.close()
