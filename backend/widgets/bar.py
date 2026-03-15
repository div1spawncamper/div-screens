"""Progress bar widget."""

from PIL import ImageDraw

from .base import BaseWidget


class BarWidget(BaseWidget):
    """Horizontal progress bar with dynamic color thresholds."""

    def render(self, draw: ImageDraw.ImageDraw, fonts: dict, value: float = 0) -> None:
        thresholds = self.config.get("thresholds", [50, 80])
        color_low = self.get_color("colorLow", (0, 230, 100))
        color_mid = self.get_color("colorMid", (255, 200, 0))
        color_high = self.get_color("colorHigh", (255, 60, 60))
        bg_color = self.get_color("barBackground", (40, 40, 60))
        radius = self.config.get("radius", 3)

        # Background
        draw.rounded_rectangle(
            [self.x, self.y, self.x + self.w, self.y + self.h],
            radius=radius,
            fill=bg_color,
        )

        # Fill
        fill_w = int(self.w * min(value, 100) / 100)
        if fill_w > 2:
            if value < thresholds[0]:
                color = color_low
            elif value < thresholds[1]:
                color = color_mid
            else:
                color = color_high

            draw.rounded_rectangle(
                [self.x, self.y, self.x + fill_w, self.y + self.h],
                radius=radius,
                fill=color,
            )


class MiniBarWidget(BaseWidget):
    """Small bar without labels, used for per-core CPU bars."""

    def render(self, draw: ImageDraw.ImageDraw, fonts: dict, values: list[float] = None) -> None:
        if not values:
            return

        cols = self.config.get("columns", 8)
        gap = self.config.get("gap", 3)
        bar_h = self.config.get("barHeight", 8)
        mini_w = (self.w - (cols - 1) * gap) // cols

        color_low = self.get_color("colorLow", (0, 230, 100))
        color_mid = self.get_color("colorMid", (255, 200, 0))
        color_high = self.get_color("colorHigh", (255, 60, 60))
        bg_color = self.get_color("barBackground", (40, 40, 60))
        thresholds = self.config.get("thresholds", [50, 80])

        for i, pct in enumerate(values):
            row = i // cols
            col = i % cols
            bx = self.x + col * (mini_w + gap)
            by = self.y + row * (bar_h + gap)

            draw.rounded_rectangle([bx, by, bx + mini_w, by + bar_h], radius=2, fill=bg_color)
            fill_w = int(mini_w * min(pct, 100) / 100)
            if fill_w > 0:
                if pct < thresholds[0]:
                    c = color_low
                elif pct < thresholds[1]:
                    c = color_mid
                else:
                    c = color_high
                draw.rounded_rectangle([bx, by, bx + fill_w, by + bar_h], radius=2, fill=c)
