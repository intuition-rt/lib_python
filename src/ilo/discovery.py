from __future__ import annotations

from enum import Enum
from typing import Any, Type
import serial.tools.list_ports
import serial
import socket
import websocket
from dataclasses import dataclass
import time
from prettytable import PrettyTable

from .ble_lib import ble_lib
from .color_encoding import base62_to_name, BASIC_COLOR_NAMES
from .copy_to_clipboard import copy_to_clipboard
from .net import get_broadcast_ip
from .transport import (
    Transport,
    BLETransport,
    SerialTransport,
    WiFiTransport
)
from .ws import _co_send_msg


__candidate_pool: dict[str, RobotCandidate] = {}
__last_ilo_id = 1


class ConnectionType(Enum):
    WIFI = 0
    BLUETOOTH = 1
    SERIAL = 2

    @property
    def transport_class(self) -> Type[Transport]:
        return {
            ConnectionType.WIFI: WiFiTransport,
            ConnectionType.SERIAL: SerialTransport,
            ConnectionType.BLUETOOTH: BLETransport,
        }[self]

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

    def get_transport(self) -> Transport:
        return self.connection_type.transport_class(self.address)


def get_all_candidates() -> tuple[RobotCandidate, ...]:
    """Retrieve a view of discovered robots available for connection."""
    return tuple(__candidate_pool.values())


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


def _generate_new_ilo_id() -> int:
    global __last_ilo_id

    __last_ilo_id += 1
    return __last_ilo_id - 1


def check_robot_on_wifi(ap_mode = True, timeout = 1):
    """
    Check the presence of the ilo(s) on the network
    """
    copy_to_clipboard("""my_ilo = ilo.robot(\"ilo\")""")
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
                                        "Unkown" if p == "?" else BASIC_COLOR_NAMES[int(p)]
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

        for _ in range(5):
            ser.write(b"<930>")
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
    copy_to_clipboard("""my_ilo = ilo.robot(\"ilo\")""")

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
    copy_to_clipboard('''my_ilo = ilo.robot(\"ilo\")''')

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


__all__ = (
    "ConnectionType",
    "RobotCandidate",
    "find_in_candidates",
    "get_all_candidates"
)
