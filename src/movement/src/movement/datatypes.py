from miniros.source import Packet

class MovementPacket(Packet):
    def __init__(self):
        super().__init__({"x": float, "y": float, "rotation": float})