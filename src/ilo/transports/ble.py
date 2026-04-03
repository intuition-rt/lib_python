import time
from typing import Callable
from ..ble_lib import ble_lib, CHARACTERISTIC_UUID


class BLETransport:

    def __init__(self, address: str):
        self.address = address
        self.on_received: Callable[[str], None] | None = None
        self._client = None

        self._size_char_uuid = "dead"

    def connect(self) -> bool:
        self._client = ble_lib.connect(self.address)
        # Not sleeping after the connection attempt
        # causes the subscription to not be taken into account at all!

        # 1s seems enough, but lets be safe.
        time.sleep(2)
        if self._client is not None:
            ble_lib.subscribe_to_notifications(
                CHARACTERISTIC_UUID,
                self._ble_notification_handler
            )

        return self._client is not None

    def disconnect(self) -> None:
        if self._client:
            try:
                ble_lib.unsubscribe_from_notifications(CHARACTERISTIC_UUID)
                ble_lib.disconnect(self._client)
            except Exception as e:
                print(f"Error during BLE disconnect: {e}")
            finally:
                self._client = None

    def send(self, message: str) -> None:
        if self._client:
            ble_lib.write_characteristic(
                self._client,
                CHARACTERISTIC_UUID,
                message.encode()
            )

    def poll(self) -> None:
        pass

    def _ble_notification_handler(self, sender: int, data: bytearray) -> None:
        if self.on_received:
            try:
                decoded_text = data.decode(errors="utf-8")
                self.on_received(decoded_text)
            except UnicodeDecodeError:
                pass
