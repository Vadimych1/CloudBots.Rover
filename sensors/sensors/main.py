from interfaces.srv import SensorInterface, ReceiveSensorInterface

import rclpy
from rclpy.node import Node

class Service(Node):
    
    
    def __init__(self):
        super().__init__('main_service')
        self.send_srv = self.create_service(SensorInterface, 'send_service', self.sensor_data_callback)
        self.receive_srv = self.create_service(ReceiveSensorInterface, 'receive_service', self.receive_data_callback)
    
    def receive_data_callback(self, request, response):
        

    def sensor_data_callback(self, request, response):
        send_video = request.sendVideoData

        if send_video:
            ...

        return response

def main():
    rclpy.init()

    service = Service()

    rclpy.spin(service)
    rclpy.shutdown()

if __name__ == "__main__":
    main()