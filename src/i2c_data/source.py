import time
from enum import Enum
from ctypes import *
import numpy as np
import quaternion as quat
import mpu6050 as mpu
import logging
import platform

_, _, _, _, arch, _ = platform.uname()
print("Using arch for I2C:", arch, "\n")

try:
    _mot = cdll.LoadLibrary(f"libs/arduino_motor/motor_{arch}.so")
except:
    print(f"! Motor library for your system ({arch}) not found or incorrect")
    print(f"? Try building lib by running (in project root): `cd libs/arduino_motor && sh build.sh`")
    print(f"? After finishing, rename file `motor.so` to `motor_{arch}.so`")
    quit(1)

MOT_ERR_SPD = 1 # getError();
MOT_ERR_DRV = 2 #	getError();
MOT_MET = 3 #	setStop(расстояние, MOT_MET); getStop(MOT_MET); setSpeed(скорость, MOT_RPM/MOT_PWM, расстояние, MOT_MET); getSum(MOT_MET);
MOT_SEC = 4 #	setStop(длительность, MOT_SEC); getStop(MOT_SEC); setSpeed(скорость, MOT_RPM/MOT_PWM, длительность, MOT_SEC); 
MOT_M_S = 5 #	setSpeed(скорость, MOT_M_S); getSpeed(MOT_M_S);
MOT_REV = 6 #	setStop(количество, MOT_REV); getStop(MOT_REV); setSpeed(скорость, MOT_RPM/MOT_PWM, количество, MOT_REV); getSum(MOT_REV);
MOT_RPM = 7 #	setSpeed(скорость, MOT_RPM); getSpeed(MOT_RPM);
MOT_PWM = 8 #	setSpeed(скорость, MOT_PWM); getSpeed(MOT_PWM);
def __init_mot():
    # Bus index
    _mot.setBus.argtypes = [c_uint8]
    _mot.setBus.restype = None

    # Radius
    _mot.setRadius.argtypes = [c_uint16]
    _mot.setRadius.restype = None

    _mot.init.argtypes = None
    _mot.init.restype = None

    # Device address, index to set in memory
    _mot.initDevice.argtypes = [c_uint8, c_uint8]
    _mot.initDevice.restype = None

    # Device index
    _mot.reset.argtypes = [c_uint8]
    _mot.reset.restype = c_bool

    # Device index
    _mot.getPullI2C.argtypes = [c_uint8]
    _mot.getPullI2C.restype = c_bool

    # Enable/disable pull, Device index
    _mot.setPullI2C.argtypes = [c_bool, c_uint8]
    _mot.setPullI2C.restype = c_bool

    # Frequency, Device index
    _mot.setFreqPWM.argtypes = [c_uint16, c_uint8]
    _mot.setFreqPWM.restype = c_bool

    # N Magnets, Device index
    _mot.setMagnet.argtypes = [c_uint8, c_uint8]
    _mot.setMagnet.restype = c_bool

    # Device index
    _mot.getMagnet.argtypes = [c_uint8]
    _mot.getMagnet.restype = c_uint8

    # Reducer, Device index
    _mot.setReducer.argtypes = [c_float, c_uint8]
    _mot.setReducer.restype = c_bool
    
    # Device index
    _mot.getReducer.argtypes = [c_uint8]
    _mot.getReducer.restype = c_float

    # Deviation, Device index
    _mot.setError.argtypes = [c_uint8, c_uint8]
    _mot.setError.restype = c_bool

    # Device index
    _mot.getError.argtypes = [c_uint8]
    _mot.getError.restype = c_uint8

    # Speed, Speed type, Stop, Stop type, Device index
    _mot.setSpeed.argtypes = [c_float, c_uint8, c_float, c_uint8, c_uint8]
    _mot.setSpeed.restype = c_bool

    # Speed type, Device index
    _mot.getSpeed.argtypes = [c_uint8, c_uint8]
    _mot.getSpeed.restype = c_float

    # Stop, Stop type, Device index
    _mot.setStop.argtypes = [c_float, c_uint8, c_uint8]
    _mot.setStop.restype = c_bool

    # Stop type, Device index
    _mot.getStop.argtypes = [c_uint8, c_uint8]
    _mot.getStop.restype = c_float

    # Neutral stop value, Device index
    _mot.setStopNeutral.argtypes = [c_bool, c_uint8]
    _mot.setStopNeutral.restype = c_bool

    # Device index
    _mot.setStopNeutral.argtypes = [c_uint8]
    _mot.setStopNeutral.restype = c_bool

    # Direction, Device index
    _mot.setDirection.argtypes = [c_bool, c_uint8]
    _mot.setDirection.restype = c_bool

    # Device index
    _mot.getDirection.argtypes = [c_uint8]
    _mot.getDirection.restype = c_bool

    # Device index
    _mot.getVoltage.argtypes = [c_uint8]
    _mot.getVoltage.restype = c_float

    # Voltage, Device index
    _mot.setVoltage.argtypes = [c_float, c_uint8]
    _mot.setVoltage.restype = c_bool
    
    # invRDR, invPIN, Device index
    _mot.setInvGear.argtypes = [c_bool, c_bool, c_uint8]
    _mot.setInvGear.restype = c_bool
    
    # Device index
    _mot.getInvGear.argtypes = [c_uint8]
    _mot.getInvGear.restype = c_bool

    # Type, Device index
    _mot.getSum.argtypes = [c_uint8, c_uint8]
    _mot.getSum.restype = c_float


def init_motors(bus: int, wh_radius: int):
    __init_mot()

    _mot.setBus(bus)
    _mot.setRadius(wh_radius)
    _mot.init()
    
last_device_index = 0

# ! Motors
class MotorDriver:
    def __init__(self, addr: int):
        global last_device_index, _mot
        
        self.addr = addr
        self.device_index = last_device_index
        last_device_index += 1
        
        _mot.initDevice(self.addr, self.device_index)
        
    def reset(self) -> bool:
        return _mot.reset(self.device_index)
        
    def getPullI2C(self) -> bool:
        return _mot.getPullI2c(self.device_index)
    
    def setPullI2C(self, value: bool) -> bool:
        return _mot.setPullI2C(value, self.device_index)
        
    def setFreqPWM(self, frequency: int) -> bool:
        return _mot.setFreqPWM(frequency, self.device_index)
    
    def setMagnet(self, n: int) -> bool:
        return _mot.setMagnet(n, self.device_index)
    
    def getMagnet(self) -> int:
        return _mot.getMagnet(self.device_index)
    
    def setError(self, deviation: int) -> bool:
        return _mot.setError(deviation, self.device_index)
    
    def getError(self) -> int:
        return _mot.getError(self.device_index)
    
    def setSpeed(self, valSpeed: float, typeSpeed: int, valStop: float, typeStop: int) -> bool:
        return _mot.setSpeed(valSpeed, typeSpeed, valStop, typeStop, self.device_index)
    
    def getSpeed(self, speedType: int) -> float:
        return _mot.getSpeed(speedType, self.device_index)
        
    def setStop(self, value: float, type: int) -> bool:
        return _mot.setStop(value, type, self.device_index)
    
    def getStop(self, type: int) -> float:
        return _mot.getStop(type, self.device_index)
    
    def setStopNeutral(self, value: bool) -> bool:
        return _mot.setStopNeutral(value, self.device_index)
    
    def getStopNeutral(self) -> bool:
        return _mot.getStopNeutral(self.device_index)
    
    def setDirection(self, direction: bool) -> bool:
        return _mot.setDirection(direction, self.device_index)
    
    def getDirection(self) -> bool:
        return _mot.getDirection(self.device_index)
    
    def setInvGear(self, value1: bool, value2: bool) -> bool:
        return _mot.setInvGear(value1, value2, self.device_index)
    
    def getInvGear(self) -> bool:
        return _mot.getInvGear(self.device_index)
    
    def getSum(self, type: int) -> float:
        return _mot.getSum(type, self.device_index)
    
    def setVoltage(self, voltage: float) -> bool:
        return _mot.setVoltage(voltage, self.device_index)

    def getVoltage(self) -> float:
        return _mot.getVoltage(self.device_index)

    def stop(self):
        self.setStop(0, 0xFF)

    def setReducer(self, reducer: float) -> bool:
        return _mot.setReducer(reducer, self.device_index)
        
    def getReducer(self):
        return _mot.getReducer(self.device_index)

class BaseMultiMotorDriver:
    """
    Class for controlling multiple motors at the same time on top-level.
    :@param motor_addrs: list of motor addresses (like 0x0a, 0x0b etc.)
    :@param motor_sides: list of motor directions (True - default/False - reversed)
    """
    def __init__(self, motor_addrs: list[int], invert: list[int] = []):
        self.logger = logging.getLogger("MotorDriver")
        
        self.prevstate = 1
        
        self.motor_addrs = motor_addrs
        self.motors = [
            MotorDriver(addr) for addr in self.motor_addrs
        ]
        
        for mot in self.motors:
            mot.setDirection(True)
            mot.setInvGear(False, False)
            mot.setDirection(True)
            mot.setMagnet(2)
            mot.setError(90)
            mot.setStopNeutral(True)
            mot.setPullI2C(True)
            mot.setReducer(200.0)
            time.sleep(0.06)
            
        self.logger.info("Motors initialized")
            
    def move(self, speeds: list[float], m_time: float):
        for i, motor in (reversed(enumerate(self.motors)) if self.prevstate < 0 else enumerate(self.motors)):
            self.logger.info(f"Moving {i}")
            motor.setSpeed(int(speeds[i]*9.549296585513718/np.pi), MOT_RPM, m_time, MOT_SEC) # convert rad/s to rpm and run motor
            time.sleep(0.01)
            
        self.prevstate *= -1
        
    def only(self, speed: float, m_time: float, addr: int):
        for m in self.motors:
            if m.addr == addr:
                m.setSpeed(int(speed*9.549296585513718/np.pi), MOT_RPM, m_time, MOT_SEC)
                break
                
    def stop(self):
        for motor in self.motors:
            motor.stop()
            time.sleep(0.015)
    
    def errors(self):
        result = True
        for motor in self.motors:
            e = motor.getError()
            if e > 0:
                if e == MOT_ERR_DRV:
                    result = False
                    
                    self.logger.error(f"{hex(motor.addr)} ERR_DRV")
                    time.sleep(0.01) # delay to not interrupt anything
                    
                    self.stop()
                    break
                else:
                    self.logger.error(f"{hex(motor.addr)} ERR_SPD")
            
            time.sleep(0.05)
        
        return result

# ! MPU6050
class MPU6050:
    def __init__(self, addr: int = None):
        self.addr = addr
        self.sensor = mpu.mpu6050(self.addr or 0x68, bus=1)
        
        self.rotation_speed = 0
        self.rotation = 0

        self.speed = np.array([0, 0, 0])
        self.position = np.array([0, 0, 0])
        
        self.e = np.array([0, 1, 0])

    def accelerometer(self):
        return self.sensor.get_accel_data()
        
    def gyroscope(self):
        return self.sensor.get_gyro_data()
        
    def temperature(self):
        return self.sensor.get_temp()
        
    def integrate_tick(self, delta_time = 1) -> np.ndarray:
        self.rotation_speed += self.gyroscope() * delta_time
        self.rotation += self.rotation_speed * delta_time
    
        r = self.rotation
        A = self.accelerometer()
        axis_angle = (r * 0.5) * self.e / np.linalg.norm(self.e)
        
        vec = quat.quaternion(0, *A)
        qlog = quat.quaternion(0, *axis_angle)   
        q = np.exp(qlog)
        A2 = q * vec * np.conjugate(q)
        A2 = A2.imag
        
        self.speed += A2 * delta_time
        self.position += self.speed * delta_time
        
        return self.position
    

# if __name__ == "__main__":
#     init_motors(
#         bus=1,
#         wh_radius=28,
#     )
    
#     d = QuadMotorDriver(
#         motor_addrs=[0x0a, 0x0b, 0x0c, 0x0d],
#         motor_sides=[False, False, True, True],
#         motor_alignments=[QuadMotorSide.FWD_LEFT, QuadMotorSide.BWD_LEFT, QuadMotorSide.FWD_RIGHT, QuadMotorSide.BWD_RIGHT],
#     )
    
#     for mot in d.motors:
#         mot.stop()
        

        
    
#     time.sleep(0.5)

#     while True:
#         s = input()
        
#         if s == "q":
#             break
        
#         elif s == "w":
#             d.forward(6, 1)
            
#             time.sleep(0.1)
            
#             for i in range(5):
#                 d.errors()
                
#             d.stop()
#             time.sleep(0.1)
        
#         elif s == "s":
#             d.backward(6, 1)
            
#             time.sleep(0.1)
            
#             for i in range(5):
#                 d.errors()
                
#             d.stop()
#             time.sleep(0.1)
        
#         elif s == "a":
#             d.left(6, 1)
            
#             time.sleep(0.1)
            
#             for i in range(5):
#                 d.errors()
                
#             d.stop()
#             time.sleep(0.1)
        
#         elif s == "d":
#             d.right(6, 1)
            
#             time.sleep(0.1)
            
#             for i in range(5):
#                 d.errors()
                
#             d.stop()
#             time.sleep(0.1)
        
#         elif s == "e":
#             d.turn_left(6, 1)
            
#             time.sleep(0.1)
            
#             for i in range(5):
#                 d.errors()
                
#             d.stop()
#             time.sleep(0.1)
        
#         elif s == "r":
#             d.turn_right(6, 1)
            
#             time.sleep(0.1)
            
#             for i in range(5):
#                 d.errors()
                
#             d.stop()
#             time.sleep(0.1)
        
#         print("Done")