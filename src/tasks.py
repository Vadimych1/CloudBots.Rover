import logging, time

LOG_TASKS_STATE = True

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s:%(levelname)s > %(message)s')
lg = logging.getLogger('tasks')
_file = logging.StreamHandler()
_file.setFormatter(logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s > %(message)s'))
_file.setStream(open('logs/tasks.log', 'w'))
lg.addHandler(_file)

class TaskManager:
    def __init__(self) -> None:
        self.last_task_id = 0
        self.tasks: list[ScheduledTask] = []
        lg.info("Initialized new task manager")

    def add_task(self, callback, ticks: int, ):
        """
        Add new task
        """
        self.tasks.append(ScheduledTask(ticks, callback, self.last_task_id))
        self.last_task_id += 1
        lg.info(f"Task {self.last_task_id} added (time: {ticks}t)") if LOG_TASKS_STATE else None
        return self.last_task_id
    
    def clear_task(self, id):
        """
        Removes task by its id
        """
        for task in self.tasks:
            if task.id == id:
                self.tasks.remove(task)

    def tick(self):
        """
        Update tasks
        """
        for task in self.tasks:
            task.tick()

    def clear(self):
        """
        Clear task list
        """
        self.tasks = []

class ScheduledTask:
    def __init__(self, ticks: int, callback, id: int) -> None:
        self.start_time = time.time()
        self.ticks = ticks
        self.callback = callback
        self.id = id

    def tick(self):
        self.ticks -= 1
        if self.ticks == 0:
            self.callback()
            lg.info(f"Task {self.id} completed in {((time.time() - self.start_time) * 10).__trunc__()/10}s") if LOG_TASKS_STATE else None