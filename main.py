import logging
import time
import sys, os
import math
import numpy as np
from collections import deque
import logging
import threading
import json


from src.lidar_module.source import Lidar
from src.i2c_data.source import BaseMultiMotorDriver, MPU6050, init_motors
from src.map.source import Map
from src.web.httpserver import R_HTTPServer
from src.web.websocket import R_WebSocket


PROD = True
DEBUG = False


_h1 = logging.FileHandler(f"logs/{time.asctime().replace(' ', '_')}.log")
_h2 = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[_h1, _h2],
    level=logging.INFO if not DEBUG else logging.DEBUG,
)

# clear logs if here is too much files
while len(_logfiles := os.listdir("logs")) > 10:
    os.remove(os.path.join("logs", _logfiles[0]))


class Robot:
    """
    Main robot class with navigation and control.

    :param wheel_radius: Wheel radius (in mm)
    :type wheel_radius: float

    :param lidar_port: Lidar port (default: "/dev/ttyUSB0")
    :type lidar_port: str

    :param d: Distance between wheels (in mm)
    :type d: float

    :param l: Length of the robot (in mm)
    :type l: float
    """
    def __init__(
        self, wheel_radius: float, d: float, l: float, lidar_port="/dev/ttyUSB0"
    ):
        self.logger = logging.getLogger("Main")
        
        self.lidar = Lidar(lidar_port) # lidar driver
        
        if PROD:
            # 0x0a - fwd_left
            # 0x0c - fwd_right
            # 0x0b - bwd_left
            # 0x0d - bwd_right
            self.motor_driver = BaseMultiMotorDriver([0x0a, 0x0c, 0x0b, 0x0d]) # motor driver
            self.mpu = MPU6050() # mpu6050 driver
        
        self.map = Map() # map
        
        self.httpd = R_HTTPServer()
        self.ws = R_WebSocket(self.handle_ws)

        self.wheel_radius = wheel_radius

        self.d = d
        self.l = l

        self.rx = 0
        self.ry = 0
        self.rphi = 0
        self.x = 0
        self.y = 0
        self.phi = 0
        
        self.mpu_acc = (0, 0)
        self.mpu_gyro = 0
        
        self.movement_start_timestamp = 0
        self.movement_time = 0
        self.x_delta = 0
        self.y_delta = 0
        self.phi_delta = 0        
        self.scheduled_movements = deque()
        self.moving = False
        
        self._running = True

        self.path = None
        self.start = None
        self.target = None

    """
    Calculate wheels speed based on robot movement.
    
    :param vx: X speed
    :param vy: Y speed
    :param w: Angular speed (Z)
    
    :return: (v1, v2, v3, v4)
    :rtype: tuple[float, float, float, float]
    """
    def _calculate_wheels_speed_by_movement(self, vx: float, vy: float, w: float):
        vx *= 2
        vy *= 2
        
        # vx /= max(vx, vy)
        # vy /= max(vx,vy)
        
        d = np.array([
            (1/self.wheel_radius) * (vx - vy - (self.l + self.d) * w), # fwd left
            (1/self.wheel_radius) * (vx + vy + (self.l + self.d) * w), # fwd right
            (1/self.wheel_radius) * (vx + vy - (self.l + self.d) * w), # bwd left
            (1/self.wheel_radius) * (vx - vy + (self.l + self.d) * w), # bwd right
        ]) * 60
        
        n = 0
        while max(d) > 400:
            vx /= 2
            vy /= 2
            w /= 2
            d = np.array([
                (1/self.wheel_radius) * (vx - vy - (self.l + self.d) * w), # fwd left
                (1/self.wheel_radius) * (vx + vy + (self.l + self.d) * w), # fwd right
                (1/self.wheel_radius) * (vx + vy - (self.l + self.d) * w), # bwd left
                (1/self.wheel_radius) * (vx - vy + (self.l + self.d) * w), # bwd right
            ]) * 60
            n += 1
    
        return d, 1 / (2 ** n)

    """
    Move robot to point and turn to angle.
    
    :param x: X coordinate
    :param y: Y coordinate
    :param phi: Angle (Z) in radians
    :param time: Time (in sec)
    
    :return: (w1, 2, w3, w4)
    :rtype: tuple[float, float, float, float]
    """
    def _move_and_turn2(self, x, y, phi, t):
        if self.moving:
            self.scheduled_movements.append((x, y, phi, t))
            return
        
        n_x = np.cos(self.phi) * x + np.sin(self.phi) * y
        n_y = np.sin(self.phi) * x + np.cos(self.phi) * y 
        
        dx = n_x - self.rx
        dy = n_y - self.ry
        dphi = phi - self.rphi
       
        v1, v2, v3, v4 = self._calculate_wheels_speed_by_movement(dx/t, dy/t, dphi/t)
        
        self.x_delta = dx
        self.y_delta = dy
        self.phi_delta = dphi
        self.moving = True
        
        PROD and self.motor_driver.move(v1, v2, v3, v4, t)
        self.movement_start_timestamp = time.time()

    def _lidar_thread(self):
        for res in self.lidar.scan():
            angle, distance = res
            angle += self.phi
            
            x = self.rx + distance * math.cos(np.radians(angle))
            y = self.ry + distance * math.sin(np.radians(angle))
            
            self.map.add_point(x, y)
            
            if not self._running:
                break

    def _mpu_thread(self):
        tick = time.time()
        while self._running:
            t = time.time()
            self.mpu.integrate_tick(t - tick)
            tick = t
            time.sleep(0.05)
        
    def _movement_thread(self):
        tick = time.time()
        
        while self._running:
            if self.moving:    
                if tick - self.movement_start_timestamp > self.movement_time:
                    self.moving = False
                    self.x = self.rx
                    self.y = self.ry
                    self.phi = self.rphi
                    self.movement_start_timestamp = 0
                    self.movement_time = 0
                    self.x_delta = 0
                    self.y_delta = 0
                    self.phi_delta = 0
                
                else:
                    self.rphi = self.phi + self.phi_delta * (tick - self.movement_start_timestamp) / self.movement_time
                    self.rx = self.x + self.x_delta * (tick - self.movement_start_timestamp) / self.movement_time
                    self.ry = self.y + self.y_delta * (tick - self.movement_start_timestamp) / self.movement_time
            
            else:
                if len(self.scheduled_movements) > 0:
                    d = self.scheduled_movements.popleft()
                    self._move_and_turn2(*d)
            
            time.sleep(0.05)
            tick = time.time()
        
    def _path_update_thread(self):
        c = 0
        while self._running:
            if self.moving and self.start and self.end:
                self.path = self.map.create_path(self.start[0], self.start[1], self.end[0], self.end[1])
                time.sleep(0.2)
            else:
                for i in range(10):
                    if self.moving: break
                    time.sleep(0.07)
            
            if c % 5 == 0:
                self.map.haf_update_chunks()
            
            c += 1     
                    
    def _error_check_thread(self):
        while self._running:
            if (not self.motor_driver.errors()) and self.moving:
                self.logger.warning("Moving stoped due to DRV errors")
                self.moving = False    
        
    def handle_ws(self, message):
        json_data = json.loads(message)
        
        if json_data["type"] == "move":
            self.start = (self.rx, self.ry)
            self.target = (json_data["x"], json_data["y"])
            self.path = self.map.create_path(*self.start, *self.target)

        elif json_data["type"] == "stop":
            self.moving = False

        elif json_data["type"] == "map":
            render = self.map.render(self.rx, self.ry, self.path, *(self.target if self.target else (None, None)))
            return f'{{"type": "map_render", "data": "{render}", "chunk_minus_offset": {{"x": {self.map.min_chunk_x * 300}, "y": {self.map.min_chunk_y * 300}}}}}'
            
        elif json_data["type"] == "data":
            return json.dumps({
                "type": "data",
                "data": {
                    "x": self.rx,
                    "y": self.ry,
                    "phi": self.rphi,
                }
            })
            
        elif json_data["type"] == "clearmap":
            self.logger.info("Incoming request to clear map")
            self._clearmap()
            
    def run_threads(self):
        self.threads = {
            "lidar": threading.Thread(target=self._lidar_thread),
            "mpu": threading.Thread(target=self._mpu_thread if PROD else lambda: ...),
            "movement": threading.Thread(target=self._movement_thread if PROD else lambda: ...),
            "path_update": threading.Thread(target=self._path_update_thread),
            "error_check": threading.Thread(target=self._error_check_thread if PROD else lambda: ...),
            "websocket": self.ws.run(),
            "httpd": self.httpd.run(),
        }
        
        for t in self.threads.values():
            t.start() 
        
    def main(self):
        self.logger.info("Running threads")
        self.run_threads()
        
        self.logger.info("Started main. Type `quit` to exit.")
        while (command := input()) != "quit":
            match command:
                case "printmap":
                    print("\n] Loaded chunks:", len(self.map.chunks))
                    print("] Chunks max values:\n|", "|".join([f"{x.d_x} {x.d_y} (max {np.max(x.data)}) (min {np.min(x.data)})\n" for x in self.map.chunks.values()]))
                
                case "clearmap":
                    print("\n] Clearing map...")
                    self._clearmap()
                    print("] Map cleared\n")
                    
                case "printchunksdata":
                    print("\n] Chunks data:")
                    for chunk in self.map.chunks.values():
                        print(chunk.data)
                
                case "help":
                    print(f'\n] ' + ("\n] ".join(["printmap", "clearmap", "help"])) + "\n")
                        
        self._running = False
        try:
            self.threads["websocket"].join()
        except:
            pass
        
        try:
            self.threads["httpd"].join()
        except:
            pass
        
    def _clearmap(self):
        del self.map.chunks
        self.map.chunks = self.map._reinit_chunks()

# PROD and init_motors(1, 50)
# r = Robot(wheel_radius=50, d=150, l=200)
# r.main()

init_motors(1, 50)
r = Robot(wheel_radius=50, d=150, l=200)

ang = np.pi / 6
phi = np.pi / 4
t = 4

q, n = r._calculate_wheels_speed_by_movement(100 * math.cos(ang), 100 * math.sin(ang), phi) * np.array([-1, 1, -1, 1])
# q = r._calculate_wheels_speed_by_movement(100, 0, 0) * np.array([-1, 1, -1, 1]) * 60
# q = r._calculate_wheels_speed_by_movement(0, 100, 0) * np.array([-1, 1, -1, 1]) * 60
# q = r._calculate_wheels_speed_by_movement(25*math.sqrt(2), 25*math.sqrt(2), 0) * np.array([-1, 1, -1, 1]) * 60

print(q, sum(q), n)
# r.motor_driver.move(q, t)
# r.motor_driver.only(70, 1, 0x0c)
time.sleep(t)