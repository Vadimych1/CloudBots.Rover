import logging
import threading
import websockets.sync.server as websockets
import websockets.exceptions as wexc

class R_WebSocket:
    def __init__(self, on_message):
        self.logger = logging.getLogger("WebSocket")
        self.socket_server = websockets.serve(self.process, "0.0.0.0", 1026)
        self.on_message = on_message

    def process(self, conn: websockets.ServerConnection):
        try:
            while True:
                data = conn.recv()
                responce = self.on_message(data)
                if responce and len(responce) > 0:
                    conn.send(responce)

        except wexc.ConnectionClosed:
            pass
        
        except Exception as e:
            self.logger.exception(e)
                
    def run(self):
        self.logger.info("Started WebSocket server on :1026")
        self.t = threading.Thread(target=self.socket_server.serve_forever)        
        return self.t