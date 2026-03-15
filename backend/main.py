#!/usr/bin/env python3
"""div-screens: Cross-platform USB LCD dashboard manager.

Usage:
    python -m backend.main          # Start service + API server
    python -m backend.main --cli    # CLI mode, no API server
"""

import argparse
import logging
import os
import signal
import sys
import threading
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("div-screens")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUTS_DIR = os.path.join(BASE_DIR, "layouts")
DEFAULT_LAYOUT = os.path.join(LAYOUTS_DIR, "default.json")


def run_renderer(screen_manager, render_engine, stop_event: threading.Event):
    """Render loop: continuously render frames to all connected screens."""
    while not stop_event.is_set():
        for port, ms in list(screen_manager.screens.items()):
            if ms.connected and port in render_engine.layouts:
                elapsed = render_engine.render_and_send(ms)
                logger.debug(f"Frame for {port}: {elapsed:.2f}s")
        stop_event.wait(0.1)  # Small sleep between render cycles


def main():
    parser = argparse.ArgumentParser(description="div-screens dashboard manager")
    parser.add_argument("--cli", action="store_true", help="CLI mode (no API server)")
    parser.add_argument("--port", type=int, default=8069, help="API server port")
    parser.add_argument("--brightness", type=int, default=25, help="Screen brightness (0-100)")
    parser.add_argument("--layout", type=str, default=DEFAULT_LAYOUT, help="Layout file to use")
    args = parser.parse_args()

    logger.info("div-screens starting...")
    logger.info(f"Layouts dir: {LAYOUTS_DIR}")

    # Import components
    from .screens.manager import ScreenManager
    from .widgets.system import SystemDataSource
    from .renderer.engine import RenderEngine

    # Initialize
    data_source = SystemDataSource()
    render_engine = RenderEngine(data_source)
    screen_manager = ScreenManager(poll_interval=2.0, brightness=args.brightness)

    # When a screen connects, load the default layout
    def on_screen_connect(ms):
        logger.info(f"Screen connected: {ms.name} on {ms.port}")
        if os.path.exists(args.layout):
            render_engine.load_layout(ms.port, args.layout)
            ms.layout_file = args.layout
        else:
            logger.warning(f"Layout not found: {args.layout}")

    def on_screen_disconnect(ms):
        logger.info(f"Screen disconnected: {ms.name} from {ms.port}")

    screen_manager.on_connect(on_screen_connect)
    screen_manager.on_disconnect(on_screen_disconnect)

    # Start screen detection
    screen_manager.start()

    # Stop event
    stop_event = threading.Event()

    def shutdown(signum=None, frame=None):
        logger.info("Shutting down...")
        stop_event.set()
        screen_manager.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start render loop in background
    render_thread = threading.Thread(target=run_renderer, args=(screen_manager, render_engine, stop_event), daemon=True)
    render_thread.start()

    if args.cli:
        # CLI mode: just run until Ctrl+C
        logger.info("Running in CLI mode. Press Ctrl+C to stop.")
        try:
            while not stop_event.is_set():
                stop_event.wait(1)
        except KeyboardInterrupt:
            shutdown()
    else:
        # API server mode
        import uvicorn
        from .api.server import app as api_app
        from .api import server as api_module

        # Inject dependencies into the API module
        api_module.screen_manager = screen_manager
        api_module.render_engine = render_engine
        api_module.layouts_dir = LAYOUTS_DIR

        logger.info(f"API server starting on http://localhost:{args.port}")
        logger.info(f"Open the editor at http://localhost:{args.port}")

        try:
            uvicorn.run(api_app, host="0.0.0.0", port=args.port, log_level="warning")
        except KeyboardInterrupt:
            pass
        finally:
            shutdown()


if __name__ == "__main__":
    main()
