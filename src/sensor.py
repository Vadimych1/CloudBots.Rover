import threading as t
import time, logging
import serial

try:
    from src.filters import BaseFilter
except:
    from filters import BaseFilter

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s:%(levelname)s > %(message)s')
lg = logging.getLogger('sensor')
_file = logging.StreamHandler()
_file.setFormatter(logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s > %(message)s'))
_file.setStream(open('logs/sensor.log', 'w'))
lg.addHandler(_file)

import configparser
CFG = configparser.ConfigParser()
CFG.read('config.ini')

DEFAULT_BAUDRATE = int(CFG.get('sensor', 'DEFAULT_BAUDRATE'))

class BaseSensor:
    """
    Base sensor. Gets value.
    """
    def __init__(self, name: str, path: str, delay: float, callback=None, call_every: int = None):
        self.name = name
        self.path = path

        self._event = t.Event()
        self._event.clear()

        self.value = None
        self.counter = 0
        self.callback = callback
        self.call_every = call_every

        self.delay = delay

        lg.info(f"Initialized new sensor ({name}[{path}])")

    def listen(self):
        """
        Starts listening.
        """
        lg.info(f"Sensor is listening ({self.name}[{self.path}])")
        thread = t.Thread(target=self._listener)
        # thread.daemon = True
        thread.start()

    def _listener(self):
        while not self._event.is_set():
            self.value = self.get_data()

            self.counter += 1
            if self.callback is not None and self.counter % self.call_every == 0:
                self.callback(self.value)
                self.counter = 0

            time.sleep(self.delay)

    def stop(self):
        """
        Stops listening.
        """
        lg.info(f"Sesnsor stopped listening ({self.name}[{self.path}])")
        self._event.set()

    def get_data(self):
        """
        Method, where all sensor data is read. Returns data from sensor<br>
        MUST be overriden.
        """
        return [0]
        # raise NotImplementedError
    
    def reset(self):
        """
        Resets the sensor value.
        """
        self.value = None

class FilteringSensor(BaseSensor):
    """
    Sensor that automatically filters all incoming data.
    """
    def __init__(self,name: str, path: str, filter: BaseFilter, delay: float, callback=None, call_every: int = None):
        self.filter = filter
        print(name, path, delay, filter, callback, call_every)
        super().__init__(name, path, delay, callback, call_every)

    def _listener(self):
        while not self._event.is_set():
            self.value = self.filter.filter(self.get_data())

            self.counter += 1
            if self.callback is not None and self.counter % self.call_every == 0:
                self.callback(self.value)
                self.counter = 0

            time.sleep(self.delay)

class SerialSensor(BaseSensor):
    def __init__(self, name: str, path: str, delay: float, callback=None, call_every: int = None, baudrate: int = DEFAULT_BAUDRATE):
        self.ser = serial.Serial(path, baudrate)
        self.baudrate = baudrate
        super().__init__(name, path, delay, callback, call_every)
    
    def _listener(self):
        while not self._event.is_set():
            self.value = self.parse_serial(self.ser.readline())

            self.counter += 1
            if self.callback is not None and self.counter % self.call_every == 0:
                self.callback(self.value)
                self.counter = 0

            time.sleep(self.delay)

    def get_data(self):
        raise DeprecationWarning

    def parse_serial(self, string):
        raise NotImplementedError

class FilteringSerialSensor(SerialSensor):
    def __init__(self, name: str, path: str, delay: float, filter: BaseFilter, callback=None, call_every: int = None, baudrate: int = DEFAULT_BAUDRATE):
        self.filter = filter
        super().__init__(name, path, delay, callback, call_every, baudrate)

    def _listener(self):
        while not self._event.is_set():
            self.value = self.filter.filter(self.parse_serial(self.ser.readline()))

            self.counter += 1
            if self.callback is not None and self.counter % self.call_every == 0:
                self.callback(self.value)
                self.counter = 0

            time.sleep(self.delay)