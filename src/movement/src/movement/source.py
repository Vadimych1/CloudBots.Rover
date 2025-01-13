import smbus2
import time
import ctypes
import math
# import sys, os

DEF_CHIP_ID_FLASH		= 0x3C																								#	ID линейки чипов - константа для всех чипов серии Flash (позволяет идентифицировать принадлежность чипа к серии).
DEF_CHIP_ID_METRO		= 0xC3																								#	ID линейки чипов - константа для всех чипов серии Metro (позволяет идентифицировать принадлежность чипа к серии).
DEF_MODEL_MOT			= 0x14																								#	Идентификатор модели - константа.
REG_FLAGS_0				= 0x00																								#	Адрес регистра флагов управления для чтения.
REG_BITS_0				= 0x01																								#	Адрес регистра битов  управления для чтения и записи.
REG_FLAGS_1				= 0x02																								#	Адрес регистра флагов управления для чтения.
REG_BITS_1				= 0x03																								#	Адрес регистра битов  управления для чтения и записи.
REG_MODEL				= 0x04																								#	Адрес регистра содержащего номер типа модуля.
REG_VERSION				= 0x05																								#	Адрес регистра содержащего версию прошивки.
REG_ADDRESS				= 0x06																								#	Адрес регистра содержащего текущий адрес модуля на шине I2C. Если адрес указан с флагом IF-PIN-ADDRES то адрес установится (и запишется в регистр) только при наличии 1 на входе PIN_ADDRES.
REG_CHIP_ID				= 0x07																								#	Адрес регистра содержащего ID линейки чипов «Flash». По данному ID можно определить принадлежность чипа к линейки «Flash».
REG_MOT_FREQUENCY_L		= 0x08																								#	Адрес регистра хранящего частоту ШИМ в Гц (младший байт).
REG_MOT_FREQUENCY_H		= 0x09																								#	Адрес регистра хранящего частоту ШИМ в Гц (старший байт).
REG_MOT_MAX_RPM_DEV		= 0x0A																								#	Адрес регистра хранящего максимально допустимый % отклонения реальной скорости от заданной. При превышении данного процента загорается светодиод ошибки и устанавливается флаг «MOT_FLG_RPM_ERR».
REG_MOT_FLG				= 0x10																								#	Адрес регистра статусных флагов «MOT_FLG_RPM_EN», «MOT_FLG_RPM_ERR», «MOT_FLG_DRV_ERR», «MOT_FLG_STOP», «MOT_FLG_NEUTRAL.
REG_MOT_MAGNET			= 0x11																								#	Адрес регистра хранящего количество магнитов на роторе мотора возле датчика Холла.
REG_MOT_REDUCER_L		= 0x12																								#	Адрес регистра (младший байт) хранящего передаточное отношение редуктора (в сотых долях) от 1:0.01 до 1:167'772.15.
REG_MOT_REDUCER_C		= 0x13																								#	Адрес регистра (средний байт).
REG_MOT_REDUCER_H		= 0x14																								#	Адрес регистра (старший байт).
REG_MOT_SET_PWM_L		= 0x15																								#	Адрес регистра (младший байт) хранящего заданое значение ШИМ ±4095. Запись любого значения приводит к сбросу регистров «REG_MOT_SET_RPM» и сбросу флага «MOT_FLG_RPM_EN».
REG_MOT_SET_PWM_H		= 0x16																								#	Адрес регистра (старший байт).
REG_MOT_SET_RPM_L		= 0x17																								#	Адрес регистра (младший байт) хранящего заданое количество оборотов в минуту ±32'767. Запись любого значения приводит к сбросу регистров «REG_MOT_SET_PWM» и установке флага «MOT_FLG_RPM_EN».
REG_MOT_SET_RPM_H		= 0x18																								#	Адрес регистра (старший байт).
REG_MOT_GET_RPM_L		= 0x19																								#	Адрес регистра (младший байт) хранящего реальное количество оборотов в минуту ±32'767. Значение берётся с датчиков Холла.
REG_MOT_GET_RPM_H		= 0x1A																								#	Адрес регистра (старший байт).
REG_MOT_GET_REV_L		= 0x1B																								#	Адрес регистра (младший байт) хранящего реальное количество совершённых оборотов колеса (в сотых долях полного оборота) от 0.00 до 167'772.15. Сброс значения осуществляется записью любого числа в тройной регистр «REG_MOT_STOP_REV».
REG_MOT_GET_REV_C		= 0x1C																								#	Адрес регистра (средний байт).
REG_MOT_GET_REV_H		= 0x1D																								#	Адрес регистра (старший байт).
REG_MOT_STOP_REV_L		= 0x1E																								#	Адрес регистра (младший байт) хранящего количество оборотов колеса (в сотых долях полного оборота) от 0.00 до 167'772.15, оставшееся до установки бита «MOT_BIT_STOP». Запись значения = 0x000000 не приводит к установке бита «MOT_BIT_STOP».
REG_MOT_STOP_REV_C		= 0x1F																								#	Адрес регистра (средний байт).
REG_MOT_STOP_REV_H		= 0x20																								#	Адрес регистра (старший байт).
REG_MOT_STOP_TMR_L		= 0x21																								#	Адрес регистра (младший байт) хранящего время (в мс) от 0 до 16'777'215, оставшееся до установки бита «MOT_BIT_STOP». Запись значения = 0x000000 не приводит к установке бита «MOT_BIT_STOP».
REG_MOT_STOP_TMR_C		= 0x22																								#	Адрес регистра (средний байт).
REG_MOT_STOP_TMR_H		= 0x23																								#	Адрес регистра (старший байт).
REG_MOT_STOP			= 0x24																								#	Адрес регистра остановки мотора. Содержит бит остановки мотора «MOT_BIT_STOP» и бит освобождения мотора «MOT_BIT_NEUTRAL» при его остановке.
REG_BITS_2				= 0x25																								#	Адрес регистра битов. Содержит бит вращения вала по ч.с. «MOT_BIT_DIR_CKW» и биты инверсии «MOT_BIT_INV_RDR», «MOT_BIT_INV_PIN».
REG_MOT_VOLTAGE			= 0x26																								#	Адрес регистра хранящего номинальное напряжение электродвигателя в десятых долях В.
REG_MOT_NOMINAL_RPM_L	= 0x27																								#	Адрес регистра (младший байт) хранящего номинальное количество оборотов в минуту. Количество оборотов вала редуктора при номинальном напряжении питания мотора и 100% ШИМ.
REG_MOT_NOMINAL_RPM_H	= 0x28																								#	Адрес регистра (старший байт).
MOT_FLG_RPM_EN			= 0x80																								#	Флаг указывает на то, что скорость мотора задана количеством оборотов в минуту. Если флаг сброшен, значит скорость мотора задана значением ШИМ.
MOT_FLG_RPM_ERR			= 0x20																								#	Флаг отличия между заданным и реальным количеством оборотов в минуту более чем на «REG_MOT_MAX_RPM_DEV» процентов.
MOT_FLG_DRV_ERR			= 0x10																								#	Флаг ошибки драйвера (перегрузка по току, перегрев драйвера или низкий уровень напряжения питания мотора).
MOT_FLG_STOP			= 0x02																								#	Флаг указывает на то, что мотор остановлен.
MOT_FLG_NEUTRAL			= 0x01																								#	Флаг указывает на то, что выводы мотора отключены (его можно вращать).
MOT_BIT_STOP			= 0x02																								#	Бит  остановки мотора.
MOT_BIT_NEUTRAL			= 0x01																								#	Бит  освобождения выводов мотора при его остановке.
MOT_BIT_DIR_CKW			= 0x04																								#	Бит  вращения вала по ч.с., при положительной скорости. Бит позволяет менять направление вращения вала не меняя знак скорости или ШИМ. Используется для указания расположения модуля по левому (0) или правому (1) борту подвижного устройства.
MOT_BIT_INV_RDR			= 0x02																								#	Бит  инверсии редуктора.      Бит должен быть установлен если вал редуктора вращается в сторону противоположную вращению ротора мотора.
MOT_BIT_INV_PIN			= 0x01																								#	Бит  инверсии выводов мотора. Бит должен быть установлен при обратном подключении выводов мотора, если ротор мотора вращается против часовой стрелки.

MOT_ERR_SPD = 1
MOT_ERR_DRV = 2

MOT_MET = 3																									#	setStop(расстояние, MOT_MET); getStop(MOT_MET); setSpeed(скорость, MOT_RPM/MOT_PWM, расстояние, MOT_MET); getSum(MOT_MET);
MOT_SEC = 4																									#	setStop(длительность, MOT_SEC); getStop(MOT_SEC); setSpeed(скорость, MOT_RPM/MOT_PWM, длительность, MOT_SEC); 
MOT_M_S = 5																									#	setSpeed(скорость, MOT_M_S); getSpeed(MOT_M_S);
MOT_REV = 6																									#	setStop(количество, MOT_REV); getStop(MOT_REV); setSpeed(скорость, MOT_RPM/MOT_PWM, количество, MOT_REV); getSum(MOT_REV);
MOT_RPM = 7																									#	setSpeed(скорость, MOT_RPM); getSpeed(MOT_RPM);
MOT_PWM = 8																									#	setSpeed(скорость, MOT_PWM); getSpeed(MOT_PWM);

i2c = smbus2.SMBus(1)
motor_dll = ctypes.cdll.LoadLibrary("libs/motor/motor.so")

# float2
motor_dll.encodeFloat2.argtypes = [ctypes.c_float, ctypes.c_int]
motor_dll.encodeFloat2.restype = ctypes.c_uint8

motor_dll.decodeFloat2.argtypes = [ctypes.c_uint8, ctypes.c_uint8]
motor_dll.decodeFloat2.restype = ctypes.c_float

motor_dll.decodeFloat2Abs.argtypes = [ctypes.c_uint8, ctypes.c_uint8]
motor_dll.decodeFloat2.restype = ctypes.c_float

# float3
motor_dll.encodeFloat3.argtypes = [ctypes.c_float, ctypes.c_int]
motor_dll.encodeFloat3.restype = ctypes.c_uint8

motor_dll.decodeFloat3.argtypes = [ctypes.c_uint8, ctypes.c_uint8]
motor_dll.decodeFloat3.restype = ctypes.c_float

        
def setSpeedData(valSpeed):
    data = [motor_dll.encodeFloat2(valSpeed, 0), motor_dll.encodeFloat2(valSpeed, 1)]    
    return data

def getSpeedData(data):
    return motor_dll.decodeFloat2(data[0], data[1])

def setPwmData(frequency: int):
    # ???
    data = [0, 0]
    data[0] = (frequency & 0x00FF).to_bytes(1, byteorder='little')[0]
    data[1] = (frequency >> 8).to_bytes(1, byteorder='little')[0]
    return data

def setStopData(value: float):
    data = [
        motor_dll.encodeFloat3(value, 0),
        motor_dll.encodeFloat3(value, 1),
        motor_dll.encodeFloat3(value, 2),
    ]
    return data

def getStopData(data):
    rev = motor_dll.decodeFloat3(data[0], data[1], data[2]) / 100.0
    tmr = motor_dll.decodeFloat3(data[3], data[4], data[5])
    
    return rev, tmr
        
def getStopDataSec(data):
    result = motor_dll.decodeFloat2Abs(data[0], data[1])
    if result == 0:
        result = 1.0
    else:
        result = float(result)

    return result

class MotorDriver:
    def __init__(self, i2c: smbus2.SMBus, addr: int, radius: int):
        self.i2c = i2c
        self.addr = addr
        self.radius = radius

    def reset(self) -> None:
        data = self.read(REG_BITS_0, 1)
        data[0] |= 0b10000000
        self.write(REG_BITS_0, data)
        
        time.sleep(0.01)
        
        data = self.read(REG_FLAGS_0, 1)
        while data[0] & 0b10000000 == 0:
            time.sleep(0.005)
     
    def getPullI2C(self) -> bool:
        data = self.read(REG_FLAGS_0, 2)
        return data[0] & 0b00000100 != 0 and data[1] & 0b00000100 != 0
    
    def setPullI2C(self, value: bool) -> None:
        data = self.read(REG_FLAGS_0, 2)
        if data[0] & 0b00000100 == 0:
            return
        
        if value:
            data[0] = data[1] | 0b00000100
        else:
            data[0] = data[1] & ~0b00000100
            
        self.write(REG_BITS_0, data)
        time.sleep(0.05)
        
    def setFreqPWM(self, frequency: int) -> None:
        if not 1000 < frequency < 25:
            return        
        self.write(REG_MOT_FREQUENCY_L, setPwmData(frequency))
    
    def setMagnet(self, n: int) -> None:
        data = [n]
        self.write(REG_MOT_MAGNET, data)
    
    def getMagnet(self) -> int:
        return self.read(REG_MOT_MAGNET, 1)[0]
    
    def setError(self, deviation: int) -> None:
        if deviation > 100:
            deviation = 100
        data = [deviation]
        self.write(REG_MOT_MAX_RPM_DEV, data)
    
    def getError(self) -> int:
        data = self.read(REG_MOT_FLG, 1)[0]
        if data[0] & MOT_FLG_RPM_ERR > 0: return MOT_ERR_SPD
        if data[0] & MOT_FLG_DRV_ERR > 0: return MOT_ERR_DRV
        return 0
    
    def setSpeed(self, speed: float, speedType: int, stop: float, stopType: int):
        reg = None
        
        if stopType == MOT_MET or stopType == MOT_REV or stopType == MOT_SEC:
            self.setStop(stop, stopType)
            
        if speedType == MOT_RPM:
            speed = min(max(-32767.0, speed), 32767.0)
            reg = REG_MOT_SET_RPM_L
        
        elif speedType == MOT_M_S:
            speed *= 60000.0
            speed /= (2.0 * math.pi * self.radius)
            speed = min(max(-32767.0, speed), 32767.0)
            reg = REG_MOT_SET_RPM_L
            
        elif speedType == MOT_PWM:
            speed *= 4095.0
            speed /= 100.0
            speed = min(max(-4095.0, speed), 4095.0)
            reg = REG_MOT_SET_PWM_L
            
        else:
            return
        
        q = setSpeedData(speed)
        print(q)
        print(getSpeedData(q))
        self.write(reg, q)
        
    def setStop(self, value: float, type: int):
        if type == 0xFF:
            data = self.read(REG_MOT_FLG, 1)
            data = MOT_BIT_STOP | (MOT_BIT_NEUTRAL if data[0] & MOT_FLG_NEUTRAL > 0 else 0)
            self.write(REG_MOT_STOP, data)
            
        elif type == MOT_MET:
            value *= 1000.0
            value /= (2.0 * math.pi * self.radius)
            
            if value > 167772.15:
                value = 167772.15
                
            value *= 100
            
            self.write(REG_MOT_STOP_REV_L, setStopData(value))
            
        elif type == MOT_REV:
            if value > 167772.15:
                value = 167772.15
                
            value *= 100

            self.write(REG_MOT_STOP_REV_L, setStopData(value))
            
        elif type == MOT_SEC:
            if value > 16777.215:
                value = 16777.215
            
            value *= 1000
            
            self.write(REG_MOT_STOP_TMR_L, setStopData(value))
            
    def getStop(self, type: int) -> float:
        result = -1
        
        data = self.read(REG_MOT_STOP_REV_L, 6)
        rev, tmr = getStopData(data)
        
        data = self.read(REG_MOT_MAGNET, 1)
        if (data[0] == 0 and (type != MOT_SEC or not tmr)):
            return 0
        
        if type == MOT_REV or type == MOT_MET:
            if rev:
                result = rev
                
            elif tmr:
                data = self.read(REG_MOT_GET_RPM_L, 2)
                result = getStopDataSec(data)
                result = result * tmr / 60000
                
            if type == MOT_MET:
                result *= 2.0 * math.pi * self.radius 
                result /= 1000
        
        elif type == MOT_SEC:
            if tmr:
                result = tmr / 1000
            elif rev:
                data = self.read(REG_MOT_GET_RPM_L, 2)
                result = getStopDataSec(data)
                result = rev * 60.0 / result
                
        return result
    
    def read(self, reg: int, l: int) -> list:
        return self.i2c.read_i2c_block_data(self.addr, reg, l)
    
    def write(self, reg: int, data: list) -> None:
        self.i2c.write_i2c_block_data(self.addr, reg, data)
    
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