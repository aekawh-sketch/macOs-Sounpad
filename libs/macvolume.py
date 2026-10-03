"""Чтение и установка громкости конкретного аудиоустройства macOS через CoreAudio.

Зачем это нужно: BlackHole (как и любое CoreAudio-устройство) имеет собственный
регулятор громкости, который macOS запоминает между перезапусками. Драйвер
применяет его по кубической кривой, поэтому ползунок на 11% даёт примерно -57 дБ
на весь виртуальный кабель. Внешне это выглядит как "Discord меня почти не слышит",
причём ни настройки Discord, ни громкость внутри приложения не исправляют.
"""

import ctypes
import ctypes.util
from ctypes import POINTER, Structure, byref, c_float, c_uint32, c_void_p

_ca = ctypes.CDLL(ctypes.util.find_library('CoreAudio'))
_cf = ctypes.CDLL(ctypes.util.find_library('CoreFoundation'))


def _fourcc(s):
    return int.from_bytes(s.encode(), 'big')


class _Addr(Structure):
    _fields_ = [('mSelector', c_uint32), ('mScope', c_uint32), ('mElement', c_uint32)]


_SYSTEM = 1
_GLOBAL, _INPUT, _OUTPUT = _fourcc('glob'), _fourcc('inpt'), _fourcc('outp')
_DEVICES, _NAME, _VOLUME = _fourcc('dev#'), _fourcc('lnam'), _fourcc('volm')
_UTF8 = 0x08000100

_ca.AudioObjectGetPropertyDataSize.argtypes = [c_uint32, POINTER(_Addr), c_uint32, c_void_p, POINTER(c_uint32)]
_ca.AudioObjectGetPropertyData.argtypes = [c_uint32, POINTER(_Addr), c_uint32, c_void_p, POINTER(c_uint32), c_void_p]
_ca.AudioObjectSetPropertyData.argtypes = [c_uint32, POINTER(_Addr), c_uint32, c_void_p, c_uint32, c_void_p]
_ca.AudioObjectHasProperty.argtypes = [c_uint32, POINTER(_Addr)]
_ca.AudioObjectIsPropertySettable.argtypes = [c_uint32, POINTER(_Addr), POINTER(c_uint32)]
_cf.CFStringGetCString.argtypes = [c_void_p, ctypes.c_char_p, ctypes.c_long, c_uint32]


def _device_ids():
    addr = _Addr(_DEVICES, _GLOBAL, 0)
    size = c_uint32()
    if _ca.AudioObjectGetPropertyDataSize(_SYSTEM, byref(addr), 0, None, byref(size)) != 0:
        return []
    ids = (c_uint32 * (size.value // 4))()
    if _ca.AudioObjectGetPropertyData(_SYSTEM, byref(addr), 0, None, byref(size), ids) != 0:
        return []
    return list(ids)


def _device_name(dev):
    addr = _Addr(_NAME, _GLOBAL, 0)
    ref = c_void_p()
    size = c_uint32(ctypes.sizeof(c_void_p))
    if _ca.AudioObjectGetPropertyData(dev, byref(addr), 0, None, byref(size), byref(ref)) != 0:
        return None
    buf = ctypes.create_string_buffer(512)
    if not _cf.CFStringGetCString(ref, buf, 512, _UTF8):
        return None
    return buf.value.decode('utf-8', 'replace')


def _find(name):
    """Все CoreAudio-объекты с таким именем (у устройства могут быть отдельные id
    для входа и выхода — например, у AirPods)."""
    return [d for d in _device_ids() if _device_name(d) == name]


def _scopes():
    return (('output', _OUTPUT), ('input', _INPUT))


def get_volume(name):
    """Минимальная громкость устройства по всем областям, либо None если регулятора нет."""
    found = []
    try:
        for dev in _find(name):
            for _, scope in _scopes():
                addr = _Addr(_VOLUME, scope, 0)
                if not _ca.AudioObjectHasProperty(dev, byref(addr)):
                    continue
                val = c_float()
                size = c_uint32(4)
                if _ca.AudioObjectGetPropertyData(dev, byref(addr), 0, None, byref(size), byref(val)) == 0:
                    found.append(val.value)
    except Exception as e:
        print(f"macvolume.get_volume error: {e}")
    return min(found) if found else None


def set_volume(name, value):
    """Выставить громкость устройства (0.0–1.0). Возвращает True, если что-то изменилось."""
    value = max(0.0, min(1.0, float(value)))
    changed = False
    try:
        for dev in _find(name):
            for _, scope in _scopes():
                addr = _Addr(_VOLUME, scope, 0)
                if not _ca.AudioObjectHasProperty(dev, byref(addr)):
                    continue
                settable = c_uint32()
                _ca.AudioObjectIsPropertySettable(dev, byref(addr), byref(settable))
                if not settable.value:
                    continue
                val = c_float(value)
                if _ca.AudioObjectSetPropertyData(dev, byref(addr), 0, None, 4, byref(val)) == 0:
                    changed = True
    except Exception as e:
        print(f"macvolume.set_volume error: {e}")
    return changed
