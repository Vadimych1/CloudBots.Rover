import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import logging
from io import IOBase
import heapq
import math

from rplidar import RPLidar, RPLidarException
from breezyslam.algorithms import RMHC_SLAM
from breezyslam.sensors import RPLidarA1 as LaserModel

class Lidar:
    """
    Class for lidar scanning

    :param port: the USB port of lidar. Default: "/dev/ttyUSB0"
    :param fallback_ports: ports to check if lidar os not on the default port
    """
    def __init__(self, size: int = 8096, port: str = "/dev/ttyUSB0", fallback_ports=["/dev/tty0", "COM0", "COM1", "COM2", "COM3"]):
        self.logger = logging.getLogger(f"Lidar[{port}]")
        try:
            self.lidar = RPLidar(port)
        except:
            for i, fallback in enumerate(fallback_ports):
                try:
                    self.lidar = RPLidar(fallback, 115200, 3)
                    break

                except Exception as e:
                    if i == len(fallback_ports) - 1:
                        self.logger.error("Cannot connect to lidar, all fallbacks failed. Check if lidar connected or correct address.")
                        raise e
    
        self.odometry_data = (0, 0, 0)

        self.size = size
        self.map_bytes = bytearray(size * size)
        self.pos = None

        self.path = None

        self.slam = RMHC_SLAM(LaserModel(), 8096, 35)
        self.running = False

    def scan(self, buffer: int = 10000) -> None:
        """
        Start scanning
        """

        self.running = True
        
        while self.running:
            self.logger.info("Scan started")
            scans = []
            c = 0
            
            try:
                for data in self.lidar.iter_measures(max_buf_meas=buffer):
                    _, _, angle, distance = data
                    if distance <= 0:
                        continue

                    scans.append([distance, angle])

                    c += 1

                    if len(scans) == 250:
                        distances, angles = zip(*scans)
                        distances = list(distances)
                        angles = list(angles)

                        self.slam.update(distances, scan_angles_degrees=angles)
                        self.slam.getmap(self.map_bytes)
                        self.pos = self.slam.getpos()

                        scans = []

                    if c % 60001 == 0:
                        raise RPLidarException()
                    
                    
            except RPLidarException as e:
                self.lidar.stop()
                self.lidar.disconnect()
                self.lidar.connect()
            

            except Exception as e:
                self.logger.exception(e)


    def _astar(self, data, start, end):
        def get(x, y):
            return data[x * self.size + y]
        
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1)]
        
        start = tuple(map(int, start))
        end = tuple(map(int, end))
        
        self.logger.info(f"Running A*. Start/end: {start}/{end}")

        open_set = []
        heapq.heappush(open_set, (0, start))  # Сохраняем кортеж (приоритет, координаты)
        
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._astar_heuristic(start, end)}

        i = 0
        while open_set:
            if i % 10000 == 0:
                self.logger.info(f"Finding path. Iter {i}")
            
            if i // 10000 >= 20:
                break
                
            current = heapq.heappop(open_set)[1]

            if current == end:
                # Воссоздание пути
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                
                self.logger.info(f"Finding path done in {i} iterations.")
                return path[::-1]  # Возвращаем путь в правильном порядке

            for direction in directions:
                neighbor = (current[0] + direction[0], current[1] + direction[1])

                # Проверяем границы карты и проходимость
                if (0 <= neighbor[0] < self.size) and (0 <= neighbor[1] < self.size) and (get(neighbor[0], neighbor[1]) >= 0x7f): #TODO: change 0
                    tentative_g_score = g_score[current] + 1  # Предполагаемое расстояние до соседа

                    if tentative_g_score < g_score.get(neighbor, float('inf')):
                        # Этот путь лучше, чем любой, который мы рассматривали
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self._astar_heuristic(neighbor, end)

                        if neighbor not in [i[1] for i in open_set]:
                            heapq.heappush(open_set, (f_score[neighbor], neighbor))
                            
            i += 1
            
        self.logger.info(f"Finding path unsuccessful (in {i} iterations)")

        return None

    @staticmethod
    def _astar_heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def create_path(self, start: tuple, end: tuple) -> None:
        lines = []
        path = self._astar(self.map_bytes, (start[0] / 35000 * self.size, start[1] / 35000 * self.size), end)

        if path is None:
            return None

        current_line = []
        prev = path[0]
        p_dx, p_dy = None, None
        for x in path[1:]:
            dx, dy = x[0] - prev[0], x[1] - prev[1]
            if not (p_dx and p_dy):
                p_dx = dx
                p_dy = dy
            
            if p_dx == dx and p_dy == dy:
                current_line.append(x)
            else:
                lines.append((current_line[0], current_line[-1]))
                current_line = []
                p_dx, p_dy = None, None
            
            prev = x

        lines.append((current_line[0], current_line[-1]))
        
        self.path = lines

        return lines

    
    def render(self, stream: IOBase) -> None:
        """
        Render map to stream
        """

        size = self.size
        im = Image.frombuffer('L', (size, size), self.map_bytes)
        im = im.convert("RGB")

        if self.pos is not None:
            draw = ImageDraw.ImageDraw(im)
            x, y, phi = self.pos
            phi /= 180
            phi *= math.pi

            x = int(x / 35000 * self.size)
            y = int(y / 35000 * self.size)

            draw.ellipse((x - 40, y - 40, x + 40, y + 40), fill=(255, 0, 0))
            
            radius = 80
            rx, ry = radius * math.cos(phi), radius * math.sin(phi)
            draw.line((x, y, x + rx, y + ry), (0, 255, 0), 30) 

            if self.path is not None:
                for line in self.path:
                    start, end = line
                    x1, y1 = start
                    x2, y2 = end
                    draw.line((x1, y1, x2, y2), (0, 0, 255), 30) 
                    

        im = im.resize((int(im.size[0] / 4), int(im.size[1] / 4)))
        im.save(stream, format='PNG')

    def stop(self) -> None:
        """
        Stop lidar
        """     
        self.running = False
        self.logger.debug("Scan stopped")
        self.lidar.stop_motor()
        self.lidar.stop()
