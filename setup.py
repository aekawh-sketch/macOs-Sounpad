from setuptools import setup

APP = ['main.py']
DATA_FILES = []
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
    'packages': ['customtkinter', 'darkdetect', 'pynput', 'sounddevice', 'soundfile', 'pyaudio', 'tkinterdnd2', 'libs'],
    'includes': ['libs.func', 'libs.recorder'],
    'excludes': ['matplotlib', 'numpy.testing', 'test'],
    'no_zip': True,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
