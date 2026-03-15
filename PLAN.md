# div-screens - Architecture Plan

## Overview

Cross-platform desktop app (Windows, macOS, Linux) for driving USB LCD smart screens (Turing Smart Screen 3.5", 5", 8.8", XuanFang, Kipye, WeAct, and compatible devices).

**Two modes:**
- **Portable**: Run the binary, it works. Close it, it stops.
- **Installed**: Registers as a system service for auto-start at boot.

**Visual editor**: Web-based drag & drop layout editor (Svelte + HTML5 Canvas) served locally. Design layouts by dragging widgets onto a canvas that replicates the screen at real resolution.

## Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend | Python 3.10+ | Reuses proven serial/render code |
| API | FastAPI + uvicorn | Async, native WebSocket, fast |
| Serial | pyserial | Battle-tested with all screen revisions |
| Metrics | psutil | Cross-platform system metrics |
| Rendering | Pillow + numpy | Frame composition + fast RGB565 conversion |
| System tray | pystray | Cross-platform tray icon |
| Frontend | Svelte | Lightweight, reactive |
| Canvas | HTML5 Canvas / Konva.js | Widget drag & drop |
| Packaging | PyInstaller | Single binary per OS |

## Architecture

```
                    Browser (localhost:8069)
                    Editor UI (Svelte)
                         |
                    REST + WebSocket
                         |
    +--------------------+--------------------+
    |              FastAPI Server              |
    +---------+-----------+---------+----------+
              |           |         |
     ScreenManager   WidgetEngine  LayoutStore
      (detect,        (clock,bar,   (JSON files)
       hotplug,        text,cpu,
       reconnect)      ram,net...)
              |           |
              +-----+-----+
                    |
               Renderer
            (Pillow compose
             + bulk serial)
                    |
              LCD Screen(s)
```

## Data Flow

1. **ScreenManager** polls for USB serial devices every 2s
2. When a screen is detected, it loads the assigned layout JSON
3. **WidgetEngine** gathers data (psutil, APIs, clock) per widget config
4. **Renderer** composites all widgets into a single PIL Image
5. Image is converted to RGB565 and sent as a bulk serial write
6. **Editor** (when open) receives live preview frames via WebSocket

## Layout JSON Schema

Each screen has a layout file. Layouts are portable and shareable.

```json
{
  "name": "My Dashboard",
  "screen": {
    "width": 320,
    "height": 480,
    "orientation": "portrait"
  },
  "background": {
    "color": [15, 15, 25]
  },
  "widgets": [
    {
      "id": "clock-1",
      "type": "clock",
      "x": 12, "y": 4, "w": 296, "h": 24,
      "config": {
        "format": "%a %d %b %Y - %H:%M:%S",
        "locale": "es",
        "font": "JetBrainsMono-Bold",
        "fontSize": 15,
        "color": [0, 200, 255],
        "background": [30, 30, 50]
      }
    },
    {
      "id": "cpu-bar-1",
      "type": "bar",
      "x": 12, "y": 60, "w": 296, "h": 10,
      "config": {
        "source": "cpu.percent",
        "colorLow": [0, 230, 100],
        "colorMid": [255, 200, 0],
        "colorHigh": [255, 60, 60],
        "thresholds": [50, 80],
        "radius": 3
      }
    }
  ]
}
```

## Widget Types

| Type | Description | Data Source |
|------|-------------|------------|
| `clock` | Date/time display | `datetime` |
| `text` | Static or dynamic text | literal or system metric |
| `bar` | Horizontal progress bar | system metric |
| `mini_bars` | Per-core CPU bars | `cpu.percent_per_core` |
| `graph` | Line graph with history | system metric |
| `image` | Static image/logo | file path |
| `separator` | Horizontal line | none |
| `api` | External API data | HTTP endpoint |

## System Metric Sources

| Source | Description |
|--------|-------------|
| `cpu.percent` | Total CPU usage % |
| `cpu.percent_per_core` | Per-core CPU % array |
| `cpu.frequency` | Current CPU frequency GHz |
| `ram.percent` | RAM usage % |
| `ram.used` | RAM used GB |
| `ram.total` | RAM total GB |
| `disk.<letter>.percent` | Disk usage % |
| `disk.<letter>.used` | Disk used GB |
| `disk.<letter>.total` | Disk total GB |
| `disk.<letter>.label` | Volume label |
| `net.upload_speed` | Upload bytes/s |
| `net.download_speed` | Download bytes/s |
| `net.total_sent` | Total sent GB |
| `net.total_recv` | Total received GB |
| `sys.uptime` | System uptime string |
| `sys.processes` | Process count |
| `sys.load` | Load average |

## Screen Detection

Auto-detection by USB VID/PID and serial number:

| Screen | VID:PID | Serial Number |
|--------|---------|---------------|
| Turing 3.5" | `1a86:5722` | `USB35INCHIPSV2` |
| Turing 5"/8.8" | `0525:a4a7` | `20080411` |
| XuanFang 3.5" | `1a86:5722` | `2017-2-25` |
| Kipye Qiye | `454d:4e41` | - |
| WeAct | `1a86:fe0c` | starts with `AB`/`AD` |

Hot-plug: ScreenManager polls `serial.tools.list_ports.comports()` every 2 seconds and connects/disconnects screens as they appear/disappear.

## OS Service Integration

| OS | Portable | Installed |
|----|----------|-----------|
| Windows | Standalone `.exe` | Task Scheduler at logon |
| Linux | AppImage / binary | systemd user service or XDG autostart `.desktop` |
| macOS | `.app` bundle | LaunchAgent plist in `~/Library/LaunchAgents/` |

## Editor Features

- Canvas at exact screen resolution (e.g. 320x480)
- Widget palette (drag to canvas)
- Properties panel (edit selected widget config)
- Live preview via WebSocket
- Multi-screen tabs
- Export/import layouts as JSON
- Theme presets

## Development Phases

1. **v0.1** - Backend skeleton + screen detection + renderer + basic widgets + systray
2. **v0.2** - FastAPI server + REST endpoints + WebSocket preview
3. **v0.3** - Svelte editor with canvas + drag/drop + properties
4. **v0.4** - Full widget library + API widget + graphs
5. **v0.5** - Service installation scripts per OS
6. **v1.0** - PyInstaller packaging + first release
