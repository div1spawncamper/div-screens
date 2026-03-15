"""Serial protocol for Turing Smart Screen (Rev A) and compatible devices.

Adapted from turing-smart-screen-python (GPL-3.0) by mathoudebine.
"""

import logging
import time
from enum import IntEnum
from typing import Optional

import serial
import serial.tools.list_ports
from PIL import Image

from .serialize import image_to_rgb565

logger = logging.getLogger("div-screens.protocol")


class Command(IntEnum):
    HELLO = 0x45
    SET_ORIENTATION = 0x79
    DISPLAY_BITMAP = 0xC5
    SET_BRIGHTNESS = 0x6E
    RESET = 0x65
    CLEAR = 0x66
    SCREEN_OFF = 0x6C
    SCREEN_ON = 0x6D


class Orientation(IntEnum):
    PORTRAIT = 0
    LANDSCAPE = 2
    REVERSE_PORTRAIT = 1
    REVERSE_LANDSCAPE = 3


# Known screen identifiers for auto-detection
KNOWN_SCREENS = {
    "turing_3_5": {"vid": 0x1A86, "pid": 0x5722, "serial": "USB35INCHIPSV2", "width": 320, "height": 480},
    "turing_5": {"vid": 0x1A86, "pid": 0x5722, "serial": "USB35INCHIPS", "width": 480, "height": 800},
}


class TuringScreen:
    """Communicate with a Turing Smart Screen Rev A over serial."""

    def __init__(self, com_port: str, width: int = 320, height: int = 480):
        self.com_port = com_port
        self.width = width
        self.height = height
        self.orientation = Orientation.PORTRAIT
        self.lcd_serial: Optional[serial.Serial] = None

    def open(self) -> bool:
        """Open the serial connection."""
        try:
            self.lcd_serial = serial.Serial(self.com_port, 115200, timeout=1, rtscts=True)
            logger.info(f"Opened serial port {self.com_port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Cannot open {self.com_port}: {e}")
            return False

    def close(self):
        """Close the serial connection."""
        if self.lcd_serial and self.lcd_serial.is_open:
            self.lcd_serial.close()
            logger.info(f"Closed serial port {self.com_port}")

    @property
    def is_open(self) -> bool:
        return self.lcd_serial is not None and self.lcd_serial.is_open

    def _send_command(self, cmd: Command, x: int = 0, y: int = 0, ex: int = 0, ey: int = 0):
        """Send a 16-byte command packet."""
        buf = bytearray(16)
        buf[0] = x >> 2
        buf[1] = ((x & 3) << 6) + (y >> 4)
        buf[2] = ((y & 15) << 4) + (ex >> 6)
        buf[3] = ((ex & 63) << 2) + (ey >> 8)
        buf[4] = ey & 255
        buf[5] = cmd
        self.lcd_serial.write(bytes(buf))

    def initialize(self):
        """Send hello handshake and read sub-revision."""
        hello = bytearray(16)
        hello[5] = Command.HELLO
        self.lcd_serial.write(bytes(hello))
        response = self.lcd_serial.read(6)
        self.lcd_serial.reset_input_buffer()
        logger.info(f"Screen hello response: {response.hex()}")

    def set_brightness(self, level: int = 25):
        """Set brightness (0-100)."""
        level = max(0, min(100, level))
        absolute = int(255 - ((level / 100) * 255))
        self._send_command(Command.SET_BRIGHTNESS, absolute)

    def set_orientation(self, orientation: Orientation = Orientation.PORTRAIT):
        """Set screen orientation."""
        self.orientation = orientation
        w = self.width if orientation in (Orientation.PORTRAIT, Orientation.REVERSE_PORTRAIT) else self.height
        h = self.height if orientation in (Orientation.PORTRAIT, Orientation.REVERSE_PORTRAIT) else self.width

        buf = bytearray(16)
        buf[5] = Command.SET_ORIENTATION
        buf[6] = orientation + 100
        buf[7] = w >> 8
        buf[8] = w & 255
        buf[9] = h >> 8
        buf[10] = h & 255
        self.lcd_serial.write(bytes(buf))

    def get_width(self) -> int:
        if self.orientation in (Orientation.PORTRAIT, Orientation.REVERSE_PORTRAIT):
            return self.width
        return self.height

    def get_height(self) -> int:
        if self.orientation in (Orientation.PORTRAIT, Orientation.REVERSE_PORTRAIT):
            return self.height
        return self.width

    def display_image(self, image: Image.Image, x: int = 0, y: int = 0):
        """Send a PIL image to the screen. Uses bulk write for minimal tearing."""
        img_w, img_h = image.size
        screen_w, screen_h = self.get_width(), self.get_height()

        if x + img_w > screen_w:
            img_w = screen_w - x
        if y + img_h > screen_h:
            img_h = screen_h - y
        if img_w != image.size[0] or img_h != image.size[1]:
            image = image.crop((0, 0, img_w, img_h))

        x1 = x + img_w - 1
        y1 = y + img_h - 1

        rgb565 = image_to_rgb565(image, "little")
        self._send_command(Command.DISPLAY_BITMAP, x, y, x1, y1)
        # Bulk write: single write for minimum tearing
        self.lcd_serial.write(rgb565)

    @staticmethod
    def auto_detect() -> list[dict]:
        """Detect all connected Turing-compatible screens.

        Returns a list of dicts with keys: port, vid, pid, serial, name, width, height
        """
        screens = []
        for port_info in serial.tools.list_ports.comports():
            for name, spec in KNOWN_SCREENS.items():
                match = False
                if port_info.serial_number == spec["serial"]:
                    match = True
                elif port_info.vid == spec["vid"] and port_info.pid == spec["pid"]:
                    match = True

                if match:
                    screens.append({
                        "port": port_info.device,
                        "vid": port_info.vid,
                        "pid": port_info.pid,
                        "serial": port_info.serial_number,
                        "name": name,
                        "width": spec["width"],
                        "height": spec["height"],
                    })
                    break
        return screens
