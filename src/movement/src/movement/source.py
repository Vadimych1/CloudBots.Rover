import smbus2
import time
from ctypes import *
import math
# import sys, os

i2c = smbus2.SMBus(1)
_mot = cdll.LoadLibrary("libs/...") # TODO: change to library location

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
_mot.setPulli2C.restype = c_bool

# Frequency, Device index
_mot.setFreqPWM.argtypes = [c_uint16, c_uint8]
_mot.setFreqPWM.restype = c_bool

# N Magnets, Device index
_mot.setMagnet.argtypes = [c_uint8, c_uint8]
_mot.setMagnet.restype = c_bool

# Device index
_mot.getMagnet.argtypes = [c_uint8]
_mot.getMagnet.restype = c_uint8

# TODO: fix setReducer in .cpp code
# TODO: fix getReducer in .cpp code

# Deviation, Device index
_mot.setError.argtypes = [c_uint8, c_uint8]
_mot.setError.restype = c_bool

# Device index
MOT_ERR_SPD = 1 # getError();
MOT_ERR_DRV = 2 #	getError();
_mot.getError.argtypes = [c_uint8]
_mot.getError.restype = c_uint8

# Speed, Speed type, Stop, Stop type, Device index
MOT_MET = 3 #	setStop(расстояние, MOT_MET); getStop(MOT_MET); setSpeed(скорость, MOT_RPM/MOT_PWM, расстояние, MOT_MET); getSum(MOT_MET);
MOT_SEC = 4 #	setStop(длительность, MOT_SEC); getStop(MOT_SEC); setSpeed(скорость, MOT_RPM/MOT_PWM, длительность, MOT_SEC); 
MOT_M_S = 5 #	setSpeed(скорость, MOT_M_S); getSpeed(MOT_M_S);
MOT_REV = 6 #	setStop(количество, MOT_REV); getStop(MOT_REV); setSpeed(скорость, MOT_RPM/MOT_PWM, количество, MOT_REV); getSum(MOT_REV);
MOT_RPM = 7 #	setSpeed(скорость, MOT_RPM); getSpeed(MOT_RPM);
MOT_PWM = 8 #	setSpeed(скорость, MOT_PWM); getSpeed(MOT_PWM);
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

# TODO: setInvGear
# TODO: getInvGear
# ! TODO: getSum
# TODO: setVoltage
# TODO: getVoltage
# TODO: setNominalRPM
# TODO: getNominalRPM
# TODO: saveManufacturer

def init(bus: int, wh_radius: int):
    _mot.setBus(bus)
    _mot.setRadius(wh_radius)
    _mot.init()

last_device_index = 0

class InitException:
    pass

class MotorDriver:
    def __init__(self, addr: int):
        global last_device_index, _mot
        
        self.addr = addr
        self.device_index = last_device_index
        last_device_index += 1
        
        res = _mot.initDevice(self.addr, self.device_index)
        
        if not res:
            raise InitException(f"Error initializing I2C device {self.device_index} (addr:{hex(self.addr)})")
        
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
    
    def setReducer(self, gear: float) -> bool:
        raise NotImplementedError
    
    def getReducer(self) -> bool:
        raise NotImplementedError
    
    def setError(self, deviation: int) -> bool:
        return _mot.setError(deviation, self.device_index)
    
    def getError(self) -> int:
        return _mot.getError(self.device_index)
    
    def setSpeed(self, valSpeed: float, typeSpeed: int, valStop: float, typeStop: int) -> bool:
        return _mot.setSpeed(valSpeed, typeSpeed, valStop, valSpeed, typeStop, self.device_index)
    
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
    
    def setInvGear(self, value1: bool, value2: bool):
        raise NotImplementedError
    
    def getInvGear(self) -> bool: # ???
        raise NotImplementedError
    
    def getSum(self, type: int):
        raise NotImplementedError
    
    def setVoltage(self, voltage: float):
        raise NotImplementedError

    def getVoltage(self):
        raise NotImplementedError
    
    def setNominalRPM(self, value: int):
        raise NotImplementedError

    def getNominalRPM(self):
        raise NotImplementedError
    
    def saveManufacturer(self):
        raise NotImplementedError
    
m = MotorDriver(i2c, 0x0a, 10)
m.setSpeed(1.0, MOT_M_S, 1, MOT_SEC)
# m.reset()

# print(float_to_bytes(1.0))
# print(bytes_to_float(float_to_bytes(1)))

# a = motor_dll.encodeFloat2(10.0, 0)
# b = motor_dll.encodeFloat2(10.0, 1)
# print(a, b)
# c = motor_dll.decodeFloat2(a, b)
# print(c)