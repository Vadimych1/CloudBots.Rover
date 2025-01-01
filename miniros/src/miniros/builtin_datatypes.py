from miniros.source import Packet
from PIL import Image as pilimg
import numpy as np
from base64 import b64decode, b64encode

# bzip2
from bz2 import compress as bzip_compress
from bz2 import decompress as bzip_decompress

# deflate
import zlib

class XYZ(Packet):
    """
    x: float
    y: float
    z: float
    """
    def __init__(self) -> None:
        super().__init__({"x": float, "y": float, "z": float})

class String(Packet):
    """
    param_name: str
    """
    def __init__(self, param_name: str) -> None:
        super().__init__({param_name: str})

class Bool(Packet):
    """
    param_name: bool
    """
    def __init__(self, param_name: str) -> None:
        super().__init__({param_name: bool})

class Float(Packet):
    """
    param_name: float
    """
    def __init__(self, param_name: str) -> None:
        super().__init__({param_name: float})

class Int(Packet):
    """
    param_name: int
    """
    def __init__(self, param_name: str) -> None:
        super().__init__({param_name: int})

class Array(Packet):
    """
    param_name: list
    """
    def __init__(self, param_name: str) -> None:
        super().__init__({param_name: list})

class Dict(Packet):
    """
    param_name: dict
    """
    def __init__(self, param_name: str) -> None:
        super().__init__({param_name: dict})
