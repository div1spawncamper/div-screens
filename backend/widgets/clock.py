"""Clock/date widget."""

from datetime import datetime

from PIL import ImageDraw

from .base import BaseWidget

DIAS = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


class ClockWidget(BaseWidget):
    """Displays current date/time."""

    def render(self, draw: ImageDraw.ImageDraw, fonts: dict) -> None:
        now = datetime.now()
        fmt = self.config.get("format", "%H:%M:%S")
        locale = self.config.get("locale", "en")

        if locale == "es":
            # Manual Spanish formatting
            text = fmt
            text = text.replace("%a", DIAS[now.weekday()])
            text = text.replace("%b", MESES[now.month - 1])
            text = text.replace("%d", str(now.day))
            text = text.replace("%Y", str(now.year))
            text = text.replace("%H", f"{now.hour:02d}")
            text = text.replace("%M", f"{now.minute:02d}")
            text = text.replace("%S", f"{now.second:02d}")
        else:
            text = now.strftime(fmt)

        font = self.get_font(fonts)
        color = self.get_color("color")
        bg = self.config.get("background")

        if bg:
            draw.rectangle([self.x, self.y, self.x + self.w, self.y + self.h], fill=tuple(bg))

        align = self.config.get("align", "left")
        if align == "center":
            bbox = draw.textbbox((0, 0), text, font=font)
            tx = self.x + (self.w - (bbox[2] - bbox[0])) // 2
        elif align == "right":
            bbox = draw.textbbox((0, 0), text, font=font)
            tx = self.x + self.w - (bbox[2] - bbox[0])
        else:
            tx = self.x

        draw.text((tx, self.y), text, font=font, fill=color)
