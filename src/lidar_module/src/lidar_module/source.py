from rplidar import RPLidar
import time
import math
from miniros.source import Node
import logging
# from typing import Callable
# import numpy as np
import sys
from movement.datatypes import MovementPacket

logging.basicConfig()

class Lidar:
    def __init__(self, port: str = "/dev/ttyUSB0"):
        self.lidar = RPLidar("/dev/ttyUSB0")
        self.lidar.reset()

    def health(self):
        return self.lidar.get_health()

    def info(self):
        return self.lidar.get_info()
    
    def samplerate(self):
        return self.lidar.get_samplerate()
    
    def scan_modes(self):
        return self.lidar.get_scan_modes()
    
    def scan(self, n_scans: int = 3, size: int = 200) -> list[list[int]]:
        data_list = [
            [0] * (size + 1) for _ in range(size + 1)
        ]
        n = 0
        
        a =  (4000 / size)
        b = size / 2
        for n, data in enumerate(self.lidar.iter_scans()):
            for scan in data:
                quality, angle, distance = scan
                if distance == 0:
                    continue

                angle = math.radians(angle)

                x = int(math.cos(angle) * distance / a + b)
                y = int(math.sin(angle) * distance / a + b)

                try:
                    data_list[x][y] = quality
                except:
                    pass

            if n >= n_scans:
                self.lidar.stop()
                break
        
        return data_list


    def stop(self):
        self.lidar.stop_motor()
        self.lidar.stop()

class LidarPublisher(Node):
    def __init__(self, movement_node_name: str = "movement", lidar_port = "/dev/ttyUSB0", port = 4532, node_name = "lidar"):
        super().__init__(port, node_name)
        self.lidar = Lidar(lidar_port)

        self.subscribe("movement")

    def handle_movement(self, packet, additional_data):
        pack = MovementPacket().from_json(packet, additional_data)
        
        x, y, rotation = pack.get("x"), pack.get("y"), pack.get("rotation")

        # TODO

l = Lidar()
# print(q)

# size = 300
# p = 20


# max_data_q = 0
# def q(new_scan: bool, quality: int, angle: float, distance: float) -> None:
#     global max_data_q
#     if distance != 0.0:
#         max_data_q = max(max_data_q, quality)
#         angle = math.radians(angle)
#         my_map[min(size - 1, max(0, int(distance*math.cos(angle)/p + size / 2)))][min(size - 1, max(0, int(distance*math.sin(angle)/p + size / 2)))] = quality

# l.scan(q)

c = ".,aq:;!#Q$%@"
cl = len(c)
# print(max_data_q)

saveInFile = False
f = open("out.txt", "w") if saveInFile else sys.stdout

# while True:
#     q = l.scan()
#     for row in q:
#         for x in row:
#             print(c[int(x / 16 * cl)], end=" ", file=f)
#         print(file=f)

#     time.sleep(0.4)

while True:
    time.sleep(10)