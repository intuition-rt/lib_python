from typing import Protocol, Callable


class Transport(Protocol):
    on_received: Callable[[str], None] | None = None

    def __init__(self, address):
        ...

    def connect(self) -> bool:
        ...

    def disconnect(self) -> None:
        ...

    def send(self, message: str) -> None:
        ...

    def poll(self) -> None:
        ...

    def send_binary(self, data: bytes) -> None:
        ...

    @property
    def preferred_chunk_size(self) -> int:
        ...
