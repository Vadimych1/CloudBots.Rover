# import libs
from miniros.source import Node
import time
from miniros.builtin_datatypes import XYZ

# create node and run it
node = Node(4532, "publishing_node")
node.run()

# create topic to publish in
node.create_topic(XYZ(), "example_topic")

# craete packet that will be published
pack = XYZ()

# mainloop that publishes packets every 5 seconds
i = 1
while True:
    time.sleep(5)

    pack.set("x", i)
    pack.set("y", 2 * i)
    pack.set("z", 3 * i)
    node.publish(pack, "example_topic")

    i += 1