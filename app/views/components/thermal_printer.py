from __future__ import annotations

import os
from typing import Optional

from PIL import Image

try:
    from escpos.printer import Usb, Serial, Network
except Exception:  # libs podem não estar instaladas
    Usb = Serial = Network = None  # type: ignore


class ThermalPrinter:
    def __init__(self, usb: Optional[tuple[int, int]] = None, serial_port: Optional[str] = None, host: Optional[str] = None, baudrate: int = 9600):
        self._p = None
        try:
            if usb and Usb:
                vid, pid = usb
                self._p = Usb(vid, pid, timeout=0, in_ep=0x82, out_ep=0x01)
            elif serial_port and Serial:
                self._p = Serial(devfile=serial_port, baudrate=baudrate)
            elif host and Network:
                self._p = Network(host)
        except Exception:
            self._p = None

    def available(self) -> bool:
        return self._p is not None

    def print_text(self, text: str) -> bool:
        if not self._p:
            return False
        try:
            self._p.text(text)
            self._p.text("\n")
            return True
        except Exception:
            return False

    def print_image(self, image_path: str, width: int = 384) -> bool:
        if not self._p or not os.path.exists(image_path):
            return False
        try:
            img = Image.open(image_path)
            if img.width > width:
                ratio = width / img.width
                img = img.resize((width, int(img.height * ratio)))
            self._p.image(img)
            return True
        except Exception:
            return False

    def cut(self) -> None:
        if not self._p:
            return
        try:
            self._p.cut()
        except Exception:
            pass
