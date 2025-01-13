#include <stdint.h>
#include <sys/time.h>
#include <cstddef>
#include <cmath>
#include <bitset>
#include <i2c/i2c.h>
#include <string.h>

#define PI M_PI

// defs
																																			//
#define			DEF_CHIP_ID_FLASH		0x3C																								//	ID линейки чипов - константа для всех чипов серии Flash (позволяет идентифицировать принадлежность чипа к серии).
#define			DEF_CHIP_ID_METRO		0xC3																								//	ID линейки чипов - константа для всех чипов серии Metro (позволяет идентифицировать принадлежность чипа к серии).
#define			DEF_MODEL_MOT			0x14																								//	Идентификатор модели - константа.
//				Адреса регистров модуля:																									//
#define			REG_FLAGS_0				0x00																								//	Адрес регистра флагов управления для чтения.
#define			REG_BITS_0				0x01																								//	Адрес регистра битов  управления для чтения и записи.
#define			REG_FLAGS_1				0x02																								//	Адрес регистра флагов управления для чтения.
#define			REG_BITS_1				0x03																								//	Адрес регистра битов  управления для чтения и записи.
#define			REG_MODEL				0x04																								//	Адрес регистра содержащего номер типа модуля.
#define			REG_VERSION				0x05																								//	Адрес регистра содержащего версию прошивки.
#define			REG_ADDRESS				0x06																								//	Адрес регистра содержащего текущий адрес модуля на шине I2C. Если адрес указан с флагом IF-PIN-ADDRES то адрес установится (и запишется в регистр) только при наличии 1 на входе PIN_ADDRES.
#define			REG_CHIP_ID				0x07																								//	Адрес регистра содержащего ID линейки чипов «Flash». По данному ID можно определить принадлежность чипа к линейки «Flash».
#define			REG_MOT_FREQUENCY_L		0x08																								//	Адрес регистра хранящего частоту ШИМ в Гц (младший байт).
#define			REG_MOT_FREQUENCY_H		0x09																								//	Адрес регистра хранящего частоту ШИМ в Гц (старший байт).
#define			REG_MOT_MAX_RPM_DEV		0x0A																								//	Адрес регистра хранящего максимально допустимый % отклонения реальной скорости от заданной. При превышении данного процента загорается светодиод ошибки и устанавливается флаг «MOT_FLG_RPM_ERR».
#define			REG_MOT_FLG				0x10																								//	Адрес регистра статусных флагов «MOT_FLG_RPM_EN», «MOT_FLG_RPM_ERR», «MOT_FLG_DRV_ERR», «MOT_FLG_STOP», «MOT_FLG_NEUTRAL.
#define			REG_MOT_MAGNET			0x11																								//	Адрес регистра хранящего количество магнитов на роторе мотора возле датчика Холла.
#define			REG_MOT_REDUCER_L		0x12																								//	Адрес регистра (младший байт) хранящего передаточное отношение редуктора (в сотых долях) от 1:0.01 до 1:167'772.15.
#define			REG_MOT_REDUCER_C		0x13																								//	Адрес регистра (средний байт).
#define			REG_MOT_REDUCER_H		0x14																								//	Адрес регистра (старший байт).
#define			REG_MOT_SET_PWM_L		0x15																								//	Адрес регистра (младший байт) хранящего заданое значение ШИМ ±4095. Запись любого значения приводит к сбросу регистров «REG_MOT_SET_RPM» и сбросу флага «MOT_FLG_RPM_EN».
#define			REG_MOT_SET_PWM_H		0x16																								//	Адрес регистра (старший байт).
#define			REG_MOT_SET_RPM_L		0x17																								//	Адрес регистра (младший байт) хранящего заданое количество оборотов в минуту ±32'767. Запись любого значения приводит к сбросу регистров «REG_MOT_SET_PWM» и установке флага «MOT_FLG_RPM_EN».
#define			REG_MOT_SET_RPM_H		0x18																								//	Адрес регистра (старший байт).
#define			REG_MOT_GET_RPM_L		0x19																								//	Адрес регистра (младший байт) хранящего реальное количество оборотов в минуту ±32'767. Значение берётся с датчиков Холла.
#define			REG_MOT_GET_RPM_H		0x1A																								//	Адрес регистра (старший байт).
#define			REG_MOT_GET_REV_L		0x1B																								//	Адрес регистра (младший байт) хранящего реальное количество совершённых оборотов колеса (в сотых долях полного оборота) от 0.00 до 167'772.15. Сброс значения осуществляется записью любого числа в тройной регистр «REG_MOT_STOP_REV».
#define			REG_MOT_GET_REV_C		0x1C																								//	Адрес регистра (средний байт).
#define			REG_MOT_GET_REV_H		0x1D																								//	Адрес регистра (старший байт).
#define			REG_MOT_STOP_REV_L		0x1E																								//	Адрес регистра (младший байт) хранящего количество оборотов колеса (в сотых долях полного оборота) от 0.00 до 167'772.15, оставшееся до установки бита «MOT_BIT_STOP». Запись значения 0x000000 не приводит к установке бита «MOT_BIT_STOP».
#define			REG_MOT_STOP_REV_C		0x1F																								//	Адрес регистра (средний байт).
#define			REG_MOT_STOP_REV_H		0x20																								//	Адрес регистра (старший байт).
#define			REG_MOT_STOP_TMR_L		0x21																								//	Адрес регистра (младший байт) хранящего время (в мс) от 0 до 16'777'215, оставшееся до установки бита «MOT_BIT_STOP». Запись значения 0x000000 не приводит к установке бита «MOT_BIT_STOP».
#define			REG_MOT_STOP_TMR_C		0x22																								//	Адрес регистра (средний байт).
#define			REG_MOT_STOP_TMR_H		0x23																								//	Адрес регистра (старший байт).
#define			REG_MOT_STOP			0x24																								//	Адрес регистра остановки мотора. Содержит бит остановки мотора «MOT_BIT_STOP» и бит освобождения мотора «MOT_BIT_NEUTRAL» при его остановке.
#define			REG_BITS_2				0x25																								//	Адрес регистра битов. Содержит бит вращения вала по ч.с. «MOT_BIT_DIR_CKW» и биты инверсии «MOT_BIT_INV_RDR», «MOT_BIT_INV_PIN».
#define			REG_MOT_VOLTAGE			0x26																								//	Адрес регистра хранящего номинальное напряжение электродвигателя в десятых долях В.
#define			REG_MOT_NOMINAL_RPM_L	0x27																								//	Адрес регистра (младший байт) хранящего номинальное количество оборотов в минуту. Количество оборотов вала редуктора при номинальном напряжении питания мотора и 100% ШИМ.
#define			REG_MOT_NOMINAL_RPM_H	0x28																								//	Адрес регистра (старший байт).
																																			//
//				Позиция битов и флагов:																										//
#define			MOT_FLG_RPM_EN			0x80																								//	Флаг указывает на то, что скорость мотора задана количеством оборотов в минуту. Если флаг сброшен, значит скорость мотора задана значением ШИМ.
#define			MOT_FLG_RPM_ERR			0x20																								//	Флаг отличия между заданным и реальным количеством оборотов в минуту более чем на «REG_MOT_MAX_RPM_DEV» процентов.
#define			MOT_FLG_DRV_ERR			0x10																								//	Флаг ошибки драйвера (перегрузка по току, перегрев драйвера или низкий уровень напряжения питания мотора).
#define			MOT_FLG_STOP			0x02																								//	Флаг указывает на то, что мотор остановлен.
#define			MOT_FLG_NEUTRAL			0x01																								//	Флаг указывает на то, что выводы мотора отключены (его можно вращать).
#define			MOT_BIT_STOP			0x02																								//	Бит  остановки мотора.
#define			MOT_BIT_NEUTRAL			0x01																								//	Бит  освобождения выводов мотора при его остановке.
#define			MOT_BIT_DIR_CKW			0x04																								//	Бит  вращения вала по ч.с., при положительной скорости. Бит позволяет менять направление вращения вала не меняя знак скорости или ШИМ. Используется для указания расположения модуля по левому (0) или правому (1) борту подвижного устройства.
#define			MOT_BIT_INV_RDR			0x02																								//	Бит  инверсии редуктора.      Бит должен быть установлен если вал редуктора вращается в сторону противоположную вращению ротора мотора.
#define			MOT_BIT_INV_PIN			0x01																								//	Бит  инверсии выводов мотора. Бит должен быть установлен при обратном подключении выводов мотора, если ротор мотора вращается против часовой стрелки.
																																			//
#ifndef			MOT_ERR_SPD																													//
#define			MOT_ERR_SPD				1																									//	getError();
#endif																																		//
																																			//
#ifndef			MOT_ERR_DRV																													//
#define			MOT_ERR_DRV				2																									//	getError();
#endif																																		//
																																			//
#ifndef			MOT_MET																														//	Параметр информирубщий о том, что значение указано в МЕТРАХ.
#define			MOT_MET					3																									//	setStop(расстояние, MOT_MET); getStop(MOT_MET); setSpeed(скорость, MOT_RPM/MOT_PWM, расстояние, MOT_MET); getSum(MOT_MET);
#endif																																		//
																																			//
#ifndef			MOT_SEC																														//	Параметр информирубщий о том, что значение указано в СЕКУНДАХ.
#define			MOT_SEC					4																									//	setStop(длительность, MOT_SEC); getStop(MOT_SEC); setSpeed(скорость, MOT_RPM/MOT_PWM, длительность, MOT_SEC); 
#endif																																		//
																																			//
#ifndef			MOT_M_S																														//	Параметр информирубщий о том, что значение указано в МЕТРАХ В СЕКУНДУ.
#define			MOT_M_S					5																									//	setSpeed(скорость, MOT_M_S); getSpeed(MOT_M_S);
#endif																																		//
																																			//
#ifndef			MOT_REV																														//	Параметр информирубщий о том, что значение является КОЛИЧЕСТВОМ ПОЛНЫХ ОБОРОТОВ.
#define			MOT_REV					6																									//	setStop(количество, MOT_REV); getStop(MOT_REV); setSpeed(скорость, MOT_RPM/MOT_PWM, количество, MOT_REV); getSum(MOT_REV);
#endif																																		//
																																			//
#ifndef			MOT_RPM																														//	Параметр информирубщий о том, что значение является КОЛИЧЕСТВОМ ОБОРОТОВ В МИНУТУ.
#define			MOT_RPM					7																									//	setSpeed(скорость, MOT_RPM); getSpeed(MOT_RPM);
#endif																																		//
																																			//
#ifndef			MOT_PWM																														//	Параметр информирубщий о том, что значение является КОЭФФИЦИЕНТОМ ЗАПОЛНЕНИЯ ШИМ.
#define			MOT_PWM					8																									//	setSpeed(скорость, MOT_PWM); getSpeed(MOT_PWM);
#endif																																		//

// predefined funcs
uint64_t time_ms(void) {
	struct timeval tv;
	gettimeofday(&tv, NULL);
	return (uint64_t)tv.tv_sec * 1000 + tv.tv_usec / 1000;
}

void delay(uint16_t ms) {
	uint64_t t = time_ms();
	while (time_ms() - t < ms) {} 
}

uint8_t busNum;
uint64_t timReset;
uint8_t data[];
uint16_t radius; // TODO: add setRadius
i2c_device devices[];

int i2c_bus = -1;

// Module
void setBus(uint8_t bus) {
	busNum = bus;
}

void setRadius(uint16_t valRadius) {
	radius = valRadius;
}

void init(void) {
	// open i2c bus (https://github.com/amaork/libi2c/blob/master/example/i2c_tools.c ref)
	int bus;
	char bus_name[32];
	memset(bus_name, 0, sizeof(bus_name));

	if (snprintf(bus_name, sizeof(bus_name), "/dev/i2c-%u", busNum) < 0) {
		fprintf(stderr, "invalid bus");
		exit(-1);
	}

	if ((bus = i2c_open(bus_name)) == -1) {
		fprintf(stderr, "error opening bus");
		exit(-1);
	}

	i2c_bus = bus;
}

void initDevice(uint8_t addr, uint8_t device_index) {
	if (i2c_bus == -1) {
		fprintf(stderr, "i2c bus is not initialized");
		exit(-1);
	}
	
	i2c_device dev;
	memset(&dev, 0, sizeof(dev));
	i2c_init_device(&dev);

	dev.bus = i2c_bus;
	dev.addr = addr;
	dev.page_bytes = 0;
	dev.iaddr_bytes = 0;

	devices[device_index] = dev;
}

i2c_device getDev(uint8_t index) {
	return devices[index];
}

bool reset(uint8_t device)
{
	i2c_device ddev = getDev(device);

	timReset = time_ms(); //	сохраняем текущее время.
							//	Устанавливаем бит перезагрузки:																					//
	if (_readBytes(REG_BITS_0, 1, &ddev) == false)
	{
		return false;
	}					   //	Читаем 1 байт регистра «BITS_0» в массив «data».
	data[0] |= 0b10000000; //	Устанавливаем бит «SET_RESET»
	if (_writeBytes(REG_BITS_0, 1, 0, &ddev) == false)
	{
		return false;
	} //	Записываем 1 байт в регистр «BITS_0» из массива «data».
		//	Переинициируем шину в связи с программным отключением подтяжек шины I2C в модуле:								//
	delay(10);

	// selI2C->begin(); //	Ждём восстановление подтяжек линий SCL/SDA и переинициируем работу с шиной I2C. // TODO
	
	do
	{
		if (_readBytes(REG_FLAGS_0, 1, &ddev) == false)
		{
			return false;
		}
	}									 //	Читаем 1 байт регистра «REG_FLAGS_0» в массив «data».
	while ((data[0] & 0b10000000) == 0); //	Повторяем чтение пока не установится флаг «FLG_RESET».
	return true;
}

bool getPullI2C(uint8_t device)
{
	i2c_device ddev = getDev(device);

	if (_readBytes(REG_FLAGS_0, 2, &ddev) == false)
	{
		return false;
	} //	Читаем 2 байта начиная с регистра «REG_FLAGS_0» в массив «data».
		//	Проверяем поддерживает ли модуль управление подтяжкой линий шины I2C:
	if ((data[0] & 0b00000100) == false)
	{
		return false;
	} //	Если флаг «FLG_I2C_UP» регистра «REG_FLAGS_0» сброшен, значит модуль не поддерживает управление подтяжкой линий шины I2C.
		//	Проверяем установлена ли подтяжка линий шины I2C:
	if ((data[1] & 0b00000100) == false)
	{
		return false;
	}			 //	Если бит  «SET_I2C_UP» регистра «REG_BITS_0»  сброшен, значит подтяжка линий шины I2C не установлена.
	return true;
}

bool setPullI2C(bool f, uint8_t device)
{
	i2c_device ddev = getDev(device);

	if (_readBytes(REG_FLAGS_0, 2, ddev) == false)
	{
		return false;
	} //	Читаем 2 байта начиная с регистра «REG_FLAGS_0» в массив «data».
		//	Проверяем поддерживает ли модуль управление подтяжкой линий шины I2C:											//
	if ((data[0] & 0b00000100) == false)
	{
		return false;
	} //	Если флаг «FLG_I2C_UP» регистра «REG_FLAGS_0» сброшен, значит модуль не поддерживает управление подтяжкой линий шины I2C.
		//	Устанавливаем или сбрасываем бит включения подтяжки линий шины I2C:												//
	if (f)
	{
		data[0] = (data[1] | 0b00000100);
	} //	Если флаг «f» установлен, то копируем значение из 1 в 0 элемент массива «data» установив бит «SET_I2C_UP».
	else
	{
		data[0] = (data[1] & ~0b00000100);
	} //	Если флаг «f» сброшен   , то копируем значение из 1 в 0 элемент массива «data» сбросив   бит «SET_I2C_UP».
		//	Сохраняем получившееся значение в регистр «REG_BITS_0»:															//
	if (_writeBytes(REG_BITS_0, 1, 0, ddev) == false)
	{
		return false;
	}			 //	Записываем 1 байт в регистр «REG_BITS_0» из массива «data».
	delay(50);	 //	Даём время для сохранения данных в энергонезависимую память модуля.
	return true; //	Возвращаем флаг успеха.
} //
  //
//		Установка частоты ШИМ:																									//	Возвращаемое значение:	результат установки true/false.
bool setFreqPWM(uint16_t frequency, uint8_t device)
{
	i2c_device ddev = getDev(device);

	if (frequency < 25)
	{
		return false;
	} //	Если частота указана некорректно, то возвращаем false.
	if (frequency > 1000)
	{
		return false;
	}									   //	Если частота указана некорректно, то возвращаем false.
											//	Готовим два байта для записи:																					//
	data[0] = uint8_t(frequency & 0x00FF); //	Устанавливаем младший байт значения «frequency» для регистра «REG_MOT_FREQUENCY_L».
	data[1] = uint8_t(frequency >> 8);	   //	Устанавливаем старший байт значения «frequency» для регистра «REG_MOT_FREQUENCY_H».
											//	Отправляем подготовленные данные в модуль:																		//
	if (_writeBytes(REG_MOT_FREQUENCY_L, 2, 0) == false)
	{
		return false;
	}			 //	Записываем 2 байта из массива «data» в модуль, начиная с регистра «REG_MOT_FREQUENCY_L».

	return true;
}

//		Установка количества магнитов у датчика Холла:																			//	Возвращаемое значение:	результат установки true/false.
bool setMagnet(uint8_t sum, uint8_t device)
{
	i2c_device ddev = getDev(device);

					//	Готовим данные для передачи:																					//
	data[0] = sum; //	Сохраняем указанное количество магнитов.
					//	Отправляем подготовленные данные в модуль:																		//
	if (_writeBytes(REG_MOT_MAGNET, 1, 0) == false)
	{
		return false;
	}
	return true; //
}

//		Получение количества магнитов у датчика Холла:																			//	Возвращаемое значение:	количество магнитов от 1 до 63.
uint8_t getMagnet(uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Читаем и возвращаем количество магнитов у датчика Холла:														//
	if (_readBytes(REG_MOT_MAGNET, 1) == false)
	{
		return 0;
	}				//	Читаем 1 байт из регистра «REG_MOT_MAGNET» в массив «data».
	return data[0]; //	Возвращаем количество магнитов у датчика Холла.
}

//		Установка передаточного отношения редуктора:																			//	Возвращаемое значение:	результат установки true/false.
bool setReducer(float gear, uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Проверяем полученные данные:																					//
	if (gear < 0.01f)
	{
		gear = 0.01f;
	} //	Передаточное отношение не может быть ниже 0,01.
	if (gear > 167772.15f)
	{
		gear = 167772.15f;
	}											   //	Передаточное отношение не может превышать 167772,15.
													//	Готовим данные для передачи:																					//
	gear *= 100;								   //
	data[0] = ((uint32_t)gear) & 0x000000FF;	   //	Байт для записи в регистр «REG_MOT_REDUCER_L».
	data[1] = ((uint32_t)gear >> 8) & 0x000000FF;  //	Байт для записи в регистр «REG_MOT_REDUCER_C».
	data[2] = ((uint32_t)gear >> 16) & 0x000000FF; //	Байт для записи в регистр «REG_MOT_REDUCER_H».
													//	Отправляем подготовленные данные в модуль:																		//
	if (_writeBytes(REG_MOT_REDUCER_L, 3, 0) == false)
	{
		return false;
	}			 //	Записываем 3 байта из массива «data» в модуль, начиная с регистра «REG_MOT_REDUCER_L».
					//	Возвращаем результат:																							//
	return true; //
} //
  //
//		Получение передаточного отношения редуктора:																			//	Возвращаемое значение:	передаточное отношение редуктора от 0.01 до 167'772.15.
float getReducer(uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Читаем и возвращаем передаточное отношение редуктора:															//
	if (_readBytes(REG_MOT_REDUCER_L, 3) == false)
	{
		return 0;
	}																						 //	Читаем 3 байта начиная с регистра «REG_MOT_REDUCER_L» в массив «data».
	return (float)((int32_t)data[2] << 16 | (int32_t)data[1] << 8 | (int32_t)data[0]) / 100; //	Возвращаем прочитанное значение.
} //
  //
//		Установка процента отклонения скорости превышение которого приведёт к установке флага ошибки:							//	Возвращаемое значение:	результат установки true/false.
bool setError(uint8_t deviation, uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Проверяем полученные данные:																					//
	if (deviation > 100)
	{
		deviation = 100;
	}					 //	Отклонение не может превышать 100%.
							//	Готовим данные для передачи:																					//
	data[0] = deviation; //	Байт для записи в регистр «REG_MOT_MAX_RPM_DEV».
							//	Отправляем подготовленные данные в модуль:																		//
	if (_writeBytes(REG_MOT_MAX_RPM_DEV, 1, 0) == false)
	{
		return false;
	}			 //	Записываем 1 байт из массива «data» в регистр «REG_MOT_MAX_RPM_DEV».
					//	Возвращаем результат:																							//
	return true; //
} //
  //
//		Получение флага ошибки скорости или драйвера:																			//	Возвращаемое значение:	флаг наличия ошибки: 0 / MOT_ERR_SPD / MOT_ERR_DRV.
uint8_t getError(uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Считываем состояние регистра флагов:																			//
	if (_readBytes(REG_MOT_FLG, 1) == false)
	{
		return 0;
	} //	Читаем 1 байт регистра «REG_MOT_FLG» в массив «data».
		//	Возвращаем результат:																							//
	if (data[0] & MOT_FLG_RPM_ERR)
	{
		return MOT_ERR_SPD;
	} //	Если в прочитанном байте установлен флаг «MOT_FLG_RPM_ERR», то возвращаем ошибку «MOT_ERR_SPD».
	if (data[0] & MOT_FLG_DRV_ERR)
	{
		return MOT_ERR_DRV;
	} //	Если в прочитанном байте установлен флаг «MOT_FLG_DRV_ERR», то возвращаем ошибку «MOT_ERR_DRV».

	return 0;
} //
  //
//		Установка скорости и условия остановки:																					//	Возвращаемое значение:	результат установки true/false.
bool setSpeed(float valSpeed, uint8_t typeSpeed, float valStop, uint8_t typeStop, uint8_t device)
{
	i2c_device ddev = getDev(device);

	uint8_t reg; //
					//	Передаём условие остановки:																						//
	if (typeStop == MOT_MET || typeStop == MOT_REV || typeStop == MOT_SEC)
	{ //	Если тип условия остановки задан верно, то ...
		if (!setStop(valStop, typeStop))
		{
			return false;
		} //	Возвращаем false если условие остановки не принято.
	} //
	//	Проверяем полученные данные:																					//
	if (typeSpeed == MOT_RPM)
	{	//
		//	Если скорость задана количеством оборотов в минуту:															//
		if (valSpeed > 32767.0f)
		{
			valSpeed = 32767.0f;
		} //	Количество оборотов не может быть выше значения +32'767.
		if (valSpeed < -32767.0f)
		{
			valSpeed = -32767.0f;
		}						 //	Количество оборотов не может быть ниже значения -32'767.
		reg = REG_MOT_SET_RPM_L; //	Определяем адрес регистра для записи данных.
	}
	else //
		if (typeSpeed == MOT_M_S)
		{									  //
												//	Если скорость задана в м/сек:																				//
			valSpeed *= 60000.0f;			  //	Преобразуем скорость из  м/сек в мм/мин.
			valSpeed /= (2.0f * PI * radius); //	Преобразуем скорость из мм/мин в об/мин.
			if (valSpeed > 32767.0f)
			{
				valSpeed = 32767.0f;
			} //	Количество оборотов не может быть выше значения +32'767.
			if (valSpeed < -32767.0f)
			{
				valSpeed = -32767.0f;
			}						 //	Количество оборотов не может быть ниже значения -32'767.
			reg = REG_MOT_SET_RPM_L; //	Определяем адрес регистра для записи данных.
		}
		else //
			if (typeSpeed == MOT_PWM)
			{						 //
										//	Если скорость задана коэффициентом заполнения ШИМ:															//
				valSpeed *= 4095.0f; //	Преобразуем скорость из % к абсолютному значению ШИМ
				valSpeed /= 100.0f;	 //
				if (valSpeed > 4095.0f)
				{
					valSpeed = 4095.0f;
				} //	Коэффициент заполнения ШИМ не может быть выше значения +4095.
				if (valSpeed < -4095.0f)
				{
					valSpeed = -4095.0f;
				}						 //	Коэффициент заполнения ШИМ не может быть ниже значения -4095.
				reg = REG_MOT_SET_PWM_L; //	Определяем адрес регистра для записи данных.
			}
			else			  //
			{				  //	Если тип скорости задан некорректно:																		//
				return false; //
			} //
	//	Готовим данные для передачи:																					//
	data[0] = (uint8_t)((int16_t)(valSpeed) & 0x00FF);		  //	Младший байт для записи в модуль.
	data[1] = (uint8_t)(((int16_t)(valSpeed) >> 8) & 0x00FF); //	Старший байт для записи в модуль.
																//	Отправляем подготовленные данные в модуль:																		//
	if (_writeBytes(reg, 2, 0) == false)
	{
		return false;
	}			 //	Записываем 2 байта из массива «data» в модуль, начиная с регистра «reg».
					//	Возвращаем результат:																							//
	return true; //
}

//		Получение реальной скорости или коэффициента заполнения ШИМ:															//	Возвращаемое значение:	реальная скорость от 0 до ±32'767 об/мин., или установленный
float getSpeed(uint8_t type, uint8_t device)
{						   //	Параметр:				type - тип возвращаемого значения: MOT_RPM / MOT_PWM / MOT_M_S
	float valSpeed = 0.0f; //
	uint8_t reg; //
					//	Читаем реальную скорость из модуля:																				//
	switch (type)
	{ //
	case MOT_RPM:
		reg = REG_MOT_GET_RPM_L;
		break; //	Если запрошена реальная скорость в об/мин.
	case MOT_M_S:
		reg = REG_MOT_GET_RPM_L;
		break; //	Если запрошена реальная скорость в  м/сек.
	case MOT_PWM:
		reg = REG_MOT_SET_PWM_L;
		break; //	Если запрошен установленный коэффициент заполнения ШИМ.
	default:
		return 0; //
	} //
	if (_readBytes(reg, 2) == false)
	{
		return 0;
	}															  //	Читаем 2 байта начиная с регистра «reg» в массив «data».
	valSpeed = (float)((int16_t)data[1] << 8 | (int16_t)data[0]); //	Получаем прочитанные данные в переменную «valSpeed».
																	//	Преобразуем реальную скорость из об/мин в м/сек:																//
	if (type == MOT_M_S)
	{									  //	Если запрошена реальная скорость в  м/сек.
		valSpeed *= (2.0f * PI * radius); //	Преобразуем скорость из об/мин в мм/мин.
		valSpeed /= 60000.0f;			  //	Преобразуем скорость из мм/мин в  м/сек.
	} //
	//	Преобразуем реальную скорость из абсолютного ШИМ в %:															//
	if (type == MOT_PWM)
	{						 //	Если запрошена реальная скорость в  ШИМ.
		valSpeed *= 100.0f;	 //	Преобразуем скорость из абсолютного значения ШИМ в %.
		valSpeed /= 4095.0f; //
	} //

	return valSpeed; //	Возвращаем запрошенную скорость или коэффициент заполнения ШИМ.
} //
  //
//		Остановка мотора с условием:																							//	Возвращаемое значение:	результат установки остановки true/false.
bool setStop(float value, uint8_t type, uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Выполняем действия в соответствии с типом условия остановки:													//
	switch (type)
	{		   //
				//	Если условием остановки является немедленная остановка:														//
	case 0xFF: //
				//	Читаем состояние флага «MOT_FLG_NEUTRAL» из регистра флагов «REG_MOT_FLG»:								//
		if (_readBytes(REG_MOT_FLG, 1) == false)
		{
			return false;
		}																			  //	Читаем 1 байт регистра «REG_MOT_FLG» в массив «data».
																						//	Записываем данные в регистр остановки «REG_MOT_STOP»:													//
		data[0] = MOT_BIT_STOP | ((data[0] & MOT_FLG_NEUTRAL) ? MOT_BIT_NEUTRAL : 0); //	Устанавливаем бит «MOT_BIT_STOP», не меняя бит «MOT_BIT_NEUTRAL».
		if (_writeBytes(REG_MOT_STOP, 1, 0) == false)
		{
			return false;
		}							   //	Записываем 1 байт в регистр «REG_MOT_STOP» из массива «data».
		break;						   //
										//	Если условием остановки является пройденное расстояние:														//
	case MOT_MET:					   //
										//	Преобразуем расстояние до остановки (мм) в количество оборотов до остановки (об/мин):					//
		value *= 1000.0f;			   //	Преобразуем расстояние из м в мм.
		value /= (2.0f * PI * radius); //	Преобразуем расстояние в количество оборотов ( количество оборотов (об/мин) = расстояние (мм) / длина окружности (мм) ).
										//	Если условием остановки является количество совершённых оборотов:											//
	case MOT_REV:					   //
										//	Проверяем полученные данные:																			//
		if (value > 167772.15)
		{
			value = 167772.15;
		}											  //	Количество оборотов до остановки не может превышать значение 167'772.15.
														//	Готовим данные для передачи:																			//
		value *= 100;								  //	Преобразуем обороты в сотые доли оборотов.
		data[0] = (uint32_t)value & 0x0000FF;		  //	Байт для записи в регистр «REG_MOT_STOP_REV_L».
		data[1] = ((uint32_t)value >> 8) & 0x0000FF;  //	Байт для записи в регистр «REG_MOT_STOP_REV_C».
		data[2] = ((uint32_t)value >> 16) & 0x0000FF; //	Байт для записи в регистр «REG_MOT_STOP_REV_H».
														//	Отправляем подготовленные данные в модуль:																//
		if (_writeBytes(REG_MOT_STOP_REV_L, 3, 0) == false)
		{
			return false;
		}		  //	Записываем 3 байта из массива «data» в модуль, начиная с регистра «REG_MOT_SET_PWM_L».
		break;	  //
					//	Если условием остановки является пройденное время:															//
	case MOT_SEC: //
					//	Проверяем полученные данные:																			//
		if (value > 16777.215f)
		{
			value = 16777.215f;
		}											  //	Время до остановки не может превышать значение 16'777.215 сек.
														//	Готовим данные для передачи:																			//
		value *= 1000;								  //	Преобразуем время из сек в см.
		data[0] = (uint32_t)value & 0x0000FF;		  //	Байт для записи в регистр «REG_MOT_STOP_TMR_L».
		data[1] = ((uint32_t)value >> 8) & 0x0000FF;  //	Байт для записи в регистр «REG_MOT_STOP_TMR_C».
		data[2] = ((uint32_t)value >> 16) & 0x0000FF; //	Байт для записи в регистр «REG_MOT_STOP_TMR_H».
														//	Отправляем подготовленные данные в модуль:																//
		if (_writeBytes(REG_MOT_STOP_TMR_L, 3, 0) == false)
		{
			return false;
		}	   //	Записываем 3 байта из массива «data» в модуль, начиная с регистра «REG_MOT_SET_PWM_L».
		break; //
				//	Если условие остановки является некорректным:																//
	default:
		return false;
		break; //
	}

	//	Возвращаем результат:																							//
	return true; //
} //
  //
//		Получение значения условия оставшегося до остановки:																	//	Возвращаемое значение:	значение условия оставшегося до остановки, тип условия зависит от параметра.
float getStop(uint8_t type, uint8_t device)
{
	i2c_device ddev = getDev(device);

	float result = 0.0f, tmr, rev; //	Определяем переменную для хранения результата и переменные для получения данных из модуля.

	//	Читаем количество полных оборотов и время оставшееся до остановки:												//
	if (_readBytes(REG_MOT_STOP_REV_L, 6) == false)
	{
		return 0;
	}																						   //	Читаем 6 байт начиная с регистра «REG_MOT_STOP_REV_L» в массив «data».
	rev = (float)((int32_t)data[2] << 16 | (int32_t)data[1] << 8 | (int32_t)data[0]) / 100.0f; //	Сохраняем количество оставшихся оборотов в переменную «rev».
	tmr = (float)((int32_t)data[5] << 16 | (int32_t)data[4] << 8 | (int32_t)data[3]);		   //	Сохраняем количество оставшегося времени в переменную «tmr».
																								//	Читаем количество магнитов на роторе мотора:																	//
	if (_readBytes(REG_MOT_MAGNET, 1) == false)
	{
		return 0;
	} //	Читаем 1 байт из регистра «REG_MOT_MAGNET» в массив «data».
	if (data[0] == 0)
	{
		if (type != MOT_SEC || !tmr)
		{
			return 0;
		}
	} //	Если на роторе нет магнитов, то если запрошено не время до остановки или остановка задана не временем, то возвращаем 0.
		//	Возвращаем значение соответствующее указанному типу:															//
	switch (type)
	{			  //
					//	Если запрошено расстояние оставшееся до остановки:															//
	case MOT_MET: //	Расстояние будет определено из радиуса и количества оставшихся оборотов.
					//	Если запрошено количество полных оборотов оставшихся до остановки:											//
	case MOT_REV: //
					//	Если условие остановки задано количеством оборотов:														//
		if (rev)
		{
			result = rev;
		} //	Сохраняем количество оставшихся оборотов как результат «result».
			//	Если условие остановки задано временем:																	//
		else if (tmr)
		{	//
			//	Читаем текущую скорость:																			//
			if (_readBytes(REG_MOT_GET_RPM_L, 2) == false)
			{
				return 0;
			} //	Читаем 2 байта начиная с регистра «REG_MOT_GET_RPM_L» в массив «data».
			result = (float)abs((int16_t)data[1] << 8 | (int16_t)data[0]);
			if (result == 0)
			{
				result = 1.0f;
			}								  //	Сохраняем прочитанное значение в переменную «result» без знака.
												//	Вычисляем количество полных оборотов оставшихся до остановки:										//
			result = result * tmr / 60000.0f; //	Количество оборотов = скорость * время.
		} //
		//	Определяем расстояние по оставшемуся количеству оборотов:												//
		if (type == MOT_MET)
		{									//
			result *= (2.0f * PI * radius); //	Расстояние (мм) = Количество оборотов (об/мин) * длина окружности (мм).
			result /= 1000;					//	Преобразуем расстояние из мм в м.
		} //
		break;	  //
					//	Если запрошено время оставшееся до остановки:																//
	case MOT_SEC: //
					//	Если условие остановки задано временем:																	//
		if (tmr)
		{
			result = tmr / 1000;
		} //	Сохраняем оставшееся время как результат «result». Преобразовав время из мс в сек.
			//	Если условие остановки задано количеством оборотов:														//
		else if (rev)
		{	//
			//	Читаем текущую скорость:																			//
			if (_readBytes(REG_MOT_GET_RPM_L, 2) == false)
			{
				return 0;
			} //	Читаем 2 байта начиная с регистра «REG_MOT_GET_RPM_L» в массив «data».
			result = (float)abs((int16_t)data[1] << 8 | (int16_t)data[0]);
			if (result == 0)
			{
				result = 1.0f;
			}							   //	Сохраняем прочитанное значение в переменную «result» без знака.
											//	Вычисляем время оставшееся до остановки:															//
			result = rev * 60.0f / result; //	Время = количество оборотов / скорость. Так как скорость указана в об/мин, то преобразуем время в секунды, умножив результат на 60.
		}
		break;
	}
	//	Возвращаем результат:
	return result;
}

//		Установка нейтрального положения при остановке:																			//	Возвращаемое значение:	результат установки true/false.
bool setStopNeutral(bool f, uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Читаем состояние флага «MOT_FLG_STOP» из регистра флагов «REG_MOT_FLG»:											//
	if (_readBytes(REG_MOT_FLG, 1) == false)
	{
		return false;
	}																					 //	Читаем 1 байт регистра «REG_MOT_FLG» в массив «data».
																							//	Записываем данные в регистр остановки «REG_MOT_STOP»:															//
	data[0] = (f ? MOT_BIT_NEUTRAL : 0) | ((data[0] & MOT_FLG_STOP) ? MOT_BIT_STOP : 0); //	Устанавливаем бит «MOT_BIT_NEUTRAL», не меняя бит «MOT_BIT_STOP».
	if (_writeBytes(REG_MOT_STOP, 1, 0) == false)
	{
		return false;
	}			 //	Записываем 1 байт из массива «data» в регистр «REG_MOT_STOP».
	delay(10);	 //	Ждём 10 мс.
					//	Возвращаем результат:																							//
	return true; //
}
//		Получение флага установки нейтрального положения при остановке:															//	Возвращаемое значение:	флаг установки нейтрального положения при остановке true/false.
bool getStopNeutral(uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Считываем состояние регистра флагов:																			//
	if (_readBytes(REG_MOT_FLG, 1) == false)
	{
		return 0;
	} //	Читаем 1 байт регистра «REG_MOT_FLG» в массив «data».
		//	Возвращаем результат:																							//
	if (data[0] & MOT_FLG_NEUTRAL)
	{
		return true;
	} //	Если в прочитанном байте установлен флаг «MOT_FLG_NEUTRAL», то возвращаем true.

	return false; //
} //
  //
//		Установка направления вращения вала:																					//	Возвращаемое значение:	результат установки true/false.
bool setDirection(bool flgCKW, uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Готовим данные:																									//
	if (_readBytes(REG_BITS_2, 1) == false)
	{
		return 0;
	}																		   //	Читаем 1 байт регистра «REG_BITS_2» в массив «data».
	data[0] = (flgCKW ? MOT_BIT_DIR_CKW : 0) | (data[0] & (~MOT_BIT_DIR_CKW)); //	Редактируем бит «MOT_BIT_DIR_CKW» оставив остальные биты без изменений.
																				//	Отправляем подготовленные данные в модуль:																		//
	if (_writeBytes(REG_BITS_2, 1, 0) == false)
	{
		return false;
	}			 //	Записываем 1 байт из массива «data» в регистр «REG_BITS_2».
					//	Возвращаем результат:																							//
	return true; //
} //
  //
//		Получение направления вращения вала:																					//	Возвращаемое значение:	флаг вращения вала по ч.с. при положительной скорости true/false.
bool getDirection(uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Считываем значение регистра битов:																				//
	if (_readBytes(REG_BITS_2, 1) == false)
	{
		return 0;
	}										  //	Читаем 1 байт регистра «REG_BITS_2» в массив «data».
												//	Возвращаем результат:																							//
	return (bool)(data[0] & MOT_BIT_DIR_CKW); //	Возвращаем состояние бита «MOT_BIT_DIR_CKW».
}

//		Установка флагов инверсии механизма:																					//	Возвращаемое значение:	результат установки true/false.
bool setInvGear(bool invRDR, bool invPIN, uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Готовим данные:																									//
	if (_readBytes(REG_BITS_2, 1) == false)
	{
		return 0;
	}																																//	Читаем 1 байт регистра «REG_BITS_2» в массив «data».
	data[0] = (invRDR ? MOT_BIT_INV_RDR : 0) | (invPIN ? MOT_BIT_INV_PIN : 0) | (data[0] & (~(MOT_BIT_INV_RDR | MOT_BIT_INV_PIN))); //	Редактируем биты «MOT_BIT_INV_RDR» и «MOT_BIT_INV_PIN» оставив остальные биты без изменений.
																																	//	Отправляем подготовленные данные в модуль:																		//
	if (_writeBytes(REG_BITS_2, 1, 0) == false)
	{
		return false;
	}			 //	Записываем 1 байт из массива «data» в регистр «REG_BITS_2».
					//	Возвращаем результат:																							//
	return true;
}

//		Получение флагов инверсии механизма:																					//	Возвращаемое значение:	байт с флагом инверсии вращения редуктора (1 бит байта) и флагом инверсии полярности мотора (0 бит байта).
uint8_t getInvGear(uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Считываем значение регистра битов:																				//
	if (_readBytes(REG_BITS_2, 1) == false)
	{
		return 0;
	}																								//	Читаем 1 байт регистра «REG_BITS_2» в массив «data».
																									//	Возвращаем результат:																							//
	return ((data[0] & MOT_BIT_INV_RDR) ? 1 : 0) | ((data[0] & MOT_BIT_INV_PIN) ? 0 : 0); //	Возвращаем байт содержащий состояние битов «MOT_BIT_INV_RDR» (1 бит байта) и «MOT_BIT_INV_PIN» (0 бит байта).
}

//		Получение пройденного пути или количества совершённых полных оборотов:													//	Возвращаемое значение:	значение пройденного пути или количества совершённых полных оборотов, тип значения зависит от параметра.
float getSum(uint8_t type, uint8_t device)
{
	i2c_device ddev = getDev(device);

	float result = 0.0f; //	Определяем переменную для хранения результата.

	//	Проверяем запрошенный тип:																						//
	if (type == MOT_MET || type == MOT_REV)
	{	//	Если запрошенный тип указан верно, то ...
		//	Читаем количество совершённых оборотов:																		//
		if (_readBytes(REG_MOT_GET_REV_L, 3) == false)
		{
			return 0;
		}																						   //	Читаем 3 байта начиная с регистра «REG_MOT_GET_REV_L» в массив «data».
		result = (float)((int32_t)data[2] << 16 | (int32_t)data[1] << 8 | (int32_t)data[0]) / 100; //	Получаем количество совершённых полных оборотов.
																								//	Определяем расстояние по количеству оборотов:																//
		if (type == MOT_MET)
		{									//
			result *= (2.0f * PI * radius); //	Расстояние (мм) = Количество оборотов (об/мин) * длина окружности (мм).
			result /= 1000;					//	Преобразуем расстояние из мм в м.
		}
	}
																								//
	return result; //
} //

bool setVoltage(float motVoltage, uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Готовим данные:																									//
	if (motVoltage > 25.5)
	{
		motVoltage = 25.5;
	} //
	if (motVoltage < 0)
	{
		motVoltage = 0.0;
	}									  //
	data[0] = (uint8_t)(motVoltage * 10); //	Преобразуем значение в целое количество десятых долей Вольт.
											//	Отправляем подготовленные данные в модуль:																		//
	if (_writeBytes(REG_MOT_VOLTAGE, 1, 0) == false)
	{
		return false;
	}			 //	Записываем 1 байт из массива «data» в регистр «REG_MOT_VOLTAGE».
					//	Возвращаем результат:																							//
	return true;
}

float getVoltage(uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Читаем напряжение из модуля:																					//
	if (_readBytes(REG_MOT_VOLTAGE, 1) == false)
	{
		return 0;
	}							   //	Читаем 1 байт регистра «REG_MOT_VOLTAGE» в массив «data».
									//	Возвращаем результат:																							//
	return (float)data[0] / 10.0f; //	Возвращаем напряжение получив его из целого количества десятых долей Вольт.
}

bool setNominalRPM(uint16_t value, uint8_t device)
{
	i2c_device ddev = getDev(device);
												//	Готовим данные:																									//
	data[0] = (uint8_t)(value & 0x00FF);		//	Байт для записи в регистр «REG_MOT_NOMINAL_RPM_L».
	data[1] = (uint8_t)((value >> 8) & 0x00FF); //	Байт для записи в регистр «REG_MOT_NOMINAL_RPM_H».
												//	Отправляем подготовленные данные в модуль:																		//
	if (_writeBytes(REG_MOT_NOMINAL_RPM_L, 2, 0) == false)
	{
		return false;
	}			 //	Записываем 2 байта из массива «data» в модуль начиная с регистра «REG_MOT_NOMINAL_RPM_L».
					//	Возвращаем результат:																							//
	return true;
}

uint16_t getNominalRPM(uint8_t device)
{
	i2c_device ddev = getDev(device);

	//	Читаем номинальную скорость вращения из модуля:																	//
	if (_readBytes(REG_MOT_NOMINAL_RPM_L, 2) == false)
	{
		return 0;
	}												 //	Читаем 2 байта начиная с регистра «REG_MOT_NOMINAL_RPM_L» в массив «data».
														//	Возвращаем результат:																							//
	return (int16_t)data[1] << 8 | (int16_t)data[0]; //	Возвращаем скорость вращения вала редуктора в об/мин.
}

bool saveManufacturer(uint64_t code, uint8_t device)
{
	i2c_device ddev = getDev(device);

	while ((time_ms() >= timReset) && (time_ms() < (timReset + 150)))
	{
		delay(2)
	}								 //	Заперщаем сохранять данные в FLASH в течении 150 мс после перезагрузки (в т.ч. инициализации) модуля.
										//	Готовим данные для передачи:																					//
	data[0] = (code) & 0xFFLL;		 //	Байт для записи в регистр «REG_MANUFACTURER».
	data[1] = (code >> 8) & 0xFFLL;	 //	Байт для записи в регистр «REG_MANUFACTURER».
	data[2] = (code >> 16) & 0xFFLL; //	Байт для записи в регистр «REG_MANUFACTURER».
	data[3] = (code >> 24) & 0xFFLL; //	Байт для записи в регистр «REG_MANUFACTURER».
	data[4] = (code >> 32) & 0xFFLL; //	Байт для записи в регистр «REG_MANUFACTURER».
										//	Отправляем подготовленные данные в модуль:																		//
	if (_writeBytes(11, 5, 0) == false)
	{
		return false;
	}			 //	Записываем 5 байт в регистр «REG_MANUFACTURER».
	delay(50);	 //	Даём время для сохранения данных в энергонезависимую память модуля.
					//	Возвращаем результат:																							//
	return true; //
}

bool _readBytes(uint8_t reg, uint8_t sum, i2c_device* dev)
{
	ssize_t result = 0; //	Определяем флаг       для хранения результата чтения.
	uint8_t sumtry = 10; //	Определяем переменную для подсчёта количества оставшихся попыток чтения.
	do
	{
		result = i2c_ioctl_read(dev, reg, data, sum);
		sumtry--;
		if (result <= 0)
		{
			delay(2);
		} //	Уменьшаем количество попыток чтения и устанавливаем задержку при неудаче.
	} while (result <= 0 && sumtry > 0); //	Повторяем чтение если оно завершилось неудачей, но не более sumtry попыток.
	delay(2); //	Между пакетами необходимо выдерживать паузу.
	return result > 0;			//	Возвращаем результат чтения (true/false).
}

bool _writeBytes(uint8_t reg, uint8_t sum, uint8_t num, i2c_device* dev)
{						 //	Параметры:				reg - номер первого регистра, sum - количество записываемых байт, num - номер первого элемента массива data.
	size_t result = false; //	Определяем флаг       для хранения результата записи.
	uint8_t sumtry = 10; //	Определяем переменную для подсчёта количества оставшихся попыток записи.
	do
	{
		result = i2c_ioctl_write(dev, reg, data[num], sum);
		sumtry--;
		if (!result)
		{
			delay(1);
		} //	Уменьшаем количество попыток записи и устанавливаем задержку при неудаче.
	} while (result <= 0 && sumtry > 0); //	Повторяем запись если она завершилась неудачей, но не более sumtry попыток.
	delay(10);	   //	Ждём применения модулем записанных данных.
	return result > 0; //	Возвращаем результат записи (true/false).
}
