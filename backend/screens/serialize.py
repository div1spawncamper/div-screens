"""Image serialization for LCD screens. RGB565 conversion using numpy."""

from typing import Iterator, Literal

import numpy as np
from PIL import Image


def chunked(data: bytes, chunk_size: int) -> Iterator[bytes]:
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


def image_to_rgb565(image: Image.Image, endianness: Literal["big", "little"] = "little") -> bytes:
    """Convert a PIL Image to RGB565 byte array."""
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    rgb = np.asarray(image)
    rgb = rgb.reshape((image.size[1] * image.size[0], -1))

    r = rgb[:, 0].astype(np.uint16) >> 3
    g = rgb[:, 1].astype(np.uint16) >> 2
    b = rgb[:, 2].astype(np.uint16) >> 3
    rgb565 = (r << 11) | (g << 5) | b

    dtype = ">u2" if endianness == "big" else "<u2"
    return rgb565.astype(dtype).tobytes()
