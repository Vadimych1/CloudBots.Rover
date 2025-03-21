import time
from ctypes import *
import numpy as np
import logging
import platform
import smbus

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

from pyiArduinoI2Cmotor import *

class BaseMultiMotorDriver:
    """
    Class for controlling multiple motors at the same time on top-level.
    :@param motor_addrs: list of motor addresses (like 0x0a, 0x0b etc.)
    :@param motor_sides: list of motor directions (True - default/False - reversed)
    """
    def __init__(self, motor_addrs: list[int]) -> None:
        self.logger = logging.getLogger("MotorDriver")
        
        self.prevstate = 1
        
        self.motor_addrs = motor_addrs
        self.motors = [
            # MotorDriver(addr) for addr in self.motor_addrs
            MotorDriver(addr) for addr in self.motor_addrs
        ]
        
        for mot in self.motors:
            mot.setDirection(True)
            mot.setInvGear(False, False)
            mot.setDirection(True)
            mot.setMagnet(2)
            mot.setError(99)
            mot.setStopNeutral(False)
            mot.setPullI2C(False)
            mot.setReducer(500.0)
            time.sleep(0.06)
            
        self.logger.info("Motors initialized")
        
            
    def move(self, speeds: list[float], m_time: float) -> None:
        """
        Set movement speed and time to all drivers

        :param speeds: speeds of every motor
        :type speeds: list[float]

        :param m_time: movement time. Specify -1 for non-stop moving
        :type m_time: float
        """

        for i, motor in enumerate(self.motors[::self.prevstate]):
            self.logger.debug(f"Moving {i}")

            # convert rad/s to rpm and run motor
            motor.setSpeed(speeds[::self.prevstate][i]/(np.pi * 2)*60, MOT_RPM, m_time if m_time > 0 else 0, MOT_SEC if m_time > 0 else 0)
            time.sleep(0.01)
            
        self.prevstate *= -1
        

    def only(self, speed: float, m_time: float, addr: int) -> None:
        """
        Run only one motor
        
        :param speeds: speeds of every motor
        :type speeds: list[float]

        :param m_time: movement time. Specify -1 for non-stop moving
        :type m_time: float
        """

        for m in self.motors:
            if m.addr == addr:
                m.setSpeed(speed/(np.pi * 2)*60, MOT_RPM, m_time if m_time > 0 else 0, MOT_SEC if m_time > 0 else 0)
                break


    def stop(self) -> None:
        """
        Stop all motors
        """
        for motor in self.motors:
            motor.stop()
            time.sleep(0.01)
    

    def errors(self) -> None:
        """
        Check engine errors

        :return: True if no errors was detected, else False
        :rtype: bool
        """

        result = True
        for motor in self.motors:
            e = motor.getError()
            if e > 0:
                if e == MOT_ERR_DRV:
                    result = False
                    
                    self.logger.error(f"{hex(motor.addr)} :: ERR_DRV")
                    time.sleep(0.008) # delay to not interrupt anything
                    
                    self.stop()
                    break
                else:
                    self.logger.error(f"{hex(motor.addr)} :: ERR_SPD")
            
            time.sleep(0.05)
        
        return result
