from rplidar import RPLidar
from miniros.source import Node
import logging
from typing import Generator

logging.basicConfig()

class Lidar:
    def __init__(self, port: str = "/dev/ttyUSB0", fallback_ports=["/dev/tty0"]):
        self.logger = logging.getLogger(f"Lidar[{port}]")
        try:
            self.lidar = RPLidar(port)
        except:
            for i, fallback in enumerate(fallback_ports):
                try:
                    self.lidar = RPLidar(fallback)
                    break
                except:
                    if i == len(fallback_ports) - 1:
                        self.logger.error("Cannot connect to lidar, all fallbacks failed. Check if lidar connected or correct address.")
                        quit(1)
                        
        self.lidar.reset()

    def health(self):
        return self.lidar.get_health()

    def info(self):
        return self.lidar.get_info()
    
    def samplerate(self):
        return self.lidar.get_samplerate()
    
    def scan_modes(self):
        return self.lidar.get_scan_modes()
    
    def scan(self) -> Generator[tuple[int, int], None, None]:
        self.logger.info("Scan started")
        for data in self.lidar.iter_scans():
            for scan in data:
                _, angle, distance = scan
                if distance <= 0:
                    continue

                yield angle, distance

    def stop(self):
        self.logger.info("Scan stopped")
        self.lidar.stop_motor()
        self.lidar.stop()

# l = Lidar()
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

# c = ".,aq:;!#Q$%@"
# cl = len(c)
# print(max_data_q)

# saveInFile = False
# f = open("out.txt", "w") if saveInFile else sys.stdout

# writer = cv.VideoWriter("out.mp4", cv.VideoWriter_fourcc(*"mp4v"), 10, (300, 300))

# try:
#     while True:
        
#         q = l.scan()
#         frame = np.zeros((300, 300, 3), dtype=np.uint8)

#         for y, row in enumerate(q):
#             for x, quality in enumerate(row):
#                 frame[y, x, 0] = int(quality / cl * 255)
#                 frame[y, x, 1] = int(quality / cl * 255)
#                 frame[y, x, 2] = int(quality / cl * 255)

#         writer.write(frame)
#         time.sleep(0.1)
# except:
#     writer.release()


# while True:
    # time.sleep(10)
