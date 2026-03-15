"""Text widget for static or dynamic text display."""

from PIL import ImageDraw

from .base import BaseWidget


class TextWidget(BaseWidget):
    """Renders text, optionally from a data source."""

    def render(self, draw: ImageDraw.ImageDraw, fonts: dict, value: str = None) -> None:
        text = value if value is not None else self.config.get("text", "")
        font = self.get_font(fonts)
        color = self.get_color("color")
        bg = self.config.get("background")

        if bg:
            draw.rectangle([self.x, self.y, self.x + self.w, self.y + self.h], fill=tuple(bg))

        align = self.config.get("align", "left")
        if align == "right":
            bbox = draw.textbbox((0, 0), text, font=font)
            tx = self.x + self.w - (bbox[2] - bbox[0])
        elif align == "center":
            bbox = draw.textbbox((0, 0), text, font=font)
            tx = self.x + (self.w - (bbox[2] - bbox[0])) // 2
        else:
            tx = self.x

        draw.text((tx, self.y), text, font=font, fill=color)


class SeparatorWidget(BaseWidget):
    """Renders a horizontal separator line."""

    def render(self, draw: ImageDraw.ImageDraw, fonts: dict) -> None:
        color = self.get_color("color", (60, 60, 80))
        draw.line([(self.x, self.y), (self.x + self.w, self.y)], fill=color, width=1)
