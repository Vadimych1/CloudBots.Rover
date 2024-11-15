# src/rosock.py

## Класс WebSocket-клиента для роботов.
RoSock - класс вебсокет-клиента.<br>
### Аргументы:
- url - адрес вебсокета.
### Методы:
- connect() - подключение к вебсокету.
- add_callback(<span style="color: lightgreen">method</span>: <span style="color: orange">str</span>, <span style="color: lightgreen">callback</span>: <span style="color: orange">callable[WebSocketApp, str]</span>) - добавить обработчик событий/метода. Описано <a href="#обработчики">ниже</a>.
- send(<span style="color: lightgreen">data</span>: <span style="color: orange">str</span>) - отправить данные (скорее всего, вы хотите отправлять данные в формате `JSON` в виде `{"action": "ТипЗапроса", "data": ...}`).
## Обработчики
Когда на клиент приходит сообщение, тип сообщения (message["action"]) ищется в зарегистрированных обработчиках. Заранее предопределённые (зарезервированные) названия обработчиков:
- Opened - вызывается, когда открывается соединение.