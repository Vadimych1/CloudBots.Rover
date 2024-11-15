# src/sensor.py

## Классы сенсоров.
1. BaseSensor(name: str, path: str, delay: float, callback=None, call_every: int = None) - базовый класс сенсора. Получает значение по заданной функции `get_data`, которую нужно определить в дочернем классе.
2. FilteringSensor(path: str, name: str, filter: BaseFilter, delay: float, callback=None, call_every: int = None) - сенсор с фильтром. Фильтр задается через аргумент `filter` в конструкторе.

# ВАЖНО: ИСПОЛЬЗОВАТЬ BaseSensor и FilteringSensor в сыром виде НЕЛЬЗЯ - нужно создать дочерний класс для нужного элемента, который будет работать с сенсором.