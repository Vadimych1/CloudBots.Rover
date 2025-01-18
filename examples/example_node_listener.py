# import libs
from miniros.source import Node
import time
from miniros.builtin_datatypes import XYZ

class ListenerNode(Node):
    # function with name "handle_TOPIC_NAME", handle_example_topic in our case (see example_node_publisher.py)
    def handle_example_topic(self, data: dict, addtitional_data: bytes):
        # load data in packet
        data = XYZ().from_json(data, additional_data=addtitional_data)

        # print packet
        print(data.get("x"), data.get("y"), data.get("z"), data.get_additional_data("test"))

# create node and run it
node = ListenerNode(4532, "listening_node")
node.run()

# subscribe to topic
node.subscribe("example_topic")

# run mainloop
while True:
    time.sleep(1)