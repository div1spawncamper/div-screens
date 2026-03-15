# div-screens

Open-source, cross-platform dashboard manager for USB LCD smart screens. Replace the janky vendor software with something you actually control.

Built for the cheap 3.5"/5"/8.8" USB-C LCD screens sold on AliExpress, Amazon, etc. under names like "Turing Smart Screen", "XuanFang", "Kipye Qiye", "UsbPCMonitor", and dozens of unbranded clones. These screens are typically marketed as "PC system monitors" and ship with a Windows-only app that lets you pick from a handful of ugly themes. div-screens replaces all of that.

## What are these screens?

They're small IPS LCD panels (320x480, 480x800, or 600x1024 depending on model) connected via USB-C. Inside, a **WCH CH552T** microcontroller acts as a USB-to-SPI bridge -- it receives pixel data over USB serial and pushes it to the LCD controller. The screen has no intelligence of its own; it needs a host computer sending frames continuously.

The screens show a "download turzx.com" splash on power-up (hardcoded in the CH552 firmware, not changeable without hardware modification). Once the host software connects, it takes over and displays whatever you want.

**Common characteristics:**
- Resolution: 320x480 (3.5"), 480x800 (5"), 600x1024 (8.8")
- Interface: USB-C (appears as USB serial / CDC ACM device)
- Chip: WCH CH552T (USB VID `1a86`, PID `5722` for most models)
- Protocol: Proprietary serial commands + RGB565 bitmap data
- Frame rate: ~0.5 FPS for full frame (limited by serial throughput)
- Two USB-C ports: one for data, one for power passthrough (daisy-chaining power only, not data)
- No onboard storage, no standalone operation

## Features

- **Auto-detection**: Plug in a screen, div-screens finds it instantly. Unplug it, it handles that too. Multiple screens supported simultaneously.
- **Hot-plug**: Screens can be connected/disconnected at any time without restarting the app.
- **Visual layout editor**: Web-based drag & drop editor served locally. Design your dashboard on a canvas that matches the screen resolution exactly.
- **Modular widgets**: Clock, CPU bars, RAM, disk usage, network speed, per-core mini bars, text labels, separators, images, external API data.
- **Layout files**: Dashboards are defined as JSON files. Portable, shareable, version-controllable.
- **Cross-platform**: Windows, macOS, Linux. Same codebase, same layouts.
- **Portable or installed**: Run it as a standalone app, or install it as a system service that starts at boot.

## Supported Screens

| Screen | Size | Resolution | USB VID:PID | Status |
|--------|------|-----------|-------------|--------|
| Turing Smart Screen | 3.5" | 320x480 | `1a86:5722` | Supported |
| Turing Smart Screen | 5" | 480x800 | `1a86:5722` | Planned |
| Turing Smart Screen | 8.8" | 600x1024 | `0525:a4a7` | Planned |
| Turing Smart Screen | 2.1" round | 480x480 | `0525:a4a7` | Planned |
| XuanFang (Rev B/Flagship) | 3.5" | 320x480 | `1a86:5722` | Planned |
| UsbPCMonitor | 3.5"/5" | varies | `1a86:5722` | Planned |
| Kipye Qiye | 3.5" | 320x480 | `454d:4e41` | Planned |
| WeAct Studio | 3.5"/0.96" | varies | `1a86:fe0c` | Planned |

If your screen uses a CH552/CH340 USB serial chip and shows "turzx.com" on boot, it will probably work.

## Quick Start

### Prerequisites

- Python 3.10+
- The screen connected via USB (on Windows, the CH340 driver should install automatically)

### Run

```bash
# Clone
git clone https://github.com/div1spawncamper/div-screens.git
cd div-screens

# Install Python dependencies
pip install -r backend/requirements.txt

# Run in CLI mode (auto-detects screens, loads default layout)
python -m backend.main --cli

# Run with web editor on http://localhost:8069
python -m backend.main
```

### WSL2 Users

If you're running from WSL2, the USB device needs to be forwarded from Windows using [usbipd-win](https://github.com/dorssel/usbipd-win):

```powershell
# PowerShell (admin) -- find your screen's BUSID
usbipd list

# Attach to WSL (use --auto-attach to survive USB resets)
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID> --auto-attach
```

The screen should then appear as `/dev/ttyACM0` in WSL.

## How It Works

```
┌─────────────────────────────────────────────────┐
│                  div-screens                     │
│                                                  │
│  Browser (localhost:8069)                        │
│  ┌────────────────────────────────────────────┐  │
│  │         Svelte Layout Editor               │  │
│  │  [Widget Palette] [320x480 Canvas] [Props] │  │
│  └──────────────────┬─────────────────────────┘  │
│                     │ REST + WebSocket            │
│  ┌──────────────────▼─────────────────────────┐  │
│  │            FastAPI Server                   │  │
│  │  /api/screens  /api/layouts  /ws/preview    │  │
│  └──┬──────────────┬─────────────────────┬────┘  │
│     │              │                     │        │
│  ScreenManager  WidgetEngine        LayoutStore   │
│  (hot-plug      (clock, cpu,        (JSON files)  │
│   polling)       ram, net...)                     │
│     │              │                              │
│     └──────┬───────┘                              │
│            │                                      │
│       Renderer (Pillow)                           │
│       compose frame -> RGB565 -> bulk serial      │
│            │                                      │
│     ┌──────▼──────┐                               │
│     │ LCD Screen  │  /dev/ttyACM0 (115200 baud)   │
│     │ 320x480 px  │  CH552T -> SPI -> IPS LCD     │
│     └─────────────┘                               │
└─────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Bulk serial writes**: Instead of sending the frame in 120+ small chunks (which causes visible tearing), we send the entire RGB565 buffer in a single `write()` call. This cuts frame time from ~2.6s to ~1s.
- **Full-frame render**: Each cycle renders the entire screen as one PIL Image and sends it atomically. No partial updates, no flicker.
- **Layout as data**: Dashboards are JSON files, not code. The editor produces JSON, the renderer consumes JSON. You can hand-edit them, share them, or generate them programmatically.

## Layout Format

Layouts are JSON files in the `layouts/` directory. Each screen gets assigned a layout.

```json
{
  "name": "My Dashboard",
  "screen": { "width": 320, "height": 480, "orientation": "portrait" },
  "background": { "color": [15, 15, 25] },
  "widgets": [
    {
      "id": "header-clock",
      "type": "clock",
      "x": 0, "y": 0, "w": 320, "h": 28,
      "config": {
        "format": "%a %d %b %Y - %H:%M:%S",
        "locale": "es",
        "font": "JetBrainsMono-Medium",
        "fontSize": 15,
        "color": [0, 200, 255],
        "background": [30, 30, 50]
      }
    },
    {
      "id": "cpu-bar",
      "type": "bar",
      "x": 12, "y": 54, "w": 296, "h": 10,
      "config": {
        "source": "cpu.percent",
        "colorLow": [0, 230, 100],
        "colorMid": [255, 200, 0],
        "colorHigh": [255, 60, 60],
        "thresholds": [50, 80]
      }
    }
  ]
}
```

## Available Widget Types

| Type | Description | Data Source |
|------|-------------|------------|
| `clock` | Date and time display | System clock |
| `text` | Static label or dynamic value | Literal string or any metric source |
| `bar` | Horizontal progress bar with color thresholds | Any numeric metric |
| `mini_bars` | Grid of small bars (e.g. per-core CPU) | Array metric (e.g. `cpu.percent_per_core`) |
| `separator` | Horizontal line divider | None |
| `image` | Static image/logo | File path |
| `api` | Data from external HTTP API | URL + JSON path |

## Data Sources

Widgets can bind to system metrics using dot-notation source strings:

| Source | Returns | Example |
|--------|---------|---------|
| `cpu.percent` | CPU usage % | `42.5` |
| `cpu.percent_per_core` | Per-core % array | `[12, 45, 8, ...]` |
| `cpu.frequency` | Current GHz | `"4.52"` |
| `ram.percent` | RAM usage % | `67.3` |
| `ram.used` | Used RAM (GB string) | `"21.4"` |
| `ram.total` | Total RAM (GB string) | `"32"` |
| `disk.C.percent` | Disk C: usage % | `46.9` |
| `disk.C.label` | Volume label | `"Windows"` |
| `disk.E.label` | Volume label | `"games-fast"` |
| `net.upload_speed_fmt` | Formatted upload speed | `"1.2 MB/s"` |
| `net.download_speed_fmt` | Formatted download speed | `"45.3 KB/s"` |
| `sys.uptime` | System uptime | `"3d 14h 22m"` |
| `sys.processes` | Process count | `342` |

## CLI Options

```
python -m backend.main [OPTIONS]

Options:
  --cli              Run without API server (headless mode)
  --port PORT        API server port (default: 8069)
  --brightness N     Screen brightness 0-100 (default: 25)
  --layout FILE      Layout JSON file to use (default: layouts/default.json)
```

## Roadmap

- [x] Screen protocol (Turing Rev A)
- [x] Auto-detection and hot-plug
- [x] Widget engine (clock, bar, text, mini_bars, separator)
- [x] Render engine with bulk serial writes
- [x] FastAPI server with REST + WebSocket
- [x] Layout JSON format
- [ ] Svelte editor with drag & drop
- [ ] Live preview via WebSocket
- [ ] System tray icon (pystray)
- [ ] Image widget
- [ ] Line graph widget
- [ ] External API widget
- [ ] GPU metrics (Nvidia/AMD)
- [ ] Support for Rev B (XuanFang), Rev C (5"/8.8"), Rev D (Kipye)
- [ ] Service installation scripts (systemd, Task Scheduler, LaunchAgent)
- [ ] PyInstaller packaging (single binary per OS)
- [ ] Theme presets / layout gallery

## Credits

Serial protocol reverse-engineered by the [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) project (GPL-3.0) by [@mathoudebine](https://github.com/mathoudebine) and contributors. div-screens adapts the protocol implementation for its own architecture.

## License

MIT
