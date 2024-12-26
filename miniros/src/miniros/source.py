import socket
from typing import Callable, Any
import json
import logging
import threading
import time
import struct

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Packet:
    def __init__(self, fields: dict[str, type]) -> None:
        self.fields = fields

    def set(self, name: str, value: Any) -> None:
        if name not in self.fields:
            raise ValueError(f"Unknown field: {name}")

        self.__setattr__(name, self.fields[name](value))

        return self

    def get(self, name: str) -> Any:
        if name not in self.fields:
            raise ValueError(f"Unknown field: {name}")

        return self.__getattribute__(name)

    def __str__(self) -> str:
        d = {}

        for field in self.fields:
            try:
                if ("_stringify_" + field) in self.__class__.__dict__:
                    d[field] = self.__class__.__dict__["_stringify_" + field](
                        self, self.get(field)
                    )
                else:
                    d[field] = self.get(field)
            except:
                pass

        return json.dumps(d)

    def from_json(self, data: str | dict) -> "Packet":
        if type(data) is str:
            try:
                data = json.loads(data)
            except:
                return None
            
        for field in self.fields:
            try:
                if "_parse_" + field in self.__class__.__dict__:
                    self.set(
                        field,
                        self.__class__.__dict__["_parse_" + field](self, data[field]),
                    )
                else:
                    self.set(field, self.fields[field](data[field]))
            except:
                pass

        return self

    def merge(self, packet: "Packet") -> "Packet":
        fields = self.fields
        for k, v in packet.fields.items():
            if k not in fields:
                fields[k] = v
        return Packet(fields)

    def copy(self) -> "Packet":
        p = Packet(self.fields)

        for k, v in self.__dict__.items():
            p.__dict__[k] = v

        return p


class Node:
    """
    Base node class.
    Can be used as broadcast or/and listen node. Use methods `create_broadcaster` and `create_listener`
    """

    def __init__(self, port: int, node_name: str = "changeme") -> None:
        self.port = port
        self.name = node_name
        self.sock = None

        self.logger = logging.getLogger(node_name)

        self.sock = None

        self.topics: dict[str, Packet] = {}

    def run(self, max_retries: int = None) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        retries = 0
        while max_retries is None or retries < max_retries:
            try:
                self.sock.connect(("127.0.0.1", self.port))
                break
            except Exception as e:
                self.logger.info(
                    "Failed to connect to server... Retrying in 2 seconds..."
                )
                self.logger.debug(e)
                time.sleep(2)
                retries += 1

        if max_retries is not None and retries >= max_retries:
            self.logger.error("Failed to connect to server after max retries")
            quit(1)

        self.logger.info(f"Connected to server on port {self.port}")

        self._send(
            self.sock,
            json.dumps({"type": "auth", "name": self.name}).encode("utf-8"),
        )
        t = threading.Thread(target=self._listener, args=(self.sock,), daemon=True)
        t.start()
        return t
    
    def _listener(self, socket: socket.socket) -> None:
        while True:
            try:
                data = self._recv(socket).decode("utf-8")
                data = json.loads(data)
            except:
                continue

            self._process_message(data)

    def _search_for_handler(self, name: str):
        self.logger.debug(f"Searching for handler: {name}")
        for x in self.__class__.__mro__:
            self.logger.debug(f"Searching in {x}")

            if name in x.__dict__:
                return x.__dict__[name]
            elif name in x.__class__.__dict__:
                return x.__class__.__dict__[name]
        
        return None
    
    def _process_message(self, data: dict) -> None:
        try:
            if "type" in data:
                h = self._search_for_handler("_handle_" + data["type"])
                if h:
                    self.logger.debug(f"Got handler {h}")
                    h(self, data)
                else:
                    self.logger.debug("Got unknown message type")

            elif "status" in data:
                if data["status"] == "error":
                    self.logger.error(f"Error: {data['solve']}")
                else:
                    self.logger.debug(data["status"], data)

            else:
                self.logger.debug("Got unknown message format")
        except Exception as e:
            self.logger.debug(e)

    def _send(self, socket: socket.socket, data: bytes | str) -> None:
        if type(data) == str:
            data = data.encode("utf-8")

        data_len = len(data)
        data_len = struct.pack("i", data_len)
        socket.send(data_len)
        socket.send(data)

        self.logger.debug(f"Sent packet to node: {self.name}")

    def _recv(self, socket: socket.socket) -> bytes:
        data_len = socket.recv(4)
        data_len = struct.unpack("i", data_len)[0]
        return socket.recv(data_len)

    #
    def _handle_send_direct(self, data: dict):
        """
        Handle direct message from other node
        """

    def _handle_publish(self, data: dict):
        """
        Handle data from publisher node
        """

        try:
            packet = PublishPacket().from_json(data)
            self.logger.debug(f"Got packet: {packet}")
            topic = packet.get("topic")

            handler = self._search_for_handler("handle_" + topic)
            if handler:
                self.logger.debug(f"Got handler for topic: {topic} {handler}")
                handler(self, json.loads(packet.get("packet")))
            else:
                self.logger.debug(f"Got packet for unknown topic: {topic}")
        except Exception as e:
            self.logger.debug(e)

    def _handle_topic_closed(self, data: dict):
        topic = data["topic"]
        self.logger.debug(f"Topic {topic} closed")

    # user interface
    def create_topic(self, packet: Packet, topic_name: str) -> None:
        """
        Create a topic
        """

        topic_packet = CreateTopicPacket()
        topic_packet.set_packet(packet)
        topic_packet.set_topic(topic_name)

        self._send(
            self.sock,
            json.dumps({"type": "create_topic", "data": topic_packet.__str__()}),
        )

    def publish(self, packet: Packet, topic_name: str) -> None:
        """
        Publish data to topic
        """

        topic_packet = PublishPacket()
        topic_packet.set("packet", str(packet))
        topic_packet.set("topic", topic_name)

        self._send(
            self.sock, json.dumps({"type": "publish", "data": str(topic_packet)})
        )

    def subscribe(self, topic_name: str) -> None:
        packet = SubscribePacket()
        packet.set("topic", topic_name)

        self._send(
            self.sock, json.dumps({"type": "subscribe", "data": str(packet)})
        )

    def unsubscribe(self, topic_name: str) -> None:
        packet = UnsubscribePacket()
        packet.set("topic", topic_name)

        self._send(
            self.sock, json.dumps({"type": "unsubscribe", "data": str(packet)})
        )

class Server:
    """
    Server class that manages requests between nodes.
    """

    def __init__(self, port: int = 4532, secure: bool = False) -> None:
        self.port = port
        self.sock = None
        self.secure = secure
        self.logger = logging.getLogger("server")

        self.connections: dict[str, socket.socket] = {}
        self.topics: dict[str, Topic] = {}

        if secure:
            self.logger.warning("secure is not implemented yet")

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(("0.0.0.0", self.port))
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("Failed to start server due to exception")
            quit(1)

    def run(self):
        self.logger.info(f"Listening on port {self.port}")
        self.sock.listen(1)

        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        return t
    
    def _run(self):
        while True:
            conn, addr = self.sock.accept()
            threading.Thread(target=self._handle, args=(conn, addr)).start()

    def _handle(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        auth_data = self._recv(conn).decode("utf-8")
        auth_data = json.loads(auth_data)

        if auth_data["name"] not in self.connections:
            self.connections[auth_data["name"]] = conn
            self._send(conn, json.dumps({"status": "ok"}).encode("utf-8"))
        else:
            self._send(
                conn,
                json.dumps({"status": "error", "solve": "try_other_name"}).encode(
                    "utf-8"
                ),
            )

        try:
            while True:
                try:
                    data = self._recv(conn).decode("utf-8")
                    data = json.loads(data)
                except:
                    continue

                self._message(conn, data)

        except Exception as e:
            self.logger.debug(e)

        try:
            for topic in self.topics:
                self.topics[topic].unsubscribe(auth_data["name"])
        except:
            pass

        to_delete = []
        for topic in self.topics:
            try:
                if self.topics[topic].owner == auth_data["name"]:
                    self.topics[topic].disconnect(self)
                    to_delete.append(topic)
            except:
                pass

        try:
            self.connections.pop(auth_data["name"])
        except:
            pass

        for topic in to_delete:
            self.topics.pop(topic)

    def _message(self, conn: socket.socket, data: dict):
        try:
            ddata = json.loads(data["data"])
        except:
            return
        
        match data["type"]:
            case "create_topic":
                self._create_topic(conn, ddata)

            case "subscribe":
                self._subscribe(conn, ddata)

            case "unsubscribe":
                self._unsubscribe(conn, ddata)

            case "publish":
                self._publish(conn, ddata)

            case "send_direct":
                self._send_direct(conn, ddata)

            case _:
                self.logger.debug(f"Got unknown message type: {data['type']}")
                self._send(
                    conn,
                    json.dumps(
                        {
                            "status": "error",
                            "solve": "check_message_type",
                            "types": [
                                "create_topic",
                                "subscribe",
                                "unsubscribe",
                                "publish",
                                "send_direct",
                            ],
                        }
                    ).encode("utf-8"),
                )

    # low-level
    def _send(self, conn: socket.socket, data: bytes | str) -> None:
        if type(data) == str:
            data = data.encode("utf-8")

        data_len = struct.pack("i", len(data))
        conn.send(data_len)
        conn.send(data)

    def _recv(self, conn: socket.socket) -> bytes:
        data_len = conn.recv(4)
        data_len = struct.unpack("i", data_len)[0]
        return conn.recv(data_len)

    def _parse_packet(self, data: dict, p_type: type = Packet) -> Packet:
        try:
            return p_type().from_json(data["data"])

        except Exception as e:
            self.logger.debug(f"Failed to parse packet: {e}")
            return None

    def _get_name_by_socket(self, socket: socket.socket) -> str:
        for k, v in self.connections.items():
            if v == socket:
                return k

    # high-level
    def _create_topic(self, socket: socket.socket, data: dict) -> None:
        packet = CreateTopicPacket().from_json(data)

        if packet.topic in self.topics:
            self._send(
                socket,
                json.dumps({"status": "error", "solve": "topic_exists"}).encode(
                    "utf-8"
                ),
            )
            return

        owner = self._get_name_by_socket(socket)
        if owner is None:
            self._send(
                socket,
                json.dumps({"status": "error", "solve": "auth_error"}).encode("utf-8"),
            )
            return

        _packet = Packet(packet.packet_fields)
        self.topics[packet.topic] = Topic(packet.topic, owner, _packet)

        self.logger.debug(f"Created topic: {str(packet.topic)}")

        self._send(socket, json.dumps({"status": "ok"}).encode("utf-8"))

    def _subscribe(self, socket: socket.socket, data: dict) -> None:
        packet = SubscribePacket().from_json(data)

        if packet.topic not in self.topics:
            self._send(
                socket,
                json.dumps({"status": "error", "solve": "topic_not_exists"}).encode(
                    "utf-8"
                ),
            )
            return

        self.topics[packet.topic].subscribe(self._get_name_by_socket(socket))

        self.logger.debug(f"Subscribed to topic: {str(packet.topic)}")

        self._send(socket, json.dumps({"status": "ok"}).encode("utf-8"))

    def _unsubscribe(self, socket: socket.socket, data: dict) -> None:
        packet = UnsubscribePacket().from_json(data)

        if packet.topic not in self.topics:
            self._send(
                socket,
                json.dumps({"status": "error", "solve": "topic_not_exists"}).encode(
                    "utf-8"
                ),
            )
            return

        self.topics[packet.topic].unsubscribe(self._get_name_by_socket(socket))

        self.logger.debug(f"Unsubscribed from topic: {str(packet.topic)}")

        self._send(socket, json.dumps({"status": "ok"}).encode("utf-8"))

    def _publish(self, socket: socket.socket, data: dict) -> None:
        packet = PublishPacket().from_json(data)

        if packet.topic not in self.topics:
            self._send(
                socket,
                json.dumps({"status": "error", "solve": "topic_not_exists"}).encode(
                    "utf-8"
                ),
            )
            return

        self.topics[packet.topic].publish(packet.packet, self)

        self.logger.debug(f"Published packet to topic: {str(packet.topic)}")

        self._send(socket, json.dumps({"status": "ok"}).encode("utf-8"))

    def _send_direct(self, socket: socket.socket, data: dict) -> None:
        packet = SendDirectPacket().from_json(data)

        if packet.to not in self.connections:
            self._send(
                socket,
                json.dumps({"status": "error", "solve": "node_not_exists"}).encode(
                    "utf-8"
                ),
            )
            return

        self._send(
            self.connections[packet.to],
            json.dumps(
                {
                    "type": "send_direct",
                    "from": self._get_name_by_socket(socket),
                    "data": packet.packet.to_json(),
                }
            ).encode("utf-8"),
        )

        self.logger.debug(f"Sent packet to node: {str(packet.to)}")

        self._send(socket, json.dumps({"status": "ok"}).encode("utf-8"))

class Topic:
    def __init__(self, name: str, owner: str, packet: Packet) -> None:
        self.name = name
        self.subscribers = []
        self.owner = owner
        self.packet = packet

        self.logger = logging.getLogger(name+":"+owner)

    def publish(self, packet: Packet, root: Server) -> None:
        self.logger.debug(f"Publishing packet to {len(self.subscribers)} subscribers ({self.name})")

        success = 0
        for subscriber in self.subscribers:
            try:
                root._send(
                    root.connections[subscriber],
                    json.dumps(
                        {
                            "type": "publish",
                            "from": self.owner,
                            "topic": self.name,
                            "packet": packet,
                        }
                    ).encode("utf-8"),
                )
                success += 1

            except Exception as e:
                self.logger.debug(f"Failed to send packet to {subscriber}: {e}")

        self.logger.debug(
            f"Published packet to {len(self.subscribers)} subscribers, success: {success}"
        )

    def subscribe(self, node_name: str) -> None:
        self.subscribers.append(node_name)

    def unsubscribe(self, node_name: str) -> None:
        self.subscribers.remove(node_name)

    def disconnect(self, root: Server) -> None:
        for subscriber in self.subscribers:
            root._send(
                root.connections[subscriber],
                json.dumps(
                    {
                        "type": "topic_closed",
                        "from": self.owner,
                        "topic": self.name,
                    }
                )    
            )

    def __str__(self) -> str:
        return f'Topic "{self.name}" by {self.owner} with {len(self.subscribers)} subscribers'


# Server-client packets


class CreateTopicPacket(Packet):
    def __init__(self) -> None:
        super().__init__(
            {"topic": str, "packet_fields": dict[str, type], "packet": Packet}
        )

    def _stringify_packet_fields(self, packet_fields: dict[str, type]) -> str:
        r = {}
        for k, v in packet_fields.items():
            r[k] = str(v)
        return r

    def _stringify_packet(self, packet: Packet) -> str:
        return str(packet)

    def _parse_packet_fields(self, packet_fields: dict[str, str]) -> dict[str, type]:
        r = {}
        for k, v in packet_fields.items():
            r[k] = type(v)
        return r

    def _parse_packet(self, data: dict) -> Packet:
        return Packet(self.get("packet_fields")).from_json(data)

    def set_packet(self, packet: Packet):
        fields = packet.fields.copy()
        for k, v in packet.__dict__.items():
            fields[k] = str(v)

        self.set("packet_fields", fields)
        self.set("packet", packet)

    def set_topic(self, topic: str):
        self.set("topic", topic)

    def get_packet(self):
        return self.get("packet")


class SubscribePacket(Packet):
    def __init__(self):
        super().__init__({"topic": str})


class UnsubscribePacket(Packet):
    def __init__(self):
        super().__init__({"topic": str})


class PublishPacket(Packet):
    def __init__(self):
        super().__init__({"topic": str, "packet": str})


class SendDirectPacket(Packet):
    def __init__(self):
        super().__init__({"to": str, "packet": str})
