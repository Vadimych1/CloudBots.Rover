import websocket, json, ssl
import logging, threading

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s:%(levelname)s > %(message)s')
lg = logging.getLogger('rosock')
_file = logging.StreamHandler()
_file.setFormatter(logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s > %(message)s'))
_file.setStream(open('logs/rosock.log', 'w'))
lg.addHandler(_file)

class RoSock:
    """
    WebSocket client for robots.
    """
    def __init__(self, url: str):
        self.url = url
        self.ws = None
        self.callbacks = {}

    def connect(self):
        lg.info(f"Connecting to {self.url}")
        if self.ws is not None:
            lg.info(f"Closing previous connection (on `{self.url}`)")
            self.close()

        self.ws = websocket.WebSocketApp(self.url)
        self.ws.on_open = self._on_open
        self.ws.on_message = self._message_handler
        self.ws.on_error = self._on_error
        self.ws.on_close = self._on_close

        tr = threading.Thread(target=self._conn)
        tr.start()

        return self
        
    def _conn(self, *args):
        self.ws.run_forever(sslopt={
            "cert_reqs": ssl.CERT_NONE
        })
    
    def add_callback(self, method, callback):
        if method in self.callbacks:
            self.callbacks[method].append(callback)
        else:
            self.callbacks[method] = [callback]

        return self

    def send(self, data):
        self.ws.send(data)
        return self
    
    def _message_handler(self, message, *arg):
        try:
            data = json.loads(message)

            if data['action'] in self.callbacks:
                for callback in self.callbacks[data['action']]:
                    callback(self.ws, data['data'])
            else:
                lg.warning(f"Called unknown method: {data['action']} (on `{self.url}`)")
                return
        except:
            lg.error(f'Failed to parse message: {message} (on `{self.url}`)')
            return
        
    def _on_error(self, error, *args):
        lg.error(f'Error occured: {error} (on `{self.url}`)')

    def _on_close(self, *args):
        lg.info(f'Connection to {self.url} closed')

    def _on_open(self, *args):
        lg.info(f'Connected to {self.url}')
        if "Opened" in self.callbacks:
            for cb in self.callbacks["Opened"]:
                cb(self.ws)
        return

    def close(self):
        self.ws.close()