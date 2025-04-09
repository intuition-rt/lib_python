import websocket
from prettytable import PrettyTable
import threading
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import time

_tab_IP = []

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

def check_esp_on_wifi():
    """
    Check the presence of the ESP(s) on the network
    """
    try:
        print("Looking for ESP on your network ...")
        global _tab_IP
        _tab_IP = []
        ESP_AP = False

        try:
            ws_url = "ws://192.168.4.1:4583"
            print(ws_url)
            ws = websocket.create_connection(ws_url, timeout=1.3)
            if _co_send_msg(ws, "<esp>") == "esp":
                _tab_IP.append(["192.168.4.1", 1])

                ESP_AP = True
                ws.close()
                print("Your robot is working as an access point")
        except:
            pass

        if not ESP_AP:
            base_ip = "192.168.1."
            ESP_ID = 1
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
                    if _co_send_msg(ws, "<ESP>") == "ESP":
                        _co_send_msg(ws, "<>")
                        _tab_IP.append([IP, ESP_ID])
                        ESP_ID += 1
                        c += 1
                        ws.close()

                except:
                    continue  # Continue to the next IP

        table = PrettyTable() # Display the IP and ID
        table.field_names = ["IP Address", "ID of ESP"]  # add the name info <93>
        for row in _tab_IP:
            table.add_row(row)

        if len(_tab_IP) != 0:
            print(table)
            print("")
            print(
                "Use for example: my_ESP = ESP.robot(1) to create an object my_ESP with the ID = 1")
            global _connection_type
            _connection_type = 0
        else:
            print(
                "Unfortunately, no ESP is present on your current network. Check your connection.")

    except Exception as e:
        print(f"WebSocket error: {e}")

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

class ESP(object):
    _ESP_connected = {}  # Class variable to keep track of active connections

    def __init__(self, ID):
        self._ID = ID

        if ID in ESP._ESP_connected:  # Check if an ESP with this ID is already connected
            print(f"An ESP with ID {ID} is already connected, automatic disconnection of the old ESP.")
            old_robot = ESP._ESP_connected[ID]
            # Stop the thread without immediate disconnection
            old_robot.recv_thread_running = False

        self._Port = 4583
        self._ws = None
        self._connect = False
        self._IP = _get_IP_from_ID(self._ID)

        self._recv_thread = None
        self._recv_thread_running = False

        self._distance_front = 0
        self._distance_right = 0
        self._distance_back = 0
        self._distance_left = 0

        self._response_event = threading.Event()
        self._response_value = None

        # Ajouter l'ESP à la liste des ESP connectés
        ESP._ESP_connected[self._ID] = self

        print(f"ESP with ID {self._ID} will be connected")
        if self._ID:
            # print("You are trying to connect to: ", self._IP)
            self._connection()
        else:
            print("You have to run the command [plottica.check_esp_on_wifi()] to know if there are robots present on your network")

    def _connection(self):
        """
        Connection of your machine to robot object 
        """

        self._send_msg("<esp>")

        print("Trying to connect to the ESP with ID: ", self._ID)
        try:
            # Start the WebSocket to send a frame
            self._ws = websocket.create_connection(
                f"ws://{self._IP}:{self._Port}")

            # Checks whether an old receive thread is active and stops it before starting a new one
            if self._recv_thread and self._recv_thread.is_alive():
                print("Stopping the previous reception thread...")
                self._stop_reception()

            # Start WebSocket reception in a separate thread
            self._recv_thread_running = True
            self._recv_thread = threading.Thread(
                target=self._web_socket_receive)
            self._recv_thread.start()

            self._connect = True
            self._send_msg("<esp>")
            time.sleep(0.2)
            time.sleep(0.2)
            print('Your are connected to your ESP')

        except Exception as e:
            print(
                "Connection error: you have to be connect to the ESP wifi network")
            print(
                " --> If the malfunction persists, switch off and switch on your ESP")
            print(f"Error connecting to the ESP: {e}")
            self._connect = False

    def _send_msg(self, message):
        self._response_event.clear()
        if self._ws and self._connect:
            try:
                self._ws.send(message)
                print(f"Sent:     {message}")
            except websocket.WebSocketException as e:
                print(f"Error sending message: {e}")
        else:
            print("WebSocket is not connected.")

    def _web_socket_receive(self):
        """
        Thread function to continuously receive data from the WebSocket.
        Stops when recv_thread_running is set to False.
        """
        while self._recv_thread_running:
            try:
                self._ws.settimeout(1) # Add a timeout so that recv() doesn't block indefinitely
                data = self._ws.recv() # 1 second timeout to avoid recv() blocking
                if data:
                    if '/' in data:
                        sub_trames = data.split('/')[1:-1]
                        for sub_trame in sub_trames:
                            self._process_received_data(f"<{sub_trame}>")
                    else:
                        self._process_received_data(data)
                        self._marker = True
            except websocket.WebSocketTimeoutException:
                # Timeout reached, keep looping to check recv_thread_running
                continue
            except websocket.WebSocketException as e:
                # WebSocket error handling, display error for debugging
                print(f"WebSocket error: {e}")
                break

        print("Thread de réception terminé.")

    def _stop_reception(self):
        """
        Stop the WebSocket reception thread and close the connection.
        """
        if not self._recv_thread_running:
            return  # If the thread is already stopped, do nothing

        print("Stopping reception thread...")
        self._recv_thread_running = False  # Stop the loop in the receive thread

        if self._ws:
            try:
                self._ws.close()
                self._connect = False  # Update connection status after closing WebSocket
                print("WebSocket successfully closed")
            except Exception as e:
                print(f"Error closing WebSocket: {e}")

        # if self._recv_thread and self._recv_thread.is_alive():
        if self._recv_thread:
            print("Waiting for the reception thread to stop...")
            self._recv_thread.join(timeout=2)

        if self._ID in ESP._robots_connected:
            del ESP._robots_connected[self._ID]

        print(f"WebSocket connection closed for the robot {self._ID}.")

    def _process_received_data(self, data):
        """
        Process the data received from the WebSocket and update the ESP's attributes
        """
        # print(f"[process_received_data] Received: {data}")
        # Here you can parse the received data and update relevant attributes
        # Example: Update distance values

        try:

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

            self._response_event.set()

        except Exception as e:
            # -- marin add e to check the error
            print(f'[COMMUNICATION ERROR] data process: {e}')
            return None
        
    def start_trame_s(self, hertz : int, param_list: list):
        """
        Get the global trame of ilo
        """

        msg = "<0h" +str(hertz)+"z/"

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

        msg = msg + ">"

        self._send_msg(msg)

    def stop_trame_s(self):
        """
        Stop the global trame
        """
        self._send_msg("<00>")

    def draw_data(get_value_func, xmax , ymax, label="Sensor"):
        matplotlib.use("tkagg")  # Force GUI backend for pop-up window
        plt.ion()
        fig, ax = plt.subplots()
        plt.show(block=False)  # Important for GUI pop-up!

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
        
        print("CRTL+C to stop the display")

        try:
            while True:
                val = get_value_func()
                xdata.append(i)
                ydata.append(val)
                xdata = xdata[-100:]
                ydata = ydata[-100:]

                x_smooth = np.linspace(xdata[0], xdata[-1], 200)
                y_smooth = np.interp(x_smooth, xdata, ydata)

                line.set_data(x_smooth, y_smooth)
                ax.set_xlim(max(0, i - 100), i + 1)
                value_text.set_text(f"{val:.1f}")

                ax.figure.canvas.draw()
                ax.figure.canvas.flush_events()
                i += 1

        except KeyboardInterrupt:
            print("Stopped by user.")
            plt.ioff()
            plt.show()