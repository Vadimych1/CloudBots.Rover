from miniros.source import Packet
from PIL import Image as pilimg
import numpy as np
from base64 import b64decode, b64encode

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
    
    def load_image(self, image: pilimg.Image) -> None:
        self.image = image
        self.set("width", image.width)
        self.set("height", image.height)

        data = b64encode(image.tobytes()).decode()
        self.set("image_data", data)

        return self
    
    def get_image(self) -> pilimg.Image:
        return pilimg.frombytes("RGB", (self.get("width"), self.get("height")), b64decode(self.get("image_data")))
    
    def get_image_array(self) -> np.ndarray:
        return np.array(self.get_image())