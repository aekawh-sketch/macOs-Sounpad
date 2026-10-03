"""Дизайн-токены и шрифты редизайна.

Цвета заданы парами (светлая, тёмная) — CustomTkinter сам выбирает нужную по
текущему режиму оформления, поэтому переключатель темы продолжает работать без
единой правки в местах использования.

Тёмная палитра взята из задания один в один; светлая построена на тех же ролях.
"""

import ctypes
import ctypes.util
import os
from ctypes import c_bool, c_long, c_uint32, c_void_p

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _find_font_dir():
    """Каталог со шрифтами и в исходниках, и внутри собранного .app.

    py2app кладёт данные в Contents/Resources и сообщает путь через
    переменную окружения RESOURCEPATH, а в исходниках шрифты лежат рядом с
    кодом. Берём первый существующий вариант.
    """
    candidates = []
    res = os.environ.get('RESOURCEPATH')
    if res:
        candidates.append(os.path.join(res, 'assets', 'fonts'))
    candidates.append(os.path.join(BASE_DIR, 'assets', 'fonts'))
    candidates.append(os.path.join(os.path.dirname(BASE_DIR), 'assets', 'fonts'))
    for path in candidates:
        if os.path.isdir(path):
            return path
    return candidates[-1]


FONT_DIR = _find_font_dir()

# ── Цвета ───────────────────────────────────────────────────────────────────
# (светлая, тёмная)
TOKENS = {
    "bg":            ("#FAFAFB", "#111113"),
    "bg_deep":       ("#F1F1F4", "#0B0B0D"),
    "surface":       ("#FFFFFF", "#18181B"),
    "surface_2":     ("#ECECEF", "#1E1E22"),
    "surface_3":     ("#DEDEE3", "#2A2A30"),
    "border":        ("#E4E4E8", "#222226"),
    "border_strong": ("#D2D2D9", "#2E2E34"),
    "text":          ("#18181B", "#EDEDEF"),
    "text_2":        ("#52525B", "#B4B4BC"),
    "muted":         ("#8C8C96", "#8C8C96"),
    "accent":        ("#FF6A3D", "#FF6A3D"),
    "accent_hover":  ("#FF8A63", "#FF8A63"),
    "on_accent":     ("#1A0A04", "#1A0A04"),
    "star":          ("#E8A300", "#FFC43D"),
    "star_empty":    ("#B9B9C2", "#5C5C66"),
    "ok":            ("#2E9E5B", "#5FD68A"),
    "group_dot":     ("#5B7CFF", "#7C9CFF"),
    "danger":        ("#DC2626", "#F87171"),
    "transparent":   ("transparent", "transparent"),
}


def c(name):
    """Пара цветов для виджетов CustomTkinter."""
    return TOKENS[name]


def hexc(name, mode=None):
    """Один конкретный hex — для Canvas и PIL, которые пары не понимают."""
    if mode is None:
        import customtkinter as ctk
        mode = ctk.get_appearance_mode()
    return TOKENS[name][1 if str(mode).lower() == "dark" else 0]


# ── Шрифты ──────────────────────────────────────────────────────────────────
UI = "Onest"              # весь интерфейс
DISPLAY = "Unbounded"     # логотип и заголовки экранов
MONO = "JetBrains Mono"   # длительности, счётчики, клавиши

_FALLBACK = {UI: "Helvetica Neue", DISPLAY: "Helvetica Neue", MONO: "Menlo"}
_registered = False
_available = set()


def register_fonts():
    """Зарегистрировать шрифты только для этого процесса.

    Область kCTFontManagerScopeProcess намеренная: шрифты не попадают в систему
    пользователя и не требуют прав, но видны Tk внутри приложения — включая
    собранный .app, где каталог со шрифтами лежит внутри бандла.
    """
    global _registered
    if _registered:
        return
    _registered = True
    try:
        ct = ctypes.CDLL(ctypes.util.find_library('CoreText'))
        cf = ctypes.CDLL(ctypes.util.find_library('CoreFoundation'))
        cf.CFURLCreateFromFileSystemRepresentation.restype = c_void_p
        cf.CFURLCreateFromFileSystemRepresentation.argtypes = [
            c_void_p, ctypes.c_char_p, c_long, c_bool]
        ct.CTFontManagerRegisterFontsForURL.restype = c_bool
        ct.CTFontManagerRegisterFontsForURL.argtypes = [c_void_p, c_uint32, c_void_p]
        scope_process = 1
        for fname in ("Onest.ttf", "Unbounded.ttf", "JetBrainsMono.ttf"):
            path = os.path.join(FONT_DIR, fname)
            if not os.path.exists(path):
                print(f"[theme] шрифт не найден: {path}")
                continue
            raw = path.encode('utf-8')
            url = cf.CFURLCreateFromFileSystemRepresentation(None, raw, len(raw), False)
            if not ct.CTFontManagerRegisterFontsForURL(url, scope_process, None):
                print(f"[theme] не удалось зарегистрировать {fname}")
    except Exception as e:
        print(f"[theme] регистрация шрифтов не удалась: {e}")


def probe(root):
    """Запомнить, какие семейства Tk реально видит, чтобы молча откатиться на
    системные, если регистрация не сработала."""
    global _available
    try:
        import tkinter.font as tkfont
        _available = set(tkfont.families(root))
    except Exception:
        _available = set()


def family(name):
    if _available and name not in _available:
        return _FALLBACK.get(name, name)
    return name
