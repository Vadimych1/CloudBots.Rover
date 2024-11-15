import src.filters as filters
import src.rosock as sock
import time, json, threading

filter = filters.KalmanFilter(6)

data = {"action": "SendData", "data": [0, 0, 0, 0, 0, 0]}
def setData(newData: list[float]):
    global data, filter
    data["data"] = filter.filter(newData)

ip = "localhost:8418"
ws = sock.RoSock(f"wss://{ip}")

def opened(ws, *args):
    t = threading.Thread(target=mainloop)
    t.start()

ws.add_callback("Opened", opened)

def mainloop():
    while True:
        ws.send(json.dumps(data))
        time.sleep(0.2)

ws.connect()