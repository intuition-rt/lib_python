from typing import Protocol, Callable


class Transport(Protocol):
    on_received: Callable[[str], None] | None = None

    def connect(self) -> None:
        ...

    def disconnect(self) -> None:
        ...

    def send(self, message: str) -> None:
        ...

    def poll(self) -> None:
        ...

