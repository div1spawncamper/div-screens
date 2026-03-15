# div-screens

Cross-platform USB LCD dashboard manager for Turing Smart Screen and compatible devices.

**Features:**
- Auto-detect and hot-plug USB LCD screens
- Visual drag & drop layout editor (web-based)
- Modular widget system (clock, CPU, RAM, disk, network, custom API)
- Runs as portable app or system service
- Windows, macOS, Linux

## Quick Start

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run in CLI mode (auto-detects screens)
python -m backend.main --cli

# Run with web editor
python -m backend.main
# Open http://localhost:8069 in your browser
```

## Architecture

See [PLAN.md](PLAN.md) for full architecture documentation.

```
Browser (localhost:8069)  <-->  FastAPI  <-->  ScreenManager
        Editor UI                               |
     (Svelte + Canvas)                    WidgetEngine
                                               |
                                          Renderer
                                         (Pillow)
                                               |
                                         LCD Screen(s)
                                        (USB serial)
```

## Project Structure

```
div-screens/
├── backend/           # Python backend
│   ├── main.py        # Entry point
│   ├── screens/       # Screen detection & serial protocol
│   ├── widgets/       # Widget types (clock, bar, text, etc.)
│   ├── renderer/      # Frame composition engine
│   ├── api/           # FastAPI REST + WebSocket server
│   └── service/       # OS service integration (systray, autostart)
├── frontend/          # Svelte editor (web UI)
├── layouts/           # Layout JSON files
├── fonts/             # Bundled fonts
└── scripts/           # Build & packaging scripts
```

## License

MIT
