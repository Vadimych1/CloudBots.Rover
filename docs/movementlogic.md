# src/movementlogic.py

## Классы для управления моторами робота по виду колёс.
1. BaseMovementLogic - базовый абстрактный класс со всеми методами.
2. RollingMovementLogic - логика движения для роликовых колёс.

## Методы
- stop(speed: float) - остановка движения.
- left(speed: float) - движение влево.
- right(speed: float) - движение вправо.
- forward(speed: float) - движение вперёд.
- backward(speed: float) - движение назад.
- rotate_left(speed: float) - поворот влево.
- rotate_right(speed: float) - поворот вправо.