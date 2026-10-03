import customtkinter as ctk
import os, threading, json, shutil, sys, time
import libs.func, libs.recorder
from libs import theme as TH
from libs import icons as IC
import soundfile as sf
import tkinter
import numpy as np
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
TH.register_fonts()

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
        "new_group": "＋  Новая группа", "all": "Все звуки", "favorites": "Избранное", "recent": "Недавние",
        "menubar_show": "Показать окно", "menubar_stop": "Стоп", "menubar_quit": "Выход",
        "groups_title": "ГРУППЫ", "route_title": "Аудиомаршрут",
        "route_on": "Активен", "route_off": "Не настроен",
        "route_wait": "Подключаем…", "assign_key": "Назначить клавишу…", "create": "Создать", "save": "Сохранить", "name_empty": "Введите название", "group_exists": "Такая группа уже есть", "route_partial": "Есть проблемы", "route_missing": "не найдено", "route_error": "ошибка",
        "playing_local": "Играет на этом устройстве", "cancel": "Отмена",
        "settings_ui": "Интерфейс", "device_unavailable": "недоступно",
        "profiles_empty": "Профилей пока нет",
        "profiles_hint": "Сохрани текущий набор устройств, чтобы быстро переключаться между ними",
        "search_ph": "Поиск по {n} звукам", "nothing_found": "Ничего не найдено",
        "try_other": "Попробуй другой запрос", "sounds_total": "{n} звуков · {dur}",
        "playing_both": "Играет в Discord и наушниках",
        "playing_cable": "Играет в Discord", "on_pause": "На паузе", "nothing_playing": "Ничего не играет", "play": "▶  Играть",
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
        "apply": "Применить", "add_sound_short": "Добавить звук", "mic_gain": "Усиление микрофона",
        "loop_title": "Петля обратной связи",
        "loop_msg": "Микрофон и виртуальный кабель не могут быть одним устройством "
                    "({dev}) — звук зациклится и превратится в вой.\n\n"
                    "Микрофон — это твой реальный микрофон, а виртуальный кабель — "
                    "то, что слушает Discord.",
        "quiet_title": "Тихий виртуальный кабель",
        "quiet_msg": "Громкость «{dev}» стоит на {vol:.0%}. macOS применяет её по "
                     "кубической кривой, поэтому Discord получает почти тишину.\n\n"
                     "Открой «Настройки → Звук → Выход», выбери «{dev}» и выведи "
                     "громкость на максимум.",
    },
    "en": {
        "app_name": "Soundpad", "active": "● Active",
        "add_sound": "＋  Add Sound", "collections": "COLLECTIONS",
        "new_group": "＋  New Group", "all": "All Sounds", "favorites": "Favorites", "recent": "Recent",
        "menubar_show": "Show Window", "menubar_stop": "Stop", "menubar_quit": "Quit",
        "groups_title": "GROUPS", "route_title": "Audio Route",
        "route_on": "Active", "route_off": "Not set",
        "route_wait": "Connecting…", "assign_key": "Assign key…", "create": "Create", "save": "Save", "name_empty": "Enter a name", "group_exists": "This group already exists", "route_partial": "Issues", "route_missing": "not found", "route_error": "error",
        "playing_local": "Playing on this device", "cancel": "Cancel",
        "settings_ui": "Interface", "device_unavailable": "unavailable",
        "profiles_empty": "No profiles yet",
        "profiles_hint": "Save the current devices to switch between setups quickly",
        "search_ph": "Search {n} sounds", "nothing_found": "Nothing found",
        "try_other": "Try another query", "sounds_total": "{n} sounds · {dur}",
        "playing_both": "Playing to Discord and headphones",
        "playing_cable": "Playing to Discord", "on_pause": "Paused", "nothing_playing": "Nothing playing", "play": "▶  Play",
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
        "apply": "Apply", "add_sound_short": "Add Sound", "mic_gain": "Microphone Gain",
        "loop_title": "Feedback loop",
        "loop_msg": "The microphone and the virtual cable cannot be the same device "
                    "({dev}) — the audio would loop back and turn into a howl.\n\n"
                    "The microphone is your real mic; the virtual cable is what Discord listens to.",
        "quiet_title": "Virtual cable turned down",
        "quiet_msg": "The volume of \"{dev}\" is set to {vol:.0%}. macOS applies it on a cubic "
                     "curve, so Discord receives almost nothing.\n\n"
                     "Open System Settings → Sound → Output, pick \"{dev}\" and raise it to maximum.",
    },
    "es": {
        "app_name": "Soundpad", "active": "● Activo",
        "add_sound": "＋  Agregar sonido", "collections": "COLECCIONES",
        "new_group": "＋  Nuevo grupo", "all": "Todos los sonidos", "favorites": "Favoritos", "recent": "Recientes",
        "menubar_show": "Mostrar ventana", "menubar_stop": "Detener", "menubar_quit": "Salir",
        "groups_title": "GRUPOS", "route_title": "Ruta de audio",
        "route_on": "Activa", "route_off": "Sin configurar",
        "route_wait": "Conectando…", "assign_key": "Asignar tecla…", "create": "Crear", "save": "Guardar", "name_empty": "Escribe un nombre", "group_exists": "Ese grupo ya existe", "route_partial": "Con problemas", "route_missing": "no encontrado", "route_error": "error",
        "playing_local": "Reproduciendo en este dispositivo", "cancel": "Cancelar",
        "settings_ui": "Interfaz", "device_unavailable": "no disponible",
        "profiles_empty": "Aún no hay perfiles",
        "profiles_hint": "Guarda los dispositivos actuales para cambiar rápido",
        "search_ph": "Buscar en {n} sonidos", "nothing_found": "Nada encontrado",
        "try_other": "Prueba otra búsqueda", "sounds_total": "{n} sonidos · {dur}",
        "playing_both": "Sonando en Discord y auriculares",
        "playing_cable": "Sonando en Discord", "on_pause": "En pausa", "nothing_playing": "Nada sonando", "play": "▶  Reproducir",
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
        "apply": "Aplicar", "add_sound_short": "Agregar sonido", "mic_gain": "Ganancia del micrófono",
        "loop_title": "Bucle de realimentación",
        "loop_msg": "El micrófono y el cable virtual no pueden ser el mismo dispositivo ({dev}).",
        "quiet_title": "Cable virtual con volumen bajo",
        "quiet_msg": "El volumen de «{dev}» está al {vol:.0%}; Discord casi no recibe señal.",
    },
    "de": {
        "app_name": "Soundpad", "active": "● Aktiv",
        "add_sound": "＋  Sound hinzufügen", "collections": "SAMMLUNGEN",
        "new_group": "＋  Neue Gruppe", "all": "Alle Sounds", "favorites": "Favoriten", "recent": "Zuletzt",
        "menubar_show": "Fenster zeigen", "menubar_stop": "Stopp", "menubar_quit": "Beenden",
        "groups_title": "GRUPPEN", "route_title": "Audioroute",
        "route_on": "Aktiv", "route_off": "Nicht gesetzt",
        "route_wait": "Verbinde…", "assign_key": "Taste zuweisen…", "create": "Erstellen", "save": "Speichern", "name_empty": "Name eingeben", "group_exists": "Diese Gruppe existiert bereits", "route_partial": "Probleme", "route_missing": "nicht gefunden", "route_error": "Fehler",
        "playing_local": "Wiedergabe auf diesem Gerät", "cancel": "Abbrechen",
        "settings_ui": "Oberfläche", "device_unavailable": "nicht verfügbar",
        "profiles_empty": "Noch keine Profile",
        "profiles_hint": "Aktuelle Geräte speichern, um schnell zu wechseln",
        "search_ph": "{n} Sounds durchsuchen", "nothing_found": "Nichts gefunden",
        "try_other": "Andere Suche versuchen", "sounds_total": "{n} Sounds · {dur}",
        "playing_both": "Läuft in Discord und Kopfhörern",
        "playing_cable": "Läuft in Discord", "on_pause": "Pausiert", "nothing_playing": "Nichts läuft", "play": "▶  Abspielen",
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
        "apply": "Anwenden", "add_sound_short": "Sound hinzufügen", "mic_gain": "Mikrofonverstärkung",
        "loop_title": "Rückkopplungsschleife",
        "loop_msg": "Mikrofon und virtuelles Kabel dürfen nicht dasselbe Gerät sein ({dev}).",
        "quiet_title": "Virtuelles Kabel zu leise",
        "quiet_msg": "Die Lautstärke von „{dev}“ steht auf {vol:.0%}; Discord empfängt fast nichts.",
    },
    "zh": {
        "app_name": "Soundpad", "active": "● 已激活",
        "add_sound": "＋  添加声音", "collections": "收藏夹",
        "new_group": "＋  新建分组", "all": "全部声音", "favorites": "收藏", "recent": "最近",
        "menubar_show": "显示窗口", "menubar_stop": "停止", "menubar_quit": "退出",
        "groups_title": "分组", "route_title": "音频路由",
        "route_on": "已启用", "route_off": "未设置",
        "route_wait": "连接中…", "assign_key": "设置快捷键…", "create": "创建", "save": "保存", "name_empty": "请输入名称", "group_exists": "该分组已存在", "route_partial": "有问题", "route_missing": "未找到", "route_error": "错误",
        "playing_local": "正在本机播放", "cancel": "取消",
        "settings_ui": "界面", "device_unavailable": "不可用",
        "profiles_empty": "暂无配置文件",
        "profiles_hint": "保存当前设备组合以便快速切换",
        "search_ph": "搜索 {n} 个声音", "nothing_found": "未找到",
        "try_other": "换个关键词", "sounds_total": "{n} 个声音 · {dur}",
        "playing_both": "正在 Discord 和耳机播放",
        "playing_cable": "正在 Discord 播放", "on_pause": "已暂停", "nothing_playing": "未播放", "play": "▶  播放",
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
        "apply": "应用", "add_sound_short": "添加声音", "mic_gain": "麦克风增益",
        "loop_title": "音频回授",
        "loop_msg": "麦克风和虚拟声卡不能是同一个设备（{dev}）。",
        "quiet_title": "虚拟声卡音量过低",
        "quiet_msg": "「{dev}」的音量为 {vol:.0%}，Discord 几乎收不到声音。",
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


def _get_hotkeys(data, filename):
    val = data.get("hotkeys", {}).get(filename)
    if not val:
        return []
    return [val] if isinstance(val, str) else list(val)

def _set_hotkeys(data, filename, keys):
    hk = data.setdefault("hotkeys", {})
    if keys:
        hk[filename] = keys
    else:
        hk.pop(filename, None)

RECENT_LIMIT = 20


def _is_favorite(data, filename):
    return filename in data.get("favorites", [])


def _toggle_favorite(data, filename):
    favs = data.setdefault("favorites", [])
    if filename in favs:
        favs.remove(filename)
    else:
        favs.append(filename)
    return filename in favs


def _push_recent(data, filename):
    """Последний проигранный — первым.

    Список намеренно короткий: если его не обрезать, он перестаёт быть
    «недавним» и превращается во второй список всех звуков.
    """
    rec = data.setdefault("recent", [])
    if filename in rec:
        rec.remove(filename)
    rec.insert(0, filename)
    del rec[RECENT_LIMIT:]


def get_all_sounds():
    if os.path.exists(AUDIO_DIR):
        return sorted([f for f in os.listdir(AUDIO_DIR) if f.lower().endswith(('.wav', '.mp3'))])
    return []


_DUR_CACHE = {}


def duration_secs(filename):
    """Длительность в секундах с кешем по времени изменения файла.

    Без кеша подпись «N звуков · общая длительность» перечитывала бы заголовки
    всех файлов при каждой перерисовке списка.
    """
    path = os.path.join(AUDIO_DIR, filename)
    try:
        key = (filename, os.path.getmtime(path))
    except OSError:
        return None
    if key not in _DUR_CACHE:
        try:
            _DUR_CACHE[key] = sf.info(path).duration
        except Exception:
            _DUR_CACHE[key] = None
    return _DUR_CACHE[key]


def get_duration(filename):
    secs = duration_secs(filename)
    if secs is None:
        return "—"
    secs = int(secs)
    return f"{secs // 60}:{secs % 60:02d}"


def human_total(filenames):
    total = int(sum(duration_secs(f) or 0 for f in filenames))
    h, rem = divmod(total, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h} ч {m} мин"
    if m:
        return f"{m} мин {sec} с"
    return f"{sec} с"


def fmt_time(samples, samplerate):
    if not samplerate or samplerate == 0:
        return "0:00"
    secs = int(samples / samplerate)
    return f"{secs // 60}:{secs % 60:02d}"


# ── Шрифты: один объект на комбинацию параметров ────────────────────────────
# CTkFont — тяжёлый объект: создаёт tk-шрифт и подписывается на смену масштаба.
# Раньше каждая строка списка создавала их по нескольку штук при каждой
# перерисовке (80 звуков × N шрифтов) — отсюда заметные подлагивания. Кэшируем.
_FONTS = {}


def _font(family, size, weight="normal"):
    key = (family, size, weight)
    f = _FONTS.get(key)
    if f is None:
        f = _FONTS[key] = ctk.CTkFont(family=family, size=size, weight=weight)
    return f


def font_ui(size=14, weight="normal"):
    return _font(TH.family(TH.UI), size, weight)


def font_display(size=22):
    return _font(TH.family(TH.DISPLAY), size, "bold")


def font_mono(size=12):
    return _font(TH.family(TH.MONO), size, "normal")


def font_section():
    """Заголовок секции: 11 px, 600, прописные, увеличенный трекинг."""
    return _font(TH.family(TH.UI), 11, "bold")


# ── Волна прогресса ─────────────────────────────────────────────────────────

class WaveBar(ctk.CTkFrame):
    """Прогресс в виде волны. CustomTkinter такого не умеет, поэтому Canvas.

    Наружу выставлен метод set(), совместимый с CTkSlider, — вызывающий код
    про подмену виджета знать не обязан.

    Столбики создаются один раз (при смене размера, волны или темы), а на
    каждом тике прогресса перекрашиваются только те, что перешли из «не
    сыграно» в «сыграно». Раньше волна целиком удалялась и рисовалась заново
    12 раз в секунду — это и было главным источником лагов при воспроизведении.
    """

    BARS = 90

    def __init__(self, parent, on_seek):
        super().__init__(parent, fg_color="transparent", height=40)
        self._on_seek = on_seek
        self._frac = 0.0
        self._wave = None
        self._items = []          # id прямоугольников на Canvas
        self._played_n = 0        # сколько столбиков сейчас закрашено как «сыграно»
        self._col_played = self._col_rest = None
        self.cv = tkinter.Canvas(self, highlightthickness=0, bd=0, bg=TH.hexc("bg_deep"))
        self.cv.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        self.cv.bind("<Configure>", lambda e: self._render_bars())
        self.cv.bind("<Button-1>", self._seek)
        self.cv.bind("<B1-Motion>", self._seek)

    def _seek(self, e):
        w = self.cv.winfo_width()
        if w > 0:
            self._on_seek(max(0.0, min(1.0, e.x / w)))

    def _target_played(self):
        # столбик i считается сыгранным, если его середина левее позиции
        return min(self.BARS, int(self._frac * self.BARS + 0.5))

    def set(self, frac):
        self._frac = max(0.0, min(1.0, float(frac)))
        self._paint_progress()

    def set_wave(self, wave):
        self._wave = wave
        self._render_bars()

    def _paint_progress(self):
        """Перекрасить только изменившиеся столбики."""
        if not self._items:
            return
        target = self._target_played()
        if target == self._played_n:
            return
        lo, hi = sorted((self._played_n, target))
        for i in range(lo, hi):
            self.cv.itemconfigure(self._items[i],
                                  fill=self._col_played if i < target else self._col_rest)
        self._played_n = target

    def _render_bars(self):
        """Полная перерисовка: смена размера, волны или темы.

        Имя намеренно не _draw: так называется внутренний метод CTkFrame,
        и его перекрытие ломает виджет при создании."""
        cv = self.cv
        cv.delete("all")
        cv.configure(bg=TH.hexc("bg_deep"))
        self._items = []
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 10 or h < 6:
            return
        n = self.BARS
        # без загруженного файла показываем ровный «спящий» узор
        wave = self._wave or [0.18] * n
        self._col_played, self._col_rest = TH.hexc("accent"), TH.hexc("border_strong")
        step = w / n
        bw = max(2, step - 2)
        for i in range(n):
            bh = max(3, min(1.0, max(0.06, wave[i])) * (h - 8))
            x = i * step + (step - bw) / 2
            y = (h - bh) / 2
            self._items.append(cv.create_rectangle(x, y, x + bw, y + bh, width=0,
                                                   fill=self._col_rest))
        self._played_n = 0
        self._paint_progress()


# ── Глифы play / pause / stop, нарисованные на Canvas ───────────────────────

def _draw_glyph(cv, kind, cx, cy, S, col):
    """Один набор пропорций на все круглые кнопки, чтобы play в строке списка и
    в плеере выглядели одинаково. Размеры — доли диаметра S."""
    if kind == "play":
        w, h = 0.31 * S, 0.39 * S
        # треугольник центрируем ближе к центру масс, а не по габариту, —
        # иначе он кажется сдвинутым влево
        x0 = cx - w * 0.42
        cv.create_polygon(x0, cy - h / 2, x0 + w, cy, x0, cy + h / 2, fill=col, width=0)
    elif kind == "pause":
        bw, bh, gap = 0.11 * S, 0.34 * S, 0.11 * S
        cv.create_rectangle(cx - gap / 2 - bw, cy - bh / 2, cx - gap / 2, cy + bh / 2,
                            fill=col, width=0)
        cv.create_rectangle(cx + gap / 2, cy - bh / 2, cx + gap / 2 + bw, cy + bh / 2,
                            fill=col, width=0)
    elif kind == "stop":
        a = 0.34 * S / 2
        cv.create_rectangle(cx - a, cy - a, cx + a, cy + a, fill=col, width=0)


class RoundButton(tkinter.Canvas):
    """Круглая кнопка плеера — точно size × size.

    CTkButton с картинкой и пустым текстом на macOS раздувается вширь (виджет
    докладывает внутренние отступы под подпись), и круг превращался в овал:
    play выходил 70×48 вместо 48×48. Canvas имеет ровно тот размер, что задан.
    """

    def __init__(self, parent, size, glyph, on_click, solid=True):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bd=0)
        try:
            self.configure(cursor="pointinghand")
        except tkinter.TclError:
            pass
        self._size, self._glyph, self._solid = size, glyph, solid
        self._hover = False
        self.bind("<Button-1>", lambda e: on_click())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.paint()

    def _set_hover(self, v):
        if v != self._hover:
            self._hover = v
            self.paint()

    def set_glyph(self, glyph):
        if glyph != self._glyph:
            self._glyph = glyph
            self.paint()

    def paint(self):
        S = self._size
        c = S / 2
        self.configure(bg=TH.hexc("bg_deep"))
        self.delete("all")
        if self._solid:
            self.create_oval(1, 1, S - 1, S - 1, width=0,
                             fill=TH.hexc("accent_hover" if self._hover else "accent"))
            col = TH.hexc("on_accent")
        else:
            self.create_oval(1, 1, S - 1, S - 1, width=1, outline=TH.hexc("surface_3"),
                             fill=TH.hexc("surface_2") if self._hover else "")
            col = TH.hexc("text_2")
        _draw_glyph(self, self._glyph, c, c, S, col)


# ── Круглая кнопка в первой колонке строки ──────────────────────────────────

class PlayCell(tkinter.Canvas):
    """Номер строки, который при наведении превращается в круглую кнопку play,
    а у играющего звука — в залитую акцентом кнопку паузы (36 px).

    Нарисована на Canvas, а не картинкой на CTkButton. Подмена картинки при
    наведении давала на macOS чёрный прямоугольник вместо прозрачных пикселей
    и заметно тормозила: каждое наведение перенастраивало виджет CustomTkinter.
    """

    SIZE = 36

    def __init__(self, parent, num, on_click):
        super().__init__(parent, width=self.SIZE, height=self.SIZE,
                         highlightthickness=0, bd=0)
        try:
            self.configure(cursor="pointinghand")
        except tkinter.TclError:
            pass
        self._num = str(num)
        self._on_click = on_click
        self.playing = False
        self.paused = False
        self.row_hover = False
        self._btn_hover = False
        self.bind("<Button-1>", lambda e: self._on_click())
        self.bind("<Enter>", lambda e: self._set_btn_hover(True))
        self.bind("<Leave>", lambda e: self._set_btn_hover(False))
        self.paint()

    def _set_btn_hover(self, v):
        if v != self._btn_hover:
            self._btn_hover = v
            self.paint()

    def set_state(self, playing=None, paused=None, row_hover=None):
        changed = False
        for attr, val in (("playing", playing), ("paused", paused), ("row_hover", row_hover)):
            if val is not None and getattr(self, attr) != val:
                setattr(self, attr, val)
                changed = True
        if changed:
            self.paint()

    def paint(self):
        S = self.SIZE
        c = S / 2
        row_bg = TH.hexc("surface_2") if (self.row_hover or self.playing) else TH.hexc("bg")
        self.configure(bg=row_bg)
        self.delete("all")
        if self.playing or self._btn_hover or self.row_hover:
            if self.playing or self._btn_hover:
                fill = TH.hexc("accent_hover" if self._btn_hover else "accent")
                glyph = TH.hexc("on_accent")
            else:
                fill = TH.hexc("surface_3")
                glyph = TH.hexc("text")
            self.create_oval(1, 1, S - 1, S - 1, fill=fill, width=0)
            _draw_glyph(self, "pause" if (self.playing and not self.paused) else "play",
                        c, c, S, glyph)
        else:
            self.create_text(c, c, text=self._num, fill=TH.hexc("muted"),
                             font=(TH.family(TH.MONO), 12))


class SoundRowCtl:
    """Всё, что в строке списка меняется без перестройки списка: подсветка при
    наведении, состояние «играет/пауза», звезда избранного.

    Раньше при каждом play/stop список из 80 строк уничтожался и собирался
    заново (сотни виджетов CustomTkinter) — приложение на это заметно
    подвисало. Теперь перекрашивается только нужная строка.
    """

    def __init__(self, filename):
        self.filename = filename
        self.hover = False
        self.playing = False
        self.paused = False
        self.fav = False
        self.frame = self.cell = self.star = self.name = self.key = self.dur = self.dots = None

    def bg(self):
        return TH.hexc("surface_2") if (self.hover or self.playing) else TH.hexc("bg")

    def apply(self):
        bg = self.bg()
        self.frame.configure(fg_color=bg)
        for w in (self.star, self.name, self.key, self.dur, self.dots):
            w.configure(bg=bg)
        self.name.configure(fg=TH.hexc("accent" if self.playing else "text"),
                            font=font_ui(14, "bold" if self.playing else "normal"))
        self.cell.set_state(playing=self.playing, paused=self.paused, row_hover=self.hover)

    def set_hover(self, v):
        if v != self.hover:
            self.hover = v
            self.apply()

    def set_playing(self, playing, paused=False):
        self.playing, self.paused = playing, paused
        self.apply()

    def set_fav(self, fav):
        self.fav = fav
        self.star.configure(image=IC.photo("star_filled" if fav else "star", 16,
                                           "star" if fav else "star_empty"))


def _show_ctx(event, widget, filename, on_move, on_delete, t, on_bind=None):
    menu = Menu(widget, tearoff=0)
    if on_bind is not None:
        menu.add_command(label=t("assign_key"), command=lambda: on_bind(filename))
    menu.add_command(label=t("move_to_group"), command=lambda: on_move(filename))
    menu.add_separator()
    menu.add_command(label=t("delete_sound"), command=lambda: on_delete(filename))
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


# ── Settings window ─────────────────────────────────────────────────────────

class SettingsPanel(ctk.CTkFrame):
    """Настройки — боковая панель внутри главного окна, а не отдельное окно.

    Выезжает справа под плеером и лежит поверх правого края списка. Не модальна:
    список остаётся доступным, а тема, вид и сортировка применяются сразу, так
    что эффект виден рядом с панелью. Содержимое — по макету редизайна: группы-
    карточки, цепочка аудиомаршрута, профили и «Отмена / Применить» внизу.
    """

    W = 440

    def __init__(self, root, settings, callbacks, t, top, on_closed):
        super().__init__(root, width=self.W, corner_radius=0, fg_color=TH.c("bg"))
        self._main_root = root
        self._top = top                # верх панели = низ плеера
        self._on_closed = on_closed
        self._closing = False
        self.settings = settings
        self.cb = callbacks
        self.t = t
        self._missing = {}
        self._build()
        # стартуем за правым краем и выезжаем
        # place_configure, а не place: CTk-версия place запрещает width/height, а
        # нам нужна высота «всё окно минус плеер» (relheight=1 плюс height=-top)
        self.place_configure(relx=1.0, x=self.W, y=top, anchor="ne",
                             width=self.W, relheight=1.0, height=-top)
        self.tkraise()
        # Первая отрисовка ~100 виджетов занимает десятки мс. Делаем её до старта
        # анимации, чтобы эта пауза не попала в первые кадры движения.
        self.update_idletasks()
        self.after(20, lambda: self._slide(self.W, 0))

    # ── Выезд / заезд ──────────────────────────────────────────────────────
    def _slide(self, start, end, done=None, duration=0.30):
        """Плавное смещение панели по x.

        Что делает анимацию ровной:
        · шаг считается от времени кадра, но не больше ~24 мс за раз — подвисший
          кадр (например, первая отрисовка панели) не перепрыгивает полдистанции;
        · кривая smoothstep стартует и тормозит мягко, без рывка на первом кадре;
        · двигается готовая рамка, дочерние виджеты при этом не перерисовываются.
        """
        # если анимация запущена поверх другой (закрыли во время выезда) —
        # побеждает последняя, старая молча прекращается
        self._anim = getattr(self, "_anim", 0) + 1
        gen = self._anim
        state = {"k": 0.0, "last": time.perf_counter()}

        def frame():
            if gen != self._anim:
                return
            now = time.perf_counter()
            dt = min(now - state["last"], 0.024)
            state["last"] = now
            state["k"] = min(1.0, state["k"] + dt / duration)
            k = state["k"]
            eased = k * k * (3 - 2 * k)
            try:
                self.place_configure(x=round(start + (end - start) * eased))
            except tkinter.TclError:
                return                      # панель уже уничтожена
            if k < 1.0:
                self.after(8, frame)
            elif done:
                done()

        frame()

    def close(self):
        if self._closing:
            return
        self._closing = True

        def finish():
            try:
                self.destroy()
            except tkinter.TclError:
                pass
            self._on_closed()

        self._slide(0, self.W, finish, duration=0.22)

    # ── Строительные блоки ─────────────────────────────────────────────────
    def _section(self, parent, title, pady_top=22):
        ctk.CTkLabel(parent, text=title.upper(), font=font_section(), anchor="w",
                     text_color=TH.c("muted")).pack(fill="x", padx=4, pady=(pady_top, 8))
        card = ctk.CTkFrame(parent, corner_radius=14, fg_color=TH.c("surface"),
                            border_width=1, border_color=TH.c("border"))
        card.pack(fill="x")
        return card

    def _ui_row(self, card, label, first=False):
        """Строка карточки 56 px: подпись слева, элемент управления справа.
        Возвращает (обёртка, строка): обёртку можно скрывать целиком, вместе
        с разделителем."""
        wrap = ctk.CTkFrame(card, fg_color="transparent")
        wrap.pack(fill="x")
        if not first:
            ctk.CTkFrame(wrap, height=1, corner_radius=0,
                         fg_color=TH.c("border")).pack(fill="x", padx=16)
        row = ctk.CTkFrame(wrap, fg_color="transparent", height=56)
        row.pack(fill="x")
        row.pack_propagate(False)
        ctk.CTkLabel(row, text=label, font=font_ui(14),
                     text_color=TH.c("text")).pack(side="left", padx=(16, 0))
        return wrap, row

    def _menu(self, parent, values, command, width=150, height=34):
        """Тёмный селект: фон как у окна, кнопка-стрелка — surface_3."""
        return ctk.CTkOptionMenu(
            parent, values=values, command=command, width=width, height=height,
            corner_radius=10, anchor="w", font=font_ui(13), dropdown_font=font_ui(13),
            fg_color=TH.c("bg"), button_color=TH.c("surface_3"),
            button_hover_color=TH.c("border_strong"),
            text_color=TH.c("text"), dropdown_text_color=TH.c("text"),
            dropdown_fg_color=TH.c("surface"), dropdown_hover_color=TH.c("surface_2"))

    def _slider(self, parent, **kw):
        return ctk.CTkSlider(parent, progress_color=TH.c("accent"),
                             fg_color=TH.c("surface_3"),
                             button_color=("#FFFFFF", "#FFFFFF"),
                             button_hover_color=("#FFFFFF", "#FFFFFF"), **kw)

    # ── Сборка ─────────────────────────────────────────────────────────────
    def _build(self):
        t = self.t

        # граница со списком
        ctk.CTkFrame(self, width=1, corner_radius=0, fg_color=TH.c("border")).place(
            x=0, y=0, relheight=1.0)

        # шапка
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(22, 4))
        ctk.CTkLabel(head, text=t("settings_title"), font=font_display(22),
                     text_color=TH.c("text")).pack(side="left")
        ctk.CTkButton(head, text="", image=IC.icon("close", 16, "text_2"),
                      width=40, height=40, corner_radius=20,
                      fg_color=TH.c("surface"), hover_color=TH.c("surface_2"),
                      border_width=1, border_color=TH.c("border_strong"),
                      command=self.close).pack(side="right")

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=TH.c("surface_3"),
            scrollbar_button_hover_color=TH.c("border_strong"))
        scroll.pack(fill="both", expand=True, padx=(12, 6), pady=(0, 0))
        body = ctk.CTkFrame(scroll, fg_color="transparent")
        body.pack(fill="x", padx=(10, 10), pady=(0, 18))

        self._build_interface(body)
        self._build_route(body)
        self._build_profiles(body)

    def _build_interface(self, body):
        t = self.t
        card = self._section(body, t("settings_ui"), pady_top=14)

        # тема
        _, r = self._ui_row(card, t("theme_label"), first=True)
        sw = ctk.CTkSwitch(r, text="", width=46, switch_width=42, switch_height=24,
                           onvalue="dark", offvalue="light",
                           progress_color=TH.c("accent"), fg_color=TH.c("surface_3"),
                           button_color=("#FFFFFF", "#FFFFFF"),
                           button_hover_color=("#FFFFFF", "#FFFFFF"),
                           command=self._toggle_theme)
        (sw.select if self.settings.get("theme") == "dark" else sw.deselect)()
        sw.pack(side="right", padx=16)
        self._theme_sw = sw

        # язык
        _, r = self._ui_row(card, t("language_label"))
        cur_lang = LANG_NAMES.get(self.settings.get("language", "ru"), "🇷🇺  Русский")
        m = self._menu(r, list(LANG_NAMES.values()), self._change_lang, width=160)
        m.set(cur_lang)
        m.pack(side="right", padx=16)

        # вид
        self._view_wrap, r = self._ui_row(card, t("view_mode"))
        seg = ctk.CTkSegmentedButton(
            r, values=[t("view_grid"), t("view_list")], command=self._change_view,
            width=170, height=34, corner_radius=10, font=font_ui(13, "bold"),
            fg_color=TH.c("bg"), text_color=TH.c("text"),
            selected_color=TH.c("surface_3"), selected_hover_color=TH.c("surface_3"),
            unselected_color=TH.c("bg"), unselected_hover_color=TH.c("surface_2"))
        seg.set(t("view_grid") if self.settings.get("view", "list") == "grid" else t("view_list"))
        seg.pack(side="right", padx=16)
        self._view_seg = seg

        # число колонок (только для сетки)
        self._cols_wrap, r = self._ui_row(card, t("columns"))
        cols_val = self.settings.get("columns", 4)
        self._cols_label = ctk.CTkLabel(r, text=str(cols_val), width=24,
                                        font=font_mono(13), text_color=TH.c("accent"))
        self._cols_label.pack(side="right", padx=(0, 16))
        # без number_of_steps ползунок едет плавно, а на целое значение
        # «примагничивается» только при отпускании кнопки
        sl = self._slider(r, from_=2, to=6, width=110, command=self._change_cols)
        sl.set(cols_val)
        sl.pack(side="right", padx=4)
        sl.bind("<ButtonRelease-1>", lambda e: sl.set(int(round(sl.get()))), add="+")
        self._cols_slider = sl
        if self.settings.get("view", "list") == "grid":
            self._cols_wrap.pack(fill="x", after=self._view_wrap)
        else:
            self._cols_wrap.pack_forget()

        # сортировка
        _, r = self._ui_row(card, t("sort_by"))
        self._sort_map = {"az": t("sort_az"), "za": t("sort_za"),
                          "new": t("sort_new"), "old": t("sort_old")}
        sm = self._menu(r, list(self._sort_map.values()), self._change_sort, width=170)
        sm.set(self._sort_map.get(self.settings.get("sort", "az"), t("sort_az")))
        sm.pack(side="right", padx=16)

    def _build_route(self, body):
        """Цепочка: микрофон → виртуальный кабель → мониторинг, потом усиление."""
        t = self.t
        card = self._section(body, t("route_title"))

        devices = libs.func.list_devices()
        in_names = [d["name"] for d in devices if d["inputs"] > 0]
        out_names = [d["name"] for d in devices if d["outputs"] > 0]
        self._device_menus = {}
        self._missing = {}

        steps = (
            ("mic",        "mic_device",     in_names,  False),
            ("cable",      "vb_device",      out_names, True),
            ("headphones", "monitor_device", out_names, False),
        )
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(16, 6))
        inner.grid_columnconfigure(1, weight=1)

        for i, (ico, key, real, is_cable) in enumerate(steps):
            last = i == len(steps) - 1

            # левая колонка: иконка 40 px и вертикальная линия к следующему шагу
            left = ctk.CTkFrame(inner, fg_color="transparent", width=40)
            left.grid(row=i, column=0, sticky="ns", padx=(0, 14))
            badge = ctk.CTkFrame(left, width=40, height=40, corner_radius=12,
                                 fg_color=TH.c("accent") if is_cable else TH.c("surface_2"))
            badge.pack()
            badge.pack_propagate(False)
            if is_cable:
                ico_img = IC.icon(ico, 18, light=TH.hexc("on_accent", "light"),
                                  dark=TH.hexc("on_accent", "dark"))
            else:
                ico_img = IC.icon(ico, 18, "text_2")
            ctk.CTkLabel(badge, text="", image=ico_img).pack(expand=True)
            if not last:
                # height=1 обязателен: у CTkFrame высота по умолчанию 200 px, и линия
                # раздувала каждый шаг до ~250 px. С 1 px она тянется ровно на высоту
                # строки справа.
                ctk.CTkFrame(left, width=2, height=1, corner_radius=1,
                             fg_color=TH.c("border_strong")).pack(fill="y", expand=True, pady=4)

            # правая колонка: подпись и выбор устройства
            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.grid(row=i, column=1, sticky="ew", pady=(0, 0 if last else 10))
            ctk.CTkLabel(right, text=t(key), font=font_ui(12), anchor="w",
                         text_color=TH.c("muted")).pack(fill="x", pady=(0, 4))

            saved = self.settings.get(key) or ""
            names = [t("no_device")] + real
            cur = saved or t("no_device")
            if saved and saved not in real:
                # Сохранённое устройство сейчас не подключено (например, наушники).
                # Раньше селект молча показывал «не выбрано», хотя в настройках
                # имя оставалось, — и вид расходился с реальностью.
                cur = f"{saved} ({t('device_unavailable')})"
                names.append(cur)
                self._missing[key] = cur
            m = self._menu(right, names, lambda v, k=key: self._set_device(k, v), height=38)
            m.set(cur)
            m.pack(fill="x")
            self._device_menus[key] = m

        # усиление микрофона
        ctk.CTkFrame(card, height=1, corner_radius=0,
                     fg_color=TH.c("border")).pack(fill="x", padx=16, pady=(6, 0))
        gain = ctk.CTkFrame(card, fg_color="transparent")
        gain.pack(fill="x", padx=16, pady=(12, 14))
        gh = ctk.CTkFrame(gain, fg_color="transparent")
        gh.pack(fill="x")
        ctk.CTkLabel(gh, text=t("mic_gain"), font=font_ui(14),
                     text_color=TH.c("text")).pack(side="left")
        gain_val = self.settings.get("mic_gain", 5.0)
        self._gain_label = ctk.CTkLabel(gh, text=f"×{gain_val:.1f}", font=font_mono(13),
                                        text_color=TH.c("accent"))
        self._gain_label.pack(side="right")
        # Без number_of_steps ползунок непрерывный. Раньше было 18 ступеней по 0,5:
        # бегунок прыгал, а на каждом шаге ещё и перезаписывался файл настроек.
        gs = self._slider(gain, from_=1.0, to=10.0, height=16, command=self._change_gain)
        gs.set(gain_val)
        gs.pack(fill="x", pady=(10, 2))
        gs.bind("<ButtonRelease-1>", lambda e: self._flush_save(), add="+")
        ticks = ctk.CTkFrame(gain, fg_color="transparent")
        ticks.pack(fill="x")
        for col, (txt, anchor) in enumerate((("×1", "w"), ("×5", "center"), ("×10", "e"))):
            ticks.grid_columnconfigure(col, weight=1)
            ctk.CTkLabel(ticks, text=txt, font=font_mono(11), text_color=TH.c("muted"),
                         anchor=anchor).grid(row=0, column=col, sticky="ew")

    def _build_profiles(self, body):
        t = self.t
        ctk.CTkLabel(body, text=t("profiles").upper(), font=font_section(), anchor="w",
                     text_color=TH.c("muted")).pack(fill="x", padx=4, pady=(22, 8))
        self._profiles_box = ctk.CTkFrame(body, fg_color="transparent")
        self._profiles_box.pack(fill="x")
        self._render_profiles()

    def _dashed_box(self, parent, height):
        """Пунктирная рамка (Canvas: CustomTkinter пунктир не умеет).
        Возвращает контейнер, в который кладут содержимое."""
        box = ctk.CTkFrame(parent, height=height, fg_color="transparent")
        box.pack_propagate(False)
        cv = tkinter.Canvas(box, highlightthickness=0, bd=0, bg=TH.hexc("bg"))
        cv.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

        def draw(_=None):
            cv.delete("all")
            w, h = cv.winfo_width(), cv.winfo_height()
            if w < 10 or h < 10:
                return
            col, r, d, pd = TH.hexc("border_strong"), 14, (4, 4), 1
            cv.create_line(r + pd, pd, w - r - pd, pd, fill=col, dash=d)
            cv.create_line(r + pd, h - pd, w - r - pd, h - pd, fill=col, dash=d)
            cv.create_line(pd, r + pd, pd, h - r - pd, fill=col, dash=d)
            cv.create_line(w - pd, r + pd, w - pd, h - r - pd, fill=col, dash=d)
            for x, y, st in ((pd, pd, 90), (w - 2 * r - pd, pd, 0),
                             (w - 2 * r - pd, h - 2 * r - pd, 270), (pd, h - 2 * r - pd, 180)):
                cv.create_arc(x, y, x + 2 * r, y + 2 * r, start=st, extent=90,
                              style="arc", outline=col, dash=d)

        cv.bind("<Configure>", draw)
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        return box, inner

    # ── Обработчики ────────────────────────────────────────────────────────
    def _toggle_theme(self):
        val = self._theme_sw.get()
        self.settings["theme"] = val
        save_settings(self.settings)
        self.cb["theme"](val)
        # Canvas-элементы (пунктир) вне системы тем CustomTkinter — проще
        # собрать окно заново, чем перекрашивать их вручную. Через after:
        # нельзя уничтожать переключатель прямо из его же обработчика.
        self.after(60, self._rebuild)

    def _rebuild(self):
        try:
            self.configure(fg_color=TH.c("bg"))
            for w in self.winfo_children():
                w.destroy()
            self._build()
        except Exception as e:
            print(f"[settings] rebuild: {e}")

    def _change_lang(self, name):
        code = next((k for k, v in LANG_NAMES.items() if v == name), "ru")
        self.settings["language"] = code
        save_settings(self.settings)
        # Смена языка перестраивает весь интерфейс вместе с этой панелью. Делаем
        # это уже после выхода из обработчика селекта, который сейчас выполняется
        # внутри неё, и через root: панель к тому моменту уничтожена.
        self._main_root.after(10, lambda: self.cb["lang"](code))

    def _change_view(self, val):
        is_grid = (val == self.t("view_grid"))
        self.settings["view"] = "grid" if is_grid else "list"
        save_settings(self.settings)
        if is_grid:
            self._cols_wrap.pack(fill="x", after=self._view_wrap)
        else:
            self._cols_wrap.pack_forget()
        self.cb["view"]()

    def _change_cols(self, val):
        n = int(round(float(val)))
        if n == self.settings.get("columns"):
            return      # ползунок едет плавно, а колонок всего 5 — список перестраиваем только при смене числа
        self.settings["columns"] = n
        self._cols_label.configure(text=str(n))
        save_settings(self.settings)
        self.cb["view"]()

    def _change_sort(self, val):
        code = next((k for k, v in self._sort_map.items() if v == val), "az")
        self.settings["sort"] = code
        save_settings(self.settings)
        self.cb["view"]()

    def _set_device(self, key, val):
        no_dev = self.t("no_device")
        if val == self._missing.get(key):
            return  # выбрали всё ту же отключённую запись — ничего не меняется
        new = "" if val == no_dev else val

        # Микрофон и виртуальный кабель не должны совпадать: Mic открывает поток
        # (вход → выход) на одном устройстве, читает собственный выход и усиливает
        # его на каждом проходе. При gain > 1 кабель насыщается за доли секунды,
        # и Discord слышит вой вместо голоса.
        paired = {"mic_device": "vb_device", "vb_device": "mic_device"}.get(key)
        if paired and new and new == self.settings.get(paired, ""):
            messagebox.showwarning(self.t("loop_title"), self.t("loop_msg", dev=new))
            menu = getattr(self, "_device_menus", {}).get(key)
            if menu is not None:
                menu.set(self._missing.get(key) or self.settings.get(key) or no_dev)
            return

        if new == self.settings.get(key, ""):
            return
        self.settings[key] = new
        self._missing.pop(key, None)
        save_settings(self.settings)

        # Виртуальный кабель имеет собственный регулятор громкости в macOS.
        if key == "vb_device" and new:
            before, after = libs.func.ensure_cable_volume(new)
            if before is not None and before < libs.func.MIN_CABLE_VOLUME and after == before:
                messagebox.showwarning(self.t("quiet_title"),
                                       self.t("quiet_msg", dev=new, vol=before))
        self._apply_soon()

    def _apply_soon(self, delay=250):
        """Устройства применяются сразу после выбора, без кнопки «Применить».
        Небольшая задержка склеивает серию быстрых выборов в один перезапуск тракта."""
        if getattr(self, "_apply_job", None):
            self._main_root.after_cancel(self._apply_job)
        # через корень: панель может закрыться раньше таймера, а применить надо всё равно
        self._apply_job = self._main_root.after(delay, self._do_apply)

    def _do_apply(self):
        self._apply_job = None
        save_settings(self.settings)
        self.cb["devices"]()

    def _change_gain(self, val):
        val = round(float(val), 1)
        if val == self.settings.get("mic_gain") and self._gain_label.cget("text") == f"×{val:.1f}":
            return
        self.settings["mic_gain"] = val
        self._gain_label.configure(text=f"×{val:.1f}")
        self.cb["gain"](val)          # усиление меняется на лету, без перезапуска тракта
        self._save_soon()

    def _save_soon(self, delay=350):
        """Запись на диск с задержкой: при перетаскивании событий десятки в секунду,
        и синхронная запись JSON на каждое из них давала рывки. Пишем один раз,
        когда ползунок на мгновение замер, или сразу при отпускании."""
        if getattr(self, "_save_job", None):
            self._main_root.after_cancel(self._save_job)
        # через корень, а не через панель: она может закрыться раньше таймера
        self._save_job = self._main_root.after(delay, self._flush_save)

    def _flush_save(self):
        if getattr(self, "_save_job", None):
            try:
                self._main_root.after_cancel(self._save_job)
            except Exception:
                pass
            self._save_job = None
        save_settings(self.settings)

    # ── Профили ────────────────────────────────────────────────────────────
    def _render_profiles(self):
        box = self._profiles_box
        for w in box.winfo_children():
            w.destroy()
        t = self.t
        profiles = self.settings.get("profiles", {})

        if not profiles:
            dash, inner = self._dashed_box(box, 132)
            dash.pack(fill="x")
            ctk.CTkLabel(inner, text=t("profiles_empty"), font=font_ui(14, "bold"),
                         text_color=TH.c("text_2")).pack()
            ctk.CTkLabel(inner, text=t("profiles_hint"), font=font_ui(12),
                         text_color=TH.c("muted"), wraplength=330,
                         justify="center").pack(pady=(4, 10))
            ctk.CTkButton(inner, text=t("save_profile"), height=36, corner_radius=10,
                          image=IC.icon("plus", 16, "text"), compound="left",
                          font=font_ui(13, "bold"), text_color=TH.c("text"),
                          fg_color="transparent", hover_color=TH.c("surface_2"),
                          border_width=1, border_color=TH.c("border_strong"),
                          command=self._save_profile).pack()
            return

        active = self.settings.get("active_profile", "")
        for name in profiles:
            is_active = name == active
            card = ctk.CTkFrame(box, corner_radius=12, fg_color=TH.c("surface"),
                                border_width=1,
                                border_color=TH.c("accent") if is_active else TH.c("border"))
            card.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(card, text=name, anchor="w", font=font_ui(14, "bold"),
                         text_color=TH.c("accent") if is_active else TH.c("text")
                         ).pack(side="left", fill="x", expand=True, padx=(16, 8), pady=14)
            ctk.CTkButton(card, text="", image=IC.icon("close", 14, "muted"),
                          width=34, height=34, corner_radius=10,
                          fg_color="transparent", hover_color=TH.c("surface_2"),
                          command=lambda n=name: self._delete_profile(n)
                          ).pack(side="right", padx=(0, 10))
            ctk.CTkButton(card, text=t("load_profile"), width=90, height=34, corner_radius=10,
                          font=font_ui(12, "bold"), text_color=TH.c("text"),
                          fg_color=TH.c("surface_2"), hover_color=TH.c("surface_3"),
                          command=lambda n=name: self._load_profile(n)
                          ).pack(side="right", padx=(0, 4))
        ctk.CTkButton(box, text=t("save_profile"), height=40, corner_radius=12,
                      image=IC.icon("plus", 16, "text"), compound="left",
                      font=font_ui(13, "bold"), text_color=TH.c("text"),
                      fg_color="transparent", hover_color=TH.c("surface_2"),
                      border_width=1, border_color=TH.c("border_strong"),
                      command=self._save_profile).pack(fill="x", pady=(2, 0))

    def _save_profile(self):
        def validate(name):
            return None if name else self.t("name_empty")

        def done(name):
            if not name:
                return
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

        self.cb["ask_text"](self.t("profile_name_title"), self.t("profile_name_prompt"),
                            self.t("save"), validate, done)

    def _load_profile(self, name):
        profile = self.settings.get("profiles", {}).get(name)
        if not profile:
            return
        self.settings.update(profile)
        self.settings["active_profile"] = name
        save_settings(self.settings)
        self.cb["devices"]()
        self._rebuild()               # панель остаётся открытой, но показывает новый набор

    def _delete_profile(self, name):
        self.settings.get("profiles", {}).pop(name, None)
        if self.settings.get("active_profile") == name:
            self.settings["active_profile"] = ""
        save_settings(self.settings)
        self._render_profiles()


class TextPrompt(ctk.CTkFrame):
    """Запрос текста — карточка строго по центру окна приложения.

    Заменяет стандартный simpledialog: тот открывался отдельным неказистым окном
    в углу и молча проглатывал пустое или повторяющееся имя. Здесь окно не
    отдельное (как и панель настроек), а ошибка показывается прямо в карточке.
    Модальность — локальный захват мыши на самой карточке.
    """

    W, H = 380, 236

    def __init__(self, root, title, prompt, ok_text, cancel_text, validate, on_result, initial=""):
        super().__init__(root, width=self.W, height=self.H, corner_radius=18,
                         fg_color=TH.c("surface"), border_width=1,
                         border_color=TH.c("border_strong"))
        self.pack_propagate(False)
        self._validate = validate
        self._on_result = on_result
        self._done = False

        ctk.CTkLabel(self, text=title, font=font_display(18), anchor="w",
                     text_color=TH.c("text")).pack(fill="x", padx=24, pady=(24, 0))
        ctk.CTkLabel(self, text=prompt, font=font_ui(13), anchor="w",
                     text_color=TH.c("muted")).pack(fill="x", padx=24, pady=(6, 10))

        self._entry = ctk.CTkEntry(self, height=44, corner_radius=12, border_width=1,
                                   font=font_ui(14), text_color=TH.c("text"),
                                   fg_color=TH.c("bg"), border_color=TH.c("border_strong"))
        self._entry.pack(fill="x", padx=24)
        if initial:
            self._entry.insert(0, initial)
        self._entry.bind("<FocusIn>", lambda e: self._entry.configure(border_color=TH.c("accent")), add="+")
        self._entry.bind("<FocusOut>", lambda e: self._entry.configure(border_color=TH.c("border_strong")), add="+")
        self._entry.bind("<Return>", lambda e: (self._confirm(), "break")[1])
        # "break": иначе Escape дошёл бы до окна и закрыл ещё и панель настроек
        self._entry.bind("<Escape>", lambda e: (self.cancel(), "break")[1])
        self._entry.bind("<Key>", lambda e: self._set_error(""), add="+")

        # строка ошибки занимает место всегда — карточка не «прыгает» при её появлении
        self._err = ctk.CTkLabel(self, text="", font=font_ui(12), anchor="w",
                                 text_color=TH.c("danger"))
        self._err.pack(fill="x", padx=26, pady=(4, 0))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=24, pady=(6, 0))
        btns.grid_columnconfigure(0, weight=1, uniform="pb")
        btns.grid_columnconfigure(1, weight=1, uniform="pb")
        ctk.CTkButton(btns, text=cancel_text, height=42, corner_radius=12,
                      font=font_ui(14, "bold"), text_color=TH.c("text"),
                      fg_color="transparent", hover_color=TH.c("surface_2"),
                      border_width=1, border_color=TH.c("border_strong"),
                      command=self.cancel).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(btns, text=ok_text, height=42, corner_radius=12,
                      font=font_ui(14, "bold"), text_color=TH.c("on_accent"),
                      fg_color=TH.c("accent"), hover_color=TH.c("accent_hover"),
                      command=self._confirm).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.place(relx=0.5, rely=0.5, anchor="center")
        self.tkraise()
        self.update_idletasks()
        try:
            self.grab_set()          # пока карточка открыта, остальное окно не реагирует
        except tkinter.TclError:
            pass
        self.after(60, self._focus)

    def _focus(self):
        try:
            self._entry.focus_set()
            self._entry.select_range(0, "end")
        except tkinter.TclError:
            pass

    def _set_error(self, msg):
        if self._err.cget("text") != msg:
            self._err.configure(text=msg)
            self._entry.configure(border_color=TH.c("danger") if msg else TH.c("accent"))

    def _confirm(self):
        text = self._entry.get().strip()
        err = self._validate(text) if self._validate else None
        if err:
            self._set_error(err)
            return
        self._finish(text)

    def cancel(self):
        self._finish(None)

    def _finish(self, result):
        if self._done:
            return
        self._done = True
        try:
            self.grab_release()
            self.destroy()
        except tkinter.TclError:
            pass
        self._on_result(result)


# ── Main app ────────────────────────────────────────────────────────────────

class SoundpadApp:
    BAR_H = 84        # высота плеера сверху
    HEAD_H = 76       # высота шапки рабочей области (поиск и кнопки)

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
        self._search = ""
        self._wave_for = None
        self.menubar = None
        self._rows = {}            # имя файла → контроллер строки списка
        self._row_by_path = {}     # путь tk-виджета строки → контроллер (для hover)
        self._hover_ctl = None
        self._route_sig = None
        self._last_times = ("", "")
        self._settings_panel = None
        self._settings_btn = None
        self._prompt = None
        self._build_ui()
        self._setup_dnd()
        self._start_progress_loop()
        self._setup_local_hotkeys()
        # Подсветку строки при наведении ловим одним обработчиком на окно, а не
        # десятками привязок на каждую строку.
        self.root.bind("<Motion>", self._on_motion, add="+")
        self.root.bind("<Leave>", self._on_root_leave, add="+")
        self.root.bind("<Escape>", self._on_escape, add="+")
        self._route_watch()

    def t(self, key, **kw):
        text = TRANSLATIONS.get(self.lang, TRANSLATIONS["ru"]).get(key, key)
        return text.format(**kw) if kw else text

    def _show_window(self):
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception as e:
            print(f"[menubar] show error: {e}")

    def _quit_app(self):
        try:
            mic.stop()
            aud.stop_current()
        except Exception:
            pass
        self.root.quit()

    def _sync_menubar(self):
        if self.menubar:
            self.menubar.rebuild()

    def _build_ui(self):
        """Сетка: плеер 92 px во всю ширину СВЕРХУ, под ним боковая панель
        256 px слева и рабочая область."""
        TH.probe(self.root)
        self._paint_root()
        self.root.grid_columnconfigure(0, minsize=256, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, minsize=self.BAR_H, weight=0)
        self.root.grid_rowconfigure(1, weight=1)

        self._build_playbar()
        self._build_sidebar()
        self._build_content()

    def _paint_root(self):
        """Корневое окно — это TkinterDnD.Tk, обычный Tk без fg_color, когда
        доступен drag-and-drop, и CTk в остальных случаях."""
        try:
            self.root.configure(fg_color=TH.c("bg"))
        except Exception:
            try:
                self.root.configure(bg=TH.hexc("bg"))
            except Exception:
                pass

    # ── Шрифты ─────────────────────────────────────────────────────────────
    def f_ui(self, size=14, weight="normal"):
        return font_ui(size, weight)

    def f_display(self, size=22):
        return font_display(size)

    def f_mono(self, size=12):
        return font_mono(size)

    def f_section(self):
        return font_section()

    def _build_header(self, parent):
        """Шапка рабочей области: поиск · переключатель вида · настройки · добавить."""
        head = ctk.CTkFrame(parent, corner_radius=0, fg_color=TH.c("bg"), height=self.HEAD_H)
        head.grid(row=0, column=0, sticky="ew")
        head.grid_propagate(False)
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkFrame(head, height=1, corner_radius=0, fg_color=TH.c("border")).place(
            relx=0, rely=1.0, relwidth=1.0, anchor="sw")

        inner = ctk.CTkFrame(head, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="ew", padx=32, pady=16)
        inner.grid_columnconfigure(0, weight=1)

        # ── поиск ──
        box = ctk.CTkFrame(inner, height=44, corner_radius=12, fg_color=TH.c("surface"),
                           border_width=1, border_color=TH.c("border_strong"))
        box.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        box.grid_propagate(False)
        ctk.CTkLabel(box, text="", image=IC.icon("search", 18, "muted")).pack(side="left", padx=(14, 0))

        self._search_var = ctk.StringVar(value=self._search)
        self._search_var.trace_add("write", lambda *a: self._on_search())
        self._search_entry = ctk.CTkEntry(
            box, textvariable=self._search_var, border_width=0, fg_color="transparent",
            font=self.f_ui(14), text_color=TH.c("text"),
            placeholder_text=self.t("search_ph", n=len(get_all_sounds())),
            placeholder_text_color=TH.c("muted"))
        self._search_entry.pack(side="left", fill="both", expand=True, padx=(10, 8), pady=2)

        chip = ctk.CTkLabel(box, text="\u2318K", font=self.f_mono(11), text_color=TH.c("muted"),
                            corner_radius=6, fg_color="transparent", width=34, height=20)
        chip.pack(side="right", padx=(0, 12))
        self.root.bind("<Command-k>", lambda e: self._search_entry.focus_set())

        # ── переключатель вида ──
        seg = ctk.CTkFrame(inner, corner_radius=12, fg_color=TH.c("surface"),
                           border_width=1, border_color=TH.c("border_strong"))
        seg.grid(row=0, column=1, padx=(0, 12))
        view = self.settings.get("view", "list")
        for name, ico in (("list", "list"), ("grid", "grid")):
            on = view == name
            ctk.CTkButton(seg, text="", image=IC.icon(ico, 18, "text" if on else "muted"),
                          width=40, height=36, corner_radius=9,
                          fg_color=TH.c("surface_3") if on else "transparent",
                          hover_color=TH.c("surface_3"),
                          command=lambda v=name: self._set_view(v)).pack(side="left", padx=3, pady=3)

        self._settings_btn = ctk.CTkButton(
            inner, text="", image=IC.icon("settings", 18, "text_2"),
            width=44, height=44, corner_radius=12,
            fg_color=TH.c("surface"), hover_color=TH.c("surface_2"),
            border_width=1, border_color=TH.c("border_strong"),
            command=self._open_settings)
        self._settings_btn.grid(row=0, column=2, padx=(0, 12))
        self._style_settings_btn()

        ctk.CTkButton(inner, text=self.t("add_sound_short"),
                      image=IC.icon("plus", 18, light=TH.hexc("on_accent", "light"),
                                    dark=TH.hexc("on_accent", "dark")),
                      compound="left", height=44, corner_radius=12,
                      font=self.f_ui(14, "bold"),
                      fg_color=TH.c("accent"), hover_color=TH.c("accent_hover"),
                      text_color=TH.c("on_accent"),
                      command=self._add_sound_dialog).grid(row=0, column=3)

    def _set_view(self, view):
        self.settings["view"] = view
        save_settings(self.settings)
        self._build_content()

    def _on_search(self):
        self._search = self._search_var.get().strip()
        self._schedule_refresh()

    def _build_playbar(self):
        bar = ctk.CTkFrame(self.root, height=self.BAR_H, corner_radius=0,
                           fg_color=TH.c("bg_deep"))
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        # вес строки — чтобы блоки плеера стояли по центру полосы, а не липли к верху
        bar.grid_rowconfigure(0, weight=1)
        bar.grid_columnconfigure(0, minsize=256, weight=0)
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_columnconfigure(2, minsize=240, weight=0)
        # разделитель — по нижнему краю плеера, отделяет его от списка
        ctk.CTkFrame(bar, height=1, corner_radius=0, fg_color=TH.c("border")).place(
            relx=0, rely=1.0, relwidth=1.0, anchor="sw")


        # ── что играет ──
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=(16, 0))
        cover = ctk.CTkFrame(left, width=48, height=48, corner_radius=10,
                             fg_color=TH.c("surface_2"))
        cover.pack(side="left")
        cover.pack_propagate(False)
        ctk.CTkLabel(cover, text="", image=IC.icon(
            "eq", 22, "accent")).pack(expand=True)

        info = ctk.CTkFrame(left, fg_color="transparent")
        info.pack(side="left", padx=(12, 0))
        self._now_label = ctk.CTkLabel(info, text="", anchor="w", font=self.f_ui(14, "bold"),
                                       text_color=TH.c("text"), width=170)
        self._now_label.pack(anchor="w")
        self._now_status = ctk.CTkLabel(info, text=self.t("nothing_playing"), anchor="w",
                                        font=self.f_ui(12), text_color=TH.c("muted"))
        self._now_status.pack(anchor="w")

        # ── транспорт ──
        mid = ctk.CTkFrame(bar, fg_color="transparent")
        mid.grid(row=0, column=1, sticky="ew", padx=24)
        mid.grid_columnconfigure(3, weight=1)

        self._play_btn = RoundButton(mid, 48, "play", self._transport_pause, solid=True)
        self._play_btn.grid(row=0, column=0)

        self._pause_btn = RoundButton(mid, 40, "stop", self._stop_sound, solid=False)
        self._pause_btn.grid(row=0, column=1, padx=16)

        self._cur_time = ctk.CTkLabel(mid, text="0:00", width=44, anchor="e",
                                      font=self.f_mono(12), text_color=TH.c("accent"))
        self._cur_time.grid(row=0, column=2)

        self._progress = WaveBar(mid, on_seek=self._seek_to)
        self._progress.grid(row=0, column=3, sticky="ew", padx=14)

        self._tot_time = ctk.CTkLabel(mid, text="0:00", width=44, anchor="w",
                                      font=self.f_mono(12), text_color=TH.c("muted"))
        self._tot_time.grid(row=0, column=4)

        # ── громкость ──
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=(0, 24))
        ctk.CTkLabel(right, text="", image=IC.icon("volume", 18, "text_2")).pack(side="left")
        vol = ctk.CTkSlider(right, from_=0, to=1, width=150, height=16,
                            button_color=("#FFFFFF", "#FFFFFF"),
                            button_hover_color=("#FFFFFF", "#FFFFFF"),
                            progress_color=TH.c("text"), fg_color=TH.c("surface_3"),
                            command=self._set_volume)
        vol.set(getattr(aud, "volume", 1.0))
        vol.pack(side="left", padx=12)
        self._vol_pct = ctk.CTkLabel(right, text=f"{int(getattr(aud, 'volume', 1.0) * 100)}%",
                                     width=34, anchor="w", font=self.f_mono(11),
                                     text_color=TH.c("muted"))
        self._vol_pct.pack(side="left")

    def _seek_to(self, frac):
        self._seeking = True
        aud.seek(frac)
        self._progress.set(frac)
        self.root.after(120, lambda: setattr(self, "_seeking", False))

    def _update_transport(self):
        """Единая точка правды для вида транспорта — раньше стили кнопок
        дублировались в четырёх местах и разъезжались."""
        active = self.playing_filename is not None
        icon = "pause" if (active and not self.paused) else "play"
        self._play_btn.set_glyph(icon)
        if not active:
            self._now_label.configure(text="")
            self._now_status.configure(text=self.t("nothing_playing"))
            self._cur_time.configure(text="0:00")
            self._tot_time.configure(text="0:00")
            self._last_times = ("0:00", "0:00")
            self._progress.set(0)
            self._progress.set_wave(None)
        else:
            name = self.playing_filename.rsplit('.', 1)[0]
            self._now_label.configure(text=name)
            if self.paused:
                status = self.t("on_pause")
            else:
                # смотрим на устройства, которые движок реально нашёл: имя в
                # настройках ещё не значит, что наушники подключены
                to_cable = aud.vbidx is not None
                to_monitor = aud.monitor_idx is not None and aud.monitor_idx != aud.vbidx
                if to_cable and to_monitor:
                    status = self.t("playing_both")
                elif to_cable:
                    status = self.t("playing_cable")
                else:
                    status = self.t("playing_local")
            self._now_status.configure(text=status)

    def _compute_wave(self):
        """90 пиков из уже загруженных отсчётов — файл повторно не читаем."""
        try:
            data = aud.data
            if data is None or len(data) == 0:
                return None
            mono = np.abs(data).max(axis=1) if data.ndim > 1 else np.abs(data)
            chunks = np.array_split(mono, WaveBar.BARS)
            peaks = np.array([c.max() if len(c) else 0.0 for c in chunks], dtype=float)
            top = peaks.max()
            return list(peaks / top) if top > 0 else None
        except Exception:
            return None

    def _transport_play_stop(self):
        """Оставлено для совместимости: остановить активный звук или повторить
        последний."""
        if self.playing_filename:
            self._stop_sound()
        elif self._last_played:
            self._play_sound(self._last_played)

    def _transport_pause(self):
        """Главная кнопка плеера: пауза · продолжение · повтор последнего."""
        if self.playing_filename and not self.paused:
            self.paused = True
            aud.pause()
        elif self.playing_filename and self.paused:
            self.paused = False
            aud.resume()
        elif self._last_played:
            self._play_sound(self._last_played)
            return
        self._update_transport()
        self._sync_playing_rows()

    def _start_progress_loop(self):
        self._last_played = None
        self._progress_running = True
        self._tick_progress()

    def _tick_progress(self):
        if not self._progress_running:
            return
        try:
            if self.playing_filename:
                # волну считаем один раз на файл — как только поток загрузил отсчёты
                if (self._wave_for != self.playing_filename
                        and aud.data is not getattr(self, "_stale_wave_data", None)):
                    wave = self._compute_wave()
                    if wave:
                        self._progress.set_wave(wave)
                        self._wave_for = self.playing_filename
                cur, total = aud.get_progress()
                sr = aud.samplerate or 48000
                if aud.playing and not self._seeking:
                    self._progress.set(cur / total if total > 0 else 0)
                # CTkLabel.configure перерисовывает виджет, даже если текст тот же
                t_cur, t_tot = fmt_time(cur, sr), fmt_time(total, sr)
                if t_cur != self._last_times[0]:
                    self._cur_time.configure(text=t_cur)
                if t_tot != self._last_times[1]:
                    self._tot_time.configure(text=t_tot)
                self._last_times = (t_cur, t_tot)
        except Exception:
            pass
        self.root.after(100, self._tick_progress)

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self.root, corner_radius=0, fg_color=TH.c("bg_deep"))
        sb.grid(row=1, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)
        sb.grid_rowconfigure(2, weight=1)
        self._sidebar = sb

        # правая граница панели
        ctk.CTkFrame(sb, width=1, corner_radius=0, fg_color=TH.c("border")).place(
            relx=1.0, rely=0, relheight=1.0, anchor="ne")

        # ── логотип ──
        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 20))
        mark = ctk.CTkFrame(logo, width=36, height=36, corner_radius=10,
                            fg_color=TH.c("accent"))
        mark.pack(side="left")
        mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="", image=IC.icon("eq", 20, light=TH.hexc("on_accent", "light"),
                                                  dark=TH.hexc("on_accent", "dark"))).pack(expand=True)
        ctk.CTkLabel(logo, text="soundpad", font=self.f_display(18),
                     text_color=TH.c("text")).pack(side="left", padx=(12, 0))

        # ── коллекции ──
        self._collections = ctk.CTkFrame(sb, fg_color="transparent")
        self._collections.grid(row=1, column=0, sticky="ew", padx=16)

        # ── группы ──
        gwrap = ctk.CTkFrame(sb, fg_color="transparent")
        gwrap.grid(row=2, column=0, sticky="nsew", padx=16, pady=(20, 0))
        gwrap.grid_columnconfigure(0, weight=1)
        gwrap.grid_rowconfigure(1, weight=1)

        ghead = ctk.CTkFrame(gwrap, fg_color="transparent")
        ghead.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(ghead, text=self.t("groups_title"), font=self.f_section(),
                     text_color=TH.c("muted")).pack(side="left", padx=(12, 0))
        ctk.CTkButton(ghead, text="", image=IC.icon("plus", 16, "muted"),
                      width=28, height=28, corner_radius=8,
                      fg_color="transparent", hover_color=TH.c("surface_2"),
                      command=self._add_group_dialog).pack(side="right", padx=(0, 4))

        self.groups_scroll = ctk.CTkScrollableFrame(
            gwrap, fg_color="transparent",
            scrollbar_button_color=TH.c("surface_3"),
            scrollbar_button_hover_color=TH.c("border_strong"))
        self.groups_scroll.grid(row=1, column=0, sticky="nsew")
        self.groups_scroll.grid_columnconfigure(0, weight=1)

        # ── карточка аудиомаршрута ──
        self._route_card = ctk.CTkFrame(sb, corner_radius=14,
                                        fg_color=TH.c("surface"),
                                        border_width=1, border_color=TH.c("border"))
        self._route_card.grid(row=3, column=0, sticky="ew", padx=16, pady=16)
        self._build_route_card()

        self._refresh_groups()

    def _route_state(self):
        """Что реально построено, а не что записано в настройках.

        Настройки — это пожелание: наушники могли отключиться, поток микрофона —
        не открыться. Поэтому смотрим на движок: какие устройства он нашёл и
        жив ли поток микрофона. У каждого звена свой статус:
        ok — работает · bad — не работает · wait — поднимается · off — не выбрано.
        """
        s = self.settings
        mic_name = s.get("mic_device") or ""
        vb_name = s.get("vb_device") or ""
        mon_name = s.get("monitor_device") or ""
        err = getattr(mic, "last_error", None) or ""

        if not mic_name:
            mic_st = ("off", "")
        elif mic.streaming:
            mic_st = ("ok", "")
        elif err:
            mic_st = ("bad", "missing" if "not found" in err.lower() else "error")
        else:
            mic_st = ("wait", "")

        if not vb_name:
            vb_st = ("off", "")
        elif aud.vbidx is not None:
            vb_st = ("ok", "")
        else:
            vb_st = ("bad", "missing")

        if not mon_name:
            mon_st = ("off", "")
        elif aud.monitor_idx is not None:
            mon_st = ("ok", "")
        else:
            mon_st = ("bad", "missing")

        kinds = [mic_st[0], vb_st[0], mon_st[0]]
        if all(k == "off" for k in kinds):
            overall = "off"
        elif "bad" in kinds:
            overall = "partial"
        elif "wait" in kinds:
            overall = "wait"
        else:
            overall = "on"

        return {
            "overall": overall,
            "rows": [("mic", mic_name, mic_st),
                     ("cable", vb_name, vb_st),
                     ("headphones", mon_name, mon_st)],
            # по этой подписи наблюдатель понимает, что маршрут изменился
            "sig": (mic_name, vb_name, mon_name, bool(mic.streaming), bool(mic.running), err,
                    aud.vbidx, aud.monitor_idx, ctk.get_appearance_mode()),
        }

    def _route_watch(self):
        """Раз в ~0.7 с сверяет маршрут с движком и перерисовывает карточку,
        только если что-то реально поменялось (микрофон поднялся, наушники
        отключились, применены новые устройства)."""
        try:
            if self._route_state()["sig"] != self._route_sig:
                self._build_route_card()
        except Exception as e:
            print(f"[route] {e}")
        self.root.after(700, self._route_watch)

    def _build_route_card(self):
        """Карточка «Аудиомаршрут» — показывает реальное состояние тракта."""
        for w in self._route_card.winfo_children():
            w.destroy()

        st = self._route_state()
        self._route_sig = st["sig"]
        overall = st["overall"]
        head_col = {"on": "ok", "partial": "danger", "wait": "muted", "off": "muted"}[overall]
        head_txt = {"on": "route_on", "partial": "route_partial",
                    "wait": "route_wait", "off": "route_off"}[overall]

        head = ctk.CTkFrame(self._route_card, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(14, 10))
        ctk.CTkLabel(head, text=self.t("route_title"), font=self.f_ui(12, "bold"),
                     text_color=TH.c("text_2")).pack(side="left")

        status = ctk.CTkFrame(head, fg_color="transparent")
        status.pack(side="right")
        ctk.CTkFrame(status, width=6, height=6, corner_radius=3,
                     fg_color=TH.c(head_col)).pack(side="left", pady=1)
        ctk.CTkLabel(status, text=self.t(head_txt), font=self.f_ui(11),
                     text_color=TH.c(head_col)).pack(side="left", padx=(6, 0))

        body = ctk.CTkFrame(self._route_card, fg_color="transparent")
        body.pack(fill="x", padx=14, pady=(0, 14))
        for ico, name, (state, why) in st["rows"]:
            text = name or self.t("no_device")
            if ico == "cable" and name:
                text = f"{name} \u2192 Discord"
            if state == "bad":
                text += " \u2014 " + self.t("route_missing" if why == "missing" else "route_error")
            icon_tok = {"ok": "ok", "bad": "danger"}.get(state, "muted")
            txt_col = {"ok": "text_2", "bad": "danger"}.get(state, "muted")
            r = ctk.CTkFrame(body, fg_color="transparent")
            r.pack(fill="x", pady=3)
            ctk.CTkLabel(r, text="", image=IC.icon(ico, 14, icon_tok)).pack(side="left")
            ctk.CTkLabel(r, text=text, font=self.f_ui(12), text_color=TH.c(txt_col),
                         anchor="w", justify="left", wraplength=170
                         ).pack(side="left", padx=(8, 0), fill="x", expand=True)

    TABLE_COLS = (44, 36, None, 136, 56, 36)   # ширины колонок: play/№ · звезда · название · клавиша · длина · меню

    def _build_content(self):
        if getattr(self, "_content", None) is not None:
            self._content.destroy()

        self._content = ctk.CTkFrame(self.root, corner_radius=0, fg_color=TH.c("bg"))
        self._content.grid(row=1, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(3, weight=1)

        self._build_header(self._content)

        # ── заголовок раздела ──
        title_row = ctk.CTkFrame(self._content, fg_color="transparent")
        title_row.grid(row=1, column=0, sticky="ew", padx=32, pady=(24, 12))
        title_row.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(title_row, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        self._section_title = ctk.CTkLabel(left, text=self.current_group, anchor="w",
                                           font=self.f_display(26), text_color=TH.c("text"))
        self._section_title.pack(anchor="w")
        self._section_sub = ctk.CTkLabel(left, text="", anchor="w",
                                         font=self.f_ui(13), text_color=TH.c("muted"))
        self._section_sub.pack(anchor="w", pady=(4, 0))

        self._sort_btn = ctk.CTkButton(
            title_row, text=self._sort_label(), image=IC.icon("sort", 14, "text_2"),
            compound="left", height=36, corner_radius=10, font=self.f_ui(13),
            fg_color="transparent", hover_color=TH.c("surface_2"),
            text_color=TH.c("text_2"), border_width=1, border_color=TH.c("border_strong"),
            command=self._cycle_sort)
        self._sort_btn.grid(row=0, column=1, sticky="e")

        # ── шапка таблицы ──
        self._table_header = ctk.CTkFrame(self._content, height=32, corner_radius=0,
                                          fg_color="transparent")
        self._table_header.grid(row=2, column=0, sticky="ew", padx=44)
        self._table_header.grid_propagate(False)
        self._build_table_header()

        # ── список ──
        self.sounds_scroll = ctk.CTkScrollableFrame(
            self._content, fg_color="transparent",
            scrollbar_button_color=TH.c("surface_3"),
            scrollbar_button_hover_color=TH.c("border_strong"))
        self.sounds_scroll.grid(row=3, column=0, sticky="nsew", padx=32, pady=(6, 0))
        self.sounds_scroll.grid_columnconfigure(0, weight=1)

        # ── зона перетаскивания ──
        self.drop_frame = ctk.CTkFrame(self._content, height=52, fg_color="transparent")
        self.drop_frame.grid(row=4, column=0, sticky="ew", padx=32, pady=(10, 16))
        self.drop_frame.grid_propagate(False)
        self._drop_canvas = tkinter.Canvas(self.drop_frame, highlightthickness=0, bd=0,
                                           bg=TH.hexc("bg"))
        self._drop_canvas.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        self._drop_canvas.bind("<Configure>", lambda e: self._draw_drop_zone())

        inner = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(inner, text="", image=IC.icon("download", 16, "muted")).pack(side="left")
        self.drop_label = ctk.CTkLabel(inner, text=self.t("drop_zone"), font=self.f_ui(13),
                                       text_color=TH.c("muted"))
        self.drop_label.pack(side="left", padx=(10, 0))

        for w in (self.drop_frame, self._drop_canvas, self.drop_label, inner):
            w.bind("<Button-1>", lambda e: self._add_sound_dialog())

        self._setup_dnd()
        self._refresh_sounds()
        if self._settings_panel is not None:
            self._settings_panel.tkraise()   # новый _content иначе лёг бы поверх панели

    def _draw_drop_zone(self, color=None):
        """Пунктирная рамка. CustomTkinter не умеет пунктир, поэтому рисуем на
        Canvas: четыре стороны линиями и четыре угла дугами."""
        cv = self._drop_canvas
        cv.delete("all")
        cv.configure(bg=TH.hexc("bg"))
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 10 or h < 10:
            return
        col = color or TH.hexc("border_strong")
        r, d, p = 12, (4, 4), 1
        cv.create_line(r + p, p, w - r - p, p, fill=col, dash=d)
        cv.create_line(r + p, h - p, w - r - p, h - p, fill=col, dash=d)
        cv.create_line(p, r + p, p, h - r - p, fill=col, dash=d)
        cv.create_line(w - p, r + p, w - p, h - r - p, fill=col, dash=d)
        for x, y, start in ((p, p, 90), (w - 2 * r - p, p, 0),
                            (w - 2 * r - p, h - 2 * r - p, 270), (p, h - 2 * r - p, 180)):
            cv.create_arc(x, y, x + 2 * r, y + 2 * r, start=start, extent=90,
                          style="arc", outline=col, dash=d)

    def _flash_drop(self):
        self._draw_drop_zone(TH.hexc("ok"))
        self.root.after(800, lambda: self._draw_drop_zone())

    def _sort_label(self):
        return self._sort_map().get(self.settings.get("sort", "az"), "")

    def _sort_map(self):
        return {"az": self.t("sort_az"), "za": self.t("sort_za"),
                "new": self.t("sort_new"), "old": self.t("sort_old")}

    def _cycle_sort(self):
        order = ["az", "za", "new", "old"]
        cur = self.settings.get("sort", "az")
        nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "az"
        self.settings["sort"] = nxt
        save_settings(self.settings)
        self._sort_btn.configure(text=self._sort_label())
        self._refresh_sounds()

    def _build_table_header(self):
        for w in self._table_header.winfo_children():
            w.destroy()
        if self.settings.get("view", "list") == "grid":
            self._table_header.grid_remove()
            return
        self._table_header.grid()

        for i, width in enumerate(self.TABLE_COLS):
            self._table_header.grid_columnconfigure(
                i, weight=1 if width is None else 0, minsize=width or 0)

        def cell(col, text, anchor="w"):
            ctk.CTkLabel(self._table_header, text=text, anchor=anchor,
                         font=self.f_section(), text_color=TH.c("muted")
                         ).grid(row=0, column=col, sticky="ew", padx=(0, 12))

        cell(0, "#")
        cell(2, self.t("col_name"))
        cell(3, self.t("col_key"))
        cell(4, self.t("col_dur"), "e")

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

    def _nav_row(self, parent, text, count, active, command,
                 icon_name=None, dot_color=None, on_ctx=None):
        """Строка навигации 44 px: иконка (или цветная метка) · название · счётчик.

        Собрана из фрейма с метками, а не из CTkButton: кнопка не умеет держать
        счётчик, прижатый к правому краю, независимо от длины названия.
        """
        bg = TH.c("surface_2") if active else TH.c("bg_deep")
        row = ctk.CTkFrame(parent, height=44, corner_radius=10, fg_color=bg)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        if dot_color is not None:
            mark = ctk.CTkFrame(row, width=10, height=10, corner_radius=3, fg_color=dot_color)
            mark.pack(side="left", padx=(16, 0))
        elif icon_name:
            ctk.CTkLabel(row, text="", image=IC.icon(
                icon_name, 18, "text" if active else "text_2")).pack(side="left", padx=(12, 0))

        name = ctk.CTkLabel(row, text=text, anchor="w",
                            font=self.f_ui(14, "bold" if active else "normal"),
                            text_color=TH.c("text") if active else TH.c("text_2"))
        name.pack(side="left", fill="x", expand=True, padx=(12, 8))

        cnt = ctk.CTkLabel(row, text=str(count), font=self.f_mono(12),
                           text_color=TH.c("accent") if active else TH.c("muted"))
        cnt.pack(side="right", padx=(0, 14))

        targets = [row, name, cnt] + list(row.winfo_children())
        for w in targets:
            w.bind("<Button-1>", lambda e, c=command: c())
            if on_ctx:
                w.bind("<Button-2>", lambda e, c=on_ctx: c())
            if not active:
                w.bind("<Enter>", lambda e, r=row: r.configure(fg_color=TH.c("surface_2")))
                w.bind("<Leave>", lambda e, r=row: r.configure(fg_color=TH.c("bg_deep")))
        return row

    GROUP_COLORS = ("#7C9CFF", "#7CE0A3", "#FFC43D", "#FF8A63", "#C58BFF", "#5FD6D6")

    def _group_color(self, name):
        """Стабильный цвет метки: одна и та же группа всегда одного цвета,
        и он не зависит от порядка групп в списке."""
        return self.GROUP_COLORS[sum(map(ord, name)) % len(self.GROUP_COLORS)]

    def _refresh_groups(self):
        for w in self._collections.winfo_children():
            w.destroy()
        for w in self.groups_scroll.winfo_children():
            w.destroy()

        all_set = set(get_all_sounds())
        all_label = self.t("all")
        fav_label = self.t("favorites")
        rec_label = self.t("recent")

        ctk.CTkLabel(self._collections, text=self.t("collections"),
                     font=self.f_section(), text_color=TH.c("muted"),
                     anchor="w").pack(fill="x", padx=12, pady=(0, 8))

        favs = [x for x in self.data.get("favorites", []) if x in all_set]
        recs = [x for x in self.data.get("recent", []) if x in all_set]
        for label, icon_name, count in ((all_label, "music", len(all_set)),
                                        (fav_label, "star", len(favs)),
                                        (rec_label, "clock", len(recs))):
            self._nav_row(self._collections, label, count,
                          self.current_group == label,
                          lambda g=label: self._select_group(g),
                          icon_name=icon_name)

        for g, sounds in self.data.get("groups", {}).items():
            self._nav_row(self.groups_scroll, g,
                          len([x for x in sounds if x in all_set]),
                          self.current_group == g,
                          lambda gn=g: self._select_group(gn),
                          dot_color=self._group_color(g),
                          on_ctx=lambda gn=g: self._delete_group(gn))

    def _select_group(self, group):
        self.current_group = group
        self._refresh_groups()
        self._refresh_sounds()

    def _apply_search(self, names):
        """Поиск по подстроке без учёта регистра. Ищем по имени без расширения —
        пользователь видит именно его."""
        q = (self._search or "").lower()
        if not q:
            return names
        return [n for n in names if q in n.rsplit('.', 1)[0].lower()]

    def _get_current_sounds(self):
        all_sounds = get_all_sounds()
        if self.current_group == self.t("recent"):
            # Порядок недавних сам по себе информация, поэтому сортировку
            # настроек здесь намеренно не применяем.
            return self._apply_search([s for s in self.data.get("recent", []) if s in all_sounds])
        if self.current_group == self.t("favorites"):
            sounds = [s for s in self.data.get("favorites", []) if s in all_sounds]
        elif self.current_group == self.t("all"):
            sounds = all_sounds
        else:
            gs = self.data.get("groups", {}).get(self.current_group, [])
            sounds = [s for s in gs if s in all_sounds]

        sort = self.settings.get("sort", "az")
        if sort == "az":
            return self._apply_search(sorted(sounds, key=lambda f: f.lower()))
        elif sort == "za":
            return self._apply_search(sorted(sounds, key=lambda f: f.lower(), reverse=True))
        elif sort in ("new", "old"):
            reverse = sort == "new"
            return self._apply_search(sorted(sounds, key=lambda f: os.path.getmtime(os.path.join(AUDIO_DIR, f)), reverse=reverse))
        return self._apply_search(sounds)

    def _sound_row(self, parent, num, filename, playing):
        """Строка таблицы 46 px по сетке колонок TABLE_COLS.

        Внутри — обычные tk-виджеты (Label/Canvas), а не CTkButton/CTkLabel:
        у каждого CTk-виджета свой внутренний Canvas, и 80 таких строк делали
        перестройку списка тяжёлой. Скруглённая подсветка — на самой CTkFrame.
        """
        ctl = SoundRowCtl(filename)
        ctl.playing = playing
        ctl.paused = playing and self.paused

        row = ctk.CTkFrame(parent, height=46, corner_radius=10, fg_color=ctl.bg())
        row.grid_propagate(False)
        row.grid_rowconfigure(0, weight=1)   # без веса ячейки липнут к верху строки
        for i, width in enumerate(self.TABLE_COLS):
            row.grid_columnconfigure(i, weight=1 if width is None else 0, minsize=width or 0)
        ctl.frame = row

        def label(**kw):
            kw.setdefault("bd", 0)
            kw.setdefault("highlightthickness", 0)
            return tkinter.Label(row, **kw)

        # ── колонка 0: номер → круглая кнопка play/пауза ──
        ctl.cell = PlayCell(row, num, on_click=lambda: (
            self._transport_pause() if ctl.playing else self._play_sound(filename)))
        ctl.cell.grid(row=0, column=0, padx=(4, 0))

        # ── колонка 1: избранное ──
        ctl.fav = _is_favorite(self.data, filename)
        ctl.star = label(image=IC.photo("star_filled" if ctl.fav else "star", 16,
                                        "star" if ctl.fav else "star_empty"),
                         width=36, height=36, cursor="pointinghand")
        ctl.star.grid(row=0, column=1)
        ctl.star.bind("<Button-1>", lambda e, f=filename: self._toggle_fav(f))

        # ── колонка 2: название ──
        ctl.name = label(text=filename.rsplit('.', 1)[0], anchor="w", padx=0)
        ctl.name.grid(row=0, column=2, sticky="ew", padx=(12, 12))
        ctl.name.bind("<Button-1>", lambda e, f=filename: self._play_sound(f))
        ctl.name.bind("<Button-2>", lambda e, f=filename: _show_ctx(
            e, row, f, self._move_sound_to_group, self._delete_sound, self.t,
            on_bind=self._bind_hotkey))

        # ── колонка 3: клавиши — плашки и ВСЕГДА видимая кнопка «＋» ──
        # Раньше тут был просто текст: пока клавиша не назначена, колонка
        # выглядела пустой, и назначить её можно было только кликом по
        # невидимому месту.
        keys = _get_hotkeys(self.data, filename)
        ctl.key = tkinter.Frame(row, bd=0, highlightthickness=0, bg=ctl.bg())
        ctl.key.grid(row=0, column=3, sticky="w")
        chip_bg, chip_fg = TH.hexc("surface_3"), TH.hexc("text")
        for k in keys[:3]:
            chip = tkinter.Label(ctl.key, text=k, font=font_mono(11), padx=7, pady=3,
                                 bd=0, highlightthickness=0, cursor="pointinghand",
                                 bg=chip_bg, fg=chip_fg)
            chip.pack(side="left", padx=(0, 4))
            # клик по плашке убирает эту клавишу; красным подсвечиваем заранее
            chip.bind("<Enter>", lambda e, c=chip: c.configure(bg=TH.hexc("danger"), fg="#FFFFFF"))
            chip.bind("<Leave>", lambda e, c=chip: c.configure(bg=chip_bg, fg=chip_fg))
            chip.bind("<Button-1>", lambda e, f=filename, key=k: self._bind_hotkey(f, remove_key=key))
        add = tkinter.Label(ctl.key, image=IC.photo("plus", 14, "text_2"), width=28, height=24,
                            bd=0, highlightthickness=0, cursor="pointinghand", bg=chip_bg)
        add.pack(side="left")
        add.bind("<Enter>", lambda e: add.configure(bg=TH.hexc("border_strong")))
        add.bind("<Leave>", lambda e: add.configure(bg=chip_bg))
        add.bind("<Button-1>", lambda e, f=filename: self._bind_hotkey(f))

        # ── колонка 4: длина ──
        ctl.dur = label(text=get_duration(filename), anchor="e", padx=0,
                        font=font_mono(12), fg=TH.hexc("muted"))
        ctl.dur.grid(row=0, column=4, sticky="ew")

        # ── колонка 5: меню ──
        ctl.dots = label(image=IC.photo("dots", 16, "muted"), width=36, height=36,
                         cursor="pointinghand")
        ctl.dots.grid(row=0, column=5)
        ctl.dots.bind("<Button-1>", lambda e, f=filename: _show_ctx(
            e, row, f, self._move_sound_to_group, self._delete_sound, self.t,
            on_bind=self._bind_hotkey))

        ctl.apply()
        self._rows[filename] = ctl
        self._row_by_path[str(row)] = ctl
        return row

    def _on_motion(self, event):
        """Одна привязка на всё окно вместо Enter/Leave на каждом виджете
        каждой строки: находим строку под курсором, поднимаясь по родителям."""
        ctl = None
        w = event.widget
        try:
            for _ in range(8):
                ctl = self._row_by_path.get(str(w))
                if ctl is not None or w is None or w is self.root:
                    break
                w = w.master
        except Exception:
            ctl = None
        if ctl is not self._hover_ctl:
            old, self._hover_ctl = self._hover_ctl, ctl
            try:
                if old is not None:
                    old.set_hover(False)
                if ctl is not None:
                    ctl.set_hover(True)
            except Exception:
                pass  # строку могли уничтожить при перерисовке списка

    def _on_root_leave(self, event):
        if event.widget is self.root and self._hover_ctl is not None:
            old, self._hover_ctl = self._hover_ctl, None
            try:
                old.set_hover(False)
            except Exception:
                pass

    def _sync_playing_rows(self):
        """Обновить «играет/пауза» у уже построенных строк — без перестройки
        списка. Карточки сетки перестраиваются целиком (их немного и они
        нужны реже)."""
        if self.settings.get("view", "list") != "list":
            self._refresh_sounds()
            return
        for fn, ctl in self._rows.items():
            playing = fn == self.playing_filename
            paused = playing and self.paused
            if playing != ctl.playing or paused != ctl.paused:
                ctl.set_playing(playing, paused)

    def _sound_card(self, parent, filename, playing):
        card = ctk.CTkFrame(parent, corner_radius=14, width=160,
                            fg_color=TH.c("surface_2") if playing else TH.c("surface"),
                            border_width=1,
                            border_color=TH.c("accent") if playing else TH.c("border"))
        ctk.CTkLabel(card, text="", image=IC.icon(
            "music", 26, light=TH.hexc("accent", "light") if playing else TH.hexc("muted", "light"),
            dark=TH.hexc("accent", "dark") if playing else TH.hexc("muted", "dark"))).pack(pady=(16, 6))
        nm = ctk.CTkLabel(card, text=filename.rsplit('.', 1)[0], font=self.f_ui(12),
                          wraplength=132, justify="center",
                          text_color=TH.c("accent") if playing else TH.c("text"))
        nm.pack(padx=10)
        ctk.CTkLabel(card, text=get_duration(filename), font=self.f_mono(11),
                     text_color=TH.c("muted")).pack(pady=(4, 14))

        fav = _is_favorite(self.data, filename)
        star = ctk.CTkLabel(card, text="", image=IC.icon(
            "star_filled" if fav else "star", 15, "star" if fav else "star_empty"))
        star.place(relx=1.0, x=-8, y=8, anchor="ne")
        star.bind("<Button-1>", lambda e, f=filename: (self._toggle_fav(f), "break")[1])

        for w in (card, nm):
            w.bind("<Button-1>", lambda e, f=filename: self._play_sound(f))
            w.bind("<Button-2>", lambda e, f=filename: _show_ctx(
                e, card, f, self._move_sound_to_group, self._delete_sound, self.t,
            on_bind=self._bind_hotkey))
        return card

    def _refresh_sounds(self):
        self._rows = {}
        self._row_by_path = {}
        self._hover_ctl = None
        for w in self.sounds_scroll.winfo_children():
            w.destroy()

        sounds = self._get_current_sounds()
        view = self.settings.get("view", "list")

        if getattr(self, "_section_title", None) is not None:
            self._section_title.configure(text=self.current_group)
            self._section_sub.configure(
                text=self.t("sounds_total", n=len(sounds), dur=human_total(sounds)))
        self._build_table_header()

        if not sounds:
            box = ctk.CTkFrame(self.sounds_scroll, fg_color="transparent")
            box.pack(expand=True, fill="both", pady=70)
            searching = bool(self._search)
            ctk.CTkLabel(box, text="", image=IC.icon(
                "search" if searching else "music", 40, "surface_3")).pack()
            ctk.CTkLabel(box, font=self.f_ui(15), text_color=TH.c("text_2"),
                         text=self.t("nothing_found") if searching else (
                             self.t("no_sounds") if self.current_group == self.t("all")
                             else self.t("no_sounds_group", group=self.current_group))
                         ).pack(pady=(12, 4))
            ctk.CTkLabel(box, font=self.f_ui(12), text_color=TH.c("muted"),
                         text=self.t("try_other") if searching else self.t("drop_hint")).pack()
            return

        if view == "list":
            for i, sound in enumerate(sounds):
                self._sound_row(self.sounds_scroll, i + 1, sound,
                                sound == self.playing_filename).pack(fill="x", pady=1)
        else:
            cols = max(1, self.settings.get("columns", 4))
            for c in range(cols):
                self.sounds_scroll.grid_columnconfigure(c, weight=1)
            for i, sound in enumerate(sounds):
                r, c = divmod(i, cols)
                self._sound_card(self.sounds_scroll, sound,
                                 sound == self.playing_filename
                                 ).grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

    def _schedule_refresh(self):
        if self._refresh_timer:
            self.root.after_cancel(self._refresh_timer)
        self._refresh_timer = self.root.after(80, self._refresh_sounds)

    def _toggle_fav(self, filename):
        _toggle_favorite(self.data, filename)
        save_data(self.data)
        self._refresh_groups()
        ctl = self._rows.get(filename)
        if ctl is not None and self.current_group != self.t("favorites"):
            ctl.set_fav(_is_favorite(self.data, filename))   # список не меняется — только звезда
        else:
            self._refresh_sounds()
        self._sync_menubar()

    def _play_sound(self, filename):
        if self.playing_filename == filename:
            return
        if not os.path.exists(os.path.join(AUDIO_DIR, filename)):
            self.data.get("hotkeys", {}).pop(filename, None)
            save_data(self.data)
            return
        _push_recent(self.data, filename)
        save_data(self.data)
        self._refresh_groups()
        self._sync_menubar()
        self.playing_filename = filename
        self._last_played = filename
        # новый звук всегда стартует «играющим»: если предыдущий стоял на паузе,
        # флаг иначе так и остался бы, и плеер показывал бы паузу при живом звуке
        self.paused = False
        self._wave_for = None
        self._stale_wave_data = aud.data   # волну считаем только по данным НОВОГО файла
        aud.on_finish_callback = self._on_sound_finish
        self._progress.set(0)
        self._cur_time.configure(text="0:00")
        self._last_times = ("0:00", self._last_times[1])
        # Без этого вызова большая кнопка оставалась с ▶, а статус — «ничего не
        # играет», хотя звук уже шёл, пока её не нажимали второй раз.
        self._update_transport()
        if self.current_group == self.t("recent"):
            self._refresh_sounds()      # порядок «недавних» поменялся
        else:
            self._sync_playing_rows()
        threading.Thread(target=aud.play_by_filename, args=(filename,), daemon=True).start()

    def _stop_sound(self):
        aud.stop_current()
        self.playing_filename = None
        self.paused = False
        self._wave_for = None
        self._update_transport()
        self._sync_playing_rows()

    def _on_sound_finish(self):
        self.playing_filename = None
        self.root.after(0, self._on_finish_ui)

    def _on_finish_ui(self):
        self.paused = False
        self._wave_for = None
        self._update_transport()
        self._sync_playing_rows()

    def _add_sound_dialog(self):
        for f in filedialog.askopenfilenames(
                title=self.t("choose_files"),
                filetypes=[(self.t("audio_files"), "*.wav *.mp3"), (self.t("all_files"), "*.*")]):
            self._copy_and_add(f)

    def _add_group_dialog(self):
        def validate(name):
            if not name:
                return self.t("name_empty")
            if name in (self.t("all"), self.t("favorites"), self.t("recent")) \
                    or name in self.data.get("groups", {}):
                return self.t("group_exists")
            return None

        def done(name):
            if not name:
                return
            self.data.setdefault("groups", {})[name] = []
            save_data(self.data)
            self._refresh_groups()

        self._ask_text(self.t("new_group_title"), self.t("group_name_prompt"),
                       self.t("create"), validate, done)

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

    def _bind_hotkey(self, filename, remove_key=None):
        if remove_key is not None:
            keys = _get_hotkeys(self.data, filename)
            keys = [k for k in keys if k != remove_key]
            _set_hotkeys(self.data, filename, keys)
            save_data(self.data)
            self._refresh_sounds()
            return
        if self._recording_for:
            return
        self._recording_for = filename

        import tkinter as _tk
        # Use tk.Toplevel — CTkToplevel on macOS auto-withdraws on creation,
        # so grab_set/focus_force called immediately have no effect.
        dialog = _tk.Toplevel(self.root)
        dialog.withdraw()
        dialog.title("Горячая клавиша")
        cx = self.root.winfo_rootx() + self.root.winfo_width() // 2 - 150
        cy = self.root.winfo_rooty() + self.root.winfo_height() // 2 - 50
        dialog.geometry(f"300x100+{cx}+{cy}")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.attributes("-topmost", True)

        name = filename.rsplit('.', 1)[0]
        existing = _get_hotkeys(self.data, filename)
        hint = f"  Уже: {', '.join(existing)}" if existing else ""
        _tk.Label(
            dialog,
            text=f"{name}{hint}\n\nНажми клавишу  •  Esc — отмена",
            font=("Helvetica", 13),
            justify="center",
        ).pack(expand=True, fill="both", padx=10, pady=10)

        def on_key(event):
            keysym = event.keysym
            if keysym != "Escape":
                if len(keysym) == 1:
                    key_str = keysym.upper()
                elif keysym.startswith("F") and keysym[1:].isdigit():
                    key_str = keysym.upper()
                else:
                    key_str = keysym.upper()
                keys = _get_hotkeys(self.data, filename)
                if key_str not in keys:
                    keys.append(key_str)
                _set_hotkeys(self.data, filename, keys)
                save_data(self.data)
            self._recording_for = None
            dialog.destroy()
            self._refresh_sounds()

        dialog.bind("<KeyPress>", on_key)

        def _show():
            dialog.deiconify()
            dialog.lift()
            dialog.focus_force()
            dialog.grab_set()

        dialog.after(50, _show)

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
        """Шестерёнка: открыть боковую панель настроек или закрыть, если она уже открыта."""
        if self._settings_panel is not None:
            self._settings_panel.close()
            return
        self._settings_panel = SettingsPanel(self.root, self.settings, callbacks={
            "theme":   self._apply_theme,
            "lang":    self._apply_lang,
            "view":    self._schedule_refresh,
            "devices": self._apply_devices,
            "gain":    self._set_mic_gain,
            "ask_text": self._ask_text,
        }, t=self.t, top=self.BAR_H, on_closed=self._on_settings_closed)
        self._style_settings_btn()

    def _on_settings_closed(self):
        self._settings_panel = None
        self._style_settings_btn()

    def _on_escape(self, event=None):
        if self._prompt is not None:
            self._prompt.cancel()          # диалог поверх всего — закрываем его первым
        elif self._settings_panel is not None and not self._recording_for:
            self._settings_panel.close()

    def _ask_text(self, title, prompt, ok_text, validate, on_result, initial=""):
        """Показать карточку ввода по центру окна. on_result получит строку
        или None, если пользователь отменил."""
        if self._prompt is not None:
            return

        def finish(result):
            self._prompt = None
            on_result(result)

        self._prompt = TextPrompt(self.root, title, prompt, ok_text, self.t("cancel"),
                                  validate, finish, initial)

    def _style_settings_btn(self):
        """Шестерёнка подсвечена, пока панель открыта."""
        btn = self._settings_btn
        if btn is None:
            return
        try:
            btn.configure(fg_color=TH.c("surface_3") if self._settings_panel is not None
                          else TH.c("surface"))
        except tkinter.TclError:
            pass

    def _rescan_devices(self):
        """PortAudio запоминает список устройств при запуске процесса, поэтому
        наушники, подключённые уже после старта, приложение не видит — и маршрут
        на них не построить. Перечитываем список, но только когда ничего не
        играет: Pa_Terminate закрывает все открытые потоки. Возвращает, было ли
        перечитано (тракт микрофона при этом остановлен)."""
        if aud.playing:
            return False
        try:
            import sounddevice as sd
            mic.stop()
            sd._terminate()
            sd._initialize()
            return True
        except Exception as e:
            print(f"[devices] rescan failed: {e}")
            return False

    def _set_mic_gain(self, val):
        mic.gain = float(val)

    def _apply_devices(self):
        """Применить устройства из настроек. Вызывается сразу при выборе в панели,
        поэтому трогаем только то, что действительно изменилось: смена наушников
        не должна на секунду обрывать голос в Discord перезапуском микрофона."""
        s = self.settings
        vb = s.get("vb_device") or None
        mon = s.get("monitor_device") or None
        mc = s.get("mic_device") or None

        # выбранное устройство движок не видит → возможно, его подключили позже
        unresolved = ((vb and aud.vbidx is None) or (mon and aud.monitor_idx is None)
                      or (mc and not mic.streaming))
        rescanned = bool(unresolved) and self._rescan_devices()

        if rescanned or (aud._vb_name, aud._monitor_name) != (vb, mon):
            aud.set_devices(vb_name=vb, monitor_name=mon)

        mic.gain = float(s.get("mic_gain", 5.0))
        if rescanned or not mic.streaming or (mic.vbname, mic.micname) != (vb, mc):
            mic.stop()
            mic.set_devices(vbname=vb, micname=mc)
            threading.Thread(target=mic.start, daemon=True).start()

    def _setup_local_hotkeys(self):
        """Hotkey playback while app window has focus — no Accessibility needed."""
        pressed = set()
        fired = set()

        def _keysym_to_str(keysym):
            if len(keysym) == 1:
                return keysym.upper()
            if keysym.startswith("F") and keysym[1:].isdigit():
                return keysym.upper()
            return None

        def on_key_press(event):
            nonlocal fired
            if self._recording_for:
                pressed.clear(); fired.clear()
                return
            key_str = _keysym_to_str(event.keysym)
            if not key_str:
                return
            pressed.add(key_str)
            hotkeys = self.data.get("hotkeys", {})
            for filename, binding in hotkeys.items():
                chord = frozenset([binding] if isinstance(binding, str) else binding)
                if chord and chord <= pressed and chord not in fired:
                    fired.add(chord)
                    self._play_sound(filename)
                    return

        def on_key_release(event):
            nonlocal fired
            key_str = _keysym_to_str(event.keysym)
            if key_str:
                pressed.discard(key_str)
                fired = {c for c in fired if key_str not in c}

        self.root.bind_all("<KeyPress>", on_key_press)
        self.root.bind_all("<KeyRelease>", on_key_release)

    def _set_volume(self, val):
        aud.volume = float(val)
        self._vol_pct.configure(text=f"{int(round(float(val) * 100))}%")

    def _apply_theme(self, theme):
        ctk.set_appearance_mode(theme)
        self._paint_root()
        # Canvas живёт вне системы тем CustomTkinter — перерисовываем вручную
        try:
            self._draw_drop_zone()
            self._progress._render_bars()
            self._play_btn.paint()
            self._pause_btn.paint()
        except Exception:
            pass
        self._refresh_groups()
        self._refresh_sounds()
        self._build_route_card()

    def _apply_lang(self, lang_code):
        was_real = self.current_group != self.t("all")
        saved = self.current_group if was_real else None
        self.lang = lang_code
        self.current_group = self.t("all")
        self._progress_running = False
        self._settings_panel = None     # её уничтожит очистка окна ниже
        self._settings_btn = None
        self._prompt = None
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


# ── Keyboard listener (NSEvent — runs on main thread, no TSM crash) ──────────

_NS_FKEYS = {
    122:'F1', 120:'F2', 99:'F3', 118:'F4', 96:'F5', 97:'F6',
    98:'F7', 100:'F8', 101:'F9', 109:'F10', 103:'F11', 111:'F12',
}

def _ns_event_to_str(event):
    kc = event.keyCode()
    if kc in _NS_FKEYS:
        return _NS_FKEYS[kc]
    try:
        chars = event.charactersIgnoringModifiers()
        if chars and len(chars) == 1 and chars.isprintable():
            return chars.upper()
    except Exception:
        pass
    return None


# ── Значок в строке меню ────────────────────────────────────────────────────

_MENUBAR_APP = None          # кому адресованы клики по пунктам меню
_MENUBAR_TARGET_CLS = None


def _menubar_target_class():
    """ObjC-класс регистрируется в рантайме под своим именем и только один раз,
    поэтому создаём его лениво и кешируем."""
    global _MENUBAR_TARGET_CLS
    if _MENUBAR_TARGET_CLS is not None:
        return _MENUBAR_TARGET_CLS
    from Foundation import NSObject

    def _later(fn, *args):
        # Клик приходит из цикла событий AppKit. Трогать виджеты Tk оттуда
        # нельзя, поэтому работу перекладываем в очередь Tk через after().
        app = _MENUBAR_APP
        if app is not None:
            app.root.after(0, lambda: fn(app, *args))

    class _MenuBarTarget(NSObject):
        def playSound_(self, sender):
            try:
                name = sender.representedObject()
                if name:
                    _later(lambda app, n: app._play_sound(n), str(name))
            except Exception as e:
                print(f"[menubar] play error: {e}")

        def stopSound_(self, sender):
            _later(lambda app: app._stop_sound())

        def showWindow_(self, sender):
            _later(lambda app: app._show_window())

        def quitApp_(self, sender):
            _later(lambda app: app._quit_app())

    _MENUBAR_TARGET_CLS = _MenuBarTarget
    return _MenuBarTarget


class MenuBarIcon:
    """Значок в строке меню: запуск звуков без переключения на окно."""

    FAV_LIMIT = 6
    RECENT_LIMIT = 6

    def __init__(self, app):
        self.app = app
        self._item = None
        self._target = None

    def start(self):
        global _MENUBAR_APP
        try:
            from AppKit import NSStatusBar, NSVariableStatusItemLength
            _MENUBAR_APP = self.app
            self._target = _menubar_target_class().alloc().init()
            self._item = NSStatusBar.systemStatusBar().statusItemWithLength_(
                NSVariableStatusItemLength)
            button = self._item.button()
            if button is not None:
                button.setTitle_("🔊")
            self.rebuild()
            print("[startup] menu bar icon started")
            return True
        except Exception as e:
            print(f"[menubar] недоступен: {e}")
            return False

    def rebuild(self):
        """Перестроить меню. Вызывается при каждом изменении избранного и
        недавних — дешевле, чем следить за отдельными пунктами."""
        if self._item is None:
            return
        try:
            from AppKit import NSMenu, NSMenuItem
            t, data = self.app.t, self.app.data
            existing = set(get_all_sounds())

            menu = NSMenu.alloc().init()
            menu.setAutoenablesItems_(False)

            def header(title):
                it = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, None, "")
                it.setEnabled_(False)
                menu.addItem_(it)

            def entry(title, action, obj=None):
                it = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, "")
                it.setTarget_(self._target)
                if obj is not None:
                    it.setRepresentedObject_(obj)
                it.setEnabled_(True)
                menu.addItem_(it)

            def section(label, names, limit):
                names = [n for n in names if n in existing][:limit]
                if not names:
                    return
                header(label)
                for n in names:
                    entry("   " + n.rsplit('.', 1)[0], "playSound:", n)
                menu.addItem_(NSMenuItem.separatorItem())

            section(t("favorites"), data.get("favorites", []), self.FAV_LIMIT)
            section(t("recent"), data.get("recent", []), self.RECENT_LIMIT)

            entry(t("menubar_stop"), "stopSound:")
            entry(t("menubar_show"), "showWindow:")
            menu.addItem_(NSMenuItem.separatorItem())
            entry(t("menubar_quit"), "quitApp:")

            self._item.setMenu_(menu)
        except Exception as e:
            print(f"[menubar] rebuild error: {e}")


class GlobalListener:
    def __init__(self, app):
        self.app = app
        self._monitors = []
        self._pressed = set()
        self._fired = set()

    def start(self):
        try:
            from AppKit import NSEvent, NSApplication
            NSKeyDownMask = 1 << 10
            NSKeyUpMask   = 1 << 11

            def on_down(event):
                try:
                    # App in foreground — local hotkeys handle it
                    if NSApplication.sharedApplication().isActive():
                        return
                    if self.app._recording_for:
                        self._pressed.clear(); self._fired.clear()
                        return
                    key_str = _ns_event_to_str(event)
                    if not key_str:
                        return
                    self._pressed.add(key_str)
                    hotkeys = self.app.data.get("hotkeys", {})
                    for filename, binding in hotkeys.items():
                        chord = frozenset([binding] if isinstance(binding, str) else binding)
                        if chord and chord <= self._pressed and chord not in self._fired:
                            self._fired.add(chord)
                            self.app.root.after(0, lambda f=filename: self.app._play_sound(f))
                except Exception as e:
                    print(f"[hotkey] ERROR: {e}")

            def on_up(event):
                try:
                    key_str = _ns_event_to_str(event)
                    if key_str:
                        self._pressed.discard(key_str)
                        self._fired = {c for c in self._fired if key_str not in c}
                except Exception:
                    pass

            m1 = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, on_down)
            m2 = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSKeyUpMask, on_up)
            if m1:
                self._monitors = [m for m in (m1, m2) if m]
                print("[startup] NSEvent GlobalListener started")
            else:
                print("[startup] NSEvent GlobalListener: grant Accessibility permission")
        except Exception as e:
            print(f"[startup] GlobalListener failed: {e}")

    def stop(self):
        try:
            from AppKit import NSEvent
            for m in self._monitors:
                NSEvent.removeMonitor_(m)
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

    # BlackHole помнит свою громкость между запусками; на 11% это -57 дБ на весь
    # тракт, и Discord получает почти тишину. Проверяем и поднимаем при старте.
    libs.func.ensure_cable_volume(s.get("vb_device") or None)

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
    GlobalListener(app).start()
    app.menubar = MenuBarIcon(app)
    app.menubar.start()
    root.mainloop()
