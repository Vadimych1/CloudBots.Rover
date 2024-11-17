# src/tasks.py

## Система задач по времени.
TaskManager - класс системы задач.
- tick() - вызывается каждый раз, когда проходит один тик.
- add_task(callback: callable, ticks: int) - добавляет задачу в систему.