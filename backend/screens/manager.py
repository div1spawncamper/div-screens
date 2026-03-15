"""Screen Manager: auto-detection, hot-plug, and lifecycle management."""

import logging
import threading
import time
from typing import Callable, Optional

from .protocol import TuringScreen, Orientation

logger = logging.getLogger("div-screens.manager")


class ManagedScreen:
    """A screen with its connection state and assigned layout."""

    def __init__(self, port: str, width: int, height: int, name: str):
        self.port = port
        self.width = width
        self.height = height
        self.name = name
        self.screen = TuringScreen(port, width, height)
        self.layout_file: Optional[str] = None
        self.connected = False

    def connect(self, brightness: int = 25) -> bool:
        if self.screen.open():
            self.screen.initialize()
            self.screen.set_brightness(brightness)
            self.screen.set_orientation(Orientation.PORTRAIT)
            self.connected = True
            logger.info(f"Screen '{self.name}' connected on {self.port}")
            return True
        return False

    def disconnect(self):
        self.screen.close()
        self.connected = False
        logger.info(f"Screen '{self.name}' disconnected from {self.port}")


class ScreenManager:
    """Manages multiple screens with hot-plug detection."""

    def __init__(self, poll_interval: float = 2.0, brightness: int = 25):
        self.poll_interval = poll_interval
        self.brightness = brightness
        self.screens: dict[str, ManagedScreen] = {}  # keyed by port
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_connect: Optional[Callable[[ManagedScreen], None]] = None
        self._on_disconnect: Optional[Callable[[ManagedScreen], None]] = None

    def on_connect(self, callback: Callable[[ManagedScreen], None]):
        """Register callback for when a screen is connected."""
        self._on_connect = callback

    def on_disconnect(self, callback: Callable[[ManagedScreen], None]):
        """Register callback for when a screen is disconnected."""
        self._on_disconnect = callback

    def scan(self) -> list[dict]:
        """Scan for connected screens. Returns list of detected screen info."""
        return TuringScreen.auto_detect()

    def _poll_loop(self):
        """Background thread: poll for screen connect/disconnect."""
        while self._running:
            try:
                detected = self.scan()
                detected_ports = {s["port"] for s in detected}

                # New screens
                for info in detected:
                    port = info["port"]
                    if port not in self.screens:
                        ms = ManagedScreen(port, info["width"], info["height"], info["name"])
                        if ms.connect(self.brightness):
                            self.screens[port] = ms
                            if self._on_connect:
                                self._on_connect(ms)

                # Disconnected screens
                for port in list(self.screens.keys()):
                    if port not in detected_ports:
                        ms = self.screens.pop(port)
                        ms.disconnect()
                        if self._on_disconnect:
                            self._on_disconnect(ms)

            except Exception as e:
                logger.error(f"Poll error: {e}")

            time.sleep(self.poll_interval)

    def start(self):
        """Start the hot-plug detection loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="screen-poll")
        self._thread.start()
        logger.info("ScreenManager started")

    def stop(self):
        """Stop polling and disconnect all screens."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        for ms in self.screens.values():
            ms.disconnect()
        self.screens.clear()
        logger.info("ScreenManager stopped")

    def get_screen(self, port: str) -> Optional[ManagedScreen]:
        return self.screens.get(port)

    def list_screens(self) -> list[dict]:
        """Return info about all connected screens."""
        return [
            {
                "port": ms.port,
                "name": ms.name,
                "width": ms.width,
                "height": ms.height,
                "connected": ms.connected,
                "layout": ms.layout_file,
            }
            for ms in self.screens.values()
        ]
