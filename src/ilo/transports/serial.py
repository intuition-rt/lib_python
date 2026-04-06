import serial
import time
from typing import Callable


INVALID_PREFIXES = (
    "<a", "<i", "<13", "<31", "<51", "<52", "<53", "<54", "<55", "<56", "<57",
    "<58", "<610", "<620", "<680", "<690", "<70", "<72", "<80", "<90", "<91",
    "<94", "<103",  "<00>", "<>"
)



class SerialTransport:
    on_received: Callable[[str], None] | None = None

    def __init__(self, port: str):
        self.on_received: Callable[[str], None] | None = None

        self._port = port
        self._ser = None

    def connect(self) -> bool:
        self._ser = serial.Serial(self._port, 115200)
        # TODO: serial.open()?
        # throws port is already open for now
        return True

    def disconnect(self) -> None:
        # TODO maybe use last-ref system?
        # self._ser.close()
        pass

    def send(self, message: str) -> None:
        if self._ser is None:
            return

        self._ser.write(message.encode())
        if not message.startswith(INVALID_PREFIXES):
            self._serial_read()

    def poll(self) -> None:
        pass

    def _serial_read(self):
        if self._ser is None:
            return

        timeout = 1
        start_time = time.time()
        try:
            trame = ""
            while True:
                if time.time() - start_time > timeout:
                    print("[serial_read] Timeout atteint dans la première boucle")
                    return

                char = self._ser.read().decode()
                if char == '<':
                    trame += char
                    break

            while True:
                if time.time() - start_time > timeout:
                    print("[serial_read] Timeout atteint dans la seconde boucle")
                    return

                char = self._ser.read().decode()
                if char:
                    trame += char
                    if char == '>':
                        break
            if trame and self.on_received:
                self.on_received(trame)
        except serial.SerialException as e:
            print(f"Error: {e}")

    def send_binary(self, data: bytes) -> None:
        raise NotImplementedError

    @property
    def preferred_chunk_size(self) -> int:
        return 1024
