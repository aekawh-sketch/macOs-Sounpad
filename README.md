# Soundpad for macOS

A macOS soundboard app that routes audio directly into voice chat (Discord, Zoom, etc.) via a virtual audio cable — no third-party app needed.

[![Download](https://img.shields.io/badge/Download-v1.3-blue?style=for-the-badge)](https://github.com/aekawh-sketch/macOs-Sounpad/releases/download/v1.3/Soundpad-v1.3-macOS.zip)

> **Based on** [opaip/Soundpad](https://github.com/opaip/Soundpad) — extended with a full GUI, dark/light themes, device settings with profiles, drag-and-drop audio loading, sound groups, and dual-stream playback.

---

## Screenshots

> Add screenshots here after uploading to GitHub

---

## Features

- 🎵 Play `.wav` / `.mp3` sounds directly into Discord/Zoom mic input
- 🎧 Simultaneous monitoring output (hear what you play)
- 🎙️ Mic routing — your real microphone goes through the virtual cable too
- 🌗 Dark / Light theme
- 🗂️ Sound groups (organize sounds into folders)
- 📁 Drag & drop audio files to add sounds
- ⚙️ Audio device settings with named profiles (save/load/delete)
- 🌍 5 languages: English, Русский, Español, Deutsch, 中文
- ⌨️ Global hotkeys (requires Accessibility permission)
- 📊 Playback progress bar with scrubbing

---

## Requirements

### macOS

- macOS 12 Monterey or later (tested on macOS 15 Sequoia)
- Python 3.10+
- [BlackHole 2ch](https://existential.audio/blackhole/) — free virtual audio cable

### Python dependencies

```
pip install -r req.txt
```

You also need `ffmpeg` for MP3 → WAV conversion:

```bash
brew install ffmpeg
```

---

## Installation

### Step 1 — Install BlackHole

1. Download **BlackHole 2ch** from [existential.audio/blackhole](https://existential.audio/blackhole/)
2. Run the installer
3. Restart your Mac (or log out/in)
4. Verify: open **System Settings → Sound** — you should see "BlackHole 2ch" in the list

### Step 2 — Install Python 3

If you don't have Python 3.10+:

```bash
brew install python
```

Or download from [python.org](https://www.python.org/downloads/)

### Step 3 — Clone the repo

```bash
git clone https://github.com/aekawh-sketch/macOs-Sounpad.git
cd Soundpad
```

### Step 4 — Install dependencies

```bash
pip3 install -r req.txt
```

> **Note:** `tkinterdnd2` requires Tcl/Tk. If you get an error, install Python from python.org (not Homebrew), or run:
> ```bash
> brew install tcl-tk
> ```

### Step 5 — Create the audio folder

```bash
mkdir audio
```

Drop your `.wav` or `.mp3` files into the `audio/` folder, or use drag & drop inside the app.

### Step 6 — Run the app

```bash
python3 main.py
```

---

## First Launch Setup

1. The app will open. Go to **Settings** (gear icon ⚙)
2. Under **Microphone** — select your real microphone (e.g. "MacBook Pro Microphone")
3. Under **Virtual Cable (Discord)** — select **BlackHole 2ch**
4. Under **Monitor (Headphones)** — select your headphones or speakers
5. Click **Apply** — settings are saved automatically

### Discord Setup

In Discord **Voice Settings**:
- **Input Device** → `BlackHole 2ch`
- **Output Device** → your headphones/speakers

Now when you play a sound in Soundpad, Discord picks it up. Your mic voice also routes through BlackHole so people hear you normally.

---

## Accessibility Permission (for hotkeys)

Global keyboard shortcuts require Accessibility access:

1. Open **System Settings → Privacy & Security → Accessibility**
2. Add **Terminal** (if running from terminal) or **Soundpad.app** (if using built app)
3. Toggle it **ON**
4. Restart the app

Without this permission the app still works — hotkeys are just disabled.

---

## Build as .app (optional)

To build a standalone macOS `.app` bundle:

```bash
pip3 install py2app
python3 setup.py py2app --alias
```

The app will be in `dist/Soundpad.app`. Copy to `/Applications`:

```bash
rsync -a dist/Soundpad.app /Applications/
```

---

## Hotkeys (default)

| Key | Action |
|-----|--------|
| F1–F12 | Configurable per sound (set in UI) |
| Click on sound | Play |

---

## Project Structure

```
Soundpad/
├── main.py              # Main app (GUI + logic)
├── libs/
│   ├── func.py          # Audio engine (sounddevice streams)
│   └── recorder.py      # Mic recorder
├── setup.py             # py2app build config
├── AppIcon.icns         # App icon
├── req.txt              # Python dependencies
└── audio/               # Your sound files (not in repo)
```

---

## Troubleshooting

**App doesn't play sound into Discord**
- Make sure BlackHole 2ch is selected as Discord's input device
- Make sure "Virtual Cable" in Settings is set to "BlackHole 2ch"

**MP3 files don't play**
- Install ffmpeg: `brew install ffmpeg`

**Hotkeys don't work**
- Add the app/Terminal to Accessibility in System Settings (see above)

**`tkinterdnd2` install error**
- Use Python from python.org, not Homebrew. Or: `brew install tcl-tk`

---

## License

MIT — see [LICENSE](LICENSE)

Original project: [opaip/Soundpad](https://github.com/opaip/Soundpad) © 2024 Opaip  
This fork adds: full GUI, themes, device profiles, drag & drop, sound groups, multilingual support.
