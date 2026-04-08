import serial
import time
import threading

from typing import Callable


class SerialTransport:
    on_received: Callable[[str], None] | None = None

    def __init__(self, port: str):
        self.on_received: Callable[[str], None] | None = None

        self._port = port
        self._running = False
        self._ser = None

    def connect(self) -> bool:
        self._ser = serial.Serial(self._port, 115200)
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        return True

    def disconnect(self) -> None:
        # TODO maybe use last-ref system?
        # self._ser.close()
        self._running = False
        pass

    def send(self, message: str) -> None:
        if self._ser is None:
            return

        self._ser.write(message.encode())

    def poll(self) -> None:
        pass

    def _read_loop(self):
        while self._running:
            if self._ser and self._ser.in_waiting:
                # Read until the next '>' or a timeout
                data = self._ser.read(self._ser.in_waiting).decode('utf-8', errors='ignore')
                if data and self.on_received:
                    self.on_received(data)
            time.sleep(0.001) # Prevent CPU spiking

    def send_binary(self, _: bytes) -> None:
        raise NotImplementedError

    @property
    def preferred_chunk_size(self) -> int:
        return 1024
