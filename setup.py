from setuptools import setup

APP = ['main.py']
# Шрифты редизайна едут внутри бандла: на чужой машине их в системе нет,
# а theme.register_fonts() подключает их только для своего процесса.
DATA_FILES = [('assets/fonts', [
    'assets/fonts/Onest.ttf',
    'assets/fonts/Unbounded.ttf',
    'assets/fonts/JetBrainsMono.ttf',
    'assets/fonts/OFL-Onest.txt',
    'assets/fonts/OFL-Unbounded.txt',
    'assets/fonts/OFL-JetBrainsMono.txt',
])]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'AppIcon.icns',
    'plist': {
        'CFBundleName': 'Soundpad',
        'CFBundleDisplayName': 'Soundpad',
        'CFBundleIdentifier': 'com.soundpad.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0',
        'NSMicrophoneUsageDescription': 'Soundpad needs microphone access to route audio.',
        'NSAccessibilityUsageDescription': 'Soundpad needs accessibility access for keyboard shortcuts.',
        'NSHighResolutionCapable': True,
    },
    # _sounddevice_data и _soundfile_data содержат нативные .dylib. Без явного
    # указания py2app пакует их в python313.zip, а dlopen не умеет грузить
    # библиотеки из архива (errno=20) — приложение падает на старте.
    'packages': ['customtkinter', 'darkdetect', 'pynput',
                 'sounddevice', '_sounddevice_data',
                 'soundfile', '_soundfile_data',
                 'pyaudio', 'tkinterdnd2', 'libs', 'AppKit', 'Foundation'],
    'includes': ['libs.func', 'libs.recorder', 'libs.macvolume', 'libs.theme', 'libs.icons'],
    'excludes': ['matplotlib', 'numpy.testing', 'test'],
    'no_zip': True,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
