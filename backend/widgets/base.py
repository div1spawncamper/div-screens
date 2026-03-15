"""Base widget class for all renderable widgets."""

from abc import ABC, abstractmethod
from typing import Any

from PIL import Image, ImageDraw, ImageFont


class BaseWidget(ABC):
    """Abstract base for all dashboard widgets."""

    def __init__(self, widget_id: str, x: int, y: int, w: int, h: int, config: dict):
        self.id = widget_id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.config = config

    @abstractmethod
    def render(self, draw: ImageDraw.ImageDraw, fonts: dict) -> None:
        """Render this widget onto the given ImageDraw surface.

        Coordinates are absolute (already offset by x, y from layout).
        """
        ...

    def get_font(self, fonts: dict, name: str = None, size: int = None) -> ImageFont.FreeTypeFont:
        font_name = name or self.config.get("font", "JetBrainsMono-Regular")
        font_size = size or self.config.get("fontSize", 13)
        key = (font_name, font_size)
        if key not in fonts:
            # Try loading from fonts directory
            import os
            font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fonts")
            for subdir in os.listdir(font_dir):
                path = os.path.join(font_dir, subdir, f"{font_name}.ttf")
                if os.path.exists(path):
                    fonts[key] = ImageFont.truetype(path, font_size)
                    return fonts[key]
            # Fallback
            fonts[key] = ImageFont.load_default()
        return fonts[key]

    def get_color(self, key: str = "color", default=(220, 220, 220)) -> tuple:
        val = self.config.get(key, default)
        if isinstance(val, (list, tuple)):
            return tuple(val)
        return default
