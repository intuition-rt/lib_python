from typing import Callable


class DummyTransport:
    on_received: Callable[[str], None] | None = None

    def __init__(self):
        pass

    def connect(self) -> bool:
        print("Dummy connect")
        raise NotImplementedError

    def disconnect(self) -> None:
        print("Dummy disconnect")
        raise NotImplementedError

    def send(self, message: str) -> None:
        print("Dummy sent", message)
        raise NotImplementedError

    def poll(self) -> None:
        print("Dummy poll")
        raise NotImplementedError
