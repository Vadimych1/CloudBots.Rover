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
from src.i2c_data.source import BaseMultiMotorDriver, MPU6050
from src.map.source import Map
from src.web.httpserver import R_HTTPServer
from src.web.websocket import R_WebSocket


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)




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
        self.motor_driver = BaseMultiMotorDriver([0x0a, 0x0b, 0x0c, 0x0d]) # motor driver
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
        return (
            (1 / self.wheel_radius)
            * np.array(
                [
                    [1, 1, 1, 1],
                    [-1, 1, -1, 1],
                    [
                        -(self.d + self.l) / 2,
                        -(self.d + self.l) / 2,
                        (self.d + self.l) / 2,
                        (self.d + self.l) / 2,
                    ],
                ]
            ).T
            @ np.array([vx, vy, w]).T
        )

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
        
        self.motor_driver.move(v1, v2, v3, v4, t)
        self.movement_start_timestamp = time.time()

    def _lidar_thread(self):
        for res in self.lidar.scan():
            angle, distance = res
            angle += self.phi
            
            x = self.rx + distance * math.cos(angle)
            y = self.ry + distance * math.sin(angle)
            
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
        while self._running:
            if self.moving and self.start and self.end:
                self.path = self.map.create_path(self.start[0], self.start[1], self.end[0], self.end[1])
                time.sleep(0.2)
            else:
                for i in range(10):
                    if self.moving: break
                    time.sleep(0.07)
                    
                    
    def _error_check_thread(self):
        while self._running:
            if (not self.motor_driver.errors()) and self.moving:
                self.logger.warning("Moving stoped due to DRV errors")
                self.moving = False    
        
    def handle_ws(self, ws, message):
        json_data = json.loads(message)
        
        if json_data["type"] == "move":
            self.start = (self.rx, self.ry)
            self.target = (json_data["x"], json_data["y"])

        elif json_data["type"] == "stop":
            self.moving = False

        elif json_data["type"] == "map":
            ws.send(f'{{"type": "map_render", "data": "self.map.render()"}}')
            
        elif json_data["type"] == "data":
            ws.send(json.dumps({
                "type": "data",
                "data": {
                    "x": self.rx,
                    "y": self.ry,
                    "phi": self.rphi,
                }
            }))
            
    def run_threads(self):
        self.threads = {
            "lidar": threading.Thread(target=self._lidar_thread),
            "mpu": threading.Thread(target=self._mpu_thread),
            "movement": threading.Thread(target=self._movement_thread),
            "path_update": threading.Thread(target=self._path_update_thread),
            "error_check": threading.Thread(target=self._error_check_thread),
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
            continue

r = Robot(wheel_radius=50, d=150, l=200)
r.main()
