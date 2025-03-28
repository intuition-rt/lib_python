# This python script is the library for using the robot ilo with python command on WiFi
# INTUITION ROBOTIQUE ET TECHNOLOGIES ALL RIGHT RESERVED
# 21/03/2025
# -----------------------------------------------------------------------------
import pyperclip
import serial.tools.list_ports
import serial
import math
import threading
import websocket
from keyboard_crossplatform import KeyBordCrossPlatform
import time
import re
import unicodedata
import asyncio
from bleak import BleakScanner, BleakClient
from prettytable import PrettyTable
import requests
import os
import psutil
import platform
import binascii
import concurrent.futures
# -----------------------------------------------------------------------------




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
        connected = await self.client.connect()
        if connected:
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
            print(f"🔔 Abonné aux notifications sur {char_uuid}")

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

            print("\n[UPDATE] Firmware sent, waiting for robot confirmation...")
            timeout = 60
            elapsed_time = 0
            while not self.update_complete and elapsed_time < timeout:
                await asyncio.sleep(1)
                elapsed_time += 1

            if not self.update_complete:
                print("[ERROR] No confirmation received, update may have failed.")
            else:
                print("[SUCCESS] Update successfully completed.")

        except Exception as e:
            print(f"Error: {e}")

    def _run_update(self):
        """Planifie la coroutine dans la boucle asyncio existante."""
        future = asyncio.run_coroutine_threadsafe(self.send_firmware(), self.loop)
        try:
            future.result()  # attend le résultat ou erreur
        except Exception as e:
            print(f"⚠️ Error in _run_update: {e}")

    def updateWithBT(self):
        """Lance l'update BLE dans un thread sans bloquer la boucle asyncio."""
        def run_with_priority():
            try:
                self._run_update()
            except Exception as e:
                print(f"⚠️ ERROR UPDATE WITH BT: {e}")

        thread = threading.Thread(target=run_with_priority, daemon=True)
        thread.start()

    def updateWithWS(self):
        """Lance l'update via WebSocket directement."""
        print("🟢 Sending the firmware via WebSocket.")
        self._run_update()

    def download_firmware(self, firmware_id):
        url = f"http://51.210.150.191:8001/api/firmwares/download/{firmware_id}/"
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
        global suspend_receive_msg
        print("Checking for online updates... Please wait.")
        
        try:
            requests.get("https://ilorobot.com", timeout=3)
        except requests.ConnectionError:
            print("No network connection. Skipping update check.")
            return
        try:
            req = requests.get("http://51.210.150.191:8001/api/firmwares/latest/", timeout=3)
            if req.status_code == 200:
                data = req.json()
                latest_version = data["version"]
                print(f"Latest version: {latest_version}")
                if latest_version != self.version:
                    suspend_receive_msg = True
                    print("A new update is available!")
                    update = input("Do you want to update your robot? (yes/no): ").strip().lower()
                    if update == "y" or update == "yes":
                        if self.download_firmware(data["id"]):
                            if self.use_ble:
                                self.updateWithBT()
                            else:
                                self.updateWithWS()
                    suspend_receive_msg = False
                else:
                    print("No updates available.")

            else:
                print("Failed to check for updates.")
        except Exception as e:
            print(f"⚠️ Impossible to check for updates :,(")

version = "0.52"

print("ilo robot library version: ", version)
print("For more information about the library use ilo.info() command line")
print("For any help or support contact us on our website, ilorobot.com")
# -----------------------------------------------------------------------------

pyperclip.copy("""ilo.check_robot_on_bluetooth()""")

_connection_type = 0
# WiFi
_tab_IP = []
# Serial
_tab_PORT = []
# BLE
_tab_ADDRESS = []

client = None
# -----------------------------------------------------------------------------


def info():
    """
    Print info about ilorobot
    """
    print("ilo robot is an education robot controlable by direct python command")
    print("To know every fonction available with ilo,  use ilo.list_function() command line")
    print("You are using the version ", version)
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
    ilo_table.add_row(["ilo.check_robot_on_network()",
                      "Scan the network for robots"], divider=True)
    ilo_table.add_row(
        ["ilo.list_function", "Print the list of all the functions available in the library"], divider=True)
    print(ilo_table)
    print("")
    my_ilo_table = PrettyTable()
    my_ilo_table.field_names = [
        "Object methods (example: my_ilo.test_connection())", "Description"]
    my_ilo_table.align["Object methods (example: my_ilo.test_connection())"] = "l"
    my_ilo_table.align["Description"] = "l"
    my_ilo_table.add_row(
        ["test_connection()", "Test the connection to the robot via a try of stop method"], divider=True)
    my_ilo_table.add_row(
        ["stop_reception()", "Stop the WebSocket reception thread and close the connection"], divider=True)
    my_ilo_table.add_row(
        ["stop()", "Stop the robots and free the engines"], divider=True)
    my_ilo_table.add_row(
        ["pause()", "Stop the robot and block engines"], divider=True)
    my_ilo_table.add_row(
        ["step(direction, step)", "Move by step ilorobot with selected direction during 2 seconds"], divider=True)
    my_ilo_table.add_row(["flat_movement(angle, distance)",
                         "Move ilo in the selected direction in angle for a selected distance"], divider=True)
    my_ilo_table.add_row(
        ["list_order(ilo_list)", "ilo will execute a list of successive displacment define in ilo_list"], divider=True)
    my_ilo_table.add_row(
        ["move(direction, speed)", "Move ilo with selected direction and speed"], divider=True)
    my_ilo_table.add_row(["direct_control(acc, axial, radial, rotation)",
                         "Control ilorobot with full control"], divider=True)
    my_ilo_table.add_row(
        ["game()", "Control ilo using arrow or numb pad of your keyboard"], divider=True)
    my_ilo_table.add_row(
        ["set_tempo_pos(value)", "Set the tempo of the position control"], divider=True)
    my_ilo_table.add_row(
        ["get_tempo_pos()", "Get the tempo of the position control"], divider=True)
    my_ilo_table.add_row(
        ["rotation(angle)", "Rotate ilo with selected angle"], divider=True)
    my_ilo_table.add_row(
        ["set_pid(kp, ki, kd)", "Set the new value of the proportional gain, the integral gain and the derivative gain"], divider=True)
    my_ilo_table.add_row(
        ["get_pid()", "Get the actual value of the proportional gain, the integral gain and the derivative gain"], divider=True)
    my_ilo_table.add_row(
        ["get_color_rgb()", "Displays the color below ilo"], divider=True)
    my_ilo_table.add_row(
        ["set_led_captor(bool)", "Turns on/off the lights under ilo"], divider=True)
    my_ilo_table.add_row(
        ["get_color_clear()", "Displays the brightness below ilo"], divider=True)
    my_ilo_table.add_row(
        ["get_color_clear_left()", "Displays the brightness below ilo only with left sensor"], divider=True)
    my_ilo_table.add_row(["get_color_clear_center()",
                         "Displays the brightness below ilo only with central sensor"], divider=True)
    my_ilo_table.add_row(["get_color_clear_right()",
                         "Displays the brightness below ilo only with right sensor"], divider=True)
    my_ilo_table.add_row(
        ["get_line()", "Detects whether ilo is on a line or not"], divider=True)
    my_ilo_table.add_row(
        ["get_line_left()", "Detects whether ilo is on a line or not according to the left sensor"], divider=True)
    my_ilo_table.add_row(
        ["get_line_center()", "Detects whether ilo is on a line or not according to the central sensor"], divider=True)
    my_ilo_table.add_row(
        ["get_line_right()", "Detects whether ilo is on a line or not according to the right sensor"], divider=True)
    my_ilo_table.add_row(["set_line_threshold_value(value)",
                         "Set the new threshold value for the line detection"], divider=True)
    my_ilo_table.add_row(["get_line_treshold_value()",
                         "Get the actual value of the threshold value for the line detection"], divider=True)
    my_ilo_table.add_row(
        ["get_distance()", "Get the distance around ilo"], divider=True)
    my_ilo_table.add_row(
        ["get_distance_front()", "Get the distance in front of ilo"], divider=True)
    my_ilo_table.add_row(
        ["get_distance_right()", "Get the distance on the right of ilo"], divider=True)
    my_ilo_table.add_row(
        ["get_distance_back()", "Get the distance behind ilo"], divider=True)
    my_ilo_table.add_row(
        ["get_distance_left()", "Get the distance on the left of ilo"], divider=True)
    my_ilo_table.add_row(["get_angle()", "Get the angle of ilo"], divider=True)
    my_ilo_table.add_row(
        ["get_roll()", "Get the roll angle of ilo"], divider=True)
    my_ilo_table.add_row(
        ["get_pitch()", "Get the pitch angle of ilo"], divider=True)
    my_ilo_table.add_row(
        ["get_yaw()", "Get the yaw angle of ilo"], divider=True)
    my_ilo_table.add_row(
        ["reset_angle()", "Reset the angle of ilo"], divider=True)
    my_ilo_table.add_row(["get_raw_imu()", "Get IMU raw data"], divider=True)
    my_ilo_table.add_row(
        ["get_battery()", "Get battery status (charged or not) and percentage"], divider=True)
    my_ilo_table.add_row(
        ["get_led_color()", "Get ilo LEDS color"], divider=True)
    my_ilo_table.add_row(["set_led_color(red, green, blue)",
                         "Set ilo LEDS color"], divider=True)
    my_ilo_table.add_row(
        ["set_led_shape(value)", "Show designs on LEDS"], divider=True)
    my_ilo_table.add_row(
        ["set_led_anim(value)", "Starting an animation with LEDs"], divider=True)
    my_ilo_table.add_row(["set_led_single(bool, id, r, g, b)",
                         "Lights up an individual led in the led matrix"], divider=True)
    my_ilo_table.add_row(
        ["get_acc_motor()", "Get the acceleration of all motors"], divider=True)
    my_ilo_table.add_row(
        ["set_acc_motor(val)", "Set the acceleration of all motors"], divider=True)
    my_ilo_table.add_row(
        ["ping_single_motor(id)", "Ping a single motor with is id"], divider=True)
    my_ilo_table.add_row(["drive_single_motor_speed(id, value)",
                         "Drive a single motor in speed with is id"], divider=True)
    my_ilo_table.add_row(["drive_single_motor_speed_front_left(value)",
                         "Control the front left motor"], divider=True)
    my_ilo_table.add_row(["drive_single_motor_speed_front_right(value)",
                         "Control the front right motor"], divider=True)
    my_ilo_table.add_row(["drive_single_motor_speed_back_left(value)",
                         "Control the back left motor"], divider=True)
    my_ilo_table.add_row(["drive_single_motor_speed_back_right(value)",
                         "Control the back right motor"], divider=True)
    my_ilo_table.add_row(["get_single_motor_speed(id)",
                         "Get the speed of a single motor with is id"], divider=True)
    my_ilo_table.add_row(["drive_single_motor_angle(id, value)",
                         "Drive a single motor in angle with is id"], divider=True)
    my_ilo_table.add_row(["get_single_motor_angle(id)",
                         "Get the angle of a single motor with is id"], divider=True)
    my_ilo_table.add_row(["get_temp_single_motor(id)",
                         "Get the temperature of a single motor with is id"], divider=True)
    my_ilo_table.add_row(["get_volt_single_motor(id)",
                         "Get the voltage of a single motor with is id"], divider=True)
    my_ilo_table.add_row(["get_torque_single_motor(id)",
                         "Get the torque of a single motor with is id"], divider=True)
    my_ilo_table.add_row(["get_current_single_motor(id)",
                         "Get the current of a single motor with is id"], divider=True)
    my_ilo_table.add_row(["get_motor_is_moving(id)",
                         "Get the state of a single motor with is id"], divider=True)
    my_ilo_table.add_row(["set_autonomous_mode(number)",
                         "Launch ilo in an autonomous mode"], divider=True)
    my_ilo_table.add_row(["set_wifi_credentials(ssid, password)",
                         "Enter your wifi details to enable ilo to connect to your network"], divider=True)
    my_ilo_table.add_row(
        ["get_wifi_credentials()", "Get wifi credentials registered on ilo"], divider=True)
    my_ilo_table.add_row(
        ["set_name()", "Set a new name for your ilo"], divider=True)
    my_ilo_table.add_row(
        ["get_name()", "Get the name you have given to your ilo"], divider=True)

    print(my_ilo_table)
    print("If the table does not display correctly, expand your terminal.")
# -----------------------------------------------------------------------------

def _co_send_msg(ws, message):
    '''
    Send a message over the WebSocket connection
    '''
    try:
        ws.send(message)
        response = ws.recv()
        print(f"Sent: {message}, Received: {response}")  # Debugging line
        return response  # Adjusted to match the expected response
    except Exception as e:
        print(f"Error sending message: {e}")
        return "..."

def check_robot_on_wifi():
    """
    Check the presence of the ilo(s) on the network
    """
    pyperclip.copy("""my_ilo = ilo.robot(1)""")
    try:
        print("Looking for ilo on your network ...")
        global _tab_IP
        _tab_IP = []
        ilo_AP = False

        try:
            ws_url = "ws://192.168.4.1:4583"
            print(ws_url)
            ws = websocket.create_connection(ws_url, timeout=1.3)
            if _co_send_msg(ws, "<ilo>") == "ilo":
                _tab_IP.append(["192.168.4.1", 1, _co_send_msg(ws, "<930>")])

                ilo_AP = True
                ws.close()
                print("Your robot is working as an access point")
        except:
            pass

        if not ilo_AP:
            base_ip = "192.168.1."
            ilo_ID = 1
            c = 3     # Checking 3 more IP addresses after success

            for i in range(100, 200):  # Between 192.168.1.100 and 192.168.1.200
                ip_check = f"{base_ip}{i}"
                IP = ip_check
                ws_url = f"ws://{IP}:4583"
                print(f"Checking {ws_url}")
                c -= 1
                if c == 0:
                    break

                try:
                    ws = websocket.create_connection(ws_url, timeout=1.3) # Set timeout for each connection
                    if _co_send_msg(ws, "<ilo>") == "ilo":
                        _co_send_msg(ws, "<>")
                        _tab_IP.append([IP, ilo_ID, _co_send_msg(ws, "<930>")])
                        ilo_ID += 1
                        c += 1
                        ws.close()

                except:
                    continue  # Continue to the next IP

        table = PrettyTable() # Display the IP and ID
        table.field_names = ["IP Address", "ID of ilo", "Name of ilo"]  # add the name info <93>
        for row in _tab_IP:
            table.add_row(row)

        if len(_tab_IP) != 0:
            print(table)
            print("")
            print(
                "Use for example: my_ilo = ilo.robot(1) to create an object my_ilo with the ID = 1")
            global _connection_type
            _connection_type = 0
        else:
            print(
                "Unfortunately, no ilo is present on your current network. Check your connection.")

    except Exception as e:
        print(f"WebSocket error: {e}")

def check_robot_on_serial(COM=None):
    """
    Check the connection to ilo in serial
    """
    pyperclip.copy("""my_ilo = ilo.robot(1)""")
    global _connection_type
    global _tab_PORT

    if COM:
        try:
            print("Check that ilo is properly connected ...")
            with serial.Serial(COM, 115200, timeout=1) as ser:
                # with serial.Serial(port.device, 115200, timeout=1, dsrdtr=False, rtscts=False) as ser:
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                time.sleep(1)

                ser.write(("<ilo>").encode())
                ser.write(("<930>").encode())
                time.sleep(1)

                response = ser.readline().decode().strip()
                ser.close()

                if response:
                    print(f"Robot {response} detected on port {COM}")
                    _tab_PORT = [[COM, 1, response]]
                    table = PrettyTable()
                    table.field_names = ["Device port","ID of ilo", "Name of ilo"]
                    table.add_row([COM, 1, response])
                    print(table)
                    print("")
                    print("Use for example: my_ilo = ilo.robot(1) to create an object my_ilo with the ID = 1")
                    _connection_type = 1
                else:
                    print(f"No valid response received on {COM}")
        except (serial.SerialException, OSError) as e:
            print(f"Error with port {COM} : {e}")

    else:
        try:
            _tab_PORT = []
            ilo_ID = 1

            print("Check that ilo is properly connected ...")
            ports = serial.tools.list_ports.comports()
            for port in ports:
                print(f"Testing port: {port.device}")
                try:
                    with serial.Serial(port.device, 115200, timeout=1, write_timeout=1) as ser:
                        # with serial.Serial(port.device, 115200, timeout=1, dsrdtr=False, rtscts=False) as ser:
                        ser.reset_input_buffer()
                        ser.reset_output_buffer()
                        time.sleep(0.2)

                        ser.write(("<ilo>").encode())
                        ser.write(("<930>").encode())
                        time.sleep(1)

                        response = ser.readline().decode().strip()
                        ser.close()

                        if response:
                            print(f"Robot {response} detected on port {port.device}")
                            _tab_PORT.append([port.device, ilo_ID, response])
                            ilo_ID += 1
                        else:
                            print(f"No valid response received on {port.device}")
                except (serial.SerialException, OSError) as e:
                    print(f"Error with port {port.device} : {e}")
                    continue

            table = PrettyTable()
            table.field_names = ["Device port", "ID of ilo", "Name of ilo"]

            for row in _tab_PORT:
                table.add_row(row)

            if len(_tab_PORT) != 0:
                print(table)
                print("")
                print(
                    "Use for example: my_ilo = ilo.robot(1) to create an object my_ilo with the ID = 1")
                _connection_type = 1
            else:
                print(
                    "Unfortunately, no ilo is connected to your computer. Check your connection.")

        except Exception as e:
            print(f"Serial error: {e}")
            return None

def check_robot_on_bluetooth():
    pyperclip.copy('''my_ilo = ilo.robot(1)''')
    global _tab_ADDRESS
    global _connection_type

    print("[ILO] Scanning for BLE devices...")
    try:    
        devices = ble_lib.scan_devices()
        table = PrettyTable()
        table.field_names = ["Device adress", "ID of ilo", "Name of ilo"]
        i = 1
        for device in devices:
            if str(device[0]).startswith("ilo_BLE_"):
                table.add_row([device[1], i, device[0]])
                _tab_ADDRESS.append(device)
                i += 1
        if len(_tab_ADDRESS) == 0:
            print("No ilo found.")
            return False
        else:
            print(table)
            _connection_type = 2
            print("Connection type: BLE")
            return True
        
    except Exception as e:
        print(f"Error check robot on Bluetooth: {e}")
        return False

# -----------------------------------------------------------------------------

def _get_IP_from_ID(ID):
    '''
    Get the IP address of the robot from its ID
    '''
    # print(ID)
    global _tab_IP
    for item in _tab_IP:
        # print(item[1])
        if item[1] == ID:
            return item[0]
    return None

def _get_PORT_from_ID(ID):
    '''
    Get the PORT of the robot from its ID
    '''
    global _tab_PORT
    for item in _tab_PORT:
        if item[1] == ID:
            return item[0]
    return None

# def get_ADDRESS_from_ID(ID):
#     '''
#     Get the ADDRESS of the robot from its ID
#     '''
#     global _tab_ADDRESS
#     for item in _tab_ADDRESS:
#         if item[1] == ID:
#             return item[0]
#     return None
# -----------------------------------------------------------------------------

class robot(object):
    global _connection_type
    _robots_connected = {}  # Variable de classe pour garder une trace des connexions actives

    def __init__(self, ID):
        self._ID = ID

        pyperclip.copy('''my_ilo.step('front')''')

        # if _connection_type == 0:
        if ID in robot._robots_connected:  # Vérification si un robot avec cet ID est déjà connecté
            print(f"Un robot avec l'ID {ID} est déjà connecté, déconnexion automatique de l'ancien robot.")
            old_robot = robot._robots_connected[ID]
            # Arrêter le thread mais sans déconnexion immédiate
            if _connection_type == 0:
                old_robot.recv_thread_running = False
            elif _connection_type == 1:
                pass
            elif _connection_type == 2:
                print("Disconnecting from the BLE device...")
                ble_lib.disconnect(old_robot.ble_device)
                
                old_robot.connect = False

            else:
                pass

        self._Port = 4583
        self._ws = None
        self._connect = False
        self._IP = _get_IP_from_ID(self._ID)

        self._recv_thread = None
        self._recv_thread_running = False

        # elif _connection_type == 1:
        self._port = _get_PORT_from_ID(self._ID)
        self._ser = None
        # self._connect = False


        self._version = ""

        #BLE:
        # self.adress = get_ADDRESS_from_ID(self._ID)
        self._ble_device = None

        self._hostname = ""

        self._red_color = 0
        self._green_color = 0
        self._blue_color = 0

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

        self._marker = True

        self._response_event = threading.Event()
        self._response_value = None

        # -- marin add all other data of the robot
        # -- thinking to a solution to get data from additional captor connected on the top of the robot via accessory PCB

        # Ajouter ce robot à la liste des robots connectés
        robot._robots_connected[self._ID] = self

        print(f"Robot with ID {self._ID} will be connected")
        if self._ID:
            # print("You are trying to connect to: ", self._IP)
            self._connection()
        else:
            print("You have to run the command [ilo.check_ilo_on_network()] to know if there are robots present on your network")
            print("or")
            print("Run the command [ilo.check_ilo_on_serial()] to know if there are robots connected to your computer")
    # -----------------------------------------------------------------------------
    def _connection(self):
        """
        Connection of your machine to robot object 
        """

        self._send_msg("<ilo>")

        #if self._hostname != "":

            #self._send_msg("<ilo>")

            #print('Your robot is already connected to ' + self._hostname)
            # -- marin check if the websocket is well working (test un envoi de trame ou spécific methode

        #else:
        print("Trying to connect to the robot with ID: ", self._ID, " and connection type: ", _connection_type)
        if _connection_type == 0: 
            try:
                # Start the WebSocket d'envoie de trame
                self._ws = websocket.create_connection(
                    f"ws://{self._IP}:{self._Port}")

                # Vérifie si un ancien thread de réception est actif et l'arrête avant d'en démarrer un nouveau
                if self._recv_thread and self._recv_thread.is_alive():
                    print("Stopping the previous reception thread...")
                    self._stop_reception()

                # Start the WebSocket de reception in a separate thread
                self._recv_thread_running = True
                self._recv_thread = threading.Thread(
                    target=self._web_socket_receive)
                self._recv_thread.start()

                self._connect = True
                self._send_msg("<ilo>")
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

        elif _connection_type == 1:
            try:
                # Start the serial connection
                self._ser = serial.Serial(self._port, 115200)

                self._connect = True
                self._send_msg("<ilo>")
                
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

        elif _connection_type == 2:
            def notification_handler(sender, data):
                global suspend_receive_msg
                try:
                    decoded_data = data.decode('utf-8')
                    if suspend_receive_msg:
                        return
                    print(f"Received: {decoded_data}")
                    self._process_received_data(decoded_data)
                except UnicodeDecodeError:
                    print(f"Received non-UTF-8 data: {data}")
            print("Connecting to the BLE device...")
            try:
                self._ble_device = ble_lib.connect(_tab_ADDRESS[self._ID - 1][1])
                ble_lib.subscribe_to_notifications(CHARACTERISTIC_UUID, notification_handler)
                self._connect = True
                print("Connected to the BLE device.")
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

    # -----------------------------------------------------------------------------
    def _send_msg(self, message):
        self._response_event.clear()
        if _connection_type == 0:
            if self._ws and self._connect:
                try:
                    self._ws.send(message)
                    print(f"Sent:     {message}")
                except websocket.WebSocketException as e:
                    print(f"Error sending message: {e}")
            else:
                print("WebSocket is not connected.")

        elif _connection_type == 1:
            if self._ser and self._connect:
                try:
                    self._ser.write(message.encode())
                    print(f"Sent:     {message}")

                    invalid_prefixes = ("<a", "<i", "<13", "<31", "<51", "<52", "<53", "<54", "<55", "<56", "<57", "<58",
                                        "<610", "<620", "<680", "<690", "<70", "<72", "<80", "<90", "<91", "<94", "<103", "<0", "<>")

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
        elif _connection_type == 2:
            if self._ble_device and self._connect:
                try:
                    ble_lib.write_characteristic(self._ble_device, CHARACTERISTIC_UUID, message.encode())
                    print(f"Sent:     {message}")
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
                self._marker = True
        except serial.SerialException as e:
            print(f"Error: {e}")
    # -----------------------------------------------------------------------------
    def _process_received_data(self, data):
        """
        Process the data received from the WebSocket or Serial and update the robot's attributes
        """
        # print(f"[process_received_data] Received: {data}")
        # Here you can parse the received data and update relevant attributes
        # Example: Update distance values

        try:

            if str(data[1:4]) == "10r":  # get_color_rgb
                self._red_color = int(data[data.find('r')+1: data.find('g')])
                self._green_color = int(data[data.find('g')+1: data.find('b')])
                self._blue_color = int(data[data.find('b')+1: data.find('>')])

            if str(data[1:4]) == "11l":  # get_color_clear
                self._clear_left = int(data[data.find('l')+1: data.find('m')])
                self._clear_center = int(data[data.find('m')+1: data.find('r')])
                self._clear_right = int(data[data.find('r')+1: data.find('>')])

            if str(data[1:4]) == "12l":  # get_line
                self._line_left = int(data[data.find('l')+1: data.find('m')])
                self._line_center = int(data[data.find('m')+1: data.find('r')])
                self._line_right = int(data[data.find('r')+1: data.find('>')])

            if str(data[1:4]) == "14t":  # get_line_threshold_value
                self._line_threshold_value = int(
                    data[data.find('t')+1: data.find('>')])

            if str(data[1:4]) == "20f":  # get_distance
                self._distance_front = int(
                    data[data.find('f')+1: data.find('r')])
                self._distance_right = int(
                    data[data.find('r')+1: data.find('b')])
                self._distance_back = int(
                    data[data.find('b')+1: data.find('l')])
                self._distance_left = int(
                    data[data.find('l')+1: data.find('>')])

            if str(data[1:4]) == "21f":  # get_distance_front
                self._distance_front = int(
                    data[data.find('f')+1: data.find('>')])

            if str(data[1:4]) == "22r":  # get_distance_right
                self._distance_right = int(
                    data[data.find('r')+1: data.find('>')])

            if str(data[1:4]) == "23b":  # get_distance_back
                self._distance_back = int(
                    data[data.find('b')+1: data.find('>')])

            if str(data[1:4]) == "24l":  # get_distance_left
                self._distance_left = int(
                    data[data.find('l')+1: data.find('>')])

            if str(data[1:4]) == "30r":  # get_angle - données traités en degrés
                self._roll = float(data[data.find('r')+1: data.find('p')])
                self._pitch = float(data[data.find('p')+1: data.find('y')])
                self._yaw = float(data[data.find('y')+1: data.find('>')])

            if str(data[1:4]) == "32x":  # get_raw_imu
                self._accX = int(data[data.find('x')+1: data.find('y')])
                self._accY = int(data[data.find('y')+1: data.find('z')])
                self._accZ = int(data[data.find('z')+1: data.find('r')])
                self._gyroX = int(data[data.find('r')+1: data.find('p')])
                self._gyroY = int(data[data.find('p')+1: data.find('g')])
                self._gyroZ = int(data[data.find('g')+1: data.find('>')])

            if str(data[1:4]) == "40s":  # get_battery
                self._battery_status = int(
                    data[data.find('s')+1: data.find('p')])
                self._battery_pourcentage = int(
                    data[data.find('p')+1: data.find('>')])

            if str(data[1:4]) == "50r":  # get_led_color
                self._red_led = int(data[data.find('r')+1: data.find('g')])
                self._green_led = int(data[data.find('g')+1: data.find('b')])
                self._blue_led = int(data[data.find('b')+1: data.find('>')])

            if str(data[1:4]) == "60i":  # ping_single_motor
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_ping = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "611":  # get_single_motor_speed
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_speed = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "621":  # get_single_motor_angle
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_angle = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "63i":  # get_temp_single_motor
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._temp_motor = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "64i":  # get_volt_single_motor
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_volt = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "65i":  # get_torque_single_motor
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_torque = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "66i":  # get_current_single_motor
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_current = int(
                    data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "67i":  # get_motor_is_moving
                self._motor_id = int(data[data.find('i')+1: data.find('s')])
                self._motor_is_moving = int(
                    data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "681":  # get_acc_motor
                self._acc_motor = int(data[data.find('a')+1: data.find('>')])

            if str(data[1:4]) == "691":  # get_tempo_pos
                self._tempo_pos = int(data[data.find('t')+1: data.find('>')])

            if str(data[1:4]) == "71p":  # get_pid
                self._kp = float(data[data.find('p')+1: data.find('i')])
                self._ki = float(data[data.find('i')+1: data.find('d')])
                self._kd = float(data[data.find('d')+1: data.find('>')])

            if str(data[1:4]) == "92s":  # get_wifi_credentials
                self._ssid = str(data[data.find('s')+1: data.find('p')])
                self._password = str(data[data.find('p')+1: data.find('>')])

            if str(data[1:4]) == "93n":  # get_name
                self._hostname = str(data[data.find('n')+1: data.find('>')])

            if str(data[1:4]) == "101":  # get_accessory
                self._accessory = float(data[data.find('t')+1: data.find('>')])

            if str(data[1:4]) == "102":  # get_accessory
                self._potard_value = float(data[data.find('a')+1: data.find('>')])

            if str(data[1:4]) == "120":  # get_manufacturing_date
                self._manufacturing_date = str(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "130":  # get_first_use_date
                self._first_use_date = str(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "140":  # get_product_version
                self._product_version = str(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "150":  # get_product_id
                self._product_id = str(data[data.find('s')+1: data.find('>')])

            if str(data[1:5]) == "500y": # get_version
                self._version = str(data[data.find('y')+1: data.find('>')])

            if str(data[1:4]) == "500":  # get_global_trame
                
                self._version = str(data[data.find('y')+1: data.find('>')])
                print(f"Version: {self._version}")

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
                self._ws.close()
                self._connect = False  # Mettre à jour l'état de connexion après la fermeture de WebSocket
                print("WebSocket successfully closed")
            except Exception as e:
                print(f"Erreur lors de la fermeture de la WebSocket: {e}")

        # if self._recv_thread and self._recv_thread.is_alive():
        if self._recv_thread:
            print("Waiting for the reception thread to stop...")
            self._recv_thread.join(timeout=2)

        if self._ID in robot._robots_connected:
            del robot._robots_connected[self._ID]

        print(f"WebSocket connection closed for the robot {self._ID}.")
    # -----------------------------------------------------------------------------
    def __del__(self):
        """
        Destructor to ensure the WebSocket connection is closed gracefully
        and the ID is removed from the list of connected robots
        """
        print(f"Destruction de l'objet robot avec l'ID {self._ID}")
        if _connection_type == 0:
            self._ws.close()
        
        elif _connection_type == 1:
            pass   # on ne peut pas paraleléliser les ouverture de port comme les websocket
        elif _connection_type == 2:
            ble_lib.disconnect(self._ble_device)
        else:
            pass  
    # -----------------------------------------------------------------------------
    def test_connection(self):
        """
        Test the connection to the robot via a try of stop method
        :return: True or False
        """
        if _connection_type == 0:
            try:
                self._send_msg("<ilo>")
                return True
            except:
                print("Error connection to the robot")
                return False
        elif _connection_type == 1:
            try:
                self._send_msg("<ilo>")
                return True
            except:
                print("Error connection to the robot")
                return False
        elif _connection_type == 2:
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
        Stop ilo and free its engines
        """
        self._send_msg("<>")

    def pause(self):
        """
        Stop ilo and block its motors
        """
        self.direct_control(200, 128, 128, 128)

    def step(self, direction, step=None, finish_state=None):
        """
        Move ilo in the selected direction 

        Parameters:
            direction (str): The direction in which the robot is moving
            step (int): The number of steps the robot will do

        Raises:
            TypeError: If the direction is not a string
            ValueError: If the direction is not one of the following: front, back, left, right, rot_trigo or rot_clock
            TypeError: If the step is not an integer or a float
            ValueError: If value is not between 0.01 and 100

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

            step = int(step*100)

        elif (direction == 'rot_trigo' or direction == 'rot_clock'):

            if step is None:
                step = 90

            if not isinstance(step, (int, float)):
                print("[ERROR] 'step' should be an integer or a float")
                return None

            if step < 1:
                print("[ERROR] 'step' should be more than 1 for rotation")
                return None

        else:
            print("[ERROR] 'step' unknow name")
            return None
        
        if finish_state != None:

            if not isinstance(finish_state, bool):
                print ("[ERROR] 'finish_state' should be a boolean")
                return None

        if direction == 'front':
            msg = '<a60vpx1' + str(step) + 'yr>'
            self._send_msg(msg)
        elif direction == 'back':
            msg = '<a60vpx0' + str(step) + 'yr>'
            self._send_msg(msg)
        elif direction == 'left':
            msg = '<a60vpxy0' + str(step) + 'r>'
            self._send_msg(msg)
        elif direction == 'right':
            msg = '<a60vpxy1' + str(step) + 'r>'
            self._send_msg(msg)
        elif direction == 'rot_trigo':
            msg = '<a60vpxyr0' + str(step) + '>'
            self._send_msg(msg)
        elif direction == 'rot_clock':
            msg = '<a60vpxyr1' + str(step) + '>'
            self._send_msg(msg)
        else:
            print(
                "[ERROR] 'Direction' should be 'front', 'back', 'left', 'rot_trigo', 'rot_clock'")
            
        if finish_state == True:
            print("Finish state is True")
            # self._response_event.wait(timeout=5)
            # return (self._version)

    def flat_movement(self, angle, distance):
        """
        Move ilo in the selected direction in angle for a selected distance

        Parameters:
            angle (int): The direction in which the robot is moving
            distance (int): The distance the robot will travel

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
               "y" + str(indice_y) + str(distance_y) + ">")
        self._send_msg(msg)

    def list_order(self, ilo_list):
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
            acceleration (int): Between 1 to 200

        Raises:
            TypeError: If the direction is not a string
            ValueError: If the direction is not one of the following: front, back, left, right, rot_trigo, rot_clock or stop
            TypeError: If the speed is not an integer
            ValueError: If the speed is not between 0 and 100

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

        if acc > 200 or acc < 1:
            print("[ERROR] 'acc' parameter must be include between 1 to 200 ")
            return None

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

            keylogger = KeyBordCrossPlatform()
            print('Game mode start, use keyboard arrow to control ilo')
            print("Press echap to leave the game mode")

            while (True):
                key = keylogger.getKey()
                if key == "8" or key == "f7":
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    axial_value = axial_value + 5
                    if axial_value > 255:
                        axial_value = 255
                elif key == "2" or key == "f20":
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    axial_value = axial_value - 5
                    if axial_value < 1:
                        axial_value = 0
                elif key == "6" or key == "kp_add":
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    radial_value = radial_value + 5
                    if radial_value > 255:
                         radial_value = 255
                elif key == "4" or key == "kp_multiply":
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    radial_value = radial_value - 5
                    if radial_value < 1:
                        radial_value = 0
                elif key == "3" or key == "kp_divide":
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    rotation_value = rotation_value + 5
                    if rotation_value > 255:
                        rotation_value = 255
                elif key == "1" or key == "f19":
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    rotation_value = rotation_value - 5
                    if rotation_value < 1:
                        rotation_value = 0
                elif key == "5" or key == "kp_subtract":
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    axial_value = 128
                    radial_value = 128
                    rotation_value = 128
                elif key == "esc":
                    print("Game mode stop")
                    self.stop()
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

        msg = "<690t"+str(value)+">"
        self._send_msg(msg)

    def get_tempo_pos(self):
        """
        Get the tempo of the position control
        """
        self._send_msg("<691>")
        self._response_event.wait(timeout=5)
        return (self._tempo_pos)

    def rotation(self, angle: int):
        """
        Rotate ilo with selected angle

        Parameters:
            angle (int): The rotation angle

        Raises:
            TypeError: If 'angle' is not an integer or a float

        Examples:
            my_ilo.rotation(90)
            my_ilo.rotation(-50.3)
        """

        if not isinstance(angle, int):
            print("[ERROR] 'angle' should be an integer")
            return None

        if angle > 0:
            indice = 1
        else:
            indice = 0

        command = ("<avpxyr" + str(indice) + str(abs(angle)) + ">")
        self._send_msg(command)

    def set_pid(self, kp, ki, kd):
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

        msg = "<70p"+str(kp)+"i" + str(ki) + "d" + str(kd) + ">"
        self._send_msg(msg)

    def get_pid(self):
        """
        Get the actual value of the proportional gain, the integral gain and the derivative gain
        """
        self._send_msg("<71>")
        self._response_event.wait(timeout=5)
        return (self._kp, self._ki, self._kd)
    # -----------------------------------------------------------------------------
    def get_color_rgb(self):
        """
        Displays the color below ilo
        """
        self._send_msg("<10>")
        self._response_event.wait(timeout=5)

        return (self._red_color, self._green_color, self._blue_color)

    def set_led_captor(self, state: bool):
        """
        Turns on/off the lights under ilo

        Parameters:
            state (bool): allows you to turn on or off the leds

        Raises:
            TypeError: If state is not a bool

        Examples:
            my_ilo.set_led_captor(True)
        """

        if not isinstance(state, bool):
            print("[ERROR] 'state' parameter must be a bool")
            return None

        if (state == True):
            msg = "<54l1>"
        elif (state == False):
            msg = "<54l0>"
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
            my_ilo.set_line_treshold_value()
            my_ilo.set_line_treshold_value(40)
        """

        if value is not None:

            if not isinstance(value, int):
                print("[ERROR] 'value' parameter must be a integer")
                return None

        else:
            self._clear_center = 0
            self.get_color_clear()
            while self._clear_center == 0:
                time.sleep(0.1)
            value = round(self._clear_center*1.2)
            print(f"La nouvelle valeur de seuil est: {value}")

        msg = "<13t"+str(value)+">"
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

        msg = "<51r"+str(red)+"g"+str(green)+"b"+str(blue)+">"
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

        msg = "<52v"+str(value)+">"
        self._send_msg(msg)

    def set_led_anim(self, value: str):
        """
        Starting an animation with LEDs

        Parameters:
            value (str): led animation name

        Raises:
            TypeError: If value is not a string

        Examples:
            my_ilo.set_led_anim("wave")
        """

        if not isinstance(value, str):
            print("[ERROR] 'value' parameter must be a string")
            return None

        msg = "<53"+str(value)+">"
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

        msg = "<55t"+str(type)+"d"+str(id)+"r"+str(red)+"g" + \
            str(green)+"b"+str(blue)+"l"+str(luminosity)+">"
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
            my_ilo.set_led_word("reveal", "Hello")
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
            msg = "<56w"+str(word.upper())+"d"+ str(delay)+">"
        else:
            msg = "<57w"+str(word.upper())+"d"+ str(delay)+">"
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
        msg = "<680a"+str(acc)+">"
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

        msg = "<60i"+str(id)+">"
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
        if vel > 7000 or vel < -7000:
            print("[ERROR] 'value' parameter must be include between -100 and 100")
            return None

        if not isinstance(acc, int):
            print("[ERROR] 'acc' parameter must be a integer")
            return None
        if acc > 200 or acc < 0:
            print("[ERROR] 'acc' parameter must be include between 1 and 200")
            return None

        msg = "<610i"+str(id)+"a"+str(acc)+"v"+str(vel)+">"
        self._send_msg(msg)

    def drive_single_motor_speed_front_left(self, value: int):  # de -100 à 100
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

        self.drive_single_motor_speed(1, value)

    def drive_single_motor_speed_front_right(self, value: int):
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

        self.drive_single_motor_speed(2, value)

    def drive_single_motor_speed_back_left(self, value: int):
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

        self.drive_single_motor_speed(4, value)

    def drive_single_motor_speed_back_right(self, value: int):
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

        self.drive_single_motor_speed(3, value)
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

        msg = "<611i"+str(id)+">"
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
        if acc >= 200 or acc < 0:
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

        msg = "<620i"+str(id)+"a"+str(acc)+"v"+str(vel)+"p"+str(pos)+">"
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

        msg = "<621i"+str(id)+">"
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

        msg = "<63i"+str(id)+">"
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

        msg = "<64i"+str(id)+">"
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

        msg = "<65i"+str(id)+">"
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

        msg = "<66i"+str(id)+">"
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

        msg = "<67i"+str(id)+">"
        self._send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self._motor_id, self.motor_moving)

    def get_vmax():
        pass

    def set_vmax(vmax):
        pass

    def set_motor_mode(self, motor_id:int, mode:str):
        """
        Set the mode of a single motor with is id

        Parameters:
            motor_id (int): the motor id
            mode (str): the mode you want to set

        Raises:
            TypeError: If 'motor_id' is not an integer
            ValueError: If 'motor_id' is not between 5 and 255
            TypeError: If 'mode' is not a string
            ValueError: If 'mode' is not "position" or "speed"

        Examples:
            my_ilo.set_motor_mode(5, "position")
            my_ilo.set_motor_mode(6, "speed")
        """

        if not isinstance(motor_id, int):
            print("[ERROR] 'motor_id' parameter must be a integer")
            return None
        if motor_id > 255 or motor_id < 5:
            print("[ERROR] 'motor_id' parameter must be include between 5 and 255")
            return None
        
        if not isinstance(mode, str):
            print("[ERROR] 'mode' parameter must be a string")
            return None
        if mode != "position" and mode != "speed":
            print("[ERROR] 'mode' parameter must be 'position' or 'speed'")
            return None
        
        if mode == "position":
            msg = "<72"+str(motor_id)+"m0>"
        if mode == "speed":
            msg = "<72"+str(motor_id)+"m1>"
        self._send_msg(msg)
        
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

        msg = "<80"+str(value)+">"
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

        msg = "<90s"+str(ssid)+">"
        self._send_msg(msg)

        msg = "<91p"+str(password)+">"
        self._send_msg(msg)

    def get_wifi_credentials(self):
        """
        Get wifi credentials registered on ilo
        """
        self._send_msg("<92>")
        self._response_event.wait(timeout=5)
        return (self._ssid, self._password)
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

        msg = "<94n"+str(name)+">"
        self._send_msg(msg)

    def get_name(self):
        """
        Get the name you have given to your ilo
        """
        self._send_msg("<93>")
        self._marker = False
        self._response_event.wait(timeout=5)
        return (self._hostname)
    # -----------------------------------------------------------------------------
    def get_accessory(self):
        """
        Get information about the accessory connected to ilo
        """
        self._send_msg("<100>")
        self._response_event.wait(timeout=5)
        return (self._accessory)
    # -----------------------------------------------------------------------------
    def set_debug_state(self, state: bool):  # pas à jour

        if not isinstance(state, bool):
            print("[ERROR] 'state' parameter must be a bool like True or False")
            return None

        if state == True:
            msg = "<103s1>"
        else:
            msg = "<103s2>"

        self._send_msg(msg)
    # -----------------------------------------------------------------------------
    def send_trame_s(self, param_list: list):
        """
        Get the global trame of ilo
        """

        msg = "<0/"

        if "color" in param_list:
            msg = msg + "10/"
        if "luminosity" in param_list:
            msg = msg + "11/"
        if "distance" in param_list:
            msg = msg + "20/"

        if "accessory_angle" in param_list:
            msg = msg + "100/"

        msg = msg + ">"

        self._send_msg(msg)

    def del_trame_s(self):
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
        msg = "<121s"+str(date)+">"
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
        msg = "<131s"+str(date)+">"
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
        msg = "<141s"+str(version)+">"
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
        msg = "<151s"+str(id)+">"
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

