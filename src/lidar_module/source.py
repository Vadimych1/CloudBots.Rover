from rplidar import RPLidar, RPLidarException
import logging
import time
from typing import Generator

class Lidar:
    """
    Class for lidar scanning

    :param port: the USB port of lidar. Default: "/dev/ttyUSB0"
    :param fallback_ports: ports to check if lidar os not on the default port
    """
    def __init__(self, port: str = "/dev/ttyUSB0", fallback_ports=["/dev/tty0"]):
        self.logger = logging.getLogger(f"Lidar[{port}]")
        try:
            self.lidar = RPLidar(port)
        except:
            for i, fallback in enumerate(fallback_ports):
                try:
                    self.lidar = RPLidar(fallback, 115200, 3)
                    break
                except:
                    if i == len(fallback_ports) - 1:
                        self.logger.error("Cannot connect to lidar, all fallbacks failed. Check if lidar connected or correct address.")
                        quit(1)
                        
        self.running = False


    def health(self):
        """
        Returns lidar health
        """
        return self.lidar.get_health()


    def info(self):
        """
        Returns lidar info
        """
        return self.lidar.get_info()
    

    def samplerate(self):
        """
        Returns lidar samplerate
        """
        return self.lidar.get_samplerate()
    

    def scan_modes(self):
        """
        Returns all lidar scan modes
        """
        return self.lidar.get_scan_modes()
    

    def scan(self, buffer: int = 10000) -> Generator[tuple[int, int], None, None]:
        """
        Start scan
        Yields every scan value
        """

        self.running = True
        
        while self.running:
            self.logger.info("Scan started")
            c = 0
            
            try:
                for data in self.lidar.iter_measures(max_buf_meas=buffer):
                    _, _, angle, distance = data
                    if distance <= 0:
                        continue

                    yield angle, distance

                    c += 1
                    
                    if c % 300 == 0:   
                        self.lidar.clean_input()
                    elif c % 15001 == 0:
                        raise RPLidarException()
                    
                    
            except RPLidarException as e:
                self.lidar.stop()
                self.lidar.disconnect()
                self.lidar.connect()
            
            except Exception as e:
                self.logger.exception(e)

       
    def stop(self):
        """
        Stop lidar
        """     
        self.running = False
        self.logger.info("Scan stopped")
        self.lidar.stop_motor()
        self.lidar.stop()


if __name__ == "__main__":
    l = Lidar()
    l.stop()

    while True:
        time.sleep(1)