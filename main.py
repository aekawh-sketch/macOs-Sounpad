import customtkinter as ctk
import os, threading, json, shutil, sys
import libs.func, libs.recorder
import soundfile as sf
from tkinter import messagebox, filedialog, Menu, simpledialog
from pynput import keyboard
import ctypes, ctypes.util

def _set_app_name(name: str):
    try:
        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('objc'))
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.objc_msgSend.restype = ctypes.c_void_p
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        cls = objc.objc_getClass(b'NSProcessInfo')
        info = objc.objc_msgSend(cls, objc.sel_registerName(b'processInfo'))
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p]
        ns_str = objc.objc_msgSend(
            objc.objc_getClass(b'NSString'),
            objc.sel_registerName(b'stringWithUTF8String:'),
            name.encode('utf-8')
        )
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        objc.objc_msgSend(info, objc.sel_registerName(b'setProcessName:'), ns_str)
    except Exception:
        pass

_set_app_name("Soundpad")

def _is_accessibility_trusted():
    try:
        appsvcs = ctypes.cdll.LoadLibrary(ctypes.util.find_library('ApplicationServices'))
        appsvcs.AXIsProcessTrusted.restype = ctypes.c_bool
        return bool(appsvcs.AXIsProcessTrusted())
    except Exception:
        return False

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_SUPPORT = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Soundpad')
os.makedirs(APP_SUPPORT, exist_ok=True)
AUDIO_DIR = os.path.join(APP_SUPPORT, 'audio')
os.makedirs(AUDIO_DIR, exist_ok=True)
DATA_FILE = os.path.join(APP_SUPPORT, 'soundpad_data.json')
SETTINGS_FILE = os.path.join(APP_SUPPORT, 'settings.json')

MICNAME = 'Микрофон MacBook Pro'
VBNAME_MIC = "BlackHole 2ch"

TRANSLATIONS = {
    "ru": {
        "app_name": "Soundpad", "active": "● Активно",
        "add_sound": "＋  Добавить звук", "collections": "КОЛЛЕКЦИИ",
        "new_group": "＋  Новая группа", "all": "Все", "play": "▶  Играть",
        "move_to_group": "Переместить в группу...", "delete_sound": "Удалить звук",
        "drop_zone": "⬇   Перетащи .wav или .mp3 файлы сюда",
        "no_sounds": "Нет звуков", "no_sounds_group": "В группе «{group}» нет звуков",
        "drop_hint": "Перетащи файлы в нижнюю зону или нажми «+ Добавить звук»",
        "group_name_prompt": "Название группы:", "new_group_title": "Новая группа",
        "delete_group_title": "Удалить группу",
        "delete_group_msg": "Удалить группу «{group}»?\n(Звуки останутся в «Все»)",
        "no_groups": "Нет групп", "no_groups_msg": "Сначала создай группу через «+ Новая группа»",
        "move_group_title": "Переместить в группу", "choose_group": "Выбери группу:",
        "delete_sound_title": "Удалить звук", "delete_sound_msg": "Удалить «{name}»?\nФайл будет удалён с диска.",
        "audio_files": "Аудио", "all_files": "Все файлы", "choose_files": "Выбери звуковые файлы",
        "settings_title": "Настройки", "theme_label": "Тёмная тема", "language_label": "Язык",
        "view_mode": "Вид отображения", "view_grid": "Сетка", "view_list": "Файлы",
        "columns": "Колонок в сетке", "sort_by": "Сортировка",
        "sort_az": "По названию А → Я", "sort_za": "По названию Я → А",
        "sort_new": "Новые первые", "sort_old": "Старые первые",
        "close": "Закрыть", "col_num": "Но.", "col_name": "Название",
        "col_dur": "Длина", "col_key": "Клавиша",
        "audio_devices": "Аудиоустройства", "mic_device": "Микрофон (вход)",
        "vb_device": "Виртуальный кабель (Discord)", "monitor_device": "Мониторинг (ты слышишь)",
        "profiles": "Профили", "save_profile": "Сохранить профиль", "load_profile": "Загрузить",
        "profile_name_prompt": "Название профиля:", "profile_name_title": "Новый профиль",
        "delete_profile": "Удалить", "no_device": "— не выбрано —",
        "apply": "Применить", "mic_gain": "Усиление микрофона",
    },
    "en": {
        "app_name": "Soundpad", "active": "● Active",
        "add_sound": "＋  Add Sound", "collections": "COLLECTIONS",
        "new_group": "＋  New Group", "all": "All", "play": "▶  Play",
        "move_to_group": "Move to group...", "delete_sound": "Delete sound",
        "drop_zone": "⬇   Drop .wav or .mp3 files here",
        "no_sounds": "No sounds", "no_sounds_group": "No sounds in «{group}»",
        "drop_hint": "Drop files below or click «+ Add Sound»",
        "group_name_prompt": "Group name:", "new_group_title": "New Group",
        "delete_group_title": "Delete Group",
        "delete_group_msg": "Delete group «{group}»?\n(Sounds will remain in «All»)",
        "no_groups": "No groups", "no_groups_msg": "Create a group first via «+ New Group»",
        "move_group_title": "Move to Group", "choose_group": "Choose group:",
        "delete_sound_title": "Delete Sound", "delete_sound_msg": "Delete «{name}»?\nThe file will be removed from disk.",
        "audio_files": "Audio", "all_files": "All files", "choose_files": "Choose audio files",
        "settings_title": "Settings", "theme_label": "Dark Theme", "language_label": "Language",
        "view_mode": "View mode", "view_grid": "Grid", "view_list": "Files",
        "columns": "Grid columns", "sort_by": "Sort by",
        "sort_az": "Name A → Z", "sort_za": "Name Z → A",
        "sort_new": "Newest first", "sort_old": "Oldest first",
        "close": "Close", "col_num": "No.", "col_name": "Name",
        "col_dur": "Dur.", "col_key": "Key",
        "audio_devices": "Audio Devices", "mic_device": "Microphone (input)",
        "vb_device": "Virtual Cable (Discord)", "monitor_device": "Monitor (you hear)",
        "profiles": "Profiles", "save_profile": "Save Profile", "load_profile": "Load",
        "profile_name_prompt": "Profile name:", "profile_name_title": "New Profile",
        "delete_profile": "Delete", "no_device": "— none —",
        "apply": "Apply", "mic_gain": "Microphone Gain",
    },
    "es": {
        "app_name": "Soundpad", "active": "● Activo",
        "add_sound": "＋  Agregar sonido", "collections": "COLECCIONES",
        "new_group": "＋  Nuevo grupo", "all": "Todo", "play": "▶  Reproducir",
        "move_to_group": "Mover al grupo...", "delete_sound": "Eliminar sonido",
        "drop_zone": "⬇   Arrastra archivos .wav o .mp3 aquí",
        "no_sounds": "Sin sonidos", "no_sounds_group": "Sin sonidos en «{group}»",
        "drop_hint": "Arrastra archivos abajo o pulsa «+ Agregar sonido»",
        "group_name_prompt": "Nombre del grupo:", "new_group_title": "Nuevo grupo",
        "delete_group_title": "Eliminar grupo",
        "delete_group_msg": "¿Eliminar grupo «{group}»?\n(Los sonidos permanecerán en «Todo»)",
        "no_groups": "Sin grupos", "no_groups_msg": "Crea un grupo primero",
        "move_group_title": "Mover al grupo", "choose_group": "Elige un grupo:",
        "delete_sound_title": "Eliminar sonido", "delete_sound_msg": "¿Eliminar «{name}»?\nEl archivo se borrará del disco.",
        "audio_files": "Audio", "all_files": "Todos los archivos", "choose_files": "Elige archivos de audio",
        "settings_title": "Configuración", "theme_label": "Tema oscuro", "language_label": "Idioma",
        "view_mode": "Vista", "view_grid": "Cuadrícula", "view_list": "Archivos",
        "columns": "Columnas", "sort_by": "Ordenar por",
        "sort_az": "Nombre A → Z", "sort_za": "Nombre Z → A",
        "sort_new": "Más nuevos primero", "sort_old": "Más antiguos primero",
        "close": "Cerrar", "col_num": "No.", "col_name": "Nombre",
        "col_dur": "Dur.", "col_key": "Tecla",
        "audio_devices": "Dispositivos de audio", "mic_device": "Micrófono (entrada)",
        "vb_device": "Cable virtual (Discord)", "monitor_device": "Monitor (tú escuchas)",
        "profiles": "Perfiles", "save_profile": "Guardar perfil", "load_profile": "Cargar",
        "profile_name_prompt": "Nombre del perfil:", "profile_name_title": "Nuevo perfil",
        "delete_profile": "Eliminar", "no_device": "— ninguno —",
        "apply": "Aplicar", "mic_gain": "Ganancia del micrófono",
    },
    "de": {
        "app_name": "Soundpad", "active": "● Aktiv",
        "add_sound": "＋  Sound hinzufügen", "collections": "SAMMLUNGEN",
        "new_group": "＋  Neue Gruppe", "all": "Alle", "play": "▶  Abspielen",
        "move_to_group": "In Gruppe verschieben...", "delete_sound": "Sound löschen",
        "drop_zone": "⬇   .wav oder .mp3 Dateien hierher ziehen",
        "no_sounds": "Keine Sounds", "no_sounds_group": "Keine Sounds in «{group}»",
        "drop_hint": "Dateien unten ablegen oder «+ Sound hinzufügen» klicken",
        "group_name_prompt": "Gruppenname:", "new_group_title": "Neue Gruppe",
        "delete_group_title": "Gruppe löschen",
        "delete_group_msg": "Gruppe «{group}» löschen?\n(Sounds bleiben in «Alle»)",
        "no_groups": "Keine Gruppen", "no_groups_msg": "Erstelle zuerst eine Gruppe",
        "move_group_title": "In Gruppe verschieben", "choose_group": "Gruppe wählen:",
        "delete_sound_title": "Sound löschen", "delete_sound_msg": "«{name}» löschen?\nDie Datei wird von der Festplatte entfernt.",
        "audio_files": "Audio", "all_files": "Alle Dateien", "choose_files": "Audiodateien wählen",
        "settings_title": "Einstellungen", "theme_label": "Dunkles Design", "language_label": "Sprache",
        "view_mode": "Ansicht", "view_grid": "Raster", "view_list": "Dateien",
        "columns": "Spalten", "sort_by": "Sortieren nach",
        "sort_az": "Name A → Z", "sort_za": "Name Z → A",
        "sort_new": "Neueste zuerst", "sort_old": "Älteste zuerst",
        "close": "Schließen", "col_num": "Nr.", "col_name": "Name",
        "col_dur": "Dauer", "col_key": "Taste",
        "audio_devices": "Audiogeräte", "mic_device": "Mikrofon (Eingang)",
        "vb_device": "Virtuelles Kabel (Discord)", "monitor_device": "Monitor (du hörst)",
        "profiles": "Profile", "save_profile": "Profil speichern", "load_profile": "Laden",
        "profile_name_prompt": "Profilname:", "profile_name_title": "Neues Profil",
        "delete_profile": "Löschen", "no_device": "— keins —",
        "apply": "Anwenden", "mic_gain": "Mikrofonverstärkung",
    },
    "zh": {
        "app_name": "Soundpad", "active": "● 已激活",
        "add_sound": "＋  添加声音", "collections": "收藏夹",
        "new_group": "＋  新建分组", "all": "全部", "play": "▶  播放",
        "move_to_group": "移动到分组...", "delete_sound": "删除声音",
        "drop_zone": "⬇   将 .wav 或 .mp3 文件拖到这里",
        "no_sounds": "没有声音", "no_sounds_group": "«{group}» 中没有声音",
        "drop_hint": "将文件拖到下方或点击「+ 添加声音」",
        "group_name_prompt": "分组名称：", "new_group_title": "新建分组",
        "delete_group_title": "删除分组",
        "delete_group_msg": "删除分组 «{group}»？\n（声音将保留在「全部」中）",
        "no_groups": "没有分组", "no_groups_msg": "请先通过「+ 新建分组」创建分组",
        "move_group_title": "移动到分组", "choose_group": "选择分组：",
        "delete_sound_title": "删除声音", "delete_sound_msg": "删除 «{name}»？\n文件将从磁盘中删除。",
        "audio_files": "音频", "all_files": "所有文件", "choose_files": "选择音频文件",
        "settings_title": "设置", "theme_label": "深色主题", "language_label": "语言",
        "view_mode": "显示方式", "view_grid": "网格", "view_list": "文件",
        "columns": "网格列数", "sort_by": "排序方式",
        "sort_az": "名称 A → Z", "sort_za": "名称 Z → A",
        "sort_new": "最新优先", "sort_old": "最旧优先",
        "close": "关闭", "col_num": "序", "col_name": "名称",
        "col_dur": "时长", "col_key": "快捷键",
        "audio_devices": "音频设备", "mic_device": "麦克风（输入）",
        "vb_device": "虚拟线缆（Discord）", "monitor_device": "监听（你听到的）",
        "profiles": "配置文件", "save_profile": "保存配置", "load_profile": "加载",
        "profile_name_prompt": "配置名称：", "profile_name_title": "新建配置",
        "delete_profile": "删除", "no_device": "— 未选择 —",
        "apply": "应用", "mic_gain": "麦克风增益",
    },
}

LANG_NAMES = {
    "ru": "🇷🇺  Русский", "en": "🇬🇧  English",
    "es": "🇪🇸  Español", "de": "🇩🇪  Deutsch", "zh": "🇨🇳  中文",
}


def load_settings():
    defaults = {
        "theme": "dark", "language": "ru", "view": "list", "columns": 4, "sort": "az",
        "profiles": {},
        "active_profile": "",
        "mic_device": "Микрофон MacBook Pro",
        "vb_device": "BlackHole 2ch",
        "monitor_device": "AirPods Max (Максим)",
    }
    if os.path.exists(SETTINGS_FILE):
        saved = json.load(open(SETTINGS_FILE))
        defaults.update(saved)
    return defaults


def save_settings(s):
    json.dump(s, open(SETTINGS_FILE, 'w'))


def load_data():
    if os.path.exists(DATA_FILE):
        return json.load(open(DATA_FILE, encoding='utf-8'))
    return {"groups": {}}


def save_data(data):
    json.dump(data, open(DATA_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


def get_all_sounds():
    if os.path.exists(AUDIO_DIR):
        return sorted([f for f in os.listdir(AUDIO_DIR) if f.lower().endswith(('.wav', '.mp3'))])
    return []


def get_duration(filename):
    try:
        path = os.path.join(AUDIO_DIR, filename)
        info = sf.info(path)
        secs = int(info.duration)
        return f"{secs // 60}:{secs % 60:02d}"
    except Exception:
        return "—"


def fmt_time(samples, samplerate):
    if not samplerate or samplerate == 0:
        return "0:00"
    secs = int(samples / samplerate)
    return f"{secs // 60}:{secs % 60:02d}"


# ── Sound card (grid view) ──────────────────────────────────────────────────

class SoundCard(ctk.CTkFrame):
    def __init__(self, parent, filename, on_play, on_stop, on_move, on_delete, t, is_playing=False, **kwargs):
        super().__init__(parent, corner_radius=12, **kwargs)
        name = filename.rsplit('.', 1)[0]

        icon = ctk.CTkLabel(self, text="🎵" if is_playing else "🔊",
                             font=ctk.CTkFont(size=24))
        icon.pack(pady=(14, 4))

        name_label = ctk.CTkLabel(self, text=name, font=ctk.CTkFont(size=11),
                                   wraplength=140, justify="center",
                                   text_color=("gray20", "gray90"))
        name_label.pack(pady=(0, 4), padx=8)

        dur_label = ctk.CTkLabel(self, text=get_duration(filename),
                                  font=ctk.CTkFont(size=10),
                                  text_color=("gray50", "gray55"))
        dur_label.pack(pady=(0, 8))

        if is_playing:
            ctk.CTkButton(self, text="■  Стоп", height=30,
                          fg_color=("#dc2626", "#b91c1c"), hover_color=("#b91c1c", "#991b1b"),
                          command=on_stop, font=ctk.CTkFont(size=12)).pack(pady=(0, 10), padx=10, fill="x")

        click_targets = [self, icon, name_label, dur_label]
        for w in click_targets:
            w.bind("<Button-1>", lambda e, f=filename: on_play(f))
            w.bind("<Enter>", lambda e: self.configure(fg_color=("gray74", "gray28")))
            w.bind("<Leave>", lambda e: self.configure(fg_color=("gray82", "#1e293b")))
            w.bind("<Button-2>", lambda e, f=filename: _show_ctx(e, self, f, on_move, on_delete, t))


# ── Table row (list view) ───────────────────────────────────────────────────

class FileRow(ctk.CTkFrame):
    def __init__(self, parent, num, filename, on_play, on_stop, on_move, on_delete, on_bind, t,
                 hotkey="", is_playing=False, **kwargs):
        bg_play  = ("#1d4ed8", "#1e3a8a")
        bg_norm  = ("gray93", "#1a2332")
        bg_hover = ("gray85", "#243b55")
        super().__init__(parent, corner_radius=0,
                         fg_color=bg_play if is_playing else bg_norm, **kwargs)
        self._bg_norm  = bg_norm
        self._bg_hover = bg_hover
        self._bg_play  = bg_play
        self._is_playing = is_playing

        name = filename.rsplit('.', 1)[0]
        txt_color = ("white", "white") if is_playing else ("gray15", "gray90")
        dim_color = ("gray80", "gray70") if is_playing else ("gray50", "gray55")

        # Number column
        num_lbl = ctk.CTkLabel(self, text=str(num), width=36,
                                font=ctk.CTkFont(size=12),
                                text_color=dim_color, anchor="center")
        num_lbl.pack(side="left", padx=(6, 0), pady=10)

        # Play indicator
        icon_lbl = ctk.CTkLabel(self, text="▶" if is_playing else "",
                                 width=20, font=ctk.CTkFont(size=11),
                                 text_color=("white", "white") if is_playing else ("gray70", "gray50"))
        icon_lbl.pack(side="left", padx=(2, 4), pady=10)

        # Name (expands)
        name_lbl = ctk.CTkLabel(self, text=name, anchor="w",
                                  font=ctk.CTkFont(size=13, weight="bold" if is_playing else "normal"),
                                  text_color=txt_color)
        name_lbl.pack(side="left", fill="x", expand=True, pady=10)

        # Duration
        dur_lbl = ctk.CTkLabel(self, text=get_duration(filename), width=48,
                                font=ctk.CTkFont(size=12), text_color=dim_color, anchor="center")
        dur_lbl.pack(side="right", padx=(0, 8), pady=10)

        # Hotkey bind button
        key_btn = ctk.CTkButton(
            self, text=hotkey if hotkey else "＋",
            width=48, height=26, corner_radius=4,
            fg_color=("#2563eb", "#1d4ed8") if hotkey else ("gray78", "gray28"),
            hover_color=("#1d4ed8", "#1e40af") if hotkey else ("gray68", "gray38"),
            text_color=("white", "white"),
            font=ctk.CTkFont(size=11),
            command=lambda f=filename: on_bind(f)
        )
        key_btn.pack(side="right", padx=(0, 4), pady=10)
        key_btn.bind("<Button-1>", lambda e: "break")
        key_btn.bind("<Button-2>", lambda e, f=filename: on_bind(f, clear=True))

        # Stop button (only when playing)
        if is_playing:
            stop_btn = ctk.CTkButton(self, text="■", width=32, height=26,
                                      fg_color=("#dc2626", "#991b1b"),
                                      hover_color=("#b91c1c", "#7f1d1d"),
                                      command=on_stop, font=ctk.CTkFont(size=12),
                                      corner_radius=4)
            stop_btn.pack(side="right", padx=(0, 6), pady=10)
            stop_btn.bind("<Button-1>", lambda e: "break")

        # Bind click-to-play on entire row
        for w in [self, num_lbl, icon_lbl, name_lbl, dur_lbl]:
            w.bind("<Button-1>", lambda e, f=filename: on_play(f))
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)
            w.bind("<Button-2>", lambda e, f=filename: _show_ctx(e, self, f, on_move, on_delete, t))

    def _on_enter(self, e):
        if not self._is_playing:
            self.configure(fg_color=self._bg_hover)

    def _on_leave(self, e):
        if not self._is_playing:
            self.configure(fg_color=self._bg_norm)


def _show_ctx(event, widget, filename, on_move, on_delete, t):
    menu = Menu(widget, tearoff=0)
    menu.add_command(label=t("move_to_group"), command=lambda: on_move(filename))
    menu.add_separator()
    menu.add_command(label=t("delete_sound"), command=lambda: on_delete(filename))
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


# ── Settings window ─────────────────────────────────────────────────────────

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, settings, callbacks, t):
        super().__init__(parent)
        self.title(t("settings_title"))
        self.geometry("380x720")
        self.resizable(False, False)
        self.grab_set()
        self.settings = settings
        self.cb = callbacks
        self.t = t
        self._build()

    def _row(self, parent, label):
        f = ctk.CTkFrame(parent, fg_color=("gray88", "gray20"), corner_radius=10)
        f.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=13)).pack(side="left", padx=14, pady=12)
        return f

    def _build(self):
        # Scrollable content area, close button pinned at bottom
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=(8, 0))
        main = ctk.CTkFrame(scroll, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=18, pady=(10, 18))

        ctk.CTkLabel(main, text=self.t("settings_title"),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 12))

        r = self._row(main, self.t("theme_label"))
        sw = ctk.CTkSwitch(r, text="", command=self._toggle_theme, onvalue="dark", offvalue="light")
        (sw.select if self.settings.get("theme") == "dark" else sw.deselect)()
        sw.pack(side="right", padx=14)
        self._theme_sw = sw

        r = self._row(main, self.t("language_label"))
        cur_lang = LANG_NAMES.get(self.settings.get("language", "ru"), "🇷🇺  Русский")
        m = ctk.CTkOptionMenu(r, values=list(LANG_NAMES.values()), command=self._change_lang, width=140)
        m.set(cur_lang)
        m.pack(side="right", padx=14)

        r = self._row(main, self.t("view_mode"))
        seg = ctk.CTkSegmentedButton(
            r, values=[self.t("view_grid"), self.t("view_list")],
            command=self._change_view, width=160
        )
        seg.set(self.t("view_grid") if self.settings.get("view", "list") == "grid" else self.t("view_list"))
        seg.pack(side="right", padx=14)
        self._view_seg = seg

        self._cols_row = self._row(main, self.t("columns"))
        cols_val = self.settings.get("columns", 4)
        self._cols_label = ctk.CTkLabel(self._cols_row, text=str(cols_val),
                                         font=ctk.CTkFont(size=13, weight="bold"), width=24)
        self._cols_label.pack(side="right", padx=(0, 14))
        sl = ctk.CTkSlider(self._cols_row, from_=2, to=6, number_of_steps=4,
                           command=self._change_cols, width=110)
        sl.set(cols_val)
        sl.pack(side="right", padx=4)
        if self.settings.get("view", "list") == "list":
            self._cols_row.pack_forget()

        r = self._row(main, self.t("sort_by"))
        sort_map = {
            "az":  self.t("sort_az"), "za":  self.t("sort_za"),
            "new": self.t("sort_new"), "old": self.t("sort_old"),
        }
        self._sort_map = sort_map
        cur_sort = sort_map.get(self.settings.get("sort", "az"), self.t("sort_az"))
        sm = ctk.CTkOptionMenu(r, values=list(sort_map.values()), command=self._change_sort, width=160)
        sm.set(cur_sort)
        sm.pack(side="right", padx=14)

        # ── Audio Devices ──
        ctk.CTkLabel(main, text=self.t("audio_devices"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(14, 4))

        devices = libs.func.list_devices()
        input_names  = [self.t("no_device")] + [d["name"] for d in devices if d["inputs"] > 0]
        output_names = [self.t("no_device")] + [d["name"] for d in devices if d["outputs"] > 0]

        def device_block(label_key, setting_key, names):
            f = ctk.CTkFrame(main, fg_color=("gray88", "gray20"), corner_radius=10)
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=self.t(label_key),
                         font=ctk.CTkFont(size=12), text_color=("gray50", "gray55"),
                         anchor="w").pack(fill="x", padx=14, pady=(10, 2))
            cur = self.settings.get(setting_key, self.t("no_device"))
            if cur not in names:
                cur = self.t("no_device")
            m = ctk.CTkOptionMenu(f, values=names,
                                   command=lambda v, k=setting_key: self._set_device(k, v),
                                   anchor="w")
            m.set(cur)
            m.pack(fill="x", padx=10, pady=(0, 10))

        device_block("mic_device",     "mic_device",     input_names)
        device_block("vb_device",      "vb_device",      output_names)
        device_block("monitor_device", "monitor_device", output_names)

        # ── Mic Gain ──
        gain_frame = ctk.CTkFrame(main, fg_color=("gray88", "gray20"), corner_radius=10)
        gain_frame.pack(fill="x", pady=4)
        gain_header = ctk.CTkFrame(gain_frame, fg_color="transparent")
        gain_header.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(gain_header, text=self.t("mic_gain"),
                     font=ctk.CTkFont(size=12), text_color=("gray50", "gray55"),
                     anchor="w").pack(side="left")
        gain_val = self.settings.get("mic_gain", 5.0)
        self._gain_label = ctk.CTkLabel(gain_header,
                                        text=f"×{gain_val:.1f}",
                                        font=ctk.CTkFont(size=12, weight="bold"), width=36)
        self._gain_label.pack(side="right")
        gain_sl = ctk.CTkSlider(gain_frame, from_=1.0, to=10.0, number_of_steps=18,
                                command=self._change_gain)
        gain_sl.set(gain_val)
        gain_sl.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(main, text=self.t("apply"), height=40,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=("#2563eb", "#1d4ed8"),
                      command=self._apply_and_close).pack(fill="x", pady=(8, 0))

        # ── Profiles ──
        prof_header = ctk.CTkFrame(main, fg_color="transparent")
        prof_header.pack(fill="x", pady=(18, 4))
        ctk.CTkLabel(prof_header, text=self.t("profiles"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(prof_header, text="＋", width=32, height=28,
                      fg_color=("#2563eb", "#1d4ed8"),
                      font=ctk.CTkFont(size=16),
                      command=self._save_profile).pack(side="right")

        self._profiles_list = ctk.CTkScrollableFrame(main, fg_color=("gray88", "gray20"),
                                                       corner_radius=10, height=120)
        self._profiles_list.pack(fill="x")
        self._render_profiles()

        # ── Close ──
        ctk.CTkFrame(self, height=1, fg_color=("gray80", "gray25"),
                     corner_radius=0).pack(fill="x", side="bottom")
        ctk.CTkButton(self, text=self.t("close"), height=52,
                      corner_radius=0,
                      fg_color=("#e11d48", "#be123c"),
                      hover_color=("#be123c", "#9f1239"),
                      text_color="white",
                      font=ctk.CTkFont(size=15, weight="bold"),
                      command=self.destroy).pack(fill="x", side="bottom")

    def _toggle_theme(self):
        val = self._theme_sw.get()
        self.settings["theme"] = val
        save_settings(self.settings)
        self.cb["theme"](val)

    def _change_lang(self, name):
        code = next((k for k, v in LANG_NAMES.items() if v == name), "ru")
        self.settings["language"] = code
        save_settings(self.settings)
        self.cb["lang"](code)
        self.destroy()

    def _change_view(self, val):
        is_grid = (val == self.t("view_grid"))
        self.settings["view"] = "grid" if is_grid else "list"
        save_settings(self.settings)
        if is_grid:
            self._cols_row.pack(fill="x", pady=5)
        else:
            self._cols_row.pack_forget()
        self.cb["view"]()

    def _change_cols(self, val):
        self.settings["columns"] = int(val)
        self._cols_label.configure(text=str(int(val)))
        save_settings(self.settings)
        self.cb["view"]()

    def _change_sort(self, val):
        code = next((k for k, v in self._sort_map.items() if v == val), "az")
        self.settings["sort"] = code
        save_settings(self.settings)
        self.cb["view"]()

    def _set_device(self, key, val):
        no_dev = self.t("no_device")
        self.settings[key] = "" if val == no_dev else val
        save_settings(self.settings)

    def _change_gain(self, val):
        val = round(float(val), 1)
        self.settings["mic_gain"] = val
        self._gain_label.configure(text=f"×{val:.1f}")
        save_settings(self.settings)

    def _apply_and_close(self):
        save_settings(self.settings)
        self.cb["devices"]()
        self.destroy()

    def _render_profiles(self):
        for w in self._profiles_list.winfo_children():
            w.destroy()
        profiles = self.settings.get("profiles", {})
        if not profiles:
            ctk.CTkLabel(self._profiles_list, text="—",
                         text_color=("gray55", "gray50"),
                         font=ctk.CTkFont(size=12)).pack(pady=10)
            return
        active = self.settings.get("active_profile", "")
        for name in profiles:
            row = ctk.CTkFrame(self._profiles_list, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=3)
            is_active = name == active
            ctk.CTkLabel(row, text=("▶  " if is_active else "    ") + name,
                         font=ctk.CTkFont(size=13, weight="bold" if is_active else "normal"),
                         text_color=("#1d4ed8", "#60a5fa") if is_active else ("gray20", "gray85"),
                         anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text=self.t("load_profile"), width=70, height=26,
                          fg_color=("#2563eb", "#1d4ed8"),
                          font=ctk.CTkFont(size=11),
                          command=lambda n=name: self._load_profile(n)).pack(side="right", padx=(4, 0))
            ctk.CTkButton(row, text="✕", width=28, height=26,
                          fg_color=("gray75", "gray35"),
                          text_color=("gray30", "gray80"),
                          font=ctk.CTkFont(size=11),
                          command=lambda n=name: self._delete_profile(n)).pack(side="right")

    def _save_profile(self):
        name = simpledialog.askstring(
            self.t("profile_name_title"),
            self.t("profile_name_prompt"),
            parent=self
        )
        if not name or not name.strip():
            return
        name = name.strip()
        if "profiles" not in self.settings:
            self.settings["profiles"] = {}
        self.settings["profiles"][name] = {
            "mic_device":     self.settings.get("mic_device", ""),
            "vb_device":      self.settings.get("vb_device", ""),
            "monitor_device": self.settings.get("monitor_device", ""),
        }
        self.settings["active_profile"] = name
        try:
            save_settings(self.settings)
        except Exception as e:
            print(f"Error saving profile: {e}")
        try:
            self._render_profiles()
        except Exception as e:
            print(f"Error rendering profiles: {e}")

    def _load_profile(self, name):
        profile = self.settings.get("profiles", {}).get(name)
        if not profile:
            return
        self.settings.update(profile)
        self.settings["active_profile"] = name
        save_settings(self.settings)
        self.cb["devices"]()
        self.destroy()

    def _delete_profile(self, name):
        self.settings.get("profiles", {}).pop(name, None)
        if self.settings.get("active_profile") == name:
            self.settings["active_profile"] = ""
        save_settings(self.settings)
        self._render_profiles()


# ── Main app ────────────────────────────────────────────────────────────────

class SoundpadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Soundpad")
        self.root.geometry("980x680")
        self.root.minsize(720, 520)

        self.data = load_data()
        self.settings = load_settings()
        self.lang = self.settings.get("language", "ru")
        self._recording_for = None

        ctk.set_appearance_mode(self.settings.get("theme", "dark"))
        ctk.set_default_color_theme("blue")

        self.current_group = self.t("all")
        self.playing_filename = None
        self.paused = False
        self._refresh_timer = None
        self._seeking = False
        self._build_ui()
        self._setup_dnd()
        self._start_progress_loop()

    def t(self, key, **kw):
        text = TRANSLATIONS.get(self.lang, TRANSLATIONS["ru"]).get(key, key)
        return text.format(**kw) if kw else text

    def _build_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self._build_topbar()
        self._build_playbar()
        self._build_sidebar()
        self._build_content()

    # ── Top bar (logo + controls) ──────────────────────────────────────────
    def _build_topbar(self):
        bar = ctk.CTkFrame(self.root, height=50, corner_radius=0,
                           fg_color=("gray95", "#0d1117"))
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="  🎵  Soundpad",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=("#1d4ed8", "#60a5fa")).grid(row=0, column=0, padx=16, pady=12, sticky="w")

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.grid(row=0, column=2, padx=12, pady=8)

        ctk.CTkButton(right, text="⚙", width=36, height=30,
                      fg_color=("gray80", "gray30"), hover_color=("gray70", "gray40"),
                      text_color=("gray20", "gray90"), font=ctk.CTkFont(size=18),
                      command=self._open_settings).pack(side="left", padx=4)

        ctk.CTkButton(right, text=self.t("add_sound"), height=30,
                      fg_color=("#2563eb", "#1d4ed8"), hover_color=("#1d4ed8", "#1e40af"),
                      command=self._add_sound_dialog).pack(side="left", padx=4)

    # ── Playback bar (transport + progress) ───────────────────────────────
    def _build_playbar(self):
        bar = ctk.CTkFrame(self.root, height=48, corner_radius=0,
                           fg_color=("white", "#161b22"),
                           border_width=0)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)

        # separator line at bottom
        sep = ctk.CTkFrame(bar, height=1, fg_color=("gray82", "gray25"), corner_radius=0)
        sep.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)

        # Play/Stop button
        self._play_btn = ctk.CTkButton(bar, text="▶", width=34, height=34,
                                        fg_color=("#e11d48", "#be123c"),
                                        hover_color=("#be123c", "#9f1239"),
                                        font=ctk.CTkFont(size=16),
                                        command=self._transport_play_stop)
        self._play_btn.place(x=10, rely=0.5, anchor="w")

        # Pause button
        self._pause_btn = ctk.CTkButton(bar, text="⏸", width=34, height=34,
                                         fg_color=("gray80", "gray30"),
                                         hover_color=("gray70", "gray40"),
                                         text_color=("gray30", "gray80"),
                                         font=ctk.CTkFont(size=16),
                                         command=self._transport_pause)
        self._pause_btn.place(x=50, rely=0.5, anchor="w")

        # Current time
        self._cur_time = ctk.CTkLabel(bar, text="0:00",
                                       font=ctk.CTkFont(size=12, weight="bold"),
                                       text_color=("#e11d48", "#f87171"),
                                       width=40)
        self._cur_time.place(x=96, rely=0.5, anchor="w")

        # Progress slider
        self._progress = ctk.CTkSlider(bar, from_=0, to=1,
                                        button_color=("#e11d48", "#f87171"),
                                        button_hover_color=("#be123c", "#ef4444"),
                                        progress_color=("#e11d48", "#b91c1c"),
                                        fg_color=("gray80", "gray30"),
                                        height=14,
                                        command=self._on_seek_move)
        self._progress.set(0)
        self._progress.place(x=142, rely=0.5, anchor="w", relwidth=0.52)
        self._progress.bind("<ButtonPress-1>",   self._on_seek_start)
        self._progress.bind("<ButtonRelease-1>", self._on_seek_end)

        # Total time
        self._tot_time = ctk.CTkLabel(bar, text="0:00",
                                       font=ctk.CTkFont(size=12),
                                       text_color=("gray45", "gray55"),
                                       width=40)
        self._tot_time.place(relx=0.62, rely=0.5, anchor="w", x=10)

        # Now-playing label
        self._now_label = ctk.CTkLabel(bar, text="",
                                        font=ctk.CTkFont(size=11, slant="italic"),
                                        text_color=("gray50", "gray50"))
        self._now_label.place(relx=0.67, rely=0.5, anchor="w")

    def _transport_play_stop(self):
        """Red button: stop when active, replay last when idle."""
        if self.playing_filename:
            self._stop_sound()
        elif self._last_played:
            self._play_sound(self._last_played)

    def _transport_pause(self):
        """Gray button: pause when playing, resume when paused."""
        if self.playing_filename and not self.paused:
            self.paused = True
            aud.pause()
            self._pause_btn.configure(text="▶", fg_color=("gray70", "gray40"),
                                       text_color=("gray20", "white"))
            self._play_btn.configure(text="■")
        elif self.paused and self.playing_filename:
            self.paused = False
            self._pause_btn.configure(text="⏸", fg_color=("gray80", "gray30"),
                                       text_color=("gray30", "gray80"))
            self._play_btn.configure(text="■")
            aud.resume()

    def _on_seek_start(self, e):
        self._seeking = True

    def _on_seek_move(self, val):
        if self._seeking and aud.data is not None:
            aud.seek(float(val))

    def _on_seek_end(self, e):
        self._seeking = False
        val = self._progress.get()
        if aud.data is not None:
            aud.seek(float(val))

    def _start_progress_loop(self):
        self._last_played = None
        self._progress_running = True
        self._tick_progress()

    def _tick_progress(self):
        if not self._progress_running:
            return
        try:
            if self.playing_filename and aud.playing and not self._seeking:
                cur, total = aud.get_progress()
                frac = cur / total if total > 0 else 0
                self._progress.set(frac)
                sr = aud.samplerate or 44100
                self._cur_time.configure(text=fmt_time(cur, sr))
                self._tot_time.configure(text=fmt_time(total, sr))
                self._play_btn.configure(text="■")
            elif self.playing_filename and self.paused:
                self._play_btn.configure(text="■")  # paused but sound loaded
            else:
                if not self.playing_filename:
                    self._play_btn.configure(text="▶")
        except Exception:
            pass
        self.root.after(80, self._tick_progress)

    # ── Sidebar ────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self.root, width=210, corner_radius=0,
                          fg_color=("gray92", "#0d1117"))
        sb.grid(row=2, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(1, weight=1)
        sb.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sb, text=self.t("collections"),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=("gray55", "gray50")).grid(row=0, column=0, padx=14, pady=(18, 6), sticky="w")

        self.groups_scroll = ctk.CTkScrollableFrame(sb, fg_color="transparent",
                                                     scrollbar_button_color=("gray80", "gray30"))
        self.groups_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self.groups_scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkFrame(sb, height=1, fg_color=("gray80", "gray25")).grid(row=2, column=0, sticky="ew", padx=12, pady=4)

        ctk.CTkButton(sb, text=self.t("new_group"), height=34,
                      fg_color="transparent", hover_color=("gray85", "gray22"),
                      anchor="w", text_color=("gray45", "gray60"),
                      command=self._add_group_dialog).grid(row=3, column=0, padx=8, pady=(4, 14), sticky="ew")

        self._refresh_groups()

    # ── Content area ───────────────────────────────────────────────────────
    def _build_content(self):
        self._content = ctk.CTkFrame(self.root, corner_radius=0,
                                      fg_color=("gray97", "#0d1117"))
        self._content.grid(row=2, column=1, sticky="nsew")
        self._content.grid_rowconfigure(1, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        # Table header (list view only, hidden in grid)
        self._table_header = ctk.CTkFrame(self._content, height=30, corner_radius=0,
                                           fg_color=("gray88", "#1a2332"))
        self._table_header.grid(row=0, column=0, sticky="ew")
        self._table_header.grid_propagate(False)
        self._build_table_header()

        self.sounds_scroll = ctk.CTkScrollableFrame(self._content, fg_color="transparent",
                                                     scrollbar_button_color=("gray80", "gray30"))
        self.sounds_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        self.drop_frame = ctk.CTkFrame(self._content, height=46, corner_radius=0,
                                        fg_color=("gray88", "#161b22"),
                                        border_width=1, border_color=("gray78", "gray25"))
        self.drop_frame.grid(row=2, column=0, sticky="ew")
        self.drop_frame.grid_propagate(False)

        self.drop_label = ctk.CTkLabel(self.drop_frame, text=self.t("drop_zone"),
                                        font=ctk.CTkFont(size=11), text_color=("gray55", "gray50"))
        self.drop_label.place(relx=0.5, rely=0.5, anchor="center")

        self.drop_frame.bind("<Button-1>", lambda e: self._add_sound_dialog())
        self.drop_label.bind("<Button-1>", lambda e: self._add_sound_dialog())

        self._refresh_sounds()

    def _build_table_header(self):
        for w in self._table_header.winfo_children():
            w.destroy()
        txt_c = ("gray40", "gray55")
        ctk.CTkLabel(self._table_header, text=self.t("col_num"), width=36,
                     font=ctk.CTkFont(size=11), text_color=txt_c, anchor="center").pack(side="left", padx=(6, 0))
        ctk.CTkLabel(self._table_header, text="", width=22,
                     font=ctk.CTkFont(size=11), text_color=txt_c).pack(side="left")
        ctk.CTkLabel(self._table_header, text=self.t("col_name"),
                     font=ctk.CTkFont(size=11), text_color=txt_c, anchor="w").pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(self._table_header, text=self.t("col_dur"), width=48,
                     font=ctk.CTkFont(size=11), text_color=txt_c, anchor="center").pack(side="right", padx=(0, 8))

        if self.settings.get("view", "list") == "grid":
            self._table_header.grid_remove()
        else:
            self._table_header.grid()

    def _setup_dnd(self):
        if HAS_DND and isinstance(self.root, TkinterDnD.Tk):
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self._on_drop)

    def _on_drop(self, event):
        for f in self.root.tk.splitlist(event.data):
            if f.lower().endswith(('.wav', '.mp3')):
                self._copy_and_add(f)
        self.drop_frame.configure(border_color=("#16a34a", "#4ade80"))
        self.root.after(800, lambda: self.drop_frame.configure(border_color=("gray78", "gray25")))

    def _copy_and_add(self, filepath):
        os.makedirs(AUDIO_DIR, exist_ok=True)
        filename = os.path.basename(filepath)
        dest = os.path.join(AUDIO_DIR, filename)
        if not os.path.exists(dest):
            shutil.copy2(filepath, dest)
        if self.current_group != self.t("all"):
            sounds = self.data.setdefault("groups", {}).setdefault(self.current_group, [])
            if filename not in sounds:
                sounds.append(filename)
            save_data(self.data)
        aud.reload_audio()
        self._refresh_groups()
        self._refresh_sounds()

    def _refresh_groups(self):
        for w in self.groups_scroll.winfo_children():
            w.destroy()

        all_label = self.t("all")
        all_set = set(get_all_sounds())
        groups_data = {all_label: len(all_set)}
        for g, sounds in self.data.get("groups", {}).items():
            groups_data[g] = len([s for s in sounds if s in all_set])

        for g, count in groups_data.items():
            active = g == self.current_group
            row_f = ctk.CTkFrame(self.groups_scroll, fg_color="transparent")
            row_f.pack(fill="x", pady=2)
            row_f.grid_columnconfigure(0, weight=1)

            btn = ctk.CTkButton(row_f, text=f"  {g}", anchor="w", height=36, corner_radius=8,
                                 fg_color=("#dbeafe", "#1e3a5f") if active else "transparent",
                                 text_color=("#1d4ed8", "#93c5fd") if active else ("gray35", "gray65"),
                                 hover_color=("#eff6ff", "#1e3a5f"),
                                 font=ctk.CTkFont(size=13, weight="bold" if active else "normal"),
                                 command=lambda gn=g: self._select_group(gn))
            btn.grid(row=0, column=0, sticky="ew")

            ctk.CTkLabel(row_f, text=str(count), width=26, font=ctk.CTkFont(size=10),
                         fg_color=("#bfdbfe", "#1e3a5f") if active else ("gray80", "gray28"),
                         corner_radius=10,
                         text_color=("#1d4ed8", "#93c5fd") if active else ("gray45", "gray55")
                         ).grid(row=0, column=1, padx=(0, 4))

            if g != all_label:
                btn.bind("<Button-2>", lambda e, gn=g: self._delete_group(gn))

    def _select_group(self, group):
        self.current_group = group
        self._refresh_groups()
        self._refresh_sounds()

    def _get_current_sounds(self):
        all_sounds = get_all_sounds()
        if self.current_group == self.t("all"):
            sounds = all_sounds
        else:
            gs = self.data.get("groups", {}).get(self.current_group, [])
            sounds = [s for s in gs if s in all_sounds]

        sort = self.settings.get("sort", "az")
        if sort == "az":
            return sorted(sounds, key=lambda f: f.lower())
        elif sort == "za":
            return sorted(sounds, key=lambda f: f.lower(), reverse=True)
        elif sort in ("new", "old"):
            reverse = sort == "new"
            return sorted(sounds, key=lambda f: os.path.getmtime(os.path.join(AUDIO_DIR, f)), reverse=reverse)
        return sounds

    def _refresh_sounds(self):
        for w in self.sounds_scroll.winfo_children():
            w.destroy()

        sounds = self._get_current_sounds()

        view = self.settings.get("view", "list")

        # Show/hide table header
        if view == "list":
            self._table_header.grid()
            self._build_table_header()
        else:
            self._table_header.grid_remove()

        if not sounds:
            frame = ctk.CTkFrame(self.sounds_scroll, fg_color="transparent")
            frame.pack(expand=True, fill="both", pady=80)
            ctk.CTkLabel(frame, text="🎵", font=ctk.CTkFont(size=48)).pack()
            ctk.CTkLabel(frame,
                         text=self.t("no_sounds") if self.current_group == self.t("all")
                              else self.t("no_sounds_group", group=self.current_group),
                         font=ctk.CTkFont(size=15), text_color=("gray55", "gray50")).pack(pady=8)
            ctk.CTkLabel(frame, text=self.t("drop_hint"),
                         font=ctk.CTkFont(size=11), text_color=("gray65", "gray45")).pack()
            return

        if view == "list":
            for i, sound in enumerate(sounds):
                playing = sound == self.playing_filename
                hk = self.data.get("hotkeys", {}).get(sound, "")
                row = FileRow(self.sounds_scroll, num=i + 1, filename=sound,
                              on_play=self._play_sound, on_stop=self._stop_sound,
                              on_move=self._move_sound_to_group,
                              on_delete=self._delete_sound,
                              on_bind=self._bind_hotkey,
                              hotkey=hk, t=self.t,
                              is_playing=playing)
                row.pack(fill="x", padx=0, pady=0)
                # alternating rows
                if not playing:
                    alt_bg = ("gray91", "#111827") if i % 2 == 0 else ("gray93", "#1a2332")
                    row.configure(fg_color=alt_bg)
                    row._bg_norm = alt_bg
        else:
            COLS = max(1, self.settings.get("columns", 4))
            for col in range(COLS):
                self.sounds_scroll.grid_columnconfigure(col, weight=1)
            for i, sound in enumerate(sounds):
                r, c = divmod(i, COLS)
                playing = sound == self.playing_filename
                SoundCard(self.sounds_scroll, filename=sound,
                          on_play=self._play_sound, on_stop=self._stop_sound,
                          on_move=self._move_sound_to_group,
                          on_delete=self._delete_sound, t=self.t,
                          is_playing=playing,
                          fg_color=("gray74", "#243b55") if playing else ("gray82", "#1e293b"),
                          width=160
                          ).grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

    def _schedule_refresh(self):
        if self._refresh_timer:
            self.root.after_cancel(self._refresh_timer)
        self._refresh_timer = self.root.after(80, self._refresh_sounds)

    def _play_sound(self, filename):
        if self.playing_filename == filename:
            return
        self.playing_filename = filename
        self._last_played = filename
        aud.on_finish_callback = self._on_sound_finish
        # Reset progress bar
        self._progress.set(0)
        self._cur_time.configure(text="0:00")
        name = filename.rsplit('.', 1)[0]
        self._now_label.configure(text=f"  {name}")
        self._refresh_sounds()
        threading.Thread(target=aud.play_by_filename, args=(filename,), daemon=True).start()

    def _stop_sound(self):
        aud.stop_current()
        self.playing_filename = None
        self.paused = False
        self._progress.set(0)
        self._cur_time.configure(text="0:00")
        self._now_label.configure(text="")
        self._play_btn.configure(text="▶")
        self._pause_btn.configure(text="⏸", fg_color=("gray80", "gray30"),
                                   text_color=("gray30", "gray80"))
        self._refresh_sounds()

    def _on_sound_finish(self):
        self.playing_filename = None
        self.root.after(0, self._on_finish_ui)

    def _on_finish_ui(self):
        self.paused = False
        self._progress.set(0)
        self._cur_time.configure(text="0:00")
        self._now_label.configure(text="")
        self._play_btn.configure(text="▶")
        self._pause_btn.configure(text="⏸", fg_color=("gray80", "gray30"),
                                   text_color=("gray30", "gray80"))
        self._refresh_sounds()

    def _add_sound_dialog(self):
        for f in filedialog.askopenfilenames(
                title=self.t("choose_files"),
                filetypes=[(self.t("audio_files"), "*.wav *.mp3"), (self.t("all_files"), "*.*")]):
            self._copy_and_add(f)

    def _add_group_dialog(self):
        name = simpledialog.askstring(
            self.t("new_group_title"),
            self.t("group_name_prompt"),
            parent=self.root
        )
        if name and name.strip() and name.strip() != self.t("all"):
            groups = self.data.setdefault("groups", {})
            if name.strip() not in groups:
                groups[name.strip()] = []
                save_data(self.data)
                self._refresh_groups()

    def _delete_group(self, group):
        if messagebox.askyesno(self.t("delete_group_title"), self.t("delete_group_msg", group=group)):
            self.data.get("groups", {}).pop(group, None)
            save_data(self.data)
            if self.current_group == group:
                self.current_group = self.t("all")
            self._refresh_groups()
            self._refresh_sounds()

    def _move_sound_to_group(self, filename):
        groups = list(self.data.get("groups", {}).keys())
        if not groups:
            messagebox.showinfo(self.t("no_groups"), self.t("no_groups_msg"))
            return
        win = ctk.CTkToplevel(self.root)
        win.title(self.t("move_group_title"))
        win.geometry(f"260x{60 + len(groups) * 46}")
        win.resizable(False, False)
        win.grab_set()
        ctk.CTkLabel(win, text=self.t("choose_group"), font=ctk.CTkFont(size=13)).pack(pady=(16, 8))
        for g in groups:
            ctk.CTkButton(win, text=g, height=36,
                          command=lambda gn=g: self._do_move(filename, gn, win)).pack(fill="x", padx=20, pady=3)

    def _do_move(self, filename, group, win):
        sounds = self.data.setdefault("groups", {}).setdefault(group, [])
        if filename not in sounds:
            sounds.append(filename)
        save_data(self.data)
        win.destroy()
        self._refresh_groups()
        self._refresh_sounds()

    def _bind_hotkey(self, filename, clear=False):
        if clear:
            self.data.setdefault("hotkeys", {}).pop(filename, None)
            save_data(self.data)
            self._refresh_sounds()
            return
        if self._recording_for:
            return  # already recording
        self._recording_for = filename
        self._refresh_sounds()
        # Show a small overlay hint
        self._record_hint = ctk.CTkLabel(
            self.root, text="  Нажми клавишу для бинда  (Esc — отмена)  ",
            fg_color=("#f59e0b", "#d97706"), text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8
        )
        self._record_hint.place(relx=0.5, rely=0.97, anchor="s")
        # Hidden Entry captures keys reliably on macOS (Canvas steals bind_all)
        import tkinter as _tk
        self._key_entry = _tk.Entry(self.root)
        self._key_entry.place(x=-200, y=-200, width=1, height=1)
        self._key_entry.bind("<KeyPress>", self._on_tk_key_recording)
        # Delay so _refresh_sounds widget creation settles before grabbing focus
        self.root.after(50, self._key_entry.focus_force)

    def _on_tk_key_recording(self, event):
        if not self._recording_for:
            try: self._key_entry.destroy()
            except Exception: pass
            return "break"
        keysym = event.keysym
        if keysym == "Escape":
            key_str = "ESC"
        elif len(keysym) == 1:
            key_str = keysym.upper()
        elif keysym.startswith("F") and keysym[1:].isdigit():
            key_str = keysym.upper()
        else:
            key_str = keysym.upper()
        self._finish_recording(key_str)
        return "break"

    def _finish_recording(self, key_str):
        if not self._recording_for:
            return
        try: self._key_entry.destroy()
        except Exception: pass
        if key_str in ("ESC", "ESCAPE"):
            self._recording_for = None
        else:
            self.data.setdefault("hotkeys", {})[self._recording_for] = key_str
            save_data(self.data)
            self._recording_for = None
        try:
            self._record_hint.destroy()
        except Exception:
            pass
        self._refresh_sounds()

    def _on_hotkey_recorded(self, key):
        if not self._recording_for:
            return
        key_str = _key_to_str(key)
        if not key_str:
            return
        self._finish_recording(key_str)

    def _delete_sound(self, filename):
        name = filename.rsplit('.', 1)[0]
        if messagebox.askyesno(self.t("delete_sound_title"), self.t("delete_sound_msg", name=name)):
            path = os.path.join(AUDIO_DIR, filename)
            if os.path.exists(path):
                os.remove(path)
            for g in self.data.get("groups", {}).values():
                if filename in g:
                    g.remove(filename)
            save_data(self.data)
            aud.reload_audio()
            self._refresh_groups()
            self._refresh_sounds()

    def _open_settings(self):
        SettingsWindow(self.root, self.settings, callbacks={
            "theme":   self._apply_theme,
            "lang":    self._apply_lang,
            "view":    self._schedule_refresh,
            "devices": self._apply_devices,
        }, t=self.t)

    def _apply_devices(self):
        s = self.settings
        aud.set_devices(
            vb_name=s.get("vb_device") or None,
            monitor_name=s.get("monitor_device") or None,
        )
        mic.stop()
        mic.set_devices(
            vbname=s.get("vb_device") or None,
            micname=s.get("mic_device") or None,
        )
        mic.gain = float(s.get("mic_gain", 5.0))
        threading.Thread(target=mic.start, daemon=True).start()

    def _apply_theme(self, theme):
        ctk.set_appearance_mode(theme)

    def _apply_lang(self, lang_code):
        was_real = self.current_group != self.t("all")
        saved = self.current_group if was_real else None
        self.lang = lang_code
        self.current_group = self.t("all")
        self._progress_running = False
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()
        self._setup_dnd()
        self._start_progress_loop()
        if saved and saved in self.data.get("groups", {}):
            self.current_group = saved
            self._refresh_groups()
            self._refresh_sounds()

    def enable_rb(self): pass
    def disable_rb(self): pass


# ── Keyboard listener ────────────────────────────────────────────────────────

def _key_to_str(key):
    try:
        if isinstance(key, keyboard.Key):
            name = key.name.upper()
            # Normalize modifier/escape names
            if name in ("ESC", "ESCAPE"): return "ESC"
            if name.startswith("F") and name[1:].isdigit(): return name  # F1-F12
            return name
        if isinstance(key, keyboard.KeyCode) and key.char:
            return key.char.upper()
    except Exception:
        pass
    return None


class GlobalListener(keyboard.Listener):
    def __init__(self, player, app):
        super().__init__(on_press=self.on_press)
        self.player = player
        self.app = app

    def on_press(self, key):
        try:
            # Recording mode — pass key to app
            if self.app._recording_for:
                self.app.root.after(0, lambda k=key: self.app._on_hotkey_recorded(k))
                return
            key_str = _key_to_str(key)
            if not key_str:
                return
            hotkeys = self.app.data.get("hotkeys", {})
            for filename, binding in hotkeys.items():
                if key_str == binding:
                    threading.Thread(target=self.player.play_by_filename,
                                     args=(filename,), daemon=True).start()
        except Exception:
            pass


if __name__ == "__main__":
    s = load_settings()
    if HAS_DND:
        root = TkinterDnD.Tk()
        ctk.set_appearance_mode(s.get("theme", "dark"))
        ctk.set_default_color_theme("blue")
    else:
        root = ctk.CTk()

    aud = libs.func.AudioInjector(
        vb_name=s.get("vb_device") or None,
        monitor_name=s.get("monitor_device") or None,
    )
    mic = libs.func.Mic(
        vbname=s.get("vb_device") or None,
        micname=s.get("mic_device") or None,
        gain=float(s.get("mic_gain", 5.0)),
    )
    threading.Thread(target=mic.start, daemon=True).start()

    app = SoundpadApp(root)
    if _is_accessibility_trusted():
        try:
            GlobalListener(aud, app).start()
        except Exception:
            pass
    root.mainloop()
