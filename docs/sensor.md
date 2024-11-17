# src/sensor.py

## Классы сенсоров.
- Базовые сенсоры
1. BaseSensor(name: str, path: str, delay: float, callback=None, call_every: int = None) - базовый класс сенсора. Получает значение по заданной функции `get_data`, которую нужно определить в дочернем классе.
2. FilteringSensor(name: str, path: str, filter: BaseFilter, delay: float, callback=None, call_every: int = None) - сенсор с фильтром. Фильтр задается через аргумент `filter` в конструкторе.
### ВАЖНО: ИСПОЛЬЗОВАТЬ BaseSensor и FilteringSensor в сыром виде НЕЛЬЗЯ - нужно создать дочерний класс и реализовать метод `get_data`.

- Serial-сенсоры
1. SerialSensor(name: str, path: str, delay: float, callback=None, call_every: int = None, baudrate: int = 9600) - сенсор, берущий данные из serial на порту 'path'.
2. FilteringSerialSensor(name: str, path: str, filter: BaseFilter, delay: float, callback=None, call_every: int = None, baudrate: int = 9600) - Serial-сенсор с фильтром.
### ВАЖНО: ИСПОЛЬЗОВАТЬ SerialSensor и FilteringSerialSensor в сыром виде НЕЛЬЗЯ - нужно создать дочерний класс и реализовать метод `parse_serial`.