"""Lossless, one-bit indexed PNG transport for binary segmentation masks."""

from io import BytesIO

import numpy as np
from PIL import Image
from sensor_msgs.msg import CompressedImage


def encode_mask(mask: np.ndarray, header) -> CompressedImage:
    """Encode a full-size binary mask with black/white palette entries."""
    # Mode P and bits=1 are both required: mode 1 produces a grayscale PNG,
    # while a palette image without bits=1 can store eight bits per pixel.
    image = Image.fromarray(mask.astype(bool).astype(np.uint8), mode='P')
    image.putpalette(bytes((0, 0, 0, 255, 255, 255)))
    with BytesIO() as buffer:
        image.save(buffer, format='PNG', bits=1, compress_level=9)
        message = CompressedImage()
        message.header = header
        message.format = 'mono8; png compressed'
        message.data = buffer.getvalue()
    return message
