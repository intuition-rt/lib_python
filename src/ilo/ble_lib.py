from __future__ import annotations

import threading
import asyncio
from bleak import BleakScanner, BleakClient
import concurrent.futures

CHARACTERISTIC_UUID = "DEAD"  # Notify  and read/write characteristic


class _SyncBleak:
    """
    Encapsule les fonctions de Bleak pour les rendre synchrone, tout en gardant
    les notifications réactives grâce à une boucle asyncio dans un thread dédié.
    """
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._start_loop, daemon=True)
        self.loop_thread.start()

        self.client = None
        self.executor = concurrent.futures.ThreadPoolExecutor()

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def get_loop(self):
        """Retourne la boucle asyncio utilisée par SyncBleak."""
        return self.loop

    def scan_devices(self, timeout=5):
        """Scan BLE devices de manière synchrone."""
        future = asyncio.run_coroutine_threadsafe(self._scan_devices(timeout), self.loop)
        return future.result()

    async def _scan_devices(self, timeout):
        devices = await BleakScanner.discover(timeout)
        return [(dev.name, dev.address) for dev in devices]

    def connect(self, address):
        """Connecte à un périphérique BLE."""
        future = asyncio.run_coroutine_threadsafe(self._connect(address), self.loop)
        return future.result()

    async def _connect(self, address):
        self.client = BleakClient(address)
        await self.client.connect()
        assert list(self.client.services) != []

        if self.client.is_connected:
            return self.client
        return None

    def write_characteristic(self, client, char_uuid, data):
        """Écrit dans une caractéristique BLE."""
        future = asyncio.run_coroutine_threadsafe(client.write_gatt_char(char_uuid, data), self.loop)
        return future.result()

    def subscribe_to_notifications(self, char_uuid, callback):
        """S'abonne aux notifications d'une caractéristique BLE sans bloquer."""

        async def async_callback(sender, data):
            # Envoie le callback dans un thread non-bloquant
            self.executor.submit(callback, sender, data)

        asyncio.run_coroutine_threadsafe(self._subscribe(char_uuid, async_callback), self.loop)

    async def _subscribe(self, char_uuid, callback):
        if self.client and self.client.is_connected:
            await self.client.start_notify(char_uuid, callback)
            # print(f"🔔 Abonné aux notifications sur {char_uuid}")

    def unsubscribe_from_notifications(self, char_uuid):
        """Se désabonne des notifications."""
        future = asyncio.run_coroutine_threadsafe(self._unsubscribe(char_uuid), self.loop)
        return future.result()

    async def _unsubscribe(self, char_uuid):
        if self.client and self.client.is_connected:
            await self.client.stop_notify(char_uuid)
            print(f"🚫 Désabonné des notifications sur {char_uuid}")

    def disconnect(self, client):
        """Déconnecte le client BLE."""
        future = asyncio.run_coroutine_threadsafe(client.disconnect(), self.loop)
        return future.result()

    def is_connected(self):
        """Vérifie si le client est connecté."""
        return self.client.is_connected if self.client else False


ble_lib = _SyncBleak()

__all__ = ('ble_lib',)
