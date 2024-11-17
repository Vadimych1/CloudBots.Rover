from src.filters import KalmanFilter
from src.movementlogic import BaseMovementLogic, RollingMovementLogic
from src.tasks import TaskManager
from src.rosock import RoSock

import threading, time
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s:%(levelname)s > %(message)s')
lg = logging.getLogger('main')
_file = logging.StreamHandler()
_file.setFormatter(logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s > %(message)s'))
_file.setStream(open('logs/main.log', 'w'))
lg.addHandler(_file)


"base class for robot"
class Robot:
    UWB_POS_PRIORITY = 7/10
    INTEGRAL_POS_PRIORITY = 3/10
    TICKER_UPDATE_TIME = 0.1
    TPS = int(1 / TICKER_UPDATE_TIME)
    CONNECT_TO_SOCKET = False
    SOCKET_URL = "ws://127.0.0.1:8080"

    def __init__(self, movement_logic: BaseMovementLogic):
        self._ticker_signal = threading.Event()

        self.movement_logic = movement_logic
        self.pos_filter = KalmanFilter(3)
        self.taskmgr = TaskManager()

        "positions"
        self.pos_x = 0
        self.pos_y = 0
        self.pos_z = 0

        self.uwb_pos_x = 0
        self.uwb_pos_y = 0
        self.uwb_pos_z = 0

        self.tick_pos_x = 0
        self.tick_pos_y = 0
        self.tick_pos_z = 0

        self.spd_x = 0
        self.spd_y = 0
        self.spd_z = 0

        "angles"
        self.ang_x = 0
        self.ang_y = 0
        self.ang_z = 0

        self.tick_ang_x = 0
        self.tick_ang_y = 0
        self.tick_ang_z = 0

        self.ang_spd_x = 0
        self.ang_spd_y = 0
        self.ang_spd_z = 0

        self.prev_pos_tick = time.time()

        "tasks"
        self.stop_task_id = None

        "sockets"
        if self.CONNECT_TO_SOCKET:
            self.rosock = RoSock(self.SOCKET_URL)
            self.rosock.connect()
        else:
            self.rosock = None

    "ticker block"
    def start_ticker(self):
        """
        Starts the main ticker thread.
        """
        lg.info("Starting robot ticker thread")
        t = threading.Thread(target=self._ticker)
        t.start()

    def stop_ticker(self):
        """
        Stops the main ticker thread.
        """
        lg.info("Stopping robot ticker thread")
        self._ticker_signal.set()

    def _ticker(self):
        lg.info("Started robot ticker thread")
        self.prev_pos_tick = time.time()
        while not self._ticker_signal.is_set():
            time.sleep(self.TICKER_UPDATE_TIME)
            
            tick_time = time.time()
            self.pos_tick(self.prev_pos_tick - tick_time)
            self.prev_pos_tick = tick_time

            self.calc_real_pos()

            self.taskmgr.tick()

        lg.info("Stopped robot ticker thread")

    def pos_tick(self, delta_time: float):
        """
        Integrates the state of the robot (rotation & position)
        """
        self.tick_pos_x += self.spd_x * delta_time
        self.tick_pos_y += self.spd_y * delta_time
        self.tick_pos_z += self.spd_z * delta_time
        self.tick_ang_x += self.ang_spd_x * delta_time
        self.tick_ang_y += self.ang_spd_y * delta_time
        self.tick_ang_z += self.ang_spd_z * delta_time

    def calc_real_pos(self):
        """
        Calculates the "real" pos of robot by combining the UWB position and the integral position and then filtering it
        """
        self.pos_x = self.uwb_pos_x * self.UWB_POS_PRIORITY + self.tick_pos_x * self.INTEGRAL_POS_PRIORITY
        self.pos_y = self.uwb_pos_y * self.UWB_POS_PRIORITY + self.tick_pos_y * self.INTEGRAL_POS_PRIORITY
        self.pos_z = self.uwb_pos_z * self.UWB_POS_PRIORITY + self.tick_pos_z * self.INTEGRAL_POS_PRIORITY
        self.pos_x, self.pos_y, self.pos_z = self.pos_filter.filter([self.pos_x, self.pos_y, self.pos_z])

    "base movement functions"
    def set_motors_speed(self, speeds: list[float]):
        """
        Set motors speed
        """
        # TODO

    def _forward(self, speed: float):
        self.set_motors_speed(self.movement_logic.forward(speed))

    def _backward(self, speed: float):
        self.set_motors_speed(self.movement_logic.backward(speed))

    def _left(self, speed: float):
        self.set_motors_speed(self.movement_logic.left(speed))

    def _right(self, speed: float):
        self.set_motors_speed(self.movement_logic.right(speed))

    def _rotate_left(self, speed: float):
        self.set_motors_speed(self.movement_logic.rotate_left(speed))

    def _rotate_right(self, speed: float):
        self.set_motors_speed(self.movement_logic.rotate_right(speed))

    def _stop(self, speed: float):
        self.set_motors_speed(self.movement_logic.stop(speed))

    "movement functions"
    def move_by(self, distance: float, speed: float = 0.5):
        """
        Move forward/backward by `distance` with `speed`
        """
        if speed < 0: return
        seconds = abs(distance) / speed
        
        self.cancel_stop()
        self._forward(speed) if distance > 0 else self._backward(speed)
        self.stop_task_id = self.taskmgr.add_task(lambda: self._stop(0), int(seconds * self.TPS))
    
    def move_side_by(self, distance: float, speed: float = 0.5):
        """
        Move left/right by `distance` with `speed`
        """
        if speed < 0: return
        seconds = abs(distance) / speed
        
        self.cancel_stop()
        self._right(speed) if distance > 0 else self._left(speed)
        self.stop_task_id = self.taskmgr.add_task(lambda: self._stop(0), int(seconds * self.TPS))

    def rotate_by(self, angle: float, speed: float = 0.5):
        """
        Rotate left/right by `angle` with `speed`
        """
        if speed < 0: return
        seconds = abs(angle) / speed

        self.cancel_stop()
        self._rotate_right(speed) if angle > 0 else self._rotate_left(speed)
        self.stop_task_id = self.taskmgr.add_task(lambda: self._stop(0), int(seconds * self.TPS))

    "tasks"
    def clear_tasks(self):
        """
        Clear tasks
        """
        self.taskmgr.clear()

    def clear_task(self, id):
        """
        Clear task by its id
        """
        self.taskmgr.clear_task(id)

    def cancel_stop(self):
        """
        Cancel stop task
        """
        self.taskmgr.clear_task(self.stop_task_id)


movementlogic = RollingMovementLogic()
bot = Robot(movementlogic)

bot.start_ticker()
bot.move_by(10, 0.5)

lg.info("Command listener started. Type command and press Enter to execute it")
while True:
    inp = input("").lower()
    lg.info(f"Executing: {inp}")
    match inp:
        case "exit", "quit", "q":
            bot.stop_ticker()
            break
        case _:
            lg.info(f"Unknown command: {inp}")
            continue