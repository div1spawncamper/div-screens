"""Render engine: composes widgets into a single PIL frame and sends to screen."""

import json
import logging
import os
import time
from typing import Optional

from PIL import Image, ImageDraw

from ..widgets.base import BaseWidget
from ..widgets.clock import ClockWidget
from ..widgets.bar import BarWidget, MiniBarWidget
from ..widgets.text import TextWidget, SeparatorWidget
from ..widgets.system import SystemDataSource
from ..screens.manager import ManagedScreen

logger = logging.getLogger("div-screens.renderer")

WIDGET_TYPES = {
    "clock": ClockWidget,
    "bar": BarWidget,
    "mini_bars": MiniBarWidget,
    "text": TextWidget,
    "separator": SeparatorWidget,
}


class RenderEngine:
    """Loads a layout JSON, creates widget instances, renders frames."""

    def __init__(self, data_source: SystemDataSource):
        self.data_source = data_source
        self.fonts: dict = {}  # Font cache
        self.layouts: dict[str, dict] = {}  # port -> parsed layout
        self.widgets: dict[str, list] = {}  # port -> list of widget instances

    def load_layout(self, port: str, layout_path: str) -> bool:
        """Load a layout JSON file for a screen."""
        try:
            with open(layout_path, "r") as f:
                layout = json.load(f)
            self.layouts[port] = layout
            self._build_widgets(port, layout)
            logger.info(f"Loaded layout '{layout.get('name', 'unnamed')}' for {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to load layout {layout_path}: {e}")
            return False

    def _build_widgets(self, port: str, layout: dict):
        """Instantiate widget objects from layout config."""
        widgets = []
        for w_data in layout.get("widgets", []):
            w_type = w_data.get("type")
            cls = WIDGET_TYPES.get(w_type)
            if cls:
                widget = cls(
                    widget_id=w_data.get("id", f"{w_type}-auto"),
                    x=w_data.get("x", 0),
                    y=w_data.get("y", 0),
                    w=w_data.get("w", 100),
                    h=w_data.get("h", 20),
                    config=w_data.get("config", {}),
                )
                widgets.append((widget, w_data.get("config", {})))
            else:
                logger.warning(f"Unknown widget type: {w_type}")
        self.widgets[port] = widgets

    def render_frame(self, port: str, width: int, height: int) -> Optional[Image.Image]:
        """Render a single frame for the given screen port."""
        layout = self.layouts.get(port)
        if not layout:
            return None

        bg_color = tuple(layout.get("background", {}).get("color", [15, 15, 25]))
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        for widget, config in self.widgets.get(port, []):
            try:
                source = config.get("source")

                if isinstance(widget, ClockWidget):
                    widget.render(draw, self.fonts)
                elif isinstance(widget, (BarWidget,)):
                    value = self.data_source.get(source) if source else 0
                    widget.render(draw, self.fonts, value=float(value or 0))
                elif isinstance(widget, MiniBarWidget):
                    values = self.data_source.get(source) if source else []
                    widget.render(draw, self.fonts, values=values or [])
                elif isinstance(widget, TextWidget):
                    if source:
                        value = self.data_source.get(source)
                        widget.render(draw, self.fonts, value=str(value or ""))
                    else:
                        widget.render(draw, self.fonts)
                elif isinstance(widget, SeparatorWidget):
                    widget.render(draw, self.fonts)
                else:
                    widget.render(draw, self.fonts)
            except Exception as e:
                logger.error(f"Widget {widget.id} render error: {e}")

        return img

    def render_and_send(self, screen: ManagedScreen) -> float:
        """Render a frame and send it to the screen. Returns elapsed time."""
        start = time.perf_counter()

        img = self.render_frame(screen.port, screen.width, screen.height)
        if img and screen.connected:
            try:
                screen.screen.display_image(img, 0, 0)
            except Exception as e:
                logger.error(f"Send error on {screen.port}: {e}")
                screen.connected = False

        return time.perf_counter() - start
