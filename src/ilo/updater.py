from __future__ import annotations

import websocket
from typing import Dict
import asyncio
import requests
from .ble_lib import ble_lib


# This is used for development purpose in order to rapidly test scripts
# on custom firmware, that is not synced with the API.

# Keep you robot up to date if possible!
_skip_update = False


class _IloUpdater:
    def __init__(self, client, version, use_ble=True, ws=None):
        self.client = client
        self.version = version
        self.service_uuid = "5f6d"
        self.data_char_uuid = "c0de"
        self.size_char_uuid = "dead"
        self.notify_char_uuid = "1A2B"
        self.use_ble = use_ble
        self.ws = ws
        self.CHUNK_SIZE = 509 if use_ble else 1024
        self.update_complete = False
        self.loop = ble_lib.get_loop()

    async def send_firmware(self):
        try:
            with open("firmware.bin", "rb") as f:
                firmware_data = f.read()
            firmware_size = len(firmware_data)
            print(f"Firmware loaded: {firmware_size} octets")

            if self.use_ble and not self.client.is_connected:
                print("BLE client not connected.")
                return
            if not self.use_ble and self.ws is None:
                print("WebSocket not connected.")
                return
            print("\nConnected.")
            size_bytes = f"<500x{firmware_size}>".encode()
            if self.use_ble:
                await self.client.write_gatt_char(self.size_char_uuid, size_bytes, response=False)
            else:
                self.ws.send(size_bytes)
            print("\nFirmware size sent.")
            await asyncio.sleep(0.1)
            for i in range(0, firmware_size, self.CHUNK_SIZE):
                chunk = firmware_data[i:i+self.CHUNK_SIZE]
                if self.use_ble:
                    await self.client.write_gatt_char(self.data_char_uuid, chunk, response=False)
                else:
                    self.ws.send(bytes(chunk), opcode=websocket.ABNF.OPCODE_BINARY)

                print(f"\rSent {i + len(chunk)} / {firmware_size} octets", end="", flush=True)
                await asyncio.sleep(0.01)

            print("\n[UPDATE] Firmware sent\n")
            # TODO: reintroduce update confirmation

        except Exception as e:
            print(f"Error: {e}")

    def _run_update(self):
        """Planifie la coroutine dans la boucle asyncio existante."""
        future = asyncio.run_coroutine_threadsafe(self.send_firmware(), self.loop)
        try:
            future.result()  # attend le résultat ou erreur
        except Exception as e:
            print(f"⚠️ Error in _run_update: {e}")

    def download_firmware(self, data: Dict[str, str]):
        filepath = data.get("file")

        url = f"https://api.ilorobot.com/{filepath}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open("firmware.bin", "wb") as f:
                    f.write(response.content)
                print("Firmware downloaded successfully!")
                return True
            else:
                print(f"Failed to download firmware: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️ Error downloading firmware: {e}")
            return False

    def check_update(self):
        if _skip_update:
            return

        global suspend_receive_msg
        print("Checking for online updates... Please wait.")

        try:
            requests.get("https://ilorobot.com", timeout=3)
        except requests.ConnectionError:
            print("No network connection. Skipping update check.")
            return
        try:
            req = requests.get("https://api.ilorobot.com/firmwares/latest", timeout=3)
            if req.status_code == 200:
                data = req.json()
                latest_version = data["version"]
                print(f"Latest version: {latest_version}")
                if latest_version != self.version:
                    suspend_receive_msg = True
                    print("A new update is available!")
                    update = input("Do you want to update your robot? (yes/no): ").strip().lower()
                    if update == "y" or update == "yes":
                        if self.download_firmware(data):
                            self._run_update()
                    suspend_receive_msg = False
                else:
                    print("Your ilo is already up to date ;)")

            else:
                print("Failed to check for updates.")
        except Exception as e:
            print(f"⚠️ Impossible to check for updates :,(")

__all__ = ('_IloUpdater', '_skip_update')
