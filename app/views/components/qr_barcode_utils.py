from __future__ import annotations

import os
import tempfile
from typing import Literal

import qrcode
from PIL import Image
from barcode import Code128
from barcode.writer import ImageWriter


def generate_qr_png(data: str) -> str:
    img = qrcode.make(data)
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(path)
    return path


def generate_barcode_png(data: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    code = Code128(data, writer=ImageWriter())
    code.save(path[:-4])  # writer adiciona extensão
    # garante caminho com .png
    if not os.path.exists(path):
        path = path[:-4] + ".png"
    return path
