from interfaces.srv import SensorInterface

import rclpy
from rclpy.node import Node

class AsyncReceiver(Node):
    def __init__(self):
        super().__init__('sensor_data_receiver')

        self.cli = self.create_client(SensorInterface, 'sensor_data_receiver')
        
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for service to connect.")

        self.req = SensorInterface.Request()

    def get_sensors_data(self, videoData: bool):
        self.req.sendVideoData = videoData
        return self.cli.call_async(self.req)
    
def main():
    rclpy.init()

    recv = AsyncReceiver()
    future = recv.get_sensors_data(False)
    rclpy.spin_until_future_complete(recv, future)

    response = future.result()

    recv.get_logger().info(f"Got message! {response.message_out}")

    recv.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
