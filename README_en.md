# AtRadio console - Console Radio Player

A console application for playing internet radio stations using VLC Media Player. Supports keyboard control, station list editing, and playlist save/load functionality.

## Features

- 🎵 Internet radio station playback via VLC
- 📋 Station list management (add, remove, edit)
- 🔧 Intuitive interface with keyboard navigation
- 💾 Save and load playlists in CSV format
- 🔊 Volume control during playback
- 📱 Move stations within the list
- 🚀 Automatic playback on startup

## Requirements

- Python 3.6+
- VLC Media Player
- Python libraries:
  - `curses` (built-in on Unix systems)
  - `click`
  - `telnetlib` (built-in)

## Installation

### 1. Install VLC Media Player

**Windows:**
- Download and install VLC from the [official website](https://www.videolan.org/vlc/)
- Make sure VLC is installed in the standard folder `C:\Program Files (x86)\VideoLAN\VLC\`

**Ubuntu/Debian:**
```bash
sudo apt install vlc
```

**Fedora:**
```bash
sudo dnf install vlc
```

**macOS (with Homebrew):**
```bash
brew install vlc
```

### 2. Install uv (if not installed)

```bash
# On Unix systems (Linux, macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip
pip install uv
```

### 3. Install dependencies and run

```bash
# Install dependencies
uv init # if pyproject.toml file doesn't exist
uv add click python-vlc 
```

For Windows, you need to install:

```bash
uv add windows-curses
```

```bash
# Run the application
uv run atradio.py

# Run with autoplay
uv run atradio.py --autoplay 0
```

### 4. Prepare project structure

Create the following folder structure:
```
atradio/
├── atradio.py
├── pyproject.toml  # will be created automatically when using uv
├── data/
│   └── radio_stations.csv
└── ui/
    ├── ui_interface.py
    └── ui_app.py
```

## Usage

### Basic launch
```bash
uv run atradio.py
```

### Automatic playback
```bash
uv run atradio.py --autoplay 0  # Start first station
uv run atradio.py --autoplay 5  # Start sixth station
```

## Controls

### Navigation
- **↑/↓** - Move through station list
- **Enter** - Play selected station
- **Esc** - Stop playback
- **Q** and **F10** - Exit program

### Station management
- **Insert** - Add new station
- **Delete** - Delete current station (with confirmation)
- **F3** - Enter station move mode
- **F4** - Edit current station
- **F2** - Save stations to file
- **F5** - Load stations from file located in project folder

### Audio control
- **+** - Increase volume by 10%
- **-** - Decrease volume by 10%

### Move mode (F3)
- **↑/↓** - Move station up/down
- **Enter** - Confirm new position
- **Esc** - Cancel move

## CSV file format

The stations file should have the following format:
```csv
Name;URL
Radio Mayak;http://icecast.vgtrk.cdnvideo.ru/mayakfm
Europa Plus;http://ep256.hostingradio.ru:8052/europaplus256.mp3
```

Fields are separated by semicolon (`;`).

## Project structure

- `atradio.py` - Main application file
- `data/radio_stations.csv` - Default radio stations file
- `ui/ui_interface.py` - User interface module
- `ui/ui_app.py` - Additional UI components

## Technical details

### VLC communication
The application controls VLC through a telnet interface on localhost:5000. VLC is launched with parameters:
- `--intf rc` - disable graphical interface
- `--rc-host localhost:5000` - enable remote control

### Supported platforms
- Windows (VLC path: `C:\Program Files (x86)\VideoLAN\VLC\vlc.exe`)
- Linux (command: `vlc`)
- macOS (command: `vlc`)

## Troubleshooting

### VLC not responding
- Make sure VLC is properly installed
- Check that port 5000 is not occupied by other applications
- Restart the application

### Encoding errors
- Make sure the CSV file is saved in UTF-8
- Check the correctness of separators in the CSV file

### Display issues
- Increase terminal size for correct display
- Make sure the terminal supports colors

## License

The project is distributed under the MIT license.

## Support

If you encounter problems, create an issue in the project repository or contact the developer.