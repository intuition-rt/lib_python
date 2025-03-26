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
# -----------------------------------------------------------------------------

class SyncBleak:
    """
    Encapsule les fonctions de Bleak pour les rendre synchrone.
    """
    def __init__(self):
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        self.client = None

    def get_loop(self):
        """Retourne la boucle asyncio utilisée par SyncBleak."""
        return self.loop

    def scan_devices(self, timeout=5):
        """Scan BLE devices de manière synchrone."""
        return self.loop.run_until_complete(self._scan_devices(timeout))

    async def _scan_devices(self, timeout):
        devices = await BleakScanner.discover(timeout)
        return [(dev.name, dev.address) for dev in devices]

    def connect(self, address):
        """Connecte à un périphérique BLE."""
        return self.loop.run_until_complete(self._connect(address))

    async def _connect(self, address):
        self.client = BleakClient(address)
        connected = await self.client.connect()
        if connected:
            return self.client
        return None

    def write_characteristic(self, client, char_uuid, data):
        """Écrit dans une caractéristique BLE."""
        return self.loop.run_until_complete(client.write_gatt_char(char_uuid, data))
    
    def subscribe_to_notifications(self, char_uuid, callback):
        """S'abonne aux notifications d'une caractéristique BLE."""
        self.loop.run_until_complete(self._subscribe(char_uuid, callback))

    async def _subscribe(self, char_uuid, callback):
        if self.client and self.client.is_connected:
            await self.client.start_notify(char_uuid, callback)
            print(f"🔔 Abonné aux notifications sur {char_uuid}")

    def unsubscribe_from_notifications(self, char_uuid):
        """Se désabonne des notifications."""
        self.loop.run_until_complete(self._unsubscribe(char_uuid))

    async def _unsubscribe(self, char_uuid):
        if self.client and self.client.is_connected:
            await self.client.stop_notify(char_uuid)
            print(f"🚫 Désabonné des notifications sur {char_uuid}")

    def disconnect(self, client):
        """Déconnecte le client BLE."""
        return self.loop.run_until_complete(client.disconnect())
    

    def is_connected(self):
        """Vérifie si le client est connecté."""
        return self.client.is_connected
    
ble_lib = SyncBleak()
CHARACTERISTIC_UUID = "DEAD"  # Notify  and read/write characteristic

class IloUpdater():
    def __init__(self, client, version, use_ble=True, ws=None):
        self.client = client
        self.version = version
        self.service_uuid = "5f6d"
        self.data_char_uuid = "c0de"
        self.size_char_uuid = "dead"
        self.notify_char_uuid = "1A2B"
        self.use_ble = use_ble
        if use_ble:
            self.CHUNK_SIZE = 509  # Taille maximale d'un paquet BLE
        else:
            self.CHUNK_SIZE = 1024
            self.ws = ws
        self.update_complete = False

        self.loop = ble_lib.get_loop()  # Utilisation de la même boucle que SyncBleak

    async def send_firmware(self):
        """Envoie un firmware en OTA via BLE au ESP32 et attend une notification de fin."""
        try:
            with open("firmware.bin", "rb") as f:
                firmware_data = f.read()
            firmware_size = len(firmware_data)
            print(f"Firmware chargé: {firmware_size} octets")
            if self.use_ble:
                if not self.client.is_connected:
                    print("Client BLE non connecté.")
                    return
            else:
                if self.ws is None:
                    print("WebSocket non connecté.")
                    return
            print("\nConnecté.")
            size_bytes = f"<500x{firmware_size}>".encode() # Envoyer la taille du firmware
            if (self.use_ble):
                await self.client.write_gatt_char(self.size_char_uuid, size_bytes, response=False)
            else:
                self.ws.send(size_bytes)
            print("\nTaille du firmware envoyée.")
            await asyncio.sleep(0.1)
            for i in range(0, firmware_size, self.CHUNK_SIZE):  # Envoi du firmware par morceaux
                chunk = firmware_data[i:i+self.CHUNK_SIZE]
                if (self.use_ble):
                    await self.client.write_gatt_char(self.data_char_uuid, chunk, response=False)
                else:
                    self.ws.send(bytes(chunk), opcode=websocket.ABNF.OPCODE_BINARY)
                print(f"\rEnvoyé {i + len(chunk)} / {firmware_size} octets", end="", flush=True)
                await asyncio.sleep(0.01) 
            print("\n[UPDATE] Firmware envoyé, en attente de confirmation du robot...")
            timeout = 60
            elapsed_time = 0
            while not self.update_complete and elapsed_time < timeout:
                await asyncio.sleep(1)
                elapsed_time += 1

            if not self.update_complete:
                print("[ERROR] Aucune confirmation reçue, la mise à jour pourrait avoir échoué.")
            else:
                print("[SUCCESS] Mise à jour terminée avec succès.")

        except Exception as e:
            print(f"Erreur: {e}")

    def _run_update(self):
        """Exécute `send_firmware` dans la boucle asyncio existante."""
        self.loop.run_until_complete(self.send_firmware())

    def updateWithBT(self):
        """Lance l'update dans un thread avec une priorité CPU élevée en fonction de l'OS."""
        def run_with_priority():
            try:
                p = psutil.Process(os.getpid())
                system_name = platform.system()

                if system_name == "Windows":
                    p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)  # Windows: priorité modérée
                    print("🟢 Priorité du thread ajustée (Windows, Below Normal).")
                elif system_name in ["Linux", "Darwin"]:  # Darwin = macOS
                    p.nice(0)  # Linux/macOS: valeur normale (sans sudo)
                    print("🟢 Priorité du thread ajustée (Linux/macOS, Normal).")
                else:
                    print(f"⚠️ Système inconnu ({system_name}), priorité non modifiée.")

                self._run_update()  # Exécute la boucle asyncio dans le thread
            except Exception as e:
                print(f"⚠️ Erreur en changeant la priorité: {e}")

        # Lancer le processus dans un thread dédié
        thread = threading.Thread(target=run_with_priority, daemon=True)
        thread.start()

    def updateWithWS(self):
        """Lance l'update via WebSocket."""
        print("🟢 Envoi du firmware via WebSocket.")
        self._run_update()
    
    def download_firmware(self, firmware_id):
        url = f"http://51.210.150.191:8001/api/firmwares/download/{firmware_id}/"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open("firmware.bin", "wb") as f:
                    f.write(response.content)
                print("Firmware downloaded successfully.")
                return True
            else:
                print(f"Failed to download firmware: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error downloading firmware: {e}")
            return False

    def check_update(self):
        print("Checking for updates...")

        try:
            requests.get("https://ilorobot.com", timeout=3)
        except requests.ConnectionError:
            print("No network connection. Skipping update check.")
            return
        try:
            req = requests.get("http://51.210.150.191:8001/api/firmwares/latest/")
            if req.status_code == 200:
                data = req.json()
                latest_version = data["version"]
                print(f"Latest version: {latest_version}")
                if latest_version != self.version:
                    print("New update available.")
                    update = input("Do you want to update? (y/n): ").strip().lower()
                    if update == "y":
                        if self.download_firmware(data["id"]):
                            if self.use_ble:
                                self.updateWithBT()
                            else:
                                self.updateWithWS()
                else:
                    print("No updates available.")
            else:
                print("Failed to check for updates.")
        except Exception as e:
            print(f"Error during update check: {e}")



version = "0.50"

print("ilo robot library version: ", version)
print("For more information about the library use ilo.info() command line")
print("For any help or support contact us on our website, ilorobot.com")
# -----------------------------------------------------------------------------

pyperclip.copy("""ilo.check_robot_on_wifi()""")

connection_type = 0
# WiFi
tab_IP = []
# Serial
tab_PORT = []
# BLE
tab_ADDRESS = []

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

def co_send_msg(ws, message):
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
        global tab_IP
        tab_IP = []
        ilo_AP = False

        try:
            ws_url = "ws://192.168.4.1:4583"
            print(ws_url)
            ws = websocket.create_connection(ws_url, timeout=1.3)
            if co_send_msg(ws, "<ilo>") == "ilo":
                tab_IP.append(["192.168.4.1", 1, co_send_msg(ws, "<930>")])

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
                    if co_send_msg(ws, "<ilo>") == "ilo":
                        co_send_msg(ws, "<>")
                        tab_IP.append([IP, ilo_ID, co_send_msg(ws, "<930>")])
                        ilo_ID += 1
                        c += 1
                        ws.close()

                except:
                    continue  # Continue to the next IP

        table = PrettyTable() # Display the IP and ID
        table.field_names = ["IP Address", "ID of ilo", "Name of ilo"]  # add the name info <93>
        for row in tab_IP:
            table.add_row(row)

        if len(tab_IP) != 0:
            print(table)
            print("")
            print(
                "Use for example: my_ilo = ilo.robot(1) to create an object my_ilo with the ID = 1")
            global connection_type
            connection_type = 0
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
    global connection_type
    global tab_PORT

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
                    tab_PORT = [[COM, 1, response]]
                    table = PrettyTable()
                    table.field_names = ["Device port","ID of ilo", "Name of ilo"]
                    table.add_row([COM, 1, response])
                    print(table)
                    print("")
                    print("Use for example: my_ilo = ilo.robot(1) to create an object my_ilo with the ID = 1")
                    connection_type = 1
                else:
                    print(f"No valid response received on {COM}")
        except (serial.SerialException, OSError) as e:
            print(f"Error with port {COM} : {e}")

    else:
        try:
            tab_PORT = []
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
                            tab_PORT.append([port.device, ilo_ID, response])
                            ilo_ID += 1
                        else:
                            print(f"No valid response received on {port.device}")
                except (serial.SerialException, OSError) as e:
                    print(f"Error with port {port.device} : {e}")
                    continue

            table = PrettyTable()
            table.field_names = ["Device port", "ID of ilo", "Name of ilo"]

            for row in tab_PORT:
                table.add_row(row)

            if len(tab_PORT) != 0:
                print(table)
                print("")
                print(
                    "Use for example: my_ilo = ilo.robot(1) to create an object my_ilo with the ID = 1")
                connection_type = 1
            else:
                print(
                    "Unfortunately, no ilo is connected to your computer. Check your connection.")

        except Exception as e:
            print(f"Serial error: {e}")
            return None

def check_robot_on_bluetooth():
    pyperclip.copy('''my_ilo = ilo.robot(1)''')
    global tab_ADDRESS
    global connection_type

    print("[ILO] Scanning for BLE devices...")
    try:    
        devices = ble_lib.scan_devices()
        table = PrettyTable()
        table.field_names = ["Device adress", "ID of ilo", "Name of ilo"]
        i = 1
        for device in devices:
            if str(device[0]).startswith("ilo_BLE_"):
                table.add_row([device[1], i, device[0]])
                tab_ADDRESS.append(device)
                i += 1
        if len(tab_ADDRESS) == 0:
            print("No ilo found.")
            return False
        else:
            print(table)
            connection_type = 2
            print("Connection type: BLE")
            return True
        
    except Exception as e:
        print(f"Error check robot on Bluetooth: {e}")
        return False

# -----------------------------------------------------------------------------

def get_IP_from_ID(ID):
    '''
    Get the IP address of the robot from its ID
    '''
    # print(ID)
    global tab_IP
    for item in tab_IP:
        # print(item[1])
        if item[1] == ID:
            return item[0]
    return None

def get_PORT_from_ID(ID):
    '''
    Get the PORT of the robot from its ID
    '''
    global tab_PORT
    for item in tab_PORT:
        if item[1] == ID:
            return item[0]
    return None

# def get_ADDRESS_from_ID(ID):
#     '''
#     Get the ADDRESS of the robot from its ID
#     '''
#     global tab_ADDRESS
#     for item in tab_ADDRESS:
#         if item[1] == ID:
#             return item[0]
#     return None
# -----------------------------------------------------------------------------

class robot(object):
    global connection_type
    robots_connected = {}  # Variable de classe pour garder une trace des connexions actives

    def __init__(self, ID):
        self.ID = ID

        pyperclip.copy('''my_ilo.step('front')''')

        # if connection_type == 0:
        if ID in robot.robots_connected:  # Vérification si un robot avec cet ID est déjà connecté
            print(f"Un robot avec l'ID {ID} est déjà connecté, déconnexion automatique de l'ancien robot.")
            old_robot = robot.robots_connected[ID]
            # Arrêter le thread mais sans déconnexion immédiate
            if connection_type == 0:
                old_robot.recv_thread_running = False
            else:
                pass

        self.Port = 4583
        self.ws = None
        self.connect = False
        self.IP = get_IP_from_ID(self.ID)

        self.recv_thread = None
        self.recv_thread_running = False

        # elif connection_type == 1:
        self.port = get_PORT_from_ID(self.ID)
        self.ser = None
        # self.connect = False


        self.version = ""

        #BLE:
        # self.adress = get_ADDRESS_from_ID(self.ID)
        self.ble_device = None

        self.hostname = ""

        self.red_color = 0
        self.green_color = 0
        self.blue_color = 0

        self.clear_left = 0
        self.clear_center = 0
        self.clear_right = 0

        self.line_left = 0
        self.line_center = 0
        self.line_right = 0

        self.line_threshold_value = 0

        self.distance_front = 0
        self.distance_right = 0
        self.distance_back = 0
        self.distance_left = 0

        self.roll = 0
        self.pitch = 0
        self.yaw = 0

        self.accX = 0
        self.accY = 0
        self.accZ = 0
        self.gyroX = 0
        self.gyroY = 0
        self.gyroZ = 0

        self.battery_status = 0
        self.battery_pourcentage = 0

        self.red_led = 0
        self.green_led = 0
        self.blue_led = 0

        self.motor_ping = 0
        self.motor_speed = 0
        self.motor_angle = 0
        self.motor_id = 0
        self.temp_motor = 0
        self.motor_volt = 0
        self.motor_torque = 0
        self.motor_current = 0
        self.motor_is_moving = 0
        self.acc_motor = 0
        self.tempo_pos = 0
        self.kp = 0
        self.ki = 0
        self.kd = 0

        self.ssid = ""
        self.password = ""

        self.accessory = 0
        self.potard_value = 0

        self.global_trame = ""

        self.version = ""

        self.manufacturing_date = ""
        self.first_use_date = ""
        self.product_version = ""
        self.product_id = ""

        self.marker = True

        self._response_event = threading.Event()
        self._response_value = None

        # -- marin add all other data of the robot
        # -- thinking to a solution to get data from additional captor connected on the top of the robot via accessory PCB

        # Ajouter ce robot à la liste des robots connectés
        robot.robots_connected[self.ID] = self

        print(f"Robot with ID {self.ID} will be connected")
        if self.ID:
            # print("You are trying to connect to: ", self.IP)
            self.connection()
        else:
            print("You have to run the command [ilo.check_ilo_on_network()] to know if there are robots present on your network")
            print("or")
            print("Run the command [ilo.check_ilo_on_serial()] to know if there are robots connected to your computer")
    # -----------------------------------------------------------------------------
    def connection(self):
        """
        Connection of your machine to robot object 
        """

        self.send_msg("<ilo>")

        #if self.hostname != "":

            #self.send_msg("<ilo>")

            #print('Your robot is already connected to ' + self.hostname)
            # -- marin check if the websocket is well working (test un envoi de trame ou spécific methode

        #else:
        print("Trying to connect to the robot with ID: ", self.ID, " and connection type: ", connection_type)
        if connection_type == 0: 
            try:
                # Start the WebSocket d'envoie de trame
                self.ws = websocket.create_connection(
                    f"ws://{self.IP}:{self.Port}")

                # Vérifie si un ancien thread de réception est actif et l'arrête avant d'en démarrer un nouveau
                if self.recv_thread and self.recv_thread.is_alive():
                    print("Stopping the previous reception thread...")
                    self.stop_reception()

                # Start the WebSocket de reception in a separate thread
                self.recv_thread_running = True
                self.recv_thread = threading.Thread(
                    target=self.web_socket_receive)
                self.recv_thread.start()

                self.connect = True
                self.send_msg("<ilo>")
                self.send_msg("<500y>")
                time.sleep(0.2)
                self.get_name()
                time.sleep(0.2)
                print('Your are connected to ' + self.hostname)
                updater = IloUpdater(self.ser, self.version, False, self.ws)
                updater.check_update()

            except Exception as e:
                print(
                    "Connection error: you have to be connect to the ilo wifi network")
                print(
                    " --> If the malfunction persists, switch off and switch on ilo")
                print(f"Error connecting to the robot: {e}")
                self.connect = False

        elif connection_type == 1:
            try:
                # Start the serial connection
                self.ser = serial.Serial(self.port, 115200)

                self.connect = True
                self.send_msg("<ilo>")
                
                time.sleep(0.2)
                self.get_name()
                time.sleep(0.2)
                print('Your are connected to ' + self.hostname)
                
            except Exception as e:
                print("Connection error: you must be connected to the ilo robot")
                print(
                    " --> If the malfunction persists, switch off and switch on ilo, or try using another cable")
                print(f"Error connecting to the robot: {e}")
                self.connect = False

        elif connection_type == 2:
            def notification_handler(sender, data):
                try:
                    decoded_data = data.decode('utf-8')
                    print(f"Received: {decoded_data}")
                    self.process_received_data(decoded_data)
                except UnicodeDecodeError:
                    print(f"Received non-UTF-8 data: {data}")
            print("Connecting to the BLE device...")
            try:
                self.ble_device = ble_lib.connect(tab_ADDRESS[self.ID - 1][1])
                ble_lib.subscribe_to_notifications(CHARACTERISTIC_UUID, notification_handler)
                self.connect = True
                print("Connected to the BLE device.")
                self.send_msg("<ilo>")
                self.send_msg("<500y>")
                time.sleep(0.2)
                self.get_name()
                time.sleep(0.2)
                print('Your are connected to ' + self.hostname)
                updater = IloUpdater(self.ble_device, self.version)
                updater.check_update()
            except Exception as e:
                print(f"Error connecting to the BLE device: {e}")
                self.connect = False

    # -----------------------------------------------------------------------------
    def send_msg(self, message):
        self._response_event.clear()
        if connection_type == 0:
            if self.ws and self.connect:
                try:
                    self.ws.send(message)
                    print(f"Sent:     {message}")
                except websocket.WebSocketException as e:
                    print(f"Error sending message: {e}")
            else:
                print("WebSocket is not connected.")

        elif connection_type == 1:
            if self.ser and self.connect:
                try:
                    self.ser.write(message.encode())
                    print(f"Sent:     {message}")

                    invalid_prefixes = ("<a", "<i", "<13", "<31", "<51", "<52", "<53", "<54", "<55", "<56", "<57", "<58",
                                        "<610", "<620", "<680", "<690", "<70", "<72", "<80", "<90", "<91", "<94", "<103", "<0", "<>")

                    if message.startswith(invalid_prefixes):
                        pass
                    else:
                        # start_time = time.time()
                        # while time.time() - start_time < 1:
                        self.serial_read()

                except Exception as e:
                    print(f"Error sending message: {e}")
            else:
                print("Serial is not connected.")
        elif connection_type == 2:
            if self.ble_device and self.connect:
                try:
                    ble_lib.write_characteristic(self.ble_device, CHARACTERISTIC_UUID, message.encode())
                    print(f"Sent:     {message}")
                except Exception as e:
                    print(f"Error sending message: {e}")
        else:
            print("No connection established (error sending message).")
    # -----------------------------------------------------------------------------
    def web_socket_receive(self):
        """
        Thread function to continuously receive data from the WebSocket.
        Stops when recv_thread_running is set to False.
        """
        while self.recv_thread_running:
            try:
                self.ws.settimeout(1) # Ajout d'un timeout pour que recv() ne bloque pas indéfiniment
                data = self.ws.recv() # Timeout de 1 seconde pour éviter un blocage sur recv()
                if data:
                    if '/' in data:
                        sub_trames = data.split('/')[1:-1]
                        for sub_trame in sub_trames:
                            self.process_received_data(f"<{sub_trame}>")
                    else:
                        self.process_received_data(data)
                        self.marker = True
            except websocket.WebSocketTimeoutException:
                # Timeout atteint, continue à boucler pour vérifier recv_thread_running
                continue
            except websocket.WebSocketException as e:
                # Gestion des erreurs de WebSocket, afficher l'erreur pour le débogage
                print(f"WebSocket error: {e}")
                break

        print("Thread de réception terminé.")

    def serial_read(self):
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

                char = self.ser.read().decode()
                if char == '<':
                    trame += char
                    break

            while True:
                if time.time() - start_time > timeout:
                    print("[serial_read] Timeout atteint dans la seconde boucle")
                    return

                char = self.ser.read().decode()
                if char:
                    trame += char
                    if char == '>':
                        break
            if trame:
                self.process_received_data(trame)
                self.marker = True
        except serial.SerialException as e:
            print(f"Error: {e}")
    # -----------------------------------------------------------------------------
    def process_received_data(self, data):
        """
        Process the data received from the WebSocket or Serial and update the robot's attributes
        """
        # print(f"[process_received_data] Received: {data}")
        # Here you can parse the received data and update relevant attributes
        # Example: Update distance values

        try:

            if str(data[1:4]) == "10r":  # get_color_rgb
                self.red_color = int(data[data.find('r')+1: data.find('g')])
                self.green_color = int(data[data.find('g')+1: data.find('b')])
                self.blue_color = int(data[data.find('b')+1: data.find('>')])

            if str(data[1:4]) == "11l":  # get_color_clear
                self.clear_left = int(data[data.find('l')+1: data.find('m')])
                self.clear_center = int(data[data.find('m')+1: data.find('r')])
                self.clear_right = int(data[data.find('r')+1: data.find('>')])

            if str(data[1:4]) == "12l":  # get_line
                self.line_left = int(data[data.find('l')+1: data.find('m')])
                self.line_center = int(data[data.find('m')+1: data.find('r')])
                self.line_right = int(data[data.find('r')+1: data.find('>')])

            if str(data[1:4]) == "14t":  # get_line_threshold_value
                self.line_threshold_value = int(
                    data[data.find('t')+1: data.find('>')])

            if str(data[1:4]) == "20f":  # get_distance
                self.distance_front = int(
                    data[data.find('f')+1: data.find('r')])
                self.distance_right = int(
                    data[data.find('r')+1: data.find('b')])
                self.distance_back = int(
                    data[data.find('b')+1: data.find('l')])
                self.distance_left = int(
                    data[data.find('l')+1: data.find('>')])

            if str(data[1:4]) == "21f":  # get_distance_front
                self.distance_front = int(
                    data[data.find('f')+1: data.find('>')])

            if str(data[1:4]) == "22r":  # get_distance_right
                self.distance_right = int(
                    data[data.find('r')+1: data.find('>')])

            if str(data[1:4]) == "23b":  # get_distance_back
                self.distance_back = int(
                    data[data.find('b')+1: data.find('>')])

            if str(data[1:4]) == "24l":  # get_distance_left
                self.distance_left = int(
                    data[data.find('l')+1: data.find('>')])

            if str(data[1:4]) == "30r":  # get_angle - données traités en degrés
                self.roll = float(data[data.find('r')+1: data.find('p')])
                self.pitch = float(data[data.find('p')+1: data.find('y')])
                self.yaw = float(data[data.find('y')+1: data.find('>')])

            if str(data[1:4]) == "32x":  # get_raw_imu
                self.accX = int(data[data.find('x')+1: data.find('y')])
                self.accY = int(data[data.find('y')+1: data.find('z')])
                self.accZ = int(data[data.find('z')+1: data.find('r')])
                self.gyroX = int(data[data.find('r')+1: data.find('p')])
                self.gyroY = int(data[data.find('p')+1: data.find('g')])
                self.gyroZ = int(data[data.find('g')+1: data.find('>')])

            if str(data[1:4]) == "40s":  # get_battery
                self.battery_status = int(
                    data[data.find('s')+1: data.find('p')])
                self.battery_pourcentage = int(
                    data[data.find('p')+1: data.find('>')])

            if str(data[1:4]) == "50r":  # get_led_color
                self.red_led = int(data[data.find('r')+1: data.find('g')])
                self.green_led = int(data[data.find('g')+1: data.find('b')])
                self.blue_led = int(data[data.find('b')+1: data.find('>')])

            if str(data[1:4]) == "60i":  # ping_single_motor
                self.motor_id = int(data[data.find('i')+1: data.find('s')])
                self.motor_ping = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "611":  # get_single_motor_speed
                self.motor_id = int(data[data.find('i')+1: data.find('s')])
                self.motor_speed = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "621":  # get_single_motor_angle
                self.motor_id = int(data[data.find('i')+1: data.find('s')])
                self.motor_angle = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "63i":  # get_temp_single_motor
                self.motor_id = int(data[data.find('i')+1: data.find('s')])
                self.temp_motor = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "64i":  # get_volt_single_motor
                self.motor_id = int(data[data.find('i')+1: data.find('s')])
                self.motor_volt = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "65i":  # get_torque_single_motor
                self.motor_id = int(data[data.find('i')+1: data.find('s')])
                self.motor_torque = int(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "66i":  # get_current_single_motor
                self.motor_id = int(data[data.find('i')+1: data.find('s')])
                self.motor_current = int(
                    data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "67i":  # get_motor_is_moving
                self.motor_id = int(data[data.find('i')+1: data.find('s')])
                self.motor_is_moving = int(
                    data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "681":  # get_acc_motor
                self.acc_motor = int(data[data.find('a')+1: data.find('>')])

            if str(data[1:4]) == "691":  # get_tempo_pos
                self.tempo_pos = int(data[data.find('t')+1: data.find('>')])

            if str(data[1:4]) == "71p":  # get_pid
                self.kp = float(data[data.find('p')+1: data.find('i')])
                self.ki = float(data[data.find('i')+1: data.find('d')])
                self.kd = float(data[data.find('d')+1: data.find('>')])

            if str(data[1:4]) == "92s":  # get_wifi_credentials
                self.ssid = str(data[data.find('s')+1: data.find('p')])
                self.password = str(data[data.find('p')+1: data.find('>')])

            if str(data[1:4]) == "93n":  # get_name
                self.hostname = str(data[data.find('n')+1: data.find('>')])

            if str(data[1:4]) == "101":  # get_accessory
                self.accessory = float(data[data.find('t')+1: data.find('>')])

            if str(data[1:4]) == "102":  # get_accessory
                self.potard_value = float(data[data.find('a')+1: data.find('>')])

            if str(data[1:4]) == "120":  # get_manufacturing_date
                self.manufacturing_date = str(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "130":  # get_first_use_date
                self.first_use_date = str(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "140":  # get_product_version
                self.product_version = str(data[data.find('s')+1: data.find('>')])

            if str(data[1:4]) == "150":  # get_product_id
                self.product_id = str(data[data.find('s')+1: data.find('>')])

            if str(data[1:5]) == "500y": # get_version
                self.version = str(data[data.find('y')+1: data.find('>')])

            if str(data[1:4]) == "500":  # get_global_trame
                
                self.version = str(data[data.find('y')+1: data.find('>')])
                print(f"Version: {self.version}")

            self._response_event.set()

        except Exception as e:
            # -- marin add e to check the error
            print(f'[COMMUNICATION ERROR] data process: {e}')
            return None
    # -----------------------------------------------------------------------------
    def stop_reception(self):
        """
        Stop the WebSocket reception thread and close the connection.
        """
        if not self.recv_thread_running:
            return  # Si le thread est déjà arrêté, ne rien faire

        print("Stopping reception thread...")
        self.recv_thread_running = False  # Arrêter la boucle dans le thread de réception

        if self.ws:
            try:
                self.ws.close()
                self.connect = False  # Mettre à jour l'état de connexion après la fermeture de WebSocket
                print("WebSocket successfully closed")
            except Exception as e:
                print(f"Erreur lors de la fermeture de la WebSocket: {e}")

        # if self.recv_thread and self.recv_thread.is_alive():
        if self.recv_thread:
            print("Waiting for the reception thread to stop...")
            self.recv_thread.join(timeout=2)

        if self.ID in robot.robots_connected:
            del robot.robots_connected[self.ID]

        print(f"WebSocket connection closed for the robot {self.ID}.")
    # -----------------------------------------------------------------------------
    def __del__(self):
        """
        Destructor to ensure the WebSocket connection is closed gracefully
        and the ID is removed from the list of connected robots
        """
        print(f"Destruction de l'objet robot avec l'ID {self.ID}")
        if connection_type == 0:
            self.ws.close()
        
        elif connection_type == 1:
            pass   # on ne peut pas paraleléliser les ouverture de port comme les websocket
        elif connection_type == 2:
            ble_lib.disconnect(self.ble_device)
        else:
            pass  
    # -----------------------------------------------------------------------------
    def test_connection(self):
        """
        Test the connection to the robot via a try of stop method
        :return: True or False
        """
        if connection_type == 0:
            try:
                self.send_msg("<ilo>")
                return True
            except:
                print("Error connection to the robot")
                return False
        elif connection_type == 1:
            try:
                self.send_msg("<ilo>")
                return True
            except:
                print("Error connection to the robot")
                return False
        elif connection_type == 2:
            try:
                self.send_msg("<ilo>")
                return True
            except:
                print("Error connection to the robot")
                return False
    # -----------------------------------------------------------------------------
    def correction_command(self, acc, list_course):
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
        self.send_msg("<>")

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
            self.send_msg(msg)
        elif direction == 'back':
            msg = '<a60vpx0' + str(step) + 'yr>'
            self.send_msg(msg)
        elif direction == 'left':
            msg = '<a60vpxy0' + str(step) + 'r>'
            self.send_msg(msg)
        elif direction == 'right':
            msg = '<a60vpxy1' + str(step) + 'r>'
            self.send_msg(msg)
        elif direction == 'rot_trigo':
            msg = '<a60vpxyr0' + str(step) + '>'
            self.send_msg(msg)
        elif direction == 'rot_clock':
            msg = '<a60vpxyr1' + str(step) + '>'
            self.send_msg(msg)
        else:
            print(
                "[ERROR] 'Direction' should be 'front', 'back', 'left', 'rot_trigo', 'rot_clock'")
            
        if finish_state == True:
            print("Finish state is True")
            # self._response_event.wait(timeout=5)
            # return (self.version)

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
        self.send_msg(msg)

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

        corrected_command = self.correction_command(acc, command)
        self.send_msg(corrected_command)

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
        corrected_command = self.correction_command(acc, command)
        self.send_msg(corrected_command)

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
        self.send_msg(msg)

    def get_tempo_pos(self):
        """
        Get the tempo of the position control
        """
        self.send_msg("<691>")
        self._response_event.wait(timeout=5)
        return (self.tempo_pos)

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
        self.send_msg(command)

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
        self.send_msg(msg)

    def get_pid(self):
        """
        Get the actual value of the proportional gain, the integral gain and the derivative gain
        """
        self.send_msg("<71>")
        self._response_event.wait(timeout=5)
        return (self.kp, self.ki, self.kd)
    # -----------------------------------------------------------------------------
    def get_color_rgb(self):
        """
        Displays the color below ilo
        """
        self.send_msg("<10>")
        self._response_event.wait(timeout=5)

        return (self.red_color, self.green_color, self.blue_color)

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
        self.send_msg(msg)
    # -----------------------------------------------------------------------------
    def get_color_clear(self):
        """
        Displays the brightness below ilo
        """
        self.send_msg("<11>")
        self._response_event.wait(timeout=5)
        return (self.clear_left, self.clear_center, self.clear_right)

    def get_color_clear_left(self):
        """
        Displays the brightness below ilo only with left sensor
        """
        self.send_msg("<11>")
        self._response_event.wait(timeout=5)
        return (self.clear_left)

    def get_color_clear_center(self):
        """
        Displays the brightness below ilo only with central sensor
        """
        self.send_msg("<11>")
        self._response_event.wait(timeout=5)
        return (self.clear_center)

    def get_color_clear_right(self):
        """
        Displays the brightness below ilo only with right sensor
        """
        self.send_msg("<11>")
        self._response_event.wait(timeout=5)
        return (self.clear_right)
    # -----------------------------------------------------------------------------
    def get_line(self):
        """
        Detects whether ilo is on a line or not
        """
        self.send_msg("<12>")
        self._response_event.wait(timeout=5)
        return (self.line_left, self.line_center, self.line_right)

    def get_line_left(self):
        """
        Detects whether ilo is on a line or not according to the left sensor
        """
        self.send_msg("<12>")
        self._response_event.wait(timeout=5)
        return (self.line_left)

    def get_line_center(self):
        """
        Detects whether ilo is on a line or not according to the central sensor
        """
        self.send_msg("<12>")
        self._response_event.wait(timeout=5)
        return (self.line_center)

    def get_line_right(self):
        """
        Detects whether ilo is on a line or not according to the right sensor
        """
        self.send_msg("<12>")
        self._response_event.wait(timeout=5)
        return (self.line_right)

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
            self.clear_center = 0
            self.get_color_clear()
            while self.clear_center == 0:
                time.sleep(0.1)
            value = round(self.clear_center*1.2)
            print(f"La nouvelle valeur de seuil est: {value}")

        msg = "<13t"+str(value)+">"
        self.send_msg(msg)

    def get_line_threshold_value(self):
        """
        Get the actual value of the threshold value for the line detection
        """
        self.send_msg("<14>")
        self._response_event.wait(timeout=5)
        return (self.line_threshold_value)
    # -----------------------------------------------------------------------------
    def get_distance(self):
        """
        Get the distance around ilo
        """
        # self._response_event.clear()
        self.send_msg("<20>")
        # time.sleep(0.15)
        self._response_event.wait(timeout=5)
        return (self.distance_front, self.distance_right, self.distance_back, self.distance_left)

    def get_distance_front(self):
        """
        Get the distance in front of ilo
        """
        self.send_msg("<21>")
        self._response_event.wait(timeout=5)
        return (self.distance_front)

    def get_distance_right(self):
        """
        Get the distance on the right of ilo
        """
        self.send_msg("<22>")
        self._response_event.wait(timeout=5)
        return (self.distance_right)

    def get_distance_back(self):
        """
        Get the distance behind ilo
        """
        self.send_msg("<23>")
        self._response_event.wait(timeout=5)
        return (self.distance_back)

    def get_distance_left(self):
        """
        Get the distance on the left of ilo
        """
        self.send_msg("<24>")
        self._response_event.wait(timeout=5)
        return (self.distance_left)
    # -----------------------------------------------------------------------------
    def get_angle(self):
        """
        Get the angle of ilo
        """
        self.send_msg("<30>")
        self._response_event.wait(timeout=5)
        return (self.roll, self.pitch, self.yaw)

    def get_roll(self):
        """
        Get the roll angle of ilo
        """
        self.send_msg("<30>")
        self._response_event.wait(timeout=5)
        return (self.roll)

    def get_pitch(self):
        """
        Get the pitch angle of ilo
        """
        self.send_msg("<30>")
        self._response_event.wait(timeout=5)
        return (self.pitch)

    def get_yaw(self):
        """
        Get the yaw angle of ilo
        """
        self.send_msg("<30>")
        self._response_event.wait(timeout=5)
        return (self.yaw)

    def reset_angle(self):
        """
        Reset the angle of ilo
        """
        self.send_msg("<31>")

    def get_raw_imu(self):
        """
        Get IMU raw data
        """
        self.send_msg("<32>")
        self._response_event.wait(timeout=5)
        return (self.accX, self.accY, self.accZ, self.gyroX, self.gyroY, self.gyroZ)
    # -----------------------------------------------------------------------------
    def get_battery(self):
        """
        Get battery status (charged or not) and percentage
        """
        self.send_msg("<40>")
        self._response_event.wait(timeout=5)
        return (self.battery_status, self.battery_pourcentage)
    # -----------------------------------------------------------------------------
    def get_led_color(self):
        """
        Get ilo LEDS color
        """
        self.send_msg("<50>")
        self._response_event.wait(timeout=5)
        return (self.red_led, self.green_led, self.blue_led)

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
        self.send_msg(msg)

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
        self.send_msg(msg)

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
        self.send_msg(msg)

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
        self.send_msg(msg)
    
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
        self.send_msg(msg)
    
    def stop_led_word(self):
        """
        Stop the led word
        """
        self.send_msg("<58>")

    # -----------------------------------------------------------------------------
    def get_acc_motor(self):
        """
        Get the acceleration of all motors
        """
        self.send_msg("<681>")
        self._response_event.wait(timeout=5)
        return (self.acc_motor)

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
        self.send_msg(msg)
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
        self.send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self.motor_id, self.motor_ping)
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
        self.send_msg(msg)

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
        self.send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self.motor_id, self.motor_speed)
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
        self.send_msg(msg)
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
        self.send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self.motor_id, self.motor_angle)
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
        self.send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self.motor_id, self.temp_motor)
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
        self.send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self.motor_id, self.volt_motor)
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
        self.send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self.motor_id, self.motor_torque)
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
        self.send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self.motor_id, self.current_motor)
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
        self.send_msg(msg)
        self._response_event.wait(timeout=5)
        return (self.motor_id, self.motor_moving)

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
        self.send_msg(msg)
        
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
        self.send_msg(msg)
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
        self.send_msg(msg)

        msg = "<91p"+str(password)+">"
        self.send_msg(msg)

    def get_wifi_credentials(self):
        """
        Get wifi credentials registered on ilo
        """
        self.send_msg("<92>")
        self._response_event.wait(timeout=5)
        return (self.ssid, self.password)
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
        self.send_msg(msg)

    def get_name(self):
        """
        Get the name you have given to your ilo
        """
        self.send_msg("<93>")
        self.marker = False
        self._response_event.wait(timeout=5)
        return (self.hostname)
    # -----------------------------------------------------------------------------
    def get_accessory(self):
        """
        Get information about the accessory connected to ilo
        """
        self.send_msg("<100>")
        self._response_event.wait(timeout=5)
        return (self.accessory)
    # -----------------------------------------------------------------------------
    def set_debug_state(self, state: bool):  # pas à jour

        if not isinstance(state, bool):
            print("[ERROR] 'state' parameter must be a bool like True or False")
            return None

        if state == True:
            msg = "<103s1>"
        else:
            msg = "<103s2>"

        self.send_msg(msg)
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

        self.send_msg(msg)

    def del_trame_s(self):
        """
        Stop the global trame
        """
        self.send_msg("<00>")
    # -----------------------------------------------------------------------------
    def get_diagnostic(self):
        """
        Get a diagnosis of robot status
        """
        self.send_msg("<110>")
    # -----------------------------------------------------------------------------
    def set_manufacturing_date(self, date: str):
        """
        Set the manufacturing date of ilo
        """
        msg = "<121s"+str(date)+">"
        self.send_msg(msg)

    
    def get_manufacturing_date(self):
        """
        Get the manufacturing date of ilo
        """
        self.send_msg("<120>")
        self._response_event.wait(timeout=5)
        return (self.manufacturing_date)

    def set_first_use_date(self, date: str):
        """
        Set the first use date of ilo
        """
        msg = "<131s"+str(date)+">"
        self.send_msg(msg)

    def get_first_use_date(self):
        """
        Get the first use date of ilo
        """
        self.send_msg("<130>")
        self._response_event.wait(timeout=5)
        return (self.first_use_date)

    def set_product_version(self, version: str):
        """
        Set the version of the product
        """
        msg = "<141s"+str(version)+">"
        self.send_msg(msg)

    def get_product_version(self):
        """
        Get the version of the product
        """
        self.send_msg("<140>")
        self._response_event.wait(timeout=5)
        return (self.product_version)

    def set_product_id(self, id: str):
        """
        Set the id of the product
        """
        msg = "<151s"+str(id)+">"
        self.send_msg(msg)

    def get_product_id(self):
        """
        Get the id of the product
        """
        self.send_msg("<150>")
        self._response_event.wait(timeout=5)
        return (self.product_id)


    def get_robot_version(self):
        """
        Get the version number of the code present on the robot
        """
        self.send_msg("<500y>")
        self._response_event.wait(timeout=5)
        return (self.version)

