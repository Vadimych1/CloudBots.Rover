from miniros import source


class BaseCamListener(source.Node):
    """
    How to handle incoming data:

    ```
    def handle_topic_name(self, data: dict, additional_data: bytes):
        pack: Image = Image().from_json(data, additional_data)
        # your code here
    ```
    """
