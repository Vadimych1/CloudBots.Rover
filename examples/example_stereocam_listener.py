from miniros.source import Node
from miniros.builtin_datatypes import Image
import cv2
import time

class StereocamListener(Node):
    def __init__(self, port: int, node_name: str = "changeme") -> None:
        super().__init__(port, node_name)

    def handle_stereocam_depth(self, data: dict):
        pack: Image = Image().from_json(data)
        cv2.imshow("DEPTH", pack.get_image_array())

        if cv2.waitKey(1) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            self.stop()

    def handle_stereocam_ir(self, data: dict):
        pack: Image = Image().from_json(data)
        cv2.imshow("IR", pack.get_image_array())

        if cv2.waitKey(1) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            self.stop()

node = StereocamListener(4532, "stereocam_listener")
node.run()

node.subscribe("stereocam_depth")
# node.subscribe("stereocam_ir")

while True:
    time.sleep(1)