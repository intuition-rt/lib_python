from __future__ import annotations

from typing import Dict
import asyncio
import requests
from .ble_lib import ble_lib

from .transports import Transport


# This is used for development purpose in order to rapidly test scripts
# on custom firmware, that is not synced with the API.

# Keep you robot up to date if possible!
_skip_update = False


class _IloUpdater:
    def __init__(self, transport: Transport, version):
        self.transport = transport
        self.version = version

        self.update_complete = False
        self.loop = ble_lib.get_loop()

    async def send_firmware(self):
        with open("firmware.bin", "rb") as f:
            firmware_data = f.read()
        firmware_size = len(firmware_data)

        size_trame = f"<500x{firmware_size}>"
        self.transport.send(size_trame)

        print(f"Firmware size {firmware_size} sent via standard protocol.")
        await asyncio.sleep(0.5)

        for i in range(0, firmware_size, self.transport.preferred_chunk_size):
            chunk = firmware_data[i : i + self.transport.preferred_chunk_size]

            self.transport.send_binary(chunk)
            print(f"\rProgress: {i + len(chunk)} / {firmware_size} bytes", end="")

            await asyncio.sleep(0.01)

        print("\n[UPDATE] Binary transfer complete.")

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
                    print("A new update is available!")
                    update = input("Do you want to update your robot? (yes/no): ").strip().lower()
                    if update == "y" or update == "yes":
                        if self.download_firmware(data):
                            self._run_update()
                else:
                    print("Your ilo is already up to date ;)")

            else:
                print("Failed to check for updates.")
        except Exception as e:
            print(f"⚠️ Impossible to check for updates :,(")

__all__ = ('_IloUpdater', '_skip_update')
