import websocket
import logging
import threading

class R_WebSocket:
    def __init__(self, on_message):
        self.logger = logging.getLogger("WebSocket")
        self.socket_server = websocket.WebSocketApp("0.0.0.0:81", 
                                                    on_open=lambda ws: self.logger.info("Opened server"),
                                                    on_close=lambda ws, a, b: self.logger.info("Closed server"),
                                                    on_message=on_message,
                                                )
        
    def run(self):
        self.logger.info("Started WebSocket server on :81")
        self.t = threading.Thread(target=self.socket_server.run_forever)        
        return self.t