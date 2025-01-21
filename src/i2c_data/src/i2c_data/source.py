import time
from enum import Enum
from ctypes import *
import math
import mpu6050 as mpu


_mot = cdll.LoadLibrary("libs/arduino_motor/motor.so")
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

    # TODO: setInvGear
    # TODO: getInvGear
    # ! TODO: getSum
    # TODO: setVoltage
    # TODO: getVoltage
    # TODO: setNominalRPM
    # TODO: getNominalRPM
    # TODO: saveManufacturer


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
    
    def setInvGear(self, value1: bool, value2: bool):
        raise NotImplementedError
    
    def getInvGear(self) -> bool: # ???
        raise NotImplementedError
    
    def getSum(self, type: int):
        raise NotImplementedError
    
    def setVoltage(self, voltage: float):
        raise NotImplementedError

    def getVoltage(self):
        return _mot.getVoltage(self.device_index)
    
    def setNominalRPM(self, value: int):
        raise NotImplementedError

    def getNominalRPM(self):
        raise NotImplementedError
    
    def saveManufacturer(self):
        raise NotImplementedError

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
    def __init__(self, motor_addrs: list, motor_sides: list):
        self.motor_addrs = motor_addrs
        self.motor_sides = motor_sides
        self.motors = [
            MotorDriver(addr) for addr in self.motor_addrs
        ]
        
        for motor, side in zip(self.motors, self.motor_sides):
            motor.setDirection(side)
            
    def forward(self, meters: float, speed: float):
        raise NotImplementedError
    
    def backward(self, meters: float, speed: float):
        raise NotImplementedError
    
    def left(self, meters: float, speed: float):
        raise NotImplementedError 

    def right(self, meters: float, speed: float):
        raise NotImplementedError
    
    def turn_left(self, degrees: float, speed: float):
        raise NotImplementedError
    
    def turn_right(self, degrees: float, speed: float):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

class QuadMotorSide(Enum):
    FWD_LEFT = 0
    FWD_RIGHT = 1
    BWD_LEFT = 2
    BWD_RIGHT = 3
        
class QuadMotorDriver(BaseMultiMotorDriver):
    def __init__(self, motor_addrs: list, motor_sides: list, motor_alignments: list):
        super().__init__(motor_addrs, motor_sides)
        self.motor_alignments = motor_alignments

        assert len(self.motor_addrs) == len(self.motor_sides) == len(self.motor_alignments) == 4
        self.motorsd = {}
        for motor, side in zip(self.motors, self.motor_alignments):
            self.motorsd[side.name] = motor
        
    def forward(self, meters: float, speed: float):
        self.motorsd[QuadMotorSide.FWD_LEFT.name].setSpeed(speed, MOT_M_S, meters, MOT_MET)
        self.motorsd[QuadMotorSide.FWD_RIGHT.name].setSpeed(speed, MOT_M_S, meters, MOT_MET)
        self.motorsd[QuadMotorSide.BWD_LEFT.name].setSpeed(speed, MOT_M_S, meters, MOT_MET)
        self.motorsd[QuadMotorSide.BWD_RIGHT.name].setSpeed(speed, MOT_M_S, meters, MOT_MET)
        
    def backward(self, meters: float, speed: float):
        self.forward(meters, -speed)
        
    def left(self, meters: float, speed: float):
        self.motorsd[QuadMotorSide.FWD_LEFT.name].setSpeed(speed, MOT_M_S, meters, MOT_MET)
        self.motorsd[QuadMotorSide.FWD_RIGHT.name].setSpeed(-speed, MOT_M_S, meters, MOT_MET)
        self.motorsd[QuadMotorSide.BWD_LEFT.name].setSpeed(-speed, MOT_M_S, meters, MOT_MET)
        self.motorsd[QuadMotorSide.BWD_RIGHT.name].setSpeed(speed, MOT_M_S, meters, MOT_MET)
        
    def right(self, meters: float, speed: float):
        self.left(meters, -speed)
        
    def stop(self):
        self.motorsd[QuadMotorSide.FWD_LEFT.name].stop()
        self.motorsd[QuadMotorSide.FWD_RIGHT.name].stop()
        self.motorsd[QuadMotorSide.BWD_LEFT.name].stop()
        self.motorsd[QuadMotorSide.BWD_RIGHT.name].stop()

    def turn_left(self, degrees: float, speed: float):
        self.motorsd[QuadMotorSide.FWD_LEFT.name].setSpeed(-speed, MOT_M_S, degrees, MOT_MET)
        self.motorsd[QuadMotorSide.FWD_RIGHT.name].setSpeed(speed, MOT_M_S, degrees, MOT_MET)
        self.motorsd[QuadMotorSide.BWD_LEFT.name].setSpeed(-speed, MOT_M_S, degrees, MOT_MET)
        self.motorsd[QuadMotorSide.BWD_RIGHT.name].setSpeed(speed, MOT_M_S, degrees, MOT_MET)
    
    def turn_right(self, degrees: float, speed: float):
        self.turn_left(-degrees, speed)        
        
        
    def errors(self):
        for motor in self.motors:
            e = motor.getError()
            if e > 0:
                if e == MOT_ERR_DRV:
                    print(hex(motor.addr), "ERR_DRV")
                else:
                    print(hex(motor.addr), "ERR_SPD")
            
            time.sleep(0.1)

if __name__ == "__main__":
    init_motors(
        bus=1,
        wh_radius=35,
    )
    
    d = QuadMotorDriver(
        # 
        motor_addrs=[0x0a, 0x0b, 0x0c, 0x0d],
        motor_sides=[False, False, True, True],
        motor_alignments=[QuadMotorSide.FWD_LEFT, QuadMotorSide.BWD_LEFT, QuadMotorSide.FWD_RIGHT, QuadMotorSide.BWD_RIGHT],
    )
    
    for mot in d.motors:
        mot.stop()
        

        mot.setMagnet(2)
        mot.setError(90)
        
        # mot.setInvGear(False, False)
        
        mot.setStopNeutral(True)
        mot.setPullI2C(True)
        
        mot.setReducer(200.0)
        mot.getReducer()
        
        time.sleep(0.1)
    
    time.sleep(0.5)

    # ! motor test
    # d.motors[2].setSpeed(2, MOT_M_S, 2, MOT_MET)
    # quit(0)

    while True:
        s = input()
        
        if s == "q":
            break
        elif s == "w":
            d.forward(6, 1)
            
            time.sleep(0.1)
            
            for i in range(8):
                d.errors()
                
            d.stop()
            time.sleep(0.1)
        
        elif s == "s":
            d.backward(6, 1)
            
            time.sleep(0.1)
            
            for i in range(8):
                d.errors()
                
            d.stop()
            time.sleep(0.1)
        
        elif s == "a":
            d.left(6, 1)
            
            time.sleep(0.1)
            
            for i in range(8):
                d.errors()
                
            d.stop()
            time.sleep(0.1)
        
        elif s == "d":
            d.right(6, 1)
            
            time.sleep(0.1)
            
            for i in range(8):
                d.errors()
                
            d.stop()
            time.sleep(0.1)
        
        elif s == "e":
            d.turn_left(6, 1)
            
            time.sleep(0.1)
            
            for i in range(8):
                d.errors()
                
            d.stop()
            time.sleep(0.1)
        
        elif s == "r":
            d.turn_right(6, 1)
            
            time.sleep(0.1)
            
            for i in range(8):
                d.errors()
                
            d.stop()
            time.sleep(0.1)
        
        print("Done")

# # ! MPU6050
# class MPU6050:
#     def __init__(self, addr: int = None):
#         self.addr = addr
#         self.sensor = mpu.mpu6050(self.addr or 0x68, bus=1)

#     def accelerometer(self):
#         return self.sensor.get_accel_data()
        
#     def gyroscope(self):
#         return self.sensor.get_gyro_data()
        
#     def temperature(self):
#         return self.sensor.get_temp()

# m = MPU6050(0x68)
# while True:
#     print(m.gyroscope(), m.accelerometer())
#     time.sleep(0.1)