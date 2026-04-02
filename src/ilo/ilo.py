# MIT License
# Copyright (c) 2025 Intuition Robotique & Technologique
# See the LICENSE file in the project root for full license information.
# -----------------------------------------------------------------------------
# This python library is for using the robot ilo with python command on WiFi or Bluetooth
# 21/03/2025
# -----------------------------------------------------------------------------
from __future__ import annotations

import colorsys
import psutil
import ipaddress
import serial.tools.list_ports
import serial
import socket
import math
import threading
import websocket
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Union
from keyboard_crossplatform import KeyboardCrossplatform
import time
import re
import unicodedata
import asyncio
from bleak import BleakScanner, BleakClient
from prettytable import PrettyTable
import requests
import concurrent.futures
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import signal
import sys
import webcolors

# https://stackoverflow.com/questions/2356399/tell-if-python-is-in-interactive-mode
IS_INTERACTIVE = hasattr(sys, 'ps1')

__version__ = "0.0.64"

print("ilo robot library version: ", __version__)
print("For more information about the library use ilo.info() command line")
print("For any help or support contact us on our website, ilorobot.com")

# This is used for development purpose in order to rapidly test scripts
# on custom firmware, that is not synced with the API.

# Keep you robot up to date if possible!
_skip_update = False

# -----------------------------------------------------------------------------

COLOR_NAMES = [
    "Blue",
    "Yellow",
    "Magenta",
    "Cyan",
    "Orange",
    "Purple",
    "Pink",
    "Dark Green",
    "White",
    "Deep Pink",
    "Cornflower Blue",
]

COLOR_TABLE = [
    (0,     0, 255),   # Blue
    (255, 255,   0),   # Yellow
    (255,   0, 255),   # Magenta
    (0,   255, 255),   # Cyan
    (255, 128,   0),   # Orange
    (128,   0, 128),   # Purple
    (255, 192, 203),   # Pink
    (0,   128,   0),   # Dark Green
    (255, 255, 255),   # White
    (255,  20, 147),   # Deep Pink
    (100, 149, 237),   # Cornflower Blue
]

from .copy_to_clipboard import copy_to_clipboard


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
CHARACTERISTIC_UUID = "DEAD"  # Notify  and read/write characteristic

suspend_receive_msg = False # Variable pour suspendre la réception de messages (lorsqu'il y'a des interactions avec l'utilisateur)

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

# -----------------------------------------------------------------------------

copy_to_clipboard("""ilo.check_robot_on_bluetooth()""")

class ConnectionType(Enum):
    WIFI = 0
    BLUETOOTH = 1
    SERIAL = 2

    def __str__(self) -> str:
        return self.name.removeprefix("ConnectionType.")


@dataclass
class RobotCandidate:
    """
    Represent the available data about a robot before connexion.
    This is used for the user to differenciate which robot is their, and
    connect to it.

    Collect from calls `check_robot_[serial|bluetooth|wifi]`
    """
    connection_type: ConnectionType
    address: str
    name: str
    color_pair: str | None

    def __hash__(self) -> int:
        return hash(self.address)

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, RobotCandidate):
            raise ValueError("Only comparable to the same type.")

        return self.name < other.name

    def __repr__(self) -> str:
        return f"<ilo name={self.name} @ {self.address} (via {self.connection_type})>"


__candidate_pool: dict[str, RobotCandidate] = {}


def find_in_candidates(name: str, use_connection_type = None) -> RobotCandidate | None:
    for candidate in __candidate_pool.values():
        if (
            use_connection_type is not None
            and candidate.connection_type != use_connection_type
        ):
            continue
        if candidate.name == name:
            return candidate
    return None

client = None
# -----------------------------------------------------------------------------

def info():
    """
    Print info about ilorobot
    """
    print("ilo robot is an education robot controlable by direct python command")
    print("To know every fonction available with ilo,  use ilo.list_function() command line")
    print("You are using the version ", __version__)
# -----------------------------------------------------------------------------

def list_function():
    '''
    Print the list of all the functions available in the library
    '''
    # add the name info <93>
    ilo_table = PrettyTable()
    ilo_table.field_names = ["Methods", "Description"]
    ilo_table.align["Methods"] = "l"
    ilo_table.align["Description"] = "l"
    ilo_table.add_row(
        ["ilo.info()", "Print info about ilorobot"], divider=True)
    ilo_table.add_row(
        ["ilo.list_function", "Print the list of all the functions available in the library"], divider=True)
    print(ilo_table)
    print("")

    my_ilo_table = PrettyTable()
    my_ilo_table.field_names = [
        "Object methods (example: my_ilo.game())", "Description"]
    my_ilo_table.align["Object methods (example: my_ilo.game())"] = "l"
    my_ilo_table.align["Description"] = "l"

    for entry_name in dir(Robot):
        entry: Any = getattr(Robot, entry_name)
        if not callable(entry) or entry_name.startswith("_"):
            continue

        if entry.__doc__ is None:
            continue

        desc = entry.__doc__.lstrip("\n").splitlines()[0]
        my_ilo_table.add_row([entry.__name__, desc], divider=False)

    print(my_ilo_table)
    print("If the table does not display correctly, expand your terminal.")
# -----------------------------------------------------------------------------

def _co_send_msg(ws: websocket.WebSocket, message: str) -> str:
    '''
    Send a message over the WebSocket connection
    '''
    if not ws.connected:
        return "..."

    try:
        ws.send(message)
        response = ws.recv()
        print(f"Sent: {message}, Received: {response}")  # Debugging line
        return str(response)
    except Exception as e:
        print(f"Error sending message: {e}")
        return "..."


def get_broadcast_ip():
    yield "<broadcast>"

    for iface_name, addrs in psutil.net_if_addrs().items():
        stats = psutil.net_if_stats().get(iface_name)
        if not stats or not stats.isup:
            continue

        for addr in addrs:
            if addr.family.name == "AF_INET":
                ip = addr.address
                netmask = addr.netmask

                if ip.startswith("127."):
                    continue

                iface = ipaddress.IPv4Interface(f"{ip}/{netmask}")
                broadcast = str(iface.network.broadcast_address)

                if ipaddress.ip_address(ip).is_private:
                    yield broadcast

def expand_4bit(v: int) -> int:
    return (v * 255 + 7) // 14


def base62_value(c: str) -> int:
    if '0' <= c <= '9':
        return ord(c) - ord('0')
    if 'A' <= c <= 'Z':
        return ord(c) - ord('A') + 10
    if 'a' <= c <= 'z':
        return ord(c) - ord('a') + 36
    return 0


def base62_to_rgb(s: str):
    index = base62_value(s[0]) * 62 + base62_value(s[1])

    rq = (index >> 8) & 0x0F
    gq = (index >> 4) & 0x0F
    bq = index & 0x0F

    r = expand_4bit(rq)
    g = expand_4bit(gq)
    b = expand_4bit(bq)

    return r, g, b


def closest_color_name(rgb: tuple[int, int, int]) -> str:
    def convert(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
        r, g, b = rgb
        return colorsys.rgb_to_hsv(r / 256, g / 256, b / 256)

    target_col = convert(rgb)

    min_distance = float("inf")
    closest_name = "black"

    colors = webcolors.names()

    for name in colors:
        r, g, b = webcolors.name_to_rgb(name)
        col = convert((r, g, b))

        distance = math.sqrt(
            sum(
                (b - a) ** 2 for a, b in zip(col, target_col)
            )
        )

        if distance < min_distance:
            min_distance = distance
            closest_name = name

    return closest_name


def base62_to_name(c: str) -> str:
    rgb = base62_to_rgb(c)
    return closest_color_name(rgb)


__last_ilo_id = 1

def _generate_new_ilo_id() -> int:
    global __last_ilo_id

    __last_ilo_id += 1
    return __last_ilo_id - 1



def show_available_robots(connection_type: ConnectionType):
    uid_name = {
        ConnectionType.WIFI: "IP Address",
        ConnectionType.BLUETOOTH: "Device ID",
        ConnectionType.SERIAL: "Port"
    }

    table = PrettyTable()
    table.field_names = [
        uid_name[connection_type],
        "Name of ilo",
        "Colors"
    ]

    any_matches = False
    for robot in sorted(__candidate_pool.values()):
        if robot.connection_type == connection_type:
            any_matches = True
            table.add_row(
                [robot.address, robot.name, robot.color_pair or "-"]
            )

    if any_matches:
        print(table)
    else:
        print("Unfortunately, no ilo were found.")


def check_robot_on_wifi(ap_mode = True, timeout = 1):
    """
    Check the presence of the ilo(s) on the network
    """
    copy_to_clipboard("""my_ilo = ilo.robot(1)""")
    try:
        print("Looking for ilo on your network ...")
        ilo_AP = False

        if ap_mode:
            try:
                ws_url = "ws://192.168.4.1:4583"
                print(f"Checking {ws_url}")
                ws = websocket.create_connection(ws_url, timeout=timeout)
                if _co_send_msg(ws, "<ilo>") == "ilo":
                    ilo_AP = True
                    ws.close()
                    print("Your robot is working as an access point")
            except:
                pass

        if not ilo_AP:
            _seen_ids = set()

            DISCOVERY_MESSAGE = "DISCOVER_ROBOT"
            BROADCAST_PORT = 12345
            BUFFER_SIZE = 1024

            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(timeout)

            try:
                for addr in get_broadcast_ip():
                    s.sendto(DISCOVERY_MESSAGE.encode(), (addr, BROADCAST_PORT))

                start = time.time()
                while time.time() - start < timeout:
                    try:
                        data, addr = s.recvfrom(BUFFER_SIZE)
                        msg = data.decode().strip()
                        if msg.startswith("<") and msg.endswith(">"):
                            content = msg[1:-1]
                            parts = content.split(",")

                            # old version without color pairs
                            if len(parts) == 3:
                                hostname, hostname, product_id = parts
                                color_pair = f"Ilo blue"

                            elif len(parts) == 4:
                                hostname, hostname, product_id, colors = parts

                                # New "XX/XX" color encoding
                                if len(colors) == 5:
                                    color_circle, color_center = [
                                        base62_to_name(p)
                                        for p in colors.split("/")
                                    ]

                                # Legacy 1 letter encoding
                                else:
                                    color_circle, color_center = [
                                        "Unkown" if p == "?" else COLOR_NAMES[int(p)]
                                        for p in colors.split("/")
                                    ]

                                color_pair = f"{color_circle}, {color_center}"
                            else:
                                continue

                            IP = addr[0]
                            if IP in _seen_ids:
                               continue

                            _seen_ids.add(IP)
                            __candidate_pool[IP] = RobotCandidate(
                                connection_type=ConnectionType.WIFI,
                                address=IP,
                                name=hostname,
                                color_pair=color_pair
                            )
                    except socket.timeout:
                        break
            except Exception as e:
                print(f"Discovery error: {e}")
            finally:
                s.close()

            _seen_ids.clear()

            show_available_robots(ConnectionType.WIFI)

    except Exception as e:
        print(f"WebSocket error: {e}")


def _attempt_connection_on_serial(com: str):
    try:
        ser = serial.Serial(com, 115200, timeout=1)
    except (serial.SerialException, OSError) as e:
        # Silent connection attempt
        return

    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(1)

        ser.write(b"<930>")
        time.sleep(1)

        while True:
            response = ser.readline().decode(errors="ignore").strip()
            if not response:
                print(f"No valid response received on {com}")
                break

            # skip debug logs
            # TODO: a proper wrapper to handle this transparently
            if response.startswith("["):
                continue

            print(f"Robot {response} detected on port {com}")
            __candidate_pool[com] = RobotCandidate(
                connection_type=ConnectionType.SERIAL,
                address=com,
                name=response,
                color_pair=None
            )

            break

        ser.close()

    except (serial.SerialException, OSError) as e:
        print(f"Error with port {com}: {e}")


def check_robot_on_serial(COM=None):
    """
    Check the connection to ilo in serial
    """
    copy_to_clipboard("""my_ilo = ilo.robot(1)""")

    if COM:
        try:
            print("Check that ilo is properly connected ...")
            _attempt_connection_on_serial(COM)
        except (serial.SerialException, OSError) as e:
            print(f"Error with port {COM} : {e}")

    else:
        print("Check that ilo is properly connected ...")

        try:
            ports = serial.tools.list_ports.comports()
        except Exception as e:
            print(f"Serial error: {e}")
            return None

        for port in ports:
            print(f"Testing port: {port.device}")
            _attempt_connection_on_serial(port.device)

    show_available_robots(ConnectionType.SERIAL)


def check_robot_on_bluetooth():
    copy_to_clipboard('''my_ilo = ilo.robot(1)''')

    print("[ILO] Scanning for BLE devices...")
    try:    
        devices = ble_lib.scan_devices()
        table = PrettyTable()
        table.field_names = ["Device adress", "ID of ilo", "Name of ilo", "Colors"]
        for device in devices:
            if str(device[0]).startswith("ilo_"):
                parts = str(device[0]).split("_")

                if len(parts) != 3:
                    continue

                _, hostname, colors = parts

                if len(colors) == 4:
                    center = base62_to_name(colors[:2])
                    circle = base62_to_name(colors[2:])
                    color_pair = f"{center}, {circle}"
                elif len(colors) == 5:
                    center = base62_to_name(colors[:2])
                    circle = base62_to_name(colors[3:])
                    color_pair = f"{center}, {circle}"
                else:
                    color_pair = "unknown"

                table.add_row([device[1], _generate_new_ilo_id(), hostname, color_pair])
                __candidate_pool[device[1]] = RobotCandidate(
                    connection_type=ConnectionType.BLUETOOTH,
                    address=device[1],
                    name=hostname,
                    color_pair=color_pair
                )

        show_available_robots(ConnectionType.BLUETOOTH)
        
    except Exception as e:
        print(f"Error check robot on Bluetooth: {e}")
        return False

class Robot:
    _robots_connected: Dict[str, Robot] = {}

    def __init__(self, candidate: RobotCandidate, debug=False):
        self._ws: websocket.WebSocket | None = None

        self._ser = None
        self._connect = False

        self._version = ""

        self._ble_device = None

        self._hostname = candidate.name

        self._red_color_left   = 0
        self._green_color_left = 0
        self._blue_color_left  = 0

        self._red_color_center   = 0
        self._green_color_center = 0
        self._blue_color_center  = 0

        self._red_color_right   = 0
        self._green_color_right = 0
        self._blue_color_right  = 0

        self._clear_left = 0
        self._clear_center = 0
        self._clear_right = 0

        self._line_left = 0
        self._line_center = 0
        self._line_right = 0

        self._line_threshold_value = 0

        self._distance_front = 0
        self._distance_right = 0
        self._distance_back = 0
        self._distance_left = 0

        self._roll = 0
        self._pitch = 0
        self._yaw = 0

        self._accX = 0
        self._accY = 0
        self._accZ = 0
        self._gyroX = 0
        self._gyroY = 0
        self._gyroZ = 0

        self._battery_status = 0
        self._battery_pourcentage = 0
        self._battery_voltage = 0

        self._red_led = 0
        self._green_led = 0
        self._blue_led = 0

        self._motor_ping = 0
        self._motor_speed = 0
        self._motor_angle = 0
        self._motor_id = 0
        self._temp_motor = 0
        self._motor_volt = 0
        self._motor_torque = 0
        self._motor_current = 0
        self._motor_is_moving = 0
        self._acc_motor = 0
        self._tempo_pos = 0
        self._kp = 0
        self._ki = 0
        self._kd = 0

        self._ssid = ""
        self._password = ""

        self._accessory = 0
        self._potard_value = 0

        self._global_trame = ""

        self._version = ""

        self._manufacturing_date = ""
        self._first_use_date = ""
        self._product_version = ""
        self._product_id = ""

        self._response_event = threading.Event()
        self._response_value = None
        
        self._movement_complete = threading.Event()

        self._recv_thread = None
        self._recv_thread_running = False

        self._debug = debug
        copy_to_clipboard('''my_ilo.step('front')''')

        self._Port = 4583

        self.address = candidate.address
        self.connection_type = candidate.connection_type

        print("Connnecting to", candidate)
        self._connection()


    def __repr__(self) -> str:
        return f"<ilo name={self._hostname} @ {self.address}>"

    # -----------------------------------------------------------------------------
    def _connection(self):
        """
        Connection of your machine to robot object 
        """
        if self.connection_type == ConnectionType.WIFI:
            try:
                self._ws = websocket.create_connection(f"ws://{self.address}:{self._Port}")

                # Vérifie si un ancien thread de réception est actif et l'arrête avant d'en démarrer un nouveau
                if self._recv_thread and self._recv_thread.is_alive():
                    # print("Stopping the previous reception thread...")
                    self._stop_reception()

                # Start the WebSocket de reception in a separate thread
                self._recv_thread_running = True
                self._recv_thread = threading.Thread(
                    target=self._web_socket_receive)
                self._recv_thread.start()

                self._robots_connected[self.address] = self

                self._connect = True
                self._send_msg("<500y>")
                time.sleep(0.2)
                self.get_name()
                time.sleep(0.2)
                print('Your are connected to ' + self._hostname)
                updater = _IloUpdater(self._ser, self._version, False, self._ws)
                updater.check_update()

            except Exception as e:
                print(
                    "Connection error: you have to be connect to the ilo wifi network")
                print(
                    " --> If the malfunction persists, switch off and switch on ilo")
                print(f"Error connecting to the robot: {e}")
                self._connect = False

        elif self.connection_type == ConnectionType.SERIAL:
            try:
                # Start the serial connection
                self._ser = serial.Serial(self.address, 115200)

                self._connect = True
                self._robots_connected[self.address] = self
                
                time.sleep(0.2)
                self.get_name()
                time.sleep(0.2)
                print('Your are connected to ' + self._hostname)
                
            except Exception as e:
                print("Connection error: you must be connected to the ilo robot")
                print(
                    " --> If the malfunction persists, switch off and switch on ilo, or try using another cable")
                print(f"Error connecting to the robot: {e}")
                self._connect = False

        elif self.connection_type == ConnectionType.BLUETOOTH:
            def notification_handler(sender, data):
                global suspend_receive_msg
                try:
                    decoded_data = data.decode('utf-8')
                    if suspend_receive_msg:
                        return
                    self._process_received_data(decoded_data)
                except UnicodeDecodeError:
                    print(f"Received non-UTF-8 data: {data}")
            # print("Connecting to the BLE device...")
            try:
                self._ble_device = ble_lib.connect(self.address)

                ble_lib.subscribe_to_notifications(CHARACTERISTIC_UUID, notification_handler)
                self._connect = True
                self._robots_connected[self.address] = self
                # print("Connected to the BLE device.")
                self._send_msg("<ilo>")
                self._send_msg("<500y>")
                time.sleep(0.2)
                self.get_name()
                time.sleep(0.2)
                print('Your are connected to ' + self._hostname)
                updater = _IloUpdater(self._ble_device, self._version)
                updater.check_update()
            except Exception as e:
                print(f"Error connecting to the BLE device: {e}")
                self._connect = False

    def disconnect(self):
        if self.connection_type == ConnectionType.WIFI:
            if self._ws is not None:
                _co_send_msg(self._ws, "<>")
                self._ws.close()
        elif self.connection_type == ConnectionType.SERIAL:
            pass   # on ne peut pas paraleléliser les ouverture de port comme les websocket
        elif self.connection_type == ConnectionType.BLUETOOTH:
            if self._ble_device is not None:
                ble_lib.disconnect(self._ble_device)
        else:
            pass

        self._stop_reception()


    # -----------------------------------------------------------------------------
    def _send_msg(self, message):
        self._response_event.clear()
        if self.connection_type == ConnectionType.WIFI:
            if self._ws and self._connect:
                try:
                    self._ws.send(message)
                    if self._debug:
                        print(f"Sent:     {message}")
                    # time.sleep(0.1)  # Small delay to ensure the message is sent
                except websocket.WebSocketException as e:
                    print(f"Error sending message: {e}")
            else:
                print("WebSocket is not connected.")

        elif self.connection_type == ConnectionType.SERIAL:
            if self._ser and self._connect:
                try:
                    self._ser.write(message.encode())
                    
                    print(f"Sent:     {message}")

                    invalid_prefixes = ("<a", "<i", "<13", "<31", "<51", "<52", "<53", "<54", "<55", "<56", "<57", "<58",
                                        "<610", "<620", "<680", "<690", "<70", "<72", "<80", "<90", "<91", "<94", "<103", 
                                        "<00>", "<>")

                    if message.startswith(invalid_prefixes):
                        pass
                    else:
                        # start_time = time.time()
                        # while time.time() - start_time < 1:
                        self._serial_read()

                except Exception as e:
                    print(f"Error sending message: {e}")
            else:
                print("Serial is not connected.")
        elif self.connection_type == ConnectionType.BLUETOOTH:
            if self._ble_device and self._connect:
                try:
                    ble_lib.write_characteristic(self._ble_device, CHARACTERISTIC_UUID, message.encode())
                    if self._debug:
                        print(f"Sent:     {message}")
                    # time.sleep(0.1)  # Small delay to ensure the message is sent
                except Exception as e:
                    print(f"Error sending message: {e}")
        else:
            print("No connection established (error sending message).")
    # -----------------------------------------------------------------------------
    def _web_socket_receive(self):
        """
        Thread function to continuously receive data from the WebSocket.
        Stops when recv_thread_running is set to False.
        """
        while self._recv_thread_running:
            try:
                self._ws.settimeout(1) # Ajout d'un timeout pour que recv() ne bloque pas indéfiniment
                data = self._ws.recv() # Timeout de 1 seconde pour éviter un blocage sur recv()
                if data:
                    if '/' in data:
                        sub_trames = data.split('/')[1:-1]
                        for sub_trame in sub_trames:
                            self._process_received_data(f"<{sub_trame}>")
                    else:
                        self._process_received_data(data)
                        self._marker = True
            except websocket.WebSocketTimeoutException:
                # Timeout atteint, continue à boucler pour vérifier recv_thread_running
                continue
            except websocket.WebSocketException as e:
                # Gestion des erreurs de WebSocket, afficher l'erreur pour le débogage
                print(f"WebSocket error: {e}")
                break

        print("Thread de réception terminé.")

    def _serial_read(self):
        """
        Serial function to read data from serial.
        """

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
            if trame:
                self._process_received_data(trame)
        except serial.SerialException as e:
            print(f"Error: {e}")
    # -----------------------------------------------------------------------------
    def _process_received_data(self, data):
        """
        Process the data received from the WebSocket or Serial and update the robot's attributes
        """
        if self._debug:
            print(f"Data received: {data}")
        try:

            if str(data[1:4]) == "10c":  # get_color_rgb_center
                self._red_color_center   = int(data[data.find('r')+1: data.find('g')])
                self._green_color_center = int(data[data.find('g')+1: data.find('b')])
                self._blue_color_center  = int(data[data.find('b')+1: data.find('>')])

            elif str(data[1:4]) == "10l":  # get_color_rgb_left
                self._red_color_left   = int(data[data.find('r')+1: data.find('g')])
                self._green_color_left = int(data[data.find('g')+1: data.find('b')])
                self._blue_color_left  = int(data[data.find('b')+1: data.find('>')])

            elif str(data[1:4]) == "10d":  # get_color_rgb_right
                self._red_color_right   = int(data[data.find('r')+1: data.find('g')])
                self._green_color_right = int(data[data.find('g')+1: data.find('b')])
                self._blue_color_right  = int(data[data.find('b')+1: data.find('>')])

            elif str(data[1:4]) == "11l":  # get_color_clear
                self._clear_left = int(data[data.find('l')+1: data.find('m')])
                self._clear_center = int(data[data.find('m')+1: data.find('r')])
                self._clear_right = int(data[data.find('r')+1: data.find('>')])

            elif str(data[1:4]) == "12l":  # get_line
                self._line_left = int(data[data.find('l')+1: data.find('m')])
                self._line_center = int(data[data.find('m')+1: data.find('r')])
                self._line_right = int(data[data.find('r')+1: data.find('>')])

            elif str(data[1:4]) == "14t":  # get_line_threshold_value
                self._line_threshold_value = int(data[data.find('t')+1: data.find('>')])

            elif str(data[1:4]) == "20f":  # get_distance
                self._distance_front = int(data[data.find('f')+1: data.find('r')])
                self._distance_right = int(data[data.find('r')+1: data.find('b')])
                self._distance_back = int(data[data.find('b')+1: data.find('l')])
                self._distance_left = int(data[data.find('l')+1: data.find('>')])

            elif str(data[1:4]) == "21f":  # get_distance_front
                self._distance_front = int(data[data.find('f')+1: data.find('>')])

            elif str(data[1:4]) == "22r":  # get_distance_right
                self._distance_right = int(data[data.find('r')+1: data.find('>')])

            elif str(data[1:4]) == "23b":  # get_distance_back
                self._distance_back = int(data[data.find('b')+1: data.find('>')])

            elif str(data[1:4]) == "24l":  # get_distance_left
                self._distance_left = int(data[data.find('l')+1: data.find('>')])

            elif str(data[1:4]) == "30r":  # get_angle - données traités en degrés
                self._roll = float(data[data.find('r')+1: data.find('p')])
                self._pitch = float(data[data.find('p')+1: data.find('y')])
                self._yaw = float(data[data.find('y')+1: data.find('>')])

            elif str(data[1:4]) == "32x":  # get_raw_imu
                self._accX = float(data[data.find('x')+1: data.find('y')])
                self._accY = float(data[data.find('y')+1: data.find('z')])
                self._accZ = float(data[data.find('z')+1: data.find('r')])
                self._gyroX = float(data[data.find('r')+1: data.find('p')])
                self._gyroY = float(data[data.find('p')+1: data.find('g')])
                self._gyroZ = float(data[data.find('g')+1: data.find('>')])

            elif str(data[1:4]) == "40s":  # get_battery
                self._battery_status = int(data[data.find('s')+1: data.find('p')])
                self._battery_pourcentage = int(data[data.find('p')+1: data.find('v')])
                self._battery_voltage = float(data[data.find('v')+1: data.find('>')])

            elif str(data[1:4]) == "50r":  # get_led_color
                self._red_led = int(data[data.find('r')+1: data.find('g')])
                self._green_led = int(data[data.find('g')+1: data.find('b')])
                self._blue_led = int(data[data.find('b')+1: data.find('>')])

            elif str(data[1:4]) == "60i":  # ping_single_motor
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_ping = int(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "611":  # get_single_motor_speed
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_speed = int(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "621":  # get_single_motor_angle
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_angle = int(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "63i":  # get_temp_single_motor
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._temp_motor = int(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "64i":  # get_volt_single_motor
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_volt = int(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "65i":  # get_torque_single_motor
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_torque = int(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "66i":  # get_current_single_motor
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_current = int(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "67i":  # get_motor_is_moving
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_is_moving = int(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "681":  # get_acc_motor
                self._acc_motor = int(data[data.find('a')+1: data.find('>')])

            elif str(data[1:4]) == "691":  # get_tempo_pos
                self._tempo_pos = int(data[data.find('t')+1: data.find('>')])

            elif str(data[1:4]) == "71p":  # get_pid
                self._kp = float(data[data.find('p')+1: data.find('i')])
                self._ki = float(data[data.find('i')+1: data.find('d')])
                self._kd = float(data[data.find('d')+1: data.find('>')])

            elif str(data[1:3]) == "92":  # get_wifi_credentials

                self._ssid, self._password = self._parse_credentials(data)

            elif str(data[1:4]) == "93n":  # get_name
                self._hostname = str(data[data.find('n')+1: data.find('>')])

            elif str(data[1:5]) == "101t":  # get_accessory
                self._accessory = float(data[data.find('t')+1: data.find('>')])

            elif str(data[1:5]) == "102a":  # get_accessory
                self._potard_value = float(data[data.find('a')+1: data.find('>')])

            elif str(data[1:4]) == "120":  # get_manufacturing_date
                self._manufacturing_date = str(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "130":  # get_first_use_date
                self._first_use_date = str(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "140":  # get_product_version
                self._product_version = str(data[data.find('s')+1: data.find('>')])

            elif str(data[1:4]) == "150":  # get_product_id
                self._product_id = str(data[data.find('s')+1: data.find('>')])

            elif str(data[1:5]) == "500y": # get_version
                self._version = str(data[data.find('y')+1: data.find('>')]).removeprefix("v")

            elif str(data[1:4]) == "500":  # get_global_trame
                self._version = str(data[data.find('y')+1: data.find('>')])
                print(f"Version: {self._version}")
            
            elif str(data[1:5]) == "avp0":  # step movement complete
                self._movement_complete.set()

            self._response_event.set()

        except Exception as e:
            # -- marin add e to check the error
            print(f'[COMMUNICATION ERROR] data process: {e}')
            return None
    # -----------------------------------------------------------------------------
    def _stop_reception(self):
        """
        Stop the WebSocket reception thread and close the connection.
        """
        if not self._recv_thread_running:
            return  # Si le thread est déjà arrêté, ne rien faire

        print("Stopping reception thread...")
        self._recv_thread_running = False  # Arrêter la boucle dans le thread de réception

        if self._ws:
            try:
                if self._ws is not None and self._ws.connected:
                    self._ws.close()
                self._connect = False  # Mettre à jour l'état de connexion après la fermeture de WebSocket
                print("WebSocket successfully closed")
            except Exception as e:
                print(f"Erreur lors de la fermeture de la WebSocket: {e}")

        # if self._recv_thread and self._recv_thread.is_alive():
        if self._recv_thread:
            print("Waiting for the reception thread to stop...")
            self._recv_thread.join(timeout=2)

        self._robots_connected.pop(self.address)
        print(f"WebSocket connection closed for the robot {self._hostname}.")

    # -----------------------------------------------------------------------------
    def __del__(self):
        """
        Destructor to ensure the WebSocket connection is closed gracefully
        and the ID is removed from the list of connected robots
        """
        self.disconnect()

    # -----------------------------------------------------------------------------
    def test_connection(self):
        """
        Test the connection to the robot via a try of stop method.

        :return: True or False
        """
        if self.connection_type == ConnectionType.WIFI:
            try:
                self._send_msg("<ilo>")
                return True
            except:
                print("Error connection to the robot")
                return False
        elif self.connection_type == ConnectionType.SERIAL:
            try:
                self._send_msg("<ilo>")
                return True
            except:
                print("Error connection to the robot")
                return False
        elif self.connection_type == ConnectionType.BLUETOOTH:
            try:
                self._send_msg("<ilo>")
                return True
            except:
                print("Error connection to the robot")
                return False
    # -----------------------------------------------------------------------------
    def _correction_command(self, acc, list_course):
        """
        Convert a list of 3 elements to a sendable string
        """
        if int(list_course[0]) >= 100:
            list_course[0] = str(list_course[0])
        elif 100 > int(list_course[0]) >= 10:
            list_course[0] = str('0') + str(list_course[0])
        elif 10 > int(list_course[0]) >= 1:
            list_course[0] = str('00') + str(list_course[0])
        else:
            list_course[0] = str('000')

        if int(list_course[1]) >= 100:
            list_course[1] = str(list_course[1])
        elif 100 > int(list_course[1]) >= 10:
            list_course[1] = str('0') + str(list_course[1])
        elif 10 > int(list_course[1]) >= 1:
            list_course[1] = str('00') + str(list_course[1])
        else:
            list_course[1] = str('000')

        if int(list_course[2]) >= 100:
            list_course[2] = str(list_course[2])
        elif 100 > int(list_course[2]) >= 10:
            list_course[2] = str('0') + str(list_course[2])
        elif 10 > int(list_course[2]) >= 1:
            list_course[2] = str('00') + str(list_course[2])
        else:
            list_course[2] = str('000')

        new_command = []
        str_command = str(list_course[0] + list_course[1] + list_course[2])
        new_command = "<a" + str(acc) + "v" + str_command + "pxyr>"
        return new_command
    # -----------------------------------------------------------------------------
    def stop(self):
        """
        Stop the robots and free the engines.
        """
        self._send_msg("<>")

    def pause(self, duration=1):
        """
        Stop ilo and block its motors for a selected duration in seconds
        """
        self._send_msg("<avp" + str(duration*1000) + "xyr>")

    def step(self, direction: str, step=1, finish_state=True, display_led: bool=True):
        """
        Move ilo in the selected direction 

        Parameters:
            direction (str): The direction in which the robot is moving
            step (int): The number of steps the robot will do
            finish_state (bool): If True, wait for the end of the movement before returning

        Raises:
            TypeError: If the direction is not a string
            ValueError: If the direction is not one of the following: front, back, left, right, rot_trigo or rot_clock
            TypeError: If the step is not an integer or a float
            ValueError: If value is not between 0.01 and 100
            TypeError: If finish_state is not a boolean

        Examples:
            my_ilo.step("front", 10.5)\n
            my_ilo.step("back")
        """

        if not isinstance(direction, str):
            print("[ERROR] 'direction' should be a string")
            return None
        
        if isinstance(step, bool):
            finish_state = step
            step = None

        if (direction == 'front' or direction == 'back' or direction == 'left' or direction == 'right'):

            if step is None:
                step = 1

            if not isinstance(step, (int, float)):
                print("[ERROR] 'step' should be an integer or a float")
                return None

            if step > 100 or step < 0.01:
                print("[ERROR] 'step' should be between 0.01 and 100 for translation")
                return None

            step = int(step*200)

        elif (direction == 'rot_trigo' or direction == 'rot_clock'):

            if step is None:
                step = 1

            if not isinstance(step, (int, float)):
                print("[ERROR] 'step' should be an integer or a float")
                return None

            if step < 0.01:
                print("[ERROR] 'step' should be more than 0.01 for rotation")
                return None

            # Convertir step en angle : step=1 → 90°, step=1.5 → 135°, etc.
            step = int(step * 90)

        else:
            print("[ERROR] 'step' unknow name")
            return None
        
        if finish_state != None:
            if not isinstance(finish_state, bool):
                print ("[ERROR] 'finish_state' should be a boolean")
                return None
        
        if not isinstance(display_led, bool):
            print ("[ERROR] 'display_led' should be a boolean")
            return None


        if direction == 'front':
            if display_led:
                self._send_msg('<a60vpx1' + str(step) + 'yrt>')  # Blue LED during movement
            else:
                self._send_msg('<a60vpx1' + str(step) + 'yrf>')
            # msg = '<a60vpx1' + str(step) + 'yr>'
            # self._send_msg(msg)
        elif direction == 'back':
            if display_led:
                self._send_msg('<a60vpx0' + str(step) + 'yrt>')  # Blue LED during movement
            else:
                self._send_msg('<a60vpx0' + str(step) + 'yrf>')
            # msg = '<a60vpx0' + str(step) + 'yr>'
            # self._send_msg(msg)
        elif direction == 'left':
            if display_led:
                self._send_msg('<a60vpxy0' + str(step) + 'rt>')  # Blue LED during movement
            else:
                self._send_msg('<a60vpxy0' + str(step) + 'rf>')
            # msg = '<a60vpxy0' + str(step) + 'r>'
            # self._send_msg(msg)
        elif direction == 'right':
            if display_led:
                self._send_msg('<a60vpxy1' + str(step) + 'rt>')  # Blue LED during movement
            else:
                self._send_msg('<a60vpxy1' + str(step) + 'rf>')
            # msg = '<a60vpxy1' + str(step) + 'r>'
            # self._send_msg(msg)
        elif direction == 'rot_trigo':
            if display_led:
                self._send_msg('<a60vpxyr0' + str(step) + 't>')  # Blue LED during movement
            else:
                self._send_msg('<a60vpxyr0' + str(step) + 'f>')
            # msg = '<a60vpxyr0' + str(step) + '>'
            # self._send_msg(msg)
        elif direction == 'rot_clock':
            if display_led:
                self._send_msg('<a60vpxyr1' + str(step) + 't>')  # Blue LED during movement
            else:
                self._send_msg('<a60vpxyr1' + str(step) + 'f>')
            # msg = '<a60vpxyr1' + str(step) + '>'
            # self._send_msg(msg)
        else:
            print("[ERROR] 'Direction' should be 'front', 'back', 'left', 'rot_trigo', 'rot_clock'")
            
        if finish_state == True:
            # Clear the event before waiting
            self._movement_complete.clear()
            
            # Calculate timeout based on number of steps
            # Base timeout: 2.459s for 1 step, add margin for safety
            if (direction == 'front' or direction == 'back' or direction == 'left' or direction == 'right'):
                # step was multiplied by 100 earlier, so divide to get actual steps
                actual_steps = step / 100
            elif (direction == 'rot_trigo' or direction == 'rot_clock'):
                # step was multiplied by 90 earlier for rotation
                # Consider rotation angle: base timeout for 90° (step=1)
                actual_steps = step / 45
            else:
                actual_steps = 1
                
            # Base timeout: 2.5s per step + 1s margin
            timeout = (2.5 * actual_steps) + 3.0
            
            # print(f"Waiting for end of movement (timeout: {timeout:.2f}s)...")
            
            # Wait for the "avp0" frame indicating movement completion
            movement_finished = self._movement_complete.wait(timeout=timeout)
            return True
            
            # if movement_finished:

            #     print("Movement completed successfully.")
            # else:
            #     print("[WARNING] Movement completion timeout - frame may have been lost.")

    def flat_movement(self, angle: int, distance: int):
        """
        Move ilo in the selected direction in angle for a selected distance

        Parameters:
            angle (int): The direction in which the robot is moving
            distance (int): The distance the robot will travel in centimeters

        Raises:
            TypeError: If angle is not an integer
            ValueError: If angle is not between 0 and 360
            TypeError: If distance is not an integer

        Examples:
            my_ilo.flat_movement(90, 10)
        """

        if not isinstance(angle, int):
            print("[ERROR] 'angle' should be an integer")
            return None

        if angle > 360 or angle < 0:
            print("[ERROR] 'angle' should be between 0 and 360")
            return None

        if not isinstance(distance, int):
            print("[ERROR] 'distance' should be an integer")
            return None

        if 0 <= angle < 90:
            indice_x = 1
            indice_y = 1
        elif 90 <= angle < 180:
            indice_x = 0
            indice_y = 1
        elif 180 <= angle < 270:
            indice_x = 0
            indice_y = 0
        elif 270 <= angle <= 360:
            indice_x = 1
            indice_y = 0
        else:
            print("Angle should be between 0 to 360 degrees")
            return

        radian = angle * math.pi / 180
        distance_x = abs(int(math.cos(radian) * distance))
        distance_y = abs(int(math.sin(radian) * distance))
        msg = ("<avpx" + str(indice_x) + str(distance_x) +
               "y" + str(indice_y) + str(distance_y) + "r>")
        self._send_msg(msg)

    def list_order(self, ilo_list: list):
        """
        ilo will execute a list of successive moves defined in ilo_list

        Parameters
        ----------
            ilo_list : list of str
                List of possible moves: front, back, left, right, rot_trigo, rot_clock, stop

        Raises:
            TypeError: If ilo_list is not a list

        Examples:
            my_ilo.list_order(['front', 'left', 'front', 'rot_trigo', 'back'])
        """
        if isinstance(ilo_list, list) == False:
            print('ilo_list should be a list')
            return None

        for i in range(len(ilo_list)):
            self.step(ilo_list[i])

    def move(self, direction: str, speed: int, acc: int):
        """
        Move ilo with selected direction and speed

        Parameters:
            direction (str): The direction in which the robot is moving
            speed (int): The speed of the robot, as a percentage
            acceleration (int): Between 1 to 100, the higher the value, the faster the robot will reach the selected speed

        Raises:
            TypeError: If the direction is not a string
            ValueError: If the direction is not one of the following: front, back, left, right, rot_trigo, rot_clock or stop
            TypeError: If the speed is not an integer
            ValueError: If the speed is not between 0 and 100
            TypeError: If the acc is not an integer
            ValueError: If the acc is not between 1 and 100

        Examples:
            my_ilo.move("front", 50, 100)
        """

        # ilo.move('front', 50)

        # global preview_stop
        # preview_stop = True

        if not isinstance(direction, str):
            print("[ERROR] 'direction' parameter must be a string")
            return None
        if not isinstance(speed, int):
            print("[ERROR] 'speed' parameter must be a integer")
            return None
        if not isinstance(acc, int):
            print("[ERROR] 'acc' parameter must be a integer")
            return None

        if speed > 100 or speed < 0:
            print("[ERROR] 'speed' parameter must be include between 0 to 100")
            return None

        if acc > 100 or acc < 1:
            print("[ERROR] 'acc' parameter must be include between 1 to 100 ")
            return None

        acc = acc * 2
        self.set_acc_motor(acc)

        if direction == 'front':
            command = [int((speed*1.27)+128), 128, 128]
        elif direction == 'back':
            command = [int(-(speed*1.27))+128, 128, 128]
        elif direction == 'right':
            command = [128, int((speed*1.27)+128), 128]
        elif direction == 'left':
            command = [128, int(-(speed*1.27)+128), 128]
        elif direction == 'rot_trigo':
            command = [128, 128, int(-(speed*1.27)+128)]
        elif direction == 'rot_clock':
            command = [128, 128, int((speed*1.27)+128)]
        else:
            print(
                "[ERROR] 'direction' parameter should be 'front', 'back', 'left', 'rot_trigo', 'rot_clock', 'stop'")
            return None

        corrected_command = self._correction_command(acc, command)
        self._send_msg(corrected_command)

    def direct_control(self, acc: int, axial: int, radial: int, rotation: int):
        """
        Control ilo with full control \n
        Value from 0 to 128 are negative and value from 128 to 255 are positive

        Parameters:
            acc (int): acceleration
            axial (int): axial speed
            radial (int): radial speed
            rotation (int): rotation speed

        Raises:
            TypeError: If acc is not an integer
            ValueError: If acc is not between 1 and 200
            TypeError: If axial is not an integer
            ValueError: If axial is not between 0 and 255
            TypeError: If radial is not an integer
            ValueError: If radial is not between 0 and 255
            TypeError: If rotation is not an integer
            ValueError: If rotation is not between 0 and 255

        Examples:
            my_ilo.direct_control(100, 180, 128, 128)
        """

        if not isinstance(acc, int):
            print("[ERROR] 'acc' parameter must be a integer")
            return None
        if acc > 200 or acc < 1:
            print("[ERROR] 'acc' parameter must be include between 1 to 200 ")
            return None
        if not isinstance(axial, int):
            print("[ERROR] 'axial' parameter must be a integer")
            return None
        if axial > 255 or axial < 0:
            print("[ERROR] 'axial' parameter must be include between 0 and 255")
            return None
        if not isinstance(radial, int):
            print("[ERROR] 'radial' parameter must be a integer")
            return None
        if radial > 255 or radial < 0:
            print("[ERROR] 'radial' parameter must be include between 0 and 255")
            return None
        if not isinstance(rotation, int):
            print("[ERROR] 'rotation' parameter must be a integer")
            return None
        if rotation > 255 or rotation < 0:
            print("[ERROR] 'rotation' parameter must be include between 0 and 255")
            return None

        command = [axial, radial, rotation]
        corrected_command = self._correction_command(acc, command)
        self._send_msg(corrected_command)

    def game(self):
        """
        Control ilo using arrow or numb pad of your keyboard. \n
        Available keyboard touch: 8,2,4,6,1,3 | space = stop | esc = quit

        Raises:
            ConnectionError: If you are not connected to ilo

        Examples:
            my_ilo.game()
        """

        print("Game mode start, use keyboard arrow to control ilo")
        if self.test_connection() == True:
            # self.set_acc_motor(200)
            acc = 200
            axial_value = 128
            radial_value = 128
            rotation_value = 128
            self.stop()
            new_keyboard_instruction = False

            kb = KeyboardCrossplatform()
            print('Game mode start, use keyboard arrow to control ilo')
            print("Press echap to leave the game mode")
            kb.start()

            while True:
                key = kb.get_key()
                print("->", key)

                if key == "8" or key == "f7":
                    new_keyboard_instruction = True
                    axial_value = axial_value + 5
                    if axial_value > 255:
                        axial_value = 255
                elif key == "2" or key == "f20":
                    new_keyboard_instruction = True
                    axial_value = axial_value - 5
                    if axial_value < 1:
                        axial_value = 0
                elif key == "6" or key == "kp_add":
                    new_keyboard_instruction = True
                    radial_value = radial_value + 5
                    if radial_value > 255:
                         radial_value = 255
                elif key == "4" or key == "kp_multiply":
                    new_keyboard_instruction = True
                    radial_value = radial_value - 5
                    if radial_value < 1:
                        radial_value = 0
                elif key == "3" or key == "kp_divide":
                    new_keyboard_instruction = True
                    rotation_value = rotation_value + 5
                    if rotation_value > 255:
                        rotation_value = 255
                elif key == "1" or key == "f19":
                    new_keyboard_instruction = True
                    rotation_value = rotation_value - 5
                    if rotation_value < 1:
                        rotation_value = 0
                elif key == "5" or key == "kp_subtract":
                    new_keyboard_instruction = True
                    axial_value = 128
                    radial_value = 128
                    rotation_value = 128
                elif key == "esc":
                    print("Game mode stop")
                    self.stop()
                    kb.stop()
                    break
                #else:
                    #print("Invalid key", key)

                if new_keyboard_instruction == True:
                    self.direct_control(acc, axial_value, radial_value, rotation_value)
                    new_keyboard_instruction = False
        else:
            print("You have to be connected to ILO before play with it, use ilo.connection()")

    def set_tempo_pos(self, value: int):
        """
        Set the tempo of the position control

        Parameters:
            value (int): new tempo value

        Raises:
            TypeError: If value is not an integer

        Examples:
            my_ilo.set_tempo_pos(50)
        """

        if not isinstance(value, int):
            print("[ERROR] 'value' parameter must be a integer")
            return None

        msg = f"<690t{value}>"
        self._send_msg(msg)

    def get_tempo_pos(self):
        """
        Get the tempo of the position control
        """
        self._send_msg("<691>")
        self._response_event.wait(timeout=5)
        return (self._tempo_pos)

    def rotation(self, angle: Union[int, float], finish_state=True, display_led: bool=True):
        """
        Rotate ilo with selected angle

        Parameters:
            angle (int): The rotation angle in degrees, positive for clockwise, negative for counterclockwise
                        (or in radians if a float is provided)

        Raises:
            TypeError: If 'angle' is not an integer or a float

        Examples:
            my_ilo.rotation(90) \n
            my_ilo.rotation(-50)\n
            my_ilo.rotation('pi/2')    # 90 degrés\n
            my_ilo.rotation(math.pi)   # 180 degrés\n
            my_ilo.rotation(3.14)      # 180 degrés\n
        """
    
        # Check if angle is in radians
        if isinstance(angle, float):
            angle = int(math.degrees(angle))
            print(f"[INFO] Conversion: {angle}°")

        elif not isinstance(angle, int):
            print("[ERROR] 'angle' should be an integer or a float")
            return None

        if angle > 0:
            indice = 1
        else:
            indice = 0

        if not isinstance(display_led, bool):
            print ("[ERROR] 'display_led' should be a boolean")
            return None

        if display_led:
            self._send_msg("<avpxyr" + str(indice) + str(abs(angle)) + "t>")
        else:
            self._send_msg("<avpxyr" + str(indice) + str(abs(angle)) + "f>")

        # command = ("<avpxyr" + str(indice) + str(abs(angle)) + ">")
        # self._send_msg(command)

        if finish_state == True:
            # Clear the event before waiting
            self._movement_complete.clear()
            
            # Calculate timeout based on rotation angle
            # Base timeout: 2.459s for 90° rotation, scale proportionally
            # Formula: timeout = (2.459 * angle / 90) + 1.0
            actual_angle = abs(angle) / 45
            timeout = (2.5 * actual_angle) + 3.0
            
            if self._debug:
                print(f"Waiting for end of rotation (angle: {angle}°, timeout: {timeout:.2f}s)...")
            
            # Wait for the "avp0" frame indicating movement completion
            movement_finished = self._movement_complete.wait(timeout=timeout)
            
            if self._debug:
                if movement_finished:
                    print("Rotation completed successfully.")
                else:
                    print("[WARNING] Rotation completion timeout - frame may have been lost.")
            
            return movement_finished

    def set_pid(self, kp: int, ki: int, kd: int):
        """
        Set the new value of the proportional gain, the integral gain and the derivative gain

        Parameters:
            p (int): new value of the proportional gain
            i (int): new value of the integral gain
            d (int): new value of the derivative gain

        Raises:
            TypeError: If 'p' is not an integer or a float
            ValueError: If 'p' is not between 0.1 and 10
            TypeError: If 'i' is not an integer or a float
            ValueError: If 'i' is not between 0.1 and 10
            TypeError: If 'd' is not an integer or a float
            ValueError: If 'd' is not between 0.1 and 10

        Examples:
            my_ilo.set_pid(5, 5, 5)
        """

        if not isinstance(kp, (int, float)):
            print("[ERROR] 'kp' parameter must be a integer or a float")
            return None
        if kp > 10 or kp < 0:
            print("[ERROR] 'kp' parameter must be include between 0 and 10")
            return None

        if not isinstance(ki, (int, float)):
            print("[ERROR] 'ki' parameter must be a integer or a float")
            return None
        if ki > 10 or ki < 0:
            print("[ERROR] 'ki' parameter must be include between 0 and 10")
            return None

        if not isinstance(kd, (int, float)):
            print("[ERROR] 'kd' parameter must be a integer or a float")
            return None
        if kd > 10 or kd < 0:
            print("[ERROR] 'kd' parameter must be include between 0 and 10")
            return None

        kp = int(kp * 100)
        ki = int(ki * 100)
        kd = int(kd * 100)

        msg = f"<70p{kp}i{ki}d{kd}>"
        self._send_msg(msg)

    def get_pid(self):
        """
        Get the actual value of the proportional gain, the integral gain and the derivative gain
        """
        self._send_msg("<71>")
        self._response_event.wait(timeout=5)
        return (self._kp, self._ki, self._kd)
    # -----------------------------------------------------------------------------
    def get_color_rgb_center(self):
        """
        Displays the color below ilo
        """
        self._send_msg("<10c>")
        self._response_event.wait(timeout=5)

        return (self._red_color_center, self._green_color_center, self._blue_color_center)

    def get_color_rgb_left(self):
        """
        Displays the color below ilo only with left sensor
        """
        self._send_msg("<10l>")
        self._response_event.wait(timeout=5)

        return (self._red_color_left, self._green_color_left, self._blue_color_left)

    def get_color_rgb_right(self):
        """
        Displays the color below ilo only with left sensor
        """
        self._send_msg("<10d>")
        self._response_event.wait(timeout=5)

        return (self._red_color_right, self._green_color_right, self._blue_color_right)

    def get_color_card(self, return_type: str="name"):
        """
        Detects the color of a card placed under ilo

        Parameters:
            return_type (str): "rgb" to get RGB values, "color" to get color name
        """

        rgb = self.get_color_rgb_center()
        r   = rgb[0]
        g   = rgb[1]
        b   = rgb[2]

        white_val  = abs(r - 190) + abs(g - 255) + abs(b - 252)
        orange_val = abs(r - 255) + abs(g - 234) + abs(b -  168)
        purple_val = abs(r - 250) + abs(g - 182) + abs(b - 255)
        light_blue_val  = abs(r - 86) + abs(g - 148) + abs(b -  255)
        yellow_val = abs(r - 220) + abs(g - 255) + abs(b -  165)
        green_val  = abs(r - 148) + abs(g - 255) + abs(b - 214)
        blue_val   = abs(r - 115) + abs(g - 140) + abs(b - 240)
        red_val    = abs(r - 255) + abs(g - 167) + abs(b -  163)
        black_val   = abs (r - 56) + abs(g - 73) + abs(g - 73)

        color = "white"
        mini_val = white_val

        if orange_val <= mini_val:
            mini_val = orange_val
            color = "orange"
        if purple_val <= mini_val:
            mini_val = purple_val
            color = "purple"
        if light_blue_val <= mini_val:
            mini_val = light_blue_val
            color = "light_blue"
        if yellow_val <= mini_val:
            mini_val = yellow_val
            color = "yellow"
        if green_val <= mini_val:
            mini_val = green_val
            color = "green"
        if blue_val <= mini_val:
            mini_val = blue_val
            color = "blue"
        if red_val <= mini_val:
            mini_val = red_val
            color = "red"
        if black_val <= mini_val:
            mini_val = black_val
            color = "black"

        if mini_val > 150:
            color = "None"

        if color == "white":
            rgb = (255, 255, 255)
        
        if color == "orange":
            rgb = (255, 76, 0)

        elif color == "purple":
            rgb = (182, 0, 255)

        elif color == "light_blue":
            rgb = (0, 255, 250)

        elif color == "yellow":
            rgb = (255, 255, 0)

        elif color == "green":
            rgb = (12, 255, 0)

        elif color == "blue":
            rgb = (0, 18, 255)

        elif color == "red":
            rgb = (255, 0, 3)
            
        elif color == "black":
            rgb = (0, 0, 0)
        
        elif color == "None":
            rgb = (0, 0, 0)

        if return_type == "rgb":
            return rgb
        elif return_type == "name":
            return color
        else:
            print("[ERROR] 'return_type' must be 'rgb' or 'name'")
            return None

    def set_led_captor(self, luminosity=200):
        """
        Turns on/off the lights under ilo

        Parameters:
            state (int): allows you to turn on or off the leds

        Raises:
            TypeError: If state is not a int

        Examples:
            my_ilo.set_led_captor(0) \n
            my_ilo.set_led_captor(200)\n
        """

        if isinstance(luminosity, bool):
            print("[ERROR] 'luminosity' parameter must be an integer, not a boolean")
            return None

        if not isinstance(luminosity, int):
            print("[ERROR] 'luminosity' parameter must be a integer")
            return None
        
        if luminosity < 0 or luminosity > 255:
            print("[ERROR] 'luminosity' parameter must be include between 0 to 255")
            return None

        msg = "<54l" + str(luminosity) + ">"
        self._send_msg(msg)
    # -----------------------------------------------------------------------------
    def get_color_clear(self):
        """
        Displays the brightness below ilo
        """
        self._send_msg("<11>")
        self._response_event.wait(timeout=5)
        return (self._clear_left, self._clear_center, self._clear_right)

    def get_color_clear_left(self):
        """
        Displays the brightness below ilo only with left sensor
        """
        self._send_msg("<11>")
        self._response_event.wait(timeout=5)
        return (self._clear_left)

    def get_color_clear_center(self):
        """
        Displays the brightness below ilo only with central sensor
        """
        self._send_msg("<11>")
        self._response_event.wait(timeout=5)
        return (self._clear_center)

    def get_color_clear_right(self):
        """
        Displays the brightness below ilo only with right sensor
        """
        self._send_msg("<11>")
        self._response_event.wait(timeout=5)
        return (self._clear_right)
    # -----------------------------------------------------------------------------
    def get_line(self):
        """
        Detects whether ilo is on a line or not
        """
        self._send_msg("<12>")
        self._response_event.wait(timeout=5)
        return (self._line_left, self._line_center, self._line_right)

    def get_line_left(self):
        """
        Detects whether ilo is on a line or not according to the left sensor
        """
        self._send_msg("<12>")
        self._response_event.wait(timeout=5)
        return (self._line_left)

    def get_line_center(self):
        """
        Detects whether ilo is on a line or not according to the central sensor
        """
        self._send_msg("<12>")
        self._response_event.wait(timeout=5)
        return (self._line_center)

    def get_line_right(self):
        """
        Detects whether ilo is on a line or not according to the right sensor
        """
        self._send_msg("<12>")
        self._response_event.wait(timeout=5)
        return (self._line_right)

    def set_line_threshold_value(self, value=None):
        """
        Set new threshold value for line detection (automatic or manual)

        Parameters:
            value (int, optional): new threshold value

        Raises:
            TypeError: If value is not an integer

        Examples:
            my_ilo.set_line_threshold_value()\n
            my_ilo.set_line_threshold_value(40)
        """

        if value is not None:

            if not isinstance(value, int):
                print("[ERROR] 'value' parameter must be a integer")
                return None

        else:
            self.set_led_captor(True)
            time.sleep(1)
            self._clear_center = 0
            self.get_color_clear()
            while self._clear_center == 0:
                time.sleep(0.1)
            value = round(self._clear_center*1.2)
            print(f"La nouvelle valeur de seuil est: {value}")
            self.set_led_captor(False)

        msg = f"<13tf{value}>"
        self._send_msg(msg)

    def get_line_threshold_value(self):
        """
        Get the actual value of the threshold value for the line detection
        """
        self._send_msg("<14>")
        self._response_event.wait(timeout=5)
        return (self._line_threshold_value)
    # -----------------------------------------------------------------------------
    def get_distance(self):
        """
        Get the distance around ilo
        """
        # self._response_event.clear()
        self._send_msg("<20>")
        # time.sleep(0.15)
        self._response_event.wait(timeout=5)
        return (self._distance_front, self._distance_right, self._distance_back, self._distance_left)

    def get_distance_front(self):
        """
        Get the distance in front of ilo
        """
        self._send_msg("<21>")
        self._response_event.wait(timeout=5)
        return (self._distance_front)

    def get_distance_right(self):
        """
        Get the distance on the right of ilo
        """
        self._send_msg("<22>")
        self._response_event.wait(timeout=5)
        return (self._distance_right)

    def get_distance_back(self):
        """
        Get the distance behind ilo
        """
        self._send_msg("<23>")
        self._response_event.wait(timeout=5)
        return (self._distance_back)

    def get_distance_left(self):
        """
        Get the distance on the left of ilo
        """
        self._send_msg("<24>")
        self._response_event.wait(timeout=5)
        return (self._distance_left)
    # -----------------------------------------------------------------------------
    def get_angle(self):
        """
        Get the angle of ilo
        """
        self._send_msg("<30>")
        self._response_event.wait(timeout=5)
        return (self._roll, self._pitch, self._yaw)

    def get_roll(self):
        """
        Get the roll angle of ilo
        """
        self._send_msg("<30>")
        self._response_event.wait(timeout=5)
        return (self._roll)

    def get_pitch(self):
        """
        Get the pitch angle of ilo
        """
        self._send_msg("<30>")
        self._response_event.wait(timeout=5)
        return (self._pitch)

    def get_yaw(self):
        """
        Get the yaw angle of ilo
        """
        self._send_msg("<30>")
        self._response_event.wait(timeout=5)
        return (self._yaw)

    def reset_angle(self):
        """
        Reset the angle of ilo
        """
        self._send_msg("<31>")

    def get_raw_imu(self):
        """
        Get IMU raw data
        """
        self._send_msg("<32>")
        self._response_event.wait(timeout=5)
        return (self._accX, self._accY, self._accZ, self._gyroX, self._gyroY, self._gyroZ)
    # -----------------------------------------------------------------------------
    def get_battery(self):
        """
        Get battery status (charged or not) and percentage
        """
        self._send_msg("<40>")
        self._response_event.wait(timeout=5)
        return (self._battery_status, self._battery_pourcentage)
    # -----------------------------------------------------------------------------
    def get_led_color(self):
        """
        Get ilo LEDS color
        """
        self._send_msg("<50>")
        self._response_event.wait(timeout=5)
        return (self._red_led, self._green_led, self._blue_led)

    def set_led_color(self, red: int, green: int, blue: int):
        """
        Set ilo LEDS color

        Parameters:
            red (int): the red value of the color
            green (int): the green value of the color
            blue (int): the blue value of the color

        Raises:
            TypeError: If red is not an integer
            ValueError: If red is not between 0 and 255
            TypeError: If green is not an integer
            ValueError: If green is not between 0 and 255
            TypeError: If blue is not an integer
            ValueError: If blue is not between 0 and 255

        Examples:
            my_ilo.set_led_color(128, 0, 128)
        """

        if not isinstance(red, int):
            print("[ERROR] 'red' parameter must be a integer")
            return None
        if red > 255 or red < 0:
            print("[ERROR] 'red' parameter must be include between 0 and 255")
            return None
        if not isinstance(green, int):
            print("[ERROR] 'green' parameter must be a integer")
            return None
        if green > 255 or green < 0:
            print("[ERROR] 'green' parameter must be include between 0 and 255")
            return None
        if not isinstance(blue, int):
            print("[ERROR] 'blue' parameter must be a integer")
            return None
        if blue > 255 or blue < 0:
            print("[ERROR] 'blue' parameter must be include between 0 and 255")
            return None

        msg = f"<51r{red}g{green}b{blue}>"
        self._send_msg(msg)

    def set_led_shape(self, value: str):
        """
        Show designs on LEDS

        Parameters:
            value (str): the shape of the leds

        Raises:
            TypeError: If value is not a string

        Examples:
            my_ilo.set_led_shape("smiley")
        """

        if not isinstance(value, str):
            print("[ERROR] 'value' parameter must be a string")
            return None

        msg = f"<52v{value}>"
        self._send_msg(msg)

    def set_led_anim(self, value: str, repeat=1):
        """
        Starting an animation with LEDs

        Parameters:
            value (str): led animation name
            repeat (int): number of times the animation will be repeated

        Raises:
            TypeError: If value is not a string
            TypeError: If repeat is not an integer
            ValueError: If repeat is not more than 0

        Examples:
            my_ilo.set_led_anim("wave")\n
            my_ilo.set_led_anim("wave", 3)
        """

        if not isinstance(value, str):
            print("[ERROR] 'value' parameter must be a string")
            return None
        if not isinstance(repeat, int):
            print("[ERROR] 'repeat' parameter must be a integer")
            return None
        if repeat < 1:
            print("[ERROR] 'repeat' parameter must be more than 0")
            return None

        msg =f"<53{value}/{repeat}>"
        self._send_msg(msg)

    def set_led_single(self, type: str, id: int, red: int, green: int, blue: int, luminosity=None):
        """
        Lights up an individual led in the led matrix

        Parameters:
            type (str): allows you to choose whether to light a led on the circle or on the center
            id (int): led number
            red (int): red value of the color
            green (int): green value of the color
            blue (int): blue value of the color

        Raises:
            TypeError: If type is not a string
            ValueError: If type is not "center" or "circle"
            TypeError: If id is not an integer
            TypeError: If red is not an integer
            ValueError: If red is not between 0 and 255
            TypeError: If green is not an integer
            ValueError: If green is not between 0 and 255
            TypeError: If blue is not an integer
            ValueError: If blue is not between 0 and 255

        Examples:
            my_ilo.set_led_single("center", 15, 255, 255, 255)
        """

        if not isinstance(type, str):
            print("[ERROR] 'type' parameter must be a string")
            return None
        if type != "center" and type != "circle":
            print("[ERROR] 'type' parameter must be center or circle")
            return None
        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None

        if not isinstance(red, int):
            print("[ERROR] 'red' parameter must be a integer")
            return None
        if red > 255 or red < 0:
            print("[ERROR] 'red' parameter must be include between 0 and 255")
            return None
        if not isinstance(green, int):
            print("[ERROR] 'green' parameter must be a integer")
            return None
        if green > 255 or green < 0:
            print("[ERROR] 'green' parameter must be include between 0 and 255")
            return None
        if not isinstance(blue, int):
            print("[ERROR] 'blue' parameter must be a integer")
            return None
        if blue > 255 or blue < 0:
            print("[ERROR] 'blue' parameter must be include between 0 and 255")
            return None

        if type == "center":
            type = "1"
        if type == "circle":
            type = "0"

        if luminosity is not None:
            if not isinstance(luminosity, int):
                print("[ERROR] 'luminosity' parameter must be a integer")
                return None
        else:
            luminosity = 100

        msg = f"<55t{type}d{id}r{red}g{green}b{blue}l{luminosity}>"
        self._send_msg(msg)
    
    def set_led_word(self, type: str, word: str, delay=None):
        """
        Show your word with the robot leds.

        Parameters:
            type (str): allows you to choose whether to display your word letter by letter or with the letters sliding in a continuous flow.
            word (str): the word you want to display.
            delay (int): not required, allows you to choose the delay for the appearance or slide of your word (in milliseconds)

        Raises:
            TypeError: If type is not a string
            ValueError: If type is not "reveal" or "slide"
            TypeError: If word is not a string

        Examples:
            my_ilo.set_led_word("reveal", "Hello")\n
            my_ilo.set_led_word("slide", "robot", 300)
        """

        if not isinstance(type, str):
            print("[ERROR] 'type' parameter must be a string")
            return None
        if type != "reveal" and type != "slide":
            print("[ERROR] 'type' parameter must be reveal or slide")
            return None
        if not isinstance(word, str):
            print("[ERROR] 'word' parameter must be a string")
            return None
        
        if len(word) > 10:
            print("[ERROR] 'word' parameter must not exceed 10 characters")
            return None
    
        if type == "reveal" and delay == None:
            delay = 1000
        if type == "slide" and delay == None:
            delay = 300

        if not isinstance(delay, int):
            print("[ERROR] 'delay' parameter must be a integer")
            return None

        if delay > 2000 or delay < 10:
            print("[ERROR] 'delay' parameter must be include between 10 and 2000")
            return None

        if type == "reveal":
            msg = f"<56w{word.upper()}d{delay}/1>"
        else:
            msg = f"<57w{word.upper()}d{delay}/1>"
        self._send_msg(msg)
    
    def stop_led_word(self):
        """
        Stop the led word
        """
        self._send_msg("<58>")
    # -----------------------------------------------------------------------------
    def get_acc_motor(self):
        """
        Get the acceleration of all motors 
        """
        self._send_msg("<681>")
        self._response_event.wait(timeout=5)
        return (self._acc_motor)

    def set_acc_motor(self, acc: int):
        """
        Set the acceleration of all motors

        Parameters:
            value (int): the acceleration value

        Raises:
            TypeError: If value is not an integer
            ValueError: If value is not between 10 and 200

        Examples:
            my_ilo.set_acc_motor(67)
        """

        if not isinstance(acc, int):
            print("[ERROR] 'value' parameter must be a integer")
            return None
        if acc > 200 or acc < 1:
            print("[ERROR] 'acc' parameter must be include between 1 and 200")
            return None

        if acc < 1:
            acc = 1
        elif acc > 200:
            acc = 200
        msg = f"<680a{acc}>"
        self._send_msg(msg)
    # -----------------------------------------------------------------------------
    # <60i1s1>
    def ping_single_motor(self, id: int):
        """
        Ping a single motor with is id

        Parameters:
            id (int): motor id

        Raises:
            TypeError: If id is not an integer
            ValueError: If id is not between 0 and 255

        Examples:
            my_ilo.ping_single_motor(1)
        """

        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None
        if id > 255 or id < 0:
            print("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = f"<60i{id}>"
        self._send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self._motor_id, self._motor_ping)
    # <610i1v3000>
    def drive_single_motor_speed(self, id: int, acc: int, vel: int):
        """
        Drive a single motor in speed with is id

        Parameters:
            id (int): the motor id
            acc(int): motor acc
            vel (int): the motor speed in percentage

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255
            TypeError: If 'acc' is not an integer
            ValueError: If 'acc' is not between 0 and 200
            TypeError: If 'vel' is not an integer
            ValueError: If 'vel' is not between -100 and 100

        Examples:
            my_ilo.drive_single_motor_speed(1, 100, 50)
        """

        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None
        if id > 255 or id < 0:
            print("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        if not isinstance(vel, int):
            print("[ERROR] 'vel' parameter must be a integer")
            return None
        if vel > 100 or vel < -100:
            print("[ERROR] 'vel' parameter must be include between -100 and 100")
            return None

        if not isinstance(acc, int):
            print("[ERROR] 'acc' parameter must be a integer")
            return None
        if acc > 200 or acc < 0:
            print("[ERROR] 'acc' parameter must be include between 1 and 200")
            return None

        msg = f"<610i{id}a{acc}v{vel}>"
        self._send_msg(msg)

    def drive_single_motor_speed_front_left(self, value: int, vel: int):  # de -100 à 100
        """
        Control the front left motor

        Parameters:
            value (int): the motor speed in percentage

        Raises:
            TypeError: If 'value' is not an integer

        Examples:
            my_ilo.drive_single_motor_speed_front_left(50)
        """
        if not isinstance(value, int):
            print("[ERROR] 'value' parameter must be a integer")
            return None

        self.drive_single_motor_speed(1, value, vel)

    def drive_single_motor_speed_front_right(self, value: int, vel: int):
        """
        Control the front right motor

        Parameters:
            value (int): the motor speed in percentage

        Raises:
            TypeError: If 'value' is not an integer

        Examples:
            my_ilo.drive_single_motor_speed_front_right(50)
        """
        if not isinstance(value, int):
            print("[ERROR] 'value' parameter must be a integer")
            return None

        self.drive_single_motor_speed(2, value, vel)

    def drive_single_motor_speed_back_left(self, value: int, vel: int):
        """
        Control the back left motor

        Parameters:
            value (int): the motor speed in percentage

        Raises:
            TypeError: If 'value' is not an integer

        Examples:
            my_ilo.drive_single_motor_speed_back_left(50)
        """

        if not isinstance(value, int):
            print("[ERROR] 'value' parameter must be a integer")
            return None

        self.drive_single_motor_speed(4, value, vel)

    def drive_single_motor_speed_back_right(self, value: int, vel: int):
        """
        Control the back right motor

        Parameters:
            value (int): the motor speed in percentage

        Raises:
            TypeError: If 'value' is not an integer

        Examples:
            my_ilo.drive_single_motor_speed_back_right(50)
        """

        if not isinstance(value, int):
            print("[ERROR] 'value' parameter must be a integer")
            return None

        self.drive_single_motor_speed(3, value, vel)
    # <611i1s3000>
    def get_single_motor_speed(self, id: int):
        """
        Get the speed of a single motor with is id

        Parameters:
            id (int): the motor whose speed you want to know

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255

        Examples:
            my_ilo.get_single_motor_speed(3)
        """

        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None
        if id > 255 or id < 0:
            print("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = f"<611i{id}>"
        self._send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self._motor_id, self._motor_speed)
    # <620i6a100v100p90>
    def drive_single_motor_angle(self, id: int, acc: int, vel: int, pos: int):
        """
        Drive a single motor in angle with is id

        Parameters:
            id (int): the motor id
            acc (int): accereleration
            vel (int): velocity
            pos (int): the motor angle

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255
            TypeError: If 'acc' is not an integer
            ValueError: If 'acc' is not between 1 and 200
            TypeError: If 'vel' is not an integer
            ValueError: If 'vel' is not between -7000 and 7000 
            TypeError: If 'pos' is not an integer
            ValueError: If pos' is not between 0 and 4096

        Examples:
            my_ilo.drive_single_motor_speed(1,20,40,1024)
        """

        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None
        if id > 255 or id < 0:
            print("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        if not isinstance(acc, int):
            print("[ERROR] 'acc' parameter must be a integer")
            return None
        if acc > 200 or acc < 0:
            print("[ERROR] 'acc' parameter must be include between 0 and 200")
            return None

        if not isinstance(vel, int):
            print("[ERROR] 'vel' parameter must be a integer")
            return None
        if vel >= 7000 or vel <= -7000:
            print("[ERROR] 'vel' parameter must be include between -7000 and 7000")
            return None

        if not isinstance(pos, int):
            print("[ERROR] 'pos' parameter must be a integer")
            return None
        if pos > 4096 or pos < 0:
            print("[ERROR] 'pos' parameter must be include between 0 and 4096")
            return None

        msg = f"<620i{id}a{acc}v{vel}p{pos}>"
        self._send_msg(msg)
    # <621i6a90>
    def get_single_motor_angle(self, id: int):
        """
        Get the angle of a single motor with is id

        Parameters:
            id (int): the motor whose angle you want to know

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255

        Examples:
            my_ilo.get_single_motor_angle(2)
        """

        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None
        if id > 255 or id < 0:
            print("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = f"<621i{id}>"
        self._send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self._motor_id, self._motor_angle)
    # <63i1t45>
    def get_temp_single_motor(self, id: int):
        """
        Get the temperature of a single motor with is id

        Parameters:
            id (int): the motor whose temperature you want to know

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255

        Examples:
            my_ilo.get_temp_single_motor(1)
        """

        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None
        if id > 255 or id < 0:
            print("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = f"<63i{id}>"
        self._send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self._motor_id, self._temp_motor)
    # <64i1v6.7>
    def get_volt_single_motor(self, id: int):
        """
        Get the voltage of a single motor with is id

        Parameters:
            id (int): the motor whose voltage you want to know

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255

        Examples:
            my_ilo.get_volt_single_motor(1)
        """

        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None
        if id > 255 or id < 0:
            print("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = f"<64i{id}>"
        self._send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self._motor_id, self.volt_motor)
    # <65i1t20>
    def get_torque_single_motor(self, id: int):
        """
        Get the torque of a single motor with is id

        Parameters:
            id (int): the motor whose torque you want to know

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255

        Examples:
            my_ilo.get_torque_single_motor(1)
        """

        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None
        if id > 255 or id < 0:
            print("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = f"<65i{id}>"
        self._send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self._motor_id, self._motor_torque)
    # <66i1c20>
    def get_current_single_motor(self, id: int):
        """
        Get the current of a single motor with is id

        Parameters:
            id (int): the motor whose current you want to know

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255

        Examples:
            my_ilo.get_current_single_motor(1)
        """

        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None
        if id > 255 or id < 0:
            print("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = f"<66i{id}>"
        self._send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self._motor_id, self.current_motor)
    # <67i1s20>
    def get_motor_is_moving(self, id: int):
        """
        Get the state of a single motor with is id

        Parameters:
            id (int): the motor whose state you want to know

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255

        Examples:
            my_ilo.get_motor_is_moving(1)
        """

        if not isinstance(id, int):
            print("[ERROR] 'id' parameter must be a integer")
            return None
        if id > 255 or id < 0:
            print("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = f"<67i{id}>"
        self._send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self._motor_id, self.motor_moving)

    def set_motor_mode(self, motor_id, mode):
        """This legacy function has been removed."""
        pass

    # -----------------------------------------------------------------------------
    def set_autonomous_mode(self, value: str):
        """
        Launch ilo in an autonomous mode

        Parameters:
            value (str): the autonomous mode you want to launch

        Raises:
            TypeError: If value is not a string

        Examples:
            my_ilo.set_autonomous_mode("distance_displacement")
        """

        if not isinstance(value, str):
            print("[ERROR] 'value' parameter must be a string")
            return None

        msg = f"<80{value}>"
        self._send_msg(msg)
    # -----------------------------------------------------------------------------
    def set_wifi_credentials(self, ssid: str, password: str):
        """
        Enter your wifi details to enable ilo to connect to your network

        Parameters:
            ssid (str): the name of your wifi network
            password (str): the password of your wifi network

        Raises:
            TypeError: If ssid is not a string
            TypeError: If password is not a string

        Examples:
            my_ilo.set_wifi_credentials("my_wifi", "my_password")
        """

        if not isinstance(ssid, str):
            print("[ERROR] 'ssid' parameter must be a string")
            return None

        if not isinstance(password, str):
            print("[ERROR] 'password' parameter must be a string")
            return None

        msg = f"<90{ssid}{{|||}}{password}>"
        self._send_msg(msg)

    def get_wifi_credentials(self):
        """
        Get wifi credentials registered on ilo
        """
        self._send_msg("<92>")
        self._response_event.wait(timeout=5)
        return (self._ssid, self._password)
    
    def _parse_credentials(self, data: str):
        """
        Parse the wifi credentials from the response data

        Parameters:
            data (str): the response data from ilo

        Returns:
            tuple: a tuple containing the ssid and password
        """
        try:
            inner = data[3:-1]
            ssid, password = inner.split("{|||}")
            ssid = ssid.strip()
            password = password.strip()
            return ssid, password
        except ValueError:
            print("[ERROR] Failed to parse wifi credentials")
            return None, None
    # -----------------------------------------------------------------------------
    def set_name(self, name: str):  # going to be change by <93n>
        """
        Set a new name for your ilo

        Parameters:
            name (str): the name you want for your ilo

        Raises:
            TypeError: If name is not a string

        Examples:
            my_ilo.set_name("Marin_ilo")
        """

        if not isinstance(name, str):
            print("[ERROR] 'name' parameter must be a string")
            return None

        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if unicodedata.category(c) != "Mn") # remove accents

        name = name.lower()
        name = name.replace(" ", "_")
        name = re.sub(r"[^a-z0-9_]", "", name)

        msg = f"<94n{name}>"
        self._send_msg(msg)

    def get_name(self):
        """
        Get the name you have given to your ilo
        """
        self._send_msg("<93>")
        self._response_event.wait(timeout=5)
        return (self._hostname)
    # -----------------------------------------------------------------------------
    def get_accessory_data(self):
        """
        Get data from the accessory connected to ilo
        """
        self._send_msg("<100>")
        self._response_event.wait(timeout=5)
        return (self._accessory)
    
    def get_accessory(self):
        """
        Get information about the accessory connected to ilo
        """
        self._send_msg("<101>")
        self._response_event.wait(timeout=5)
        return (self._accessory)
    # -----------------------------------------------------------------------------
    def set_debug_state(self, state: bool):

        if not isinstance(state, bool):
            print("[ERROR] 'state' parameter must be a bool like True or False")
            return None

        if state == True:
            msg = "<103s1>"
        else:
            msg = "<103s2>"

        self._send_msg(msg)
    # -----------------------------------------------------------------------------
    def start_trame_s(self, hertz: int, param_list: list):
        """
        Start the global trame of ilo

        Parameters:
            hertz (int): the frequency of the trame
            param_list (list): the parameters you want to get
                - color
                - luminosity
                - distance
                - distance_front
                - distance_right
                - distance_back
                - distance_left
                - accessory_angle

        Raises:
            TypeError: If hertz is not an integer
            ValueError: If hertz is not between 1 and 1000
            TypeError: If param_list is not a list
            ValueError: If param_list is empty
            TypeError: If param_list contains non-string elements
            ValueError: If param_list contains invalid parameter names

        Examples:
            my_ilo.start_trame_s(100, ["color", "luminosity"])
        """

        if not isinstance(hertz, int):
            print("[ERROR] 'hertz' parameter must be a integer")
            return None
        if hertz > 100 or hertz < 1:
            print("[ERROR] 'hertz' parameter must be include between 1 and 1000")
            return None
        if not isinstance(param_list, list):
            print("[ERROR] 'param_list' parameter must be a list")
            return None
        if len(param_list) == 0:
            print("[ERROR] 'param_list' parameter must not be empty")
            return None
        if not all(isinstance(item, str) for item in param_list):
            print("[ERROR] 'param_list' parameter must be a list of strings")
            return None

        valid_params = {
            "color",
            "clearance",
            "distance",
            "distance_front",
            "distance_right",
            "distance_back",
            "distance_left",
            "accessory_angle"
        }
        invalid_params = [item for item in param_list if item not in valid_params]
        if invalid_params:
            print(f"[ERROR] 'param_list' contains invalid parameters: {invalid_params}")
            return None

        msg = f"<0h{hertz}z/"

        if "color" in param_list:
            msg = msg + "10/"
        if "clearance" in param_list:
            msg = msg + "11/"
        if "distance" in param_list:
            msg = msg + "20/"
        if "distance_front" in param_list:
            msg = msg + "21/"
        if "distance_right" in param_list:
            msg = msg + "22/"
        if "distance_back" in param_list:
            msg = msg + "23/"
        if "distance_left" in param_list:
            msg = msg + "24/"

        if "accessory_angle" in param_list:
            msg = msg + "100/"

        msg = msg + ">"

        self._send_msg(msg)

    def stop_trame_s(self):
        """
        Stop the global trame
        """
        self._send_msg("<00>")
    # -----------------------------------------------------------------------------
    def get_diagnostic(self):
        """
        Get a diagnosis of robot status
        """
        self._send_msg("<110>")
    # -----------------------------------------------------------------------------
    def set_manufacturing_date(self, date: str):
        """
        Set the manufacturing date of ilo
        """
        msg = f"<121s{date}>"
        self._send_msg(msg)

    def get_manufacturing_date(self):
        """
        Get the manufacturing date of ilo
        """
        self._send_msg("<120>")
        self._response_event.wait(timeout=5)
        return (self._manufacturing_date)

    def set_first_use_date(self, date: str):
        """
        Set the first use date of ilo
        """
        msg = f"<131s{date}>"
        self._send_msg(msg)

    def get_first_use_date(self):
        """
        Get the first use date of ilo
        """
        self._send_msg("<130>")
        self._response_event.wait(timeout=5)
        return (self._first_use_date)

    def set_product_version(self, version: str):
        """
        Set the version of the product
        """
        msg = f"<141s{version}>"
        self._send_msg(msg)

    def get_product_version(self):
        """
        Get the version of the product
        """
        self._send_msg("<140>")
        self._response_event.wait(timeout=5)
        return (self._product_version)

    def set_product_id(self, id: str):
        """
        Set the id of the product
        """
        msg = f"<151s{id}>"
        self._send_msg(msg)

    def get_product_id(self):
        """
        Get the id of the product
        """
        self._send_msg("<150>")
        self._response_event.wait(timeout=5)
        return (self._product_id)

    def get_robot_version(self):
        """
        Get the version number of the code present on the robot
        """
        self._send_msg("<500y>")
        self._response_event.wait(timeout=5)
        return (self._version)
    
    def draw_distance(self, distance="front", xmax=100, ymax=600):
        """
        draw_distance("front", "Distance Front", 100, 650):
        """
        if (distance == "front"):
            label = "Distance front (mm)"
            self.start_trame_s(10, ["distance_front"])
            
        elif (distance == "right"): 
            label = "Distance right (mm)"
            self.start_trame_s(10, ["distance_right"])
            
        elif (distance == "back"):  
            label = "Distance back (mm)"
            self.start_trame_s(10, ["distance_back"])
            
        elif (distance == "left"):  
            label = "Distance left (mm)"
            self.start_trame_s(10, ["distance_left"])
        else: 
            return None
        
        if not matplotlib.get_backend().lower().startswith("tk"):
            matplotlib.use("tkagg")
        plt.ion()
        fig, ax = plt.subplots()
        fig.canvas.manager.set_window_title("Draw_distance ILO ROBOT")
        plt.show(block=False)
    
        line, = ax.plot([], [], 'r-', linewidth=2)
        ax.set_ylim(0, ymax)
        ax.set_xlim(0, xmax)
        
        ax.set_ylabel(label)
        ax.set_title("Live Sensor Data")
    
        value_text = ax.text(0.5, 0.95, "", transform=ax.transAxes,
                             ha="center", va="top", fontsize=20,
                             weight='bold', bbox=dict(facecolor='white', alpha=0.8))
    
        xdata, ydata = [], []
        i = 0
    
        print("Close the window or CTRL+C to stop the display")
    
        try:
            while plt.fignum_exists(fig.number):
                if (distance == "front"):   val = self._distance_front
                elif (distance == "right"): val = self._distance_right
                elif (distance == "back"):  val = self._distance_back
                elif (distance == "left"):  val = self._distance_left

                xdata.append(i)
                ydata.append(val)
                xdata = xdata[-100:]
                ydata = ydata[-100:]
    
                x_smooth = np.linspace(xdata[0], xdata[-1], 200)
                y_smooth = np.interp(x_smooth, xdata, ydata)
    
                line.set_data(x_smooth, y_smooth)
                ax.set_xlim(max(0, i - xmax), i + 1)
                value_text.set_text(f"{val:.1f}")
    
                ax.figure.canvas.draw()
                ax.figure.canvas.flush_events()
                i += 1
            self.stop_trame_s()
    
        except KeyboardInterrupt:
            plt.ioff()
            plt.show()
            plt.close()
            self.stop_trame_s()
            
    def draw_all_distance(self, xmax=100, ymax=600):
        """
        Displays 4 live distance plots: front, back, left, right.
        """
        #self.start_trame_s(10, ["distance"])
    
        if not matplotlib.get_backend().lower().startswith("tk"):
            matplotlib.use("tkagg")
    
        plt.ion()
        fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
        fig.canvas.manager.set_window_title("Draw_all_distance ILO ROBOT")
        plt.show(block=False)
    
        directions = ["front", "back", "left", "right"]
        ax_map = {
            "front": axes[0, 0],
            "back":  axes[0, 1],
            "left":  axes[1, 0],
            "right": axes[1, 1]
        }
    
        line_map = {}
        value_text_map = {}
        xdata, ydata_map = [], {key: [] for key in directions}
    
        for key in directions:
            ax = ax_map[key]
            line, = ax.plot([], [], linewidth=2)
            ax.set_ylim(0, ymax)
            ax.set_ylabel(f"{key.capitalize()} (mm)")
            ax.set_title(f"{key.capitalize()} Distance")
            line_map[key] = line
            value_text_map[key] = ax.text(0.5, 0.95, "", transform=ax.transAxes,
                                          ha="center", va="top", fontsize=12,
                                          weight='bold', bbox=dict(facecolor='white', alpha=0.8))
    
        i = 0
        print("Close the window or CTRL+C to stop the display")
    
        try:
            while True:
                
                if not plt.get_fignums():
                    time.sleep(0.1)
                    
                    break
                val_map = {
                    "front": self._distance_front,
                    "back":  self._distance_back,
                    "left":  self._distance_left,
                    "right": self._distance_right
                }
    
                xdata.append(i)
                xdata = xdata[-100:]
    
                for key in directions:
                    ydata_map[key].append(val_map[key])
                    ydata_map[key] = ydata_map[key][-100:]
    
                    x_smooth = np.linspace(xdata[0], xdata[-1], 200)
                    y_smooth = np.interp(x_smooth, xdata, ydata_map[key])
    
                    line_map[key].set_data(x_smooth, y_smooth)
                    ax_map[key].set_xlim(max(0, i - xmax), i + 1)
                    value_text_map[key].set_text(f"{val_map[key]:.1f}")
    
                fig.canvas.draw()
                plt.pause(0.005)  #could be decrease
                i += 1
    
        except KeyboardInterrupt:
            plt.ioff()
            plt.show()
            plt.close()
           
    def draw_clearance(self, xmax=100, ymax=600):
        """
        Displays 3 live clearance plots: left, center, right,
        each with a constant threshold line.
        """
        self.get_line_threshold_value()
        self.start_trame_s(10, ["clearance"])
    
        if not matplotlib.get_backend().lower().startswith("tk"):
            matplotlib.use("tkagg")
    
        plt.ion()
        fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharex=True)
        fig.canvas.manager.set_window_title("Draw_clearance ILO ROBOT")
        plt.show(block=False)
    
        directions = ["left", "center", "right"]
        ax_map = {
            "left":   axes[0],
            "center": axes[1],
            "right":  axes[2]
        }
    
        line_map = {}
        value_text_map = {}
        xdata, ydata_map = [], {key: [] for key in directions}
    
        for key in directions:
            ax = ax_map[key]
            line, = ax.plot([], [], linewidth=2)
            ax.set_ylim(0, ymax)
            ax.set_ylabel(f"{key.capitalize()} (mm)")
            ax.set_title(f"{key.capitalize()} Clearance")
            ax.axhline(self._line_threshold_value, color='r', linestyle='--', linewidth=2)
            line_map[key] = line
            value_text_map[key] = ax.text(0.5, 0.95, "", transform=ax.transAxes,
                                          ha="center", va="top", fontsize=12,
                                          weight='bold', bbox=dict(facecolor='white', alpha=0.8))
    
        i = 0
        print("Close the window or CTRL+C to stop the display")
    
        try:
            while True:
                if not plt.get_fignums():
                    time.sleep(0.1)
                    self.stop_trame_s()
                    break
    
                val_map = {
                    "left": self._clear_left,
                    "center": self._clear_center,
                    "right": self._clear_right
                }
    
                xdata.append(i)
                xdata = xdata[-xmax:]
    
                for key in directions:
                    ydata_map[key].append(val_map[key])
                    ydata_map[key] = ydata_map[key][-xmax:]
    
                    x_smooth = np.linspace(xdata[0], xdata[-1], 200)
                    y_smooth = np.interp(x_smooth, xdata, ydata_map[key])
    
                    line_map[key].set_data(x_smooth, y_smooth)
                    ax_map[key].set_xlim(max(0, i - xmax), i + 1)
                    value_text_map[key].set_text(f"{val_map[key]:.1f}")
    
                fig.canvas.draw()
                plt.pause(0.005)
                i += 1
    
        except KeyboardInterrupt:
            print("Stopped by user.")
        finally:
            plt.ioff()
            plt.show()
            plt.close()
            self.stop_trame_s()


def robot(
    name: str | int,
    connect_with: ConnectionType | None = None,
    debug=False,
) -> Robot:
    if isinstance(name, int):
        raise ValueError("La création de robot par ID n'est plus possible.")

    candidate = find_in_candidates(name, use_connection_type=connect_with)
    if candidate is None:
        raise ValueError("Aucun robot correspondant")

    robot = Robot._robots_connected.get(candidate.address)
    if robot is not None:
        return robot

    return Robot(candidate, debug)


_is_handling_sigint = False


def handle_sigint(signal_number, frame):
    global _is_handling_sigint

    if _is_handling_sigint:
        return

    _is_handling_sigint = True
    print("Stopping all robot before quitting...")

    for r in Robot._robots_connected.copy().values():
        print(f"stopping {r}")
        r.disconnect()
    sys.exit(0)



if not IS_INTERACTIVE:
    signal.signal(signal.SIGINT, handle_sigint)
