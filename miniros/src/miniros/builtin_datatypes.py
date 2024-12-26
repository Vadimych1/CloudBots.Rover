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

class Image(Packet):
    """
    width: int
    height: int
    image_data: str
    """
    def __init__(self) -> None:
        self.image = None
        super().__init__({"width": int, "height": int, "image_data": str})

    def _print_debug(self) -> None:
        print(self.get("width"), "px (w)")
        print(self.get("height"), "px (h)")
        print(len(self.get("image_data")), "bytes")
    
    def load_image(self, image: pilimg.Image, compression_level: int = 9) -> None:
        self.image = image
        self.set("width", image.width)
        self.set("height", image.height)

        data = self._encode(image, compression_level)
        self.set("image_data", data)

        return self
    
    def get_image(self) -> pilimg.Image:
        return self._decode(self.get("image_data"))
    
    def get_image_array(self) -> np.ndarray:
        return np.array(self.get_image())
    
    def _encode(self, data: pilimg.Image, compression_level: int = 9) -> str:
        data = b64encode(deflate(data.tobytes(), compression_level)).decode()
        return data
    
    def _decode(self, data: str) -> pilimg.Image:
        return pilimg.frombytes("RGB", (self.get("width"), self.get("height")), inflate(b64decode(data)))
    
def deflate(data: bytes, compress_level=9):
    compress = zlib.compressobj(compress_level, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0)
    deflated = compress.compress(data)
    deflated += compress.flush()
    return deflated

def inflate(data: bytes):
    decompress = zlib.decompressobj(-zlib.MAX_WBITS)
    inflated = decompress.decompress(data)
    inflated += decompress.flush()
    return inflated