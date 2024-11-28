from interfaces.srv import SensorInterface, ReceiveSensorInterface

import rclpy
from rclpy.node import Node

class Service(Node):
    
    def __init__(self):
        super().__init__('sensor_service')
        self.send_srv = self.create_service(SensorInterface, 'send_service', self.sensor_data_callback)
        self.receive_srv = self.create_service(ReceiveSensorInterface, 'receive_service', self.receive_data_callback)
    
        self.videoData = ""
        self.global_x = 0.0
        self.global_y = 0.0
        self.global_z = 0.0

    def receive_data_callback(self, request, response):
        if request.video_data:
            self.videoData 

        if request.global_x:
            self.global_x = request.global_x
        
        if request.global_y:
            self.global_y = request.global_y
            
        if request.global_z:
            self.global_z = request.global_z

        response.success = True
        response.message = ""

        return response

    def sensor_data_callback(self, request, response):
        send_video = request.send_video_data

        if send_video:
            response.video_data = self.videoData
        else:
            response.video_data = ""

        response.global_x = self.global_x
        response.global_y = self.global_y
        response.global_z = self.global_z

        response.success = True
        response.message = ""

        return response

def main():
    print("Initializing...")
    rclpy.init()

    service = Service()

    print("Running")
    rclpy.spin(service)
    rclpy.shutdown()

if __name__ == "__main__":
    main()