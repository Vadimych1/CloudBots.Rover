# main.py

## Класс Robot
Это основной интерфейс управления роботом.
Аргументы инициализации:
- movement_logic: BaseMovementLogic - логика движения [movementlogic.md](../docs/movementlogic.md).

Методы:
- start_ticker() - запустить ticker-поток.
- stop_ticker() - остановить ticker-поток.
- pos_tick(delta_time: float) - интегрирует состояние робота.
- calc_real_pos() - вычисляет реальное положение робота с коэффициентами `UWB_POS_PRIORITY` и `INTEGRAL_POS_PRIORITY`.
- set_motors_speed(speeds: list[float]) - устанавливает скорости моторов по схеме [top_left, bottom_left, top_right, bottom_right].
- move_by(distance: float, speed: float = 0.5) - движение вперед/назад на расстояние `distance` со скоростью `speed`.
- rotate_by(angle: float, speed: float = 0.5) - поворот на угол `angle` со скоростью `speed`.
- move_side_by(distance: float, speed: float = 0.5) - движение вправо/влево на расстояние `distance` со скоростью `speed`.
- clear_tasks() - очищает список задач.
- clear_task(id: int) - очищает список задач.
- cancel_stop() - отменяет задачу остановки робота.