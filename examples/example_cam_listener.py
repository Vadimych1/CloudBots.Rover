import cv2, time
from cam.datatypes import Image
from cam.source import BaseCamListener

class ExampleCamListener(BaseCamListener):
    def handle_example_cam(self, data: dict, additional_data: bytes) -> None:
        # load data in packet
        data: Image = Image().from_json(data, additional_data)
        cv2.imshow("image", data.get_image_array())

listener = ExampleCamListener(node_name="example_cam_listener")

while True:
    time.sleep(1)