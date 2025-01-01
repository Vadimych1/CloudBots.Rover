from miniros.source import Packet
from PIL import Image as pilimg
import zlib
import numpy as np

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
        print(len(self.get_additional_data("image_data")), "bytes")
    
    def load_image(self, image: pilimg.Image, compression_level: int = 9) -> None:
        self.image = image
        self.set("width", image.width)
        self.set("height", image.height)

        data = self._encode(image, compression_level)
        self.set_additional_data("image_data", data)

        return self
    
    def get_image(self) -> pilimg.Image:
        return self._decode(self.get_additional_data("image_data"))
    
    def get_image_array(self) -> np.ndarray:
        return np.array(self.get_image())
    
    def _encode(self, data: pilimg.Image, compression_level: int = 9) -> str:
        data = data.tobytes()
        return data
    
    def _decode(self, data: str) -> pilimg.Image:
        return pilimg.frombytes("RGB", (self.get("width"), self.get("height")), data)

# Some compression functions
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
