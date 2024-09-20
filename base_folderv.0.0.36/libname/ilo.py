# This python script is the library for using the robot ilo with python command on WiFi
# INTUITION ROBOTIQUE ET TECHNOLOGIES ALL RIGHT RESERVED
# 16/09/2024
# code work with 1.2.7 version of c++
#-----------------------------------------------------------------------------
version = "0.36"
print("ilo robot library version ", version)
print("For more information about the library use ilo.info() command line")
print("For any help or support contact us on our website, ilorobot.com")
#-----------------------------------------------------------------------------
import time, keyboard, websocket, threading
from prettytable import PrettyTable

tab_IP = []
#-----------------------------------------------------------------------------
def info():
    """
    Print info about ilorobot
    """
    print("ilo robot is an education robot controlable by direct python command")
    print("To know every fonction available with ilo,  use ilo.list_function() command line")
    print("You are using the version ", version)
#-----------------------------------------------------------------------------
def list_function():
    '''
    Print the list of all the functions available in the library
    '''
    print("info()                                        -> print info about ilorobot")
    print(" ")
    print("check_robot_on_network()                      -> scan the network for robots")
    print(" ")
    print("stop()                                        -> stop the robots and free the engines")
    print("")
    print("pause()                                       -> stop the robot and block engines")
    print("")
    print("step(direction)                               -> move by step ilorobot with selected direction during 2 seconds")
    print("                                                 direction is a string and should be (front, back, left, right, rot_trigo or rot_clock)")
    print(" ")
    print("list_order(ilo_list)                          -> ilo will execute a list of successive displacment define in ilo_list")
    print("                                                 example of list ['front', 'left', 'front', 'rot_trigo', 'back'] ")
    print("                                                 value of ilo_list are string")
    print(" ")
    print("move(direction, speed)                        -> move ilorobot with selected direction speed and time control")
    print("                                                 direction is a string and should be (front, back, left, right, rot_trigo or rot_clock)")
    print("                                                 speed is an integer from 0 to 100 as a pourcentage ")
    print(" ")
    print("direct_contol(axial, radial, rotation)        -> control ilorobot with full control ")
    print("                                                 axial, radial and rotation are 3 integer from 0 to 255")
    print("                                                 value from 0 to 128 are negative, value from 128 to 255 are positve")
    print(" ")
    print("game()                                        -> control ilo using arrow or numb pad of your keyboard")
    print("                                                 available keyboard touch: 8,2,4,6,1,3 | space = stop | esc = quit")
    print("")
    print("set_name()                                    -> change the name of your robot")
    print("")
    print("get_name()                                    -> take a look at your robot's name")
    print("")
    print("get_color_rgb()                               -> return RGB color under the robot with list form as [color_left, color_middle, color_right]")
    print("")
    print("get_color_clear()                             -> return lightness under the robot with list from as [light_left, light_middle, light_right]")
    print("")
    print("get_line()                                    -> detects whether the robot is on a line or not and return a list from as [line_left, line_center, line_right]")
    print("")
    print("set_line_threshold_value(value)               -> set the threshold value for the line detector")
    print("                                                 value is an integer")
    print("")
    print("get_line_treshold_value()                     -> return the value of treshold value as an integer")
    print("")
    print("get_distance()                                -> return distance around the robot with list from as [front, right, back, left]")
    print("")
    print("get_angle()                                   -> return angle of the robot with list from as [roll, pitch, yaw]")
    print("")
    print("reset_angle()                                 -> reset the angle of the robot")
    print("")
    print("get_raw_imu()                                 -> return info about the imu with list from as [accX, accY, accZ, gyroX, gyroY, gyroZ]")
    print("")
    print("get_battery()                                 -> return info about the battery of the robot with list from as [battery status, battery pourcentage]")
    print("")
    print("get_led_color()                               -> return info about ilo leds colors")
    print("")
    print("set_led_color(red,green,blue)                 -> set ilorobot leds colors")
    print("                                                 red, green and blue are integers and must be between 0 and 255")
    print("")
    print("set_led_shape(value)                          -> set ilorobot leds shape")
    print("                                                 value is a string and must be selected from this list: [front, back, right, left, rot_clock, rot_trigo, ")
    print("                                                 stop, play, pause, smiely, 10(number 0), 11 (number 1), up to number 9, ring_1, ring_2, ring_3, ring_4, ")
    print("                                                 ring_5]")
    print("                                                 8 = ")
    print("")
    print("set_led_anim(value)                           -> set ilorobot leds animations")
    print("                                                 value is a string and must be selected from this list: [labyrinth, color_displacement, line_tracking, imu_water, ")
    print("                                                 distance_displacement]")
    print("")
    print("set_led_captor(bool)                          -> turns on/off the lights under the robot")
    print("")
    print("set_led_single(bool, id, r, g, b)             -> set one ilorobot leds colors")
    print("                                                 bool must be True or False")
    print("                                                 id must be a integer")
    print("                                                 red, green and blue are integers and must be between 0 and 255")
    print("")
    print("get_acc_motor()                               -> return info about the acceleration of the robot")
    print("")
    print("set_acc_motor(val)                            -> set the acceleration of ilo")
    print("                                                 val is an integer")
    print("")
    print("drive_single_motor_speed(id, value)           -> control only one motor at a time")
    print("                                                 id is a integer and must be between 0 and 255")
    print("                                                 value is a integer and must be between -100 and 100")
    print("")
    print("set_autonomous_mode(number)                   -> launches the robot in autonomous mode")
    print("                                                 number is an integer and must be between 0 and 5")
    print("                                                 1 = labyrinth          2 = color with displacement      3 = line tracking")
    print("                                                 4 = IMU water mode     5 = distance sensor led")
    print("")
    print("set_wifi_credentials(ssid, password)          -> save your wifi credentials")
    print("                                                 ssid and password must be strings")
    print("")
    print("get_wifi_credentials()                        -> obtain the wifi credentials registered on the robot")
    print("")
    print("test_connection()                             -> stop the robot if it is properly connected")
#-----------------------------------------------------------------------------
def co_web_socket_send(ws, message):
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

def check_robot_on_network():
    """
    Check the presence of the ilo(s) on the network
    """
    try:
        print("Looking for ilo on your network ...")
        global tab_IP
        tab_IP = []
        ilo_AP = False
        
        try:
            ws_url = "ws://192.168.4.1:4583"
            print(ws_url)
            ws = websocket.create_connection(ws_url, timeout = 1.3)
            if co_web_socket_send(ws, "<ilo>") == "ilo":
                tab_IP.append(["192.168.4.1", 1, co_web_socket_send(ws, "<930>")])
                
                ilo_AP = True
                ws.close()
                print("Your robot is working as an access point")
        except: 
            pass
        
        if not ilo_AP:
            base_ip = "192.168.1."
            ilo_ID = 1
            c = 3                       # Checking 3 more IP addresses after success

            for i in range(100, 200):  # Between 192.168.1.100 and 192.168.1.200
                ip_check = f"{base_ip}{i}"
                IP = ip_check
                ws_url = f"ws://{IP}:4583"
                print(f"Checking {ws_url}")
                c -= 1
                if c == 0:
                    break
                
                try:
                    ws = websocket.create_connection(ws_url, timeout = 1.3)  # Set timeout for each connection
                    if co_web_socket_send(ws, "<ilo>") == "ilo":
                        tab_IP.append([IP, ilo_ID, co_web_socket_send(ws, "<930>")])
                        ilo_ID += 1
                        c += 1
                        ws.close()
                        
                except:
                    continue  # Continue to the next IP
                    
       
        # Display the IP and ID
        table = PrettyTable()
        table.field_names = ["IP Address", "ID of ilo", "Name of ilo"] #♥add the name info <93>
        for row in tab_IP:
            table.add_row(row)
        
        if len(tab_IP) != 0:
            print(table)
            print("")
            print("Use for example: my_ilo = ilo.robot(1) to create an object my_ilo with the ID = 1")
        else:
            print("Unfortunately, no ilo is present on your current network. Check your connection.")

    except Exception as e:
        print(f"WebSocket error: {e}")    
#-----------------------------------------------------------------------------   
def get_IP_from_ID(ID):
    '''
    Get the IP address of the robot from its ID
    '''
    print(ID)
    global tab_IP
    for item in tab_IP:
        print(item[1])
        if item[1] == ID:
            return item[0]
    return None
#-----------------------------------------------------------------------------
class robot(object):
    
    def __init__(self, ID):
        self.ID = ID
        self.Port = 4583
        self.ws = None
        self.connect = False
        self.IP = get_IP_from_ID(self.ID)

        self.hostname = ""
        
        self.red_color   = 0
        self.green_color = 0
        self.blue_color  = 0

        self.clear_left   = 0
        self.clear_center = 0
        self.clear_right  = 0

        self.line_left   = 0
        self.line_center = 0 
        self.line_right  = 0
        
        self.line_threshold_value = 0
        
        self.distance_front = 0
        self.distance_right = 0
        self.distance_back  = 0
        self.distance_left  = 0

        self.roll  = 0
        self.pitch = 0
        self.yaw   = 0

        self.accX  = 0
        self.accY  = 0
        self.accZ  = 0
        self.gyroX = 0
        self.gyroY = 0
        self.gyroZ = 0

        self.battery_status      = 0
        self.battery_pourcentage = 0

        self.red_led   = 0
        self.green_led = 0
        self.blue_led  = 0
  
        self.motor_ping      = 0
        self.motor_speed     = 0
        self.motor_angle     = 0
        self.motor_id        = 0
        self.temp_motor      = 0
        self.motor_volt      = 0
        self.motor_torque    = 0
        self.motor_current   = 0
        self.motor_is_moving = 0
        self.acc_motor       = 0
        
        self.ssid     = ""
        self.password = ""

        self.global_trame = ""
        
        self.marker = True
 
        # -- marin add all other data of the robot
        # -- thinking to a solution to get data from additionnal captor connnected on the top of the robot via accesoire PCB
        
        self.recv_thread = None
        self.recv_thread_running = False
        
        if self.ID:
            print("You are trying to connect to: ", self.IP)
            self.connection()
        else:
            print("You have to run before the command line to know the robot present our your network: ilo.check_ilo_on_network()")
    #-----------------------------------------------------------------------------
    def connection(self):
        """
        Connection of your machine to robot object 
        """
        if self.connect:
            print('Your robot is already connected')
            #-- marin check if the websocket is well working (test un envoi de trame ou spécific methode
            
        else:
            try:
                self.ws = websocket.create_connection(f"ws://{self.IP}:{self.Port}")
                self.web_socket_send("<ilo>")
                print('Your are connected')
                self.connect = True
                
                # Start the WebSocket reception in a separate thread
                self.recv_thread_running = True
                self.recv_thread = threading.Thread(target=self.web_socket_receive)
                self.recv_thread.start()
            
            except Exception as e:
                    print("Error connection: you have to be connect to the ilo wifi network")
                    print(" --> If the disfonction continu, switch off and switch on ilo")
                    print(f"Error connecting to the robot: {e}")
                    self.connect = False   
    #-----------------------------------------------------------------------------
    def web_socket_send(self, message):
        """
        Send a message over the WebSocket connection.
        """
        if self.ws and self.connect:
            try:
                self.ws.send(message)
                print(f"Sent:     {message}")
            except websocket.WebSocketException as e:
                print(f"Error sending message: {e}")
        else:
            print("WebSocket is not connected.")
    #-----------------------------------------------------------------------------
    def web_socket_receive(self):
        """
        Thread function to continuously receive data from the WebSocket
        """
        while self.recv_thread_running:
            try:
                data = self.ws.recv()
                if data:
                    if '/' in data:
                        # parcing
                        sub_trames = data.split('/')[1:-1]
                        
                        for sub_trame in sub_trames:
                            self.process_received_data(f"<{sub_trame}>")
                    else :
                        self.process_received_data(data)
                        self.marker = True
            except websocket.WebSocketException as e:
                print(f"WebSocket error: {e}")
                #-- marin bonne solution ici pour debugger d'afficher directement le message d'erreur 
                break
    #-----------------------------------------------------------------------------
    def process_received_data(self, data):
        """
        Process the data received from the WebSocket and update the robot's attributes
        """
        print("")
        print(f"Received: {data}")
        # Here you can parse the received data and update relevant attributes
        # Example: Update distance values
        
        try: 

            if str(data[1:3]) == "10": # get_color_rgb
                self.red_color   = int(data[data.find('r')+1 : data.find('g')])
                self.green_color = int(data[data.find('g')+1 : data.find('b')])
                self.blue_color  = int(data[data.find('b')+1 : data.find('>')])

            if str(data[1:3]) == "11": # get_color_clear
                self.clear_left   = int(data[data.find('l')+1 : data.find('m')])
                self.clear_center = int(data[data.find('m')+1 : data.find('r')])
                self.clear_right  = int(data[data.find('r')+1 : data.find('>')])
            
            if str(data[1:3]) == "12": # get_line
                self.line_left   = int(data[data.find('l')+1 : data.find('m')])
                self.line_center = int(data[data.find('m')+1 : data.find('r')])
                self.line_right  = int(data[data.find('r')+1 : data.find('>')])
    
            if str(data[1:3]) == "14" : # get_line_threshold_value
                self.line_threshold_value = int(data[data.find('t')+1 : data.find('>')])
            
            if str(data[1:3]) == "20": # get_distance
                self.distance_front = int(data[data.find('f')+1 : data.find('r')])
                self.distance_right = int(data[data.find('r')+1 : data.find('b')])
                self.distance_back  = int(data[data.find('b')+1 : data.find('l')])
                self.distance_left  = int(data[data.find('l')+1 : data.find('>')])
            
            #--marin add self to every parmaeter and add inside the init methof 

            if str(data[1:3]) == "30": # get_angle - données traités en degrés
                self.roll  = float(data[data.find('r')+1 : data.find('p')])
                self.pitch = float(data[data.find('p')+1 : data.find('y')])
                self.yaw   = float(data[data.find('y')+1 : data.find('>')])
        
    
            if str(data[1:3]) == "32": #get_raw_imu
                self.accX  = int(data[data.find('x')+1 : data.find('y')])
                self.accY  = int(data[data.find('y')+1 : data.find('z')])
                self.accZ  = int(data[data.find('z')+1 : data.find('r')])
                self.gyroX = int(data[data.find('r')+1 : data.find('p')])
                self.gyroY = int(data[data.find('p')+1 : data.find('g')])
                self.gyroZ = int(data[data.find('g')+1 : data.find('>')])
    
            if str(data[1:3]) == "40": # get_battery
                self.battery_status      = int(data[data.find('s')+1 : data.find('p')])
                self.battery_pourcentage = int(data[data.find('p')+1 : data.find('>')]) 
            
            if str(data[1:3]) == "50": # get_led_color
                self.red_led   = int(data[data.find('r')+1 : data.find('g')])
                self.green_led = int(data[data.find('g')+1 : data.find('b')])
                self.blue_led  = int(data[data.find('b')+1 : data.find('>')])

            if str(data[1:3]) == "60": # ping_single_motor
                self.motor_id   = int(data[data.find('i')+1 : data.find('s')])
                self.motor_ping = int(data[data.find('s')+1 : data.find('>')])

            if str(data[1:4]) == "611": # get_single_motor_speed
                self.motor_id    = int(data[data.find('i')+1 : data.find('s')])
                self.motor_speed = int(data[data.find('s')+1 : data.find('>')])
            
            if str(data[1:4]) == "621": # get_single_motor_angle
                self.motor_id    = int(data[data.find('i')+1 : data.find('a')])
                self.motor_angle = int(data[data.find('a')+1 : data.find('>')])

            if str(data[1:3]) == "63": # get_temp_single_motor
                self.motor_id   = int(data[data.find('i')+1 : data.find('t')])
                self.temp_motor = int(data[data.find('t')+1 : data.find('>')])

            if str(data[1:3]) == "64": # get_volt_single_motor
                self.motor_id   = int(data[data.find('i')+1 : data.find('v')])
                self.motor_volt = int(data[data.find('v')+1 : data.find('>')])

            if str(data[1:3]) == "65": # get_torque_single_motor
                self.motor_id     = int(data[data.find('i')+1 : data.find('t')])
                self.motor_torque = int(data[data.find('t')+1 : data.find('>')])

            if str(data[1:3]) == "66":  # get_current_single_motor
                self.motor_id = int(data[data.find('i')+1 : data.find('c')])
                self.motor_current = int(data[data.find('c')+1 : data.find('>')])

            if str(data[1:3]) == "67":  # get_motor_is_moving
                self.motor_id = int(data[data.find('i')+1 : data.find('s')])
                self.motor_is_moving = int(data[data.find('s')+1 : data.find('>')])

            if str(data[1:3]) == "69": # get_acc_motor
                self.acc_motor = int(data[data.find('a')+1 : data.find('>')])
            
            if str(data[1:3]) == "92": # get_wifi_credentials
                self.ssid     = str(data[data.find('s')+1 : data.find('p')])
                self.password = str(data[data.find('p')+1 : data.find('>')])
            
            if str(data[1:3]) == "93": # get_name
                self.hostname = str(data[data.find('n')+1 : data.find('>')])
    
        except:
            print('[COMMUNICATION ERROR] data process')  # -- marin add e to check the error
            return None  
    #-----------------------------------------------------------------------------
    def stop_reception(self):
        """
        Stop the WebSocket reception thread and close the connection
        """
        self.recv_thread_running = False
        if self.recv_thread:
            self.recv_thread.join()
        
        if self.ws:
            self.ws.close()
            self.connect = False
            print("WebSocket connection closed.")
    #-----------------------------------------------------------------------------
    def __del__(self):
        """
        Destructor to ensure the WebSocket connection is closed gracefully
        """
        self.stop_reception()
    #-----------------------------------------------------------------------------
    def test_connection(self):
        """
        Test the connection to the robot via a try of stop method
        :return: True or False
        """
        try:
            self.web_socket_send("<ilo>")
            return True
        except:
            print("Error connection to the robot")
            return False
    #-----------------------------------------------------------------------------    
    def stop(self):
        """
        Stop ilo and free its engines
        """
        self.web_socket_send("<>")   
    #-----------------------------------------------------------------------------
    def pause(self):
        """
        Stop ilo and block its motors
        """
        self.direct_control(128,128,128)  
    #-----------------------------------------------------------------------------
    def step(self, direction: str):
        """
        Move ilo in the selected direction for 2 seconds

        Parameters:
            direction (str): The direction in which the robot is moving

        Raises:
            TypeError: If the direction is not a string
            ValueError: If the direction is not one of the following: front, back, left, right, rot_trigo, rot_clock or stop

        Examples:
            my_ilo.step("front")
        """
        if not isinstance(direction, str):
            print ('[ERROR] Direction should be a string')
            return None

        if direction == 'front':
            self.web_socket_send("<avpx110yr>")
        elif direction == 'back':
            self.web_socket_send("<avpx010yr>")
        elif direction == 'left':
            self.web_socket_send("<avpxy010r>")
        elif direction == 'right':
            self.web_socket_send("<avpxy110r>")
        elif direction == 'rot_trigo':
            self.web_socket_send("<avpxyr090>")
        elif direction == 'rot_clock':
            self.web_socket_send("<avpxyr190>")
        elif direction == 'stop':
            self.stop()
        else:
            print('[ERROR] Direction should be "front", "back", "left", "rot_trigo", "rot_clock", "stop"')
    #-----------------------------------------------------------------------------
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
            print ('ilo_list should be a list')
            return None

        for i in range(len(ilo_list)):
            self.step(ilo_list[i])     
    #-----------------------------------------------------------------------------
    def correction_command(self, list_course):
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
        elif 10  > int(list_course[1]) >= 1:
            list_course[1] = str('00') + str(list_course[1])
        else:
            list_course[1] = str('000')

        if int(list_course[2]) >= 100:
            list_course[2] = str(list_course[2])
        elif 100 > int(list_course[2]) >= 10:
            list_course[2] = str('0') + str(list_course[2])
        elif 10  > int(list_course[2]) >= 1:
            list_course[2] = str('00') + str(list_course[2])
        else:
            list_course[2] = str('000')

        new_command = []
        str_command = str(list_course[0] + list_course[1] + list_course[2])
        new_command = "<av" + str_command +"pxyr>"
        return new_command
    #-----------------------------------------------------------------------------
    def move(self, direction: str, speed: int):
        """
        Move ilo with selected direction and speed

        Parameters:
            direction (str): The direction in which the robot is moving
            speed (int): The speed of the robot, as a percentage

        Raises:
            TypeError: If the direction is not a string
            ValueError: If the direction is not one of the following: front, back, left, right, rot_trigo, rot_clock or stop
            TypeError: If the speed is not an integer
            ValueError: If the speed is not between 0 and 100

        Examples:
            my_ilo.move("front", 50)
        """

        #ilo.move('front', 50)

        #global preview_stop
        #preview_stop = True

        if not isinstance(direction, str):
            print ("[ERROR] 'direction' parameter must be a string")
            return None
        if not isinstance(speed, int):
            print ("[ERROR] 'speed' parameter must be a integer")
            return None     
        if speed> 100 or speed<0:
            print ("[ERROR] 'speed' parameter must be include between 0 and 100")
            return None

        if direction == 'front':
            command = [int((speed*1.28)+128),128,128]
        elif direction == 'back':
            command = [int(-(speed*1.28))+128,128,128]
        elif direction == 'left':
            command = [128,int((speed*1.28)+128),128]
        elif direction == 'right':
            command = [128,int(-(speed*1.28)+128),128]
        elif direction == 'rot_trigo':
            command = [128,128,int(-(speed*1.28)+128)]
        elif direction == 'rot_clock':
            command = [128,128,int((speed*1.28)+128)]
        else:
            print("[ERROR] 'direction' parameter should be 'front', 'back', 'left', 'rot_trigo', 'rot_clock', 'stop'")
            return None

        corrected_command = self.correction_command(command)
        self.web_socket_send(corrected_command) 
    #-----------------------------------------------------------------------------
    def direct_control(self, axial: int, radial: int, rotation: int):
        """
        Control ilo with full control \n
        Value from 0 to 128 are negative and value from 128 to 255 are positive

        Parameters:
            axial (int): [...]
            radial (int): [...]
            rotation (int): [...]

        Raises:
            TypeError: If axial is not an integer
            ValueError: If axial is not between 0 and 255
            TypeError: If radial is not an integer
            ValueError: If radial is not between 0 and 255
            TypeError: If rotation is not an integer
            ValueError: If rotation is not between 0 and 255

        Examples:
            my_ilo.direct_control(150, 150, 150)
        """

        if not isinstance(axial, int):
            print ("[ERROR] 'axial' parameter must be a integer")
            return None
        if axial> 255 or axial<0:
            print ("[ERROR] 'axial' parameter must be include between 0 and 255")
            return None
        if not isinstance(radial, int):
            print ("[ERROR] 'radial' parameter must be a integer")
            return None
        if radial> 255 or radial<0:
            print ("[ERROR] 'radial' parameter must be include between 0 and 255")
            return None
        if not isinstance(rotation, int):
            print ("[ERROR] 'rotation' parameter must be a integer")
            return None
        if rotation> 255 or rotation<0:
            print ("[ERROR] 'rotation' parameter must be include between 0 and 255")
            return None

        command = [axial, radial, rotation]
        corrected_command = self.correction_command(command)
        self.web_socket_send(corrected_command)  
    #-----------------------------------------------------------------------------
    def game(self):
        """
        Control ilo using arrow or numb pad of your keyboard. \n
        Available keyboard touch: 8,2,4,6,1,3 | space = stop | esc = quit

        Raises:
            ConnectionError: If you are not connected to ilo
        
        Examples:
            my_ilo.game()
        """

        if self.test_connection() == True:
            axial_value = 128
            radial_value = 128
            rotation_value = 128
            self.stop()
            new_keyboard_instruction = False

            print('Game mode start, use keyboard arrow to control ilo')
            print("Press echap to leave the game mode")

            while (True):
                if keyboard.is_pressed("8"):
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    axial_value = axial_value + 5
                    if axial_value > 255:
                        axial_value = 255
                elif keyboard.is_pressed("2"):
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    axial_value = axial_value - 5
                    if axial_value < 1:
                        axial_value = 0
                elif keyboard.is_pressed("6"):
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    radial_value = radial_value + 5
                    if radial_value > 255:
                        radial_value = 255
                elif keyboard.is_pressed("4"):
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    radial_value = radial_value - 5
                    if radial_value < 1:
                        radial_value = 0
                elif keyboard.is_pressed("3"):
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    rotation_value = rotation_value + 5
                    if rotation_value > 255:
                        rotation_value = 255
                elif keyboard.is_pressed("1"):
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    rotation_value = rotation_value - 5
                    if rotation_value < 1:
                        rotation_value = 0
                elif keyboard.is_pressed("5"):
                    new_keyboard_instruction = True
                    time.sleep(0.05)
                    axial_value = 128
                    radial_value = 128
                    rotation_value = 128
                elif keyboard.is_pressed("esc"):
                    self.stop()
                    break

                if new_keyboard_instruction == True:
                    self.direct_control(axial_value, radial_value, rotation_value)
                    new_keyboard_instruction = False
        else:
            print("You have to be connected to ILO before play with it, use ilo.connection()")   
    #-----------------------------------------------------------------------------
    def get_color_rgb(self):
        """
        Displays the color below ilo
        """
        self.web_socket_send("<10>")
        time.sleep(0.1)
        return (self.red_color, self.green_color, self.blue_color)
    #-----------------------------------------------------------------------------
    def get_color_clear(self):
        """
        Displays the brightness below ilo
        """
        self.web_socket_send("<11>")
        time.sleep(0.1)
        return (self.clear_left, self.clear_center, self.clear_right)
    
    def get_color_clear_left(self):
        """
        Displays the brightness below ilo only with left sensor
        """
        self.web_socket_send("<11>")
        time.sleep(0.1)
        return (self.clear_left)
    
    def get_color_clear_center(self):
        """
        Displays the brightness below ilo only with central sensor
        """
        self.web_socket_send("<11>")
        time.sleep(0.1)
        return (self.clear_center)

    def get_color_clear_right(self):
        """
        Displays the brightness below ilo only with right sensor
        """
        self.web_socket_send("<11>")
        time.sleep(0.1)
        return (self.clear_right)
    #-----------------------------------------------------------------------------
    def get_line(self):
        """
        Detects whether ilo is on a line or not
        """
        self.web_socket_send("<12>")
        time.sleep(0.1)
        return (self.line_left, self.line_center, self.line_right)

    def get_line_left(self):
        """
        Detects whether ilo is on a line or not according to the left sensor
        """
        self.web_socket_send("<12>")
        time.sleep(0.1)
        return (self.line_left)
    
    def get_line_center(self):
        """
        Detects whether ilo is on a line or not according to the central sensor
        """
        self.web_socket_send("<12>")
        time.sleep(0.1)
        return (self.line_center)

    def get_line_right(self):
        """
        Detects whether ilo is on a line or not according to the right sensor
        """
        self.web_socket_send("<12>")
        time.sleep(0.1)
        return (self.line_right)

    def set_line_threshold_value(self, value: int):
        """
        Set the new threshold value for the line detection

        Parameters:
            value (int): new threshold value

        Raises:
            TypeError: If value is not an integer

        Examples:
            my_ilo.set_line_treshold_value(40)
        """

        if not isinstance(value, int):
            print ("[ERROR] 'value' parameter must be a integer")
            return None

        msg = "<13t"+str(value)+">"
        self.web_socket_send(msg)  
     
    def get_line_threshold_value(self):
        """
        Displays the threshold value for the line detection
        """
        self.web_socket_send("<14>")
        time.sleep(0.1)
        return (self.line_threshold_value)
    #-----------------------------------------------------------------------------
    def get_distance(self):
        """
        Get the distance around ilo
        """
        self.web_socket_send("<20>")
        time.sleep(0.15)
        return (self.distance_front, self.distance_right, self.distance_back, self.distance_left)
    
    def get_distance_front(self):
        """
        Get the distance in front of ilo
        """
        self.web_socket_send("<20>")
        time.sleep(0.1)
        return (self.distance_front)
   
    def get_distance_right(self):
        """
        Get the distance on the right of ilo
        """
        self.web_socket_send("<20>")
        time.sleep(0.1)
        return (self.distance_right)
    
    def get_distance_back(self):
        """
        Get the distance behind ilo
        """
        self.web_socket_send("<20>")
        time.sleep(0.1)
        return (self.distance_back)
    
    def get_distance_left(self):
        """
        Get the distance on the left of ilo
        """
        self.web_socket_send("<20>")
        time.sleep(0.1)
        return (self.distance_left)
    #-----------------------------------------------------------------------------
    def get_angle(self):
        """
        Get the angle of ilo
        """
        self.web_socket_send("<30>")
        time.sleep(0.1)
        return (self.roll, self.pitch, self.yaw)
    
    def get_roll(self):
        """
        Get the roll angle of ilo
        """
        self.web_socket_send("<30>")
        time.sleep(0.1)
        return (self.roll)

    def get_pitch(self):
        """
        Get the pitch angle of ilo
        """
        self.web_socket_send("<30>")
        time.sleep(0.1)
        return (self.pitch)
    
    def get_yaw(self):
        """
        Get the yaw angle of ilo
        """
        self.web_socket_send("<30>")
        time.sleep(0.1)
        return (self.yaw)

    def reset_angle(self):
        """
        Reset the angle of ilo
        """
        self.web_socket_send("<31>")

    def get_raw_imu(self):
        """
        Get IMU raw data
        """
        self.web_socket_send("<32>")
        time.sleep(0.1)
        return (self.accX, self.accY, self.accZ, self.gyroX, self.gyroY, self.gyroZ)
    #-----------------------------------------------------------------------------
    def get_battery(self):
        """
        Get battery status (charged or not) and percentage
        """
        self.web_socket_send("<40>")
        time.sleep(0.1)
        return (self.battery_status, self.battery_pourcentage) 
    #-----------------------------------------------------------------------------
    def get_led_color(self):
        """
        Get ilo LEDS color
        """
        self.web_socket_send("<50>")
        time.sleep(0.1)
        return (self.red_led, self.green_led, self.blue_led)
            
    def set_led_color(self,red: int, green: int, blue : int):
        """
        Set the ilo LEDS color

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
            print ("[ERROR] 'red' parameter must be a integer")
            return None
        if red>255 or red<0:
            print ("[ERROR] 'red' parameter must be include between 0 and 255")
            return None
        if not isinstance(green, int):
            print ("[ERROR] 'green' parameter must be a integer")
            return None
        if green> 255 or green<0:
            print ("[ERROR] 'green' parameter must be include between 0 and 255")
            return None
        if not isinstance(blue, int):
            print ("[ERROR] 'blue' parameter must be a integer")
            return None
        if blue> 255 or blue<0:
            print ("[ERROR] 'blue' parameter must be include between 0 and 255")
            return None
        
        msg = "<51r"+str(red)+"g"+str(green)+"b"+str(blue)+">"
        self.web_socket_send(msg)

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
            print ("[ERROR] 'value' parameter must be a string")
            return None

        msg = "<52v"+str(value)+">"
        self.web_socket_send(msg)
        
    def set_led_anim(self,value: str):
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
            print ("[ERROR] 'value' parameter must be a string")
            return None


        msg = "<53v"+str(value)+">"
        self.web_socket_send(msg)

    def set_led_single(self, type: str, id: int, red: int, green: int, blue: int):
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
            print ("[ERROR] 'type' parameter must be a string")
            return None
        if type != "center" and type != "circle":
            print ("[ERROR] 'type' parameter must be center or circle")
            return None
        if not isinstance(id, int):
            print ("[ERROR] 'id' parameter must be a integer")
            return None
        
        if not isinstance(red, int):
            print ("[ERROR] 'red' parameter must be a integer")
            return None
        if red> 255 or red<0:
            print ("[ERROR] 'red' parameter must be include between 0 and 255")
            return None
        if not isinstance(green, int):
            print ("[ERROR] 'green' parameter must be a integer")
            return None
        if green> 255 or green<0:
            print ("[ERROR] 'green' parameter must be include between 0 and 255")
            return None
        if not isinstance(blue, int):
            print ("[ERROR] 'blue' parameter must be a integer")
            return None
        if blue> 255 or blue<0:
            print ("[ERROR] 'blue' parameter must be include between 0 and 255")
            return None
        
        if type == "center":
            type = "true"
        if type == "circle":
            type = "false"
        msg = "<55t"+str(type)+"d"+str(id)+"r"+str(red)+"g"+str(green)+"b"+str(blue)+">"
        self.web_socket_send(msg)

    def set_led_captor(self,state: bool):
        """
        lights up the leds under ilo

        Parameters:
            state (bool): allows you to turn on or off the leds

        Raises:
            TypeError: If state is not a bool

        Examples:
            my_ilo.set_led_captor(True)
        """

        if not isinstance(state, bool):
            print ("[ERROR] 'state' parameter must be a bool")
            return None

        if (state == True):
            msg = "<54l1>"
        elif (state == False) :
            msg = "<54l0>"
        self.web_socket_send(msg)
    #-----------------------------------------------------------------------------
    def get_acc_motor(self):
        """
        Get the acceleration of all motors
        """
        self.web_socket_send("<69>")
        time.sleep(0.1)
        return (self.acc_motor)
    
    def set_acc_motor(self, value: int):
        """
        Set the acceleration of all motors

        Parameters:
            value (int): the acceleration value

        Raises:
            TypeError: If value is not an integer
            ValueError: If value is not between 10 and 100

        Examples:
            my_ilo.set_acc_motor(67)
        """

        if not isinstance(value, int):
            print ("[ERROR] 'value' parameter must be a integer")
            return None
        if value> 100 or value<10:
            print ("[ERROR] 'value' parameter must be include between 10 and 100")
            return None

        if value < 10 : value = 10
        elif value > 100 : value = 100
        msg = "<68a"+str(value)+">"
        self.web_socket_send(msg) 
    #-----------------------------------------------------------------------------
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
            print ("[ERROR] 'id' parameter must be a integer")
            return None
        if id>255 or id<0:
            print ("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = "<60i"+str(id)+">"
        self.web_socket_send(msg)
        time.sleep(0.1)
        return (self.motor_id, self.motor_ping)
    # <610i1v3000>
    def drive_single_motor_speed(self, id: int, value: int):
        """
        Drive a single motor in speed with is id

        Parameters:
            id (int): the motor id
            value (int): the motor speed in percentage

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255
            TypeError: If 'value' is not an integer
            ValueError: If 'value' is not between -100 and 100

        Examples:
            my_ilo.drive_single_motor_speed(1, 50)
        """

        if not isinstance(id, int):
            print ("[ERROR] 'id' parameter must be a integer")
            return None
        if id>255 or id<0:
            print ("[ERROR] 'id' parameter must be include between 0 and 255")
            return None
        
        if not isinstance(value, int):
            print ("[ERROR] 'value' parameter must be a integer")
            return None
        if value> 100 or value<-100:
            print ("[ERROR] 'value' parameter must be include between -100 and 100")
            return None
        
        if id < 0 : id = 0
        elif id > 255 : id = 255
        if value < -100 : value = -100
        elif value > 100 : value = 100
        value = value * 70
        msg = "<610i"+str(id)+"v"+str(value)+">"
        self.web_socket_send(msg)

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
            print ("[ERROR] 'value' parameter must be a integer")
            return None
        
        self.drive_single_motor_speed(1,value)

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
            print ("[ERROR] 'value' parameter must be a integer")
            return None
        
        self.drive_single_motor_speed(2,value)

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
            print ("[ERROR] 'value' parameter must be a integer")
            return None
        
        self.drive_single_motor_speed(4, value)

    def drive_single_motor_motor_back_right(self, value: int):
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
            print ("[ERROR] 'value' parameter must be a integer")
            return None
        
        self.drive_single_motor_speed(3, value)
    #<611i1s3000>
    def get_single_motor_speed(self, id: int):
        """
        Get the speed of single motor with is id

        Parameters:
            id (int): the motor whose speed you want to know

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255

        Examples:
            my_ilo.get_single_motor_speed(3)
        """

        if not isinstance(id, int):
            print ("[ERROR] 'id' parameter must be a integer")
            return None
        if id>255 or id<0:
            print ("[ERROR] 'id' parameter must be include between 0 and 255")
            return None
        
        msg = "<611i"+str(id)+">"
        self.web_socket_send(msg)
        time.sleep(0.1)
        return (self.motor_id, self.motor_speed)
    # <620i6a90>
    def drive_single_motor_angle(self, id: int, angle: int):
        """
        Drive a single motor in position with is id

        Parameters:
            id (int): the motor id
            value (int): the motor angle

        Raises:
            TypeError: If 'id' is not an integer
            ValueError: If 'id' is not between 0 and 255
            TypeError: If 'angle' is not an integer
            ValueError: If 'angle' is not between 0 and 4096

        Examples:
            my_ilo.drive_single_motor_speed(1, 50)
        """

        if not isinstance(id, int):
            print ("[ERROR] 'id' parameter must be a integer")
            return None
        if id>255 or id<0:
            print ("[ERROR] 'id' parameter must be include between 0 and 255")
            return None
        
        if not isinstance(angle, int):
            print ("[ERROR] 'value' parameter must be a integer")
            return None
        if angle>4096 or angle<0:
            print ("[ERROR] 'value' parameter must be include between 0 and 4096")
            return None
        
        if id < 0 : id = 0
        elif id > 255 : id = 255
        if angle < 0 : angle = 0
        elif angle > 4096 : angle = 4096
        msg = "<610i"+str(id)+"a"+str(angle)+">"
        self.web_socket_send(msg)

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
            print ("[ERROR] 'id' parameter must be a integer")
            return None 
        if id>255 or id<0:
            print ("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = "<621i"+str(id)+">"
        self.web_socket_send(msg)
        time.sleep(0.1)
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
            print ("[ERROR] 'id' parameter must be a integer")
            return None
        if id>255 or id<0:
            print ("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = "<63i"+str(id)+">"
        self.web_socket_send(msg)
        time.sleep(0.1)
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
            print ("[ERROR] 'id' parameter must be a integer")
            return None
        if id>255 or id<0:
            print ("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = "<64i"+str(id)+">"
        self.web_socket_send(msg)
        time.sleep(0.1)
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
            print ("[ERROR] 'id' parameter must be a integer")
            return None
        if id>255 or id<0:
            print ("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = "<65i"+str(id)+">"
        self.web_socket_send(msg)
        time.sleep(0.1)
        return (self.motor_id, self.torque_motor)
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
            print ("[ERROR] 'id' parameter must be a integer")
            return None
        if id>255 or id<0:
            print ("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = "<66i"+str(id)+">"
        self.web_socket_send(msg)
        time.sleep(0.1)
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
            print ("[ERROR] 'id' parameter must be a integer")
            return None
        if id>255 or id<0:
            print ("[ERROR] 'id' parameter must be include between 0 and 255")
            return None

        msg = "<67i"+str(id)+">"
        self.web_socket_send(msg)
        time.sleep(0.1)
        return (self.motor_id, self.motor_moving)

    def get_vmax():
        pass

    def set_vmax(vmax):
        pass 

    def set_mode_motor():
        #between position or wheel mode
        pass

    #-----------------------------------------------------------------------------
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
            print ("[ERROR] 'value' parameter must be a string")
            return None

        msg = "<80"+str(value)+">"
        self.web_socket_send(msg) 
    #-----------------------------------------------------------------------------
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
            print ("[ERROR] 'ssid' parameter must be a string")
            return None
            
        if not isinstance(password, str):
            print("[ERROR] 'password' parameter must be a string")
            return None
        
        msg = "<90s"+str(ssid)+">"
        self.web_socket_send(msg)

        msg = "<91p"+str(password)+">"
        self.web_socket_send(msg)

    def get_wifi_credentials(self):
        """
        Get wifi credentials registered on ilo
        """
        self.web_socket_send("<92>")
        time.sleep(0.1)
        return (self.ssid, self.password)
    #-----------------------------------------------------------------------------
    def set_name(self, name: str): # going to be change by <93n>
        """
        Set a new name for your ilo

        Parameters:
            name (str): the name you want for your ilo

        Raises:
            TypeError: If name is not a string

        Examples:
            my_ilo.set_name("Marin's ilo")
        """
    
        if not isinstance(name, str):
            print ("[ERROR] 'name' parameter must be a string")
            return None
        
        msg = "<94n"+str(name)+">"
        self.web_socket_send(msg) 
        
    def get_name(self):
        """
        Reads the name you have given to your ilo
        """
        self.web_socket_send("<93>")
        self.marker = False
        while not self.marker :
            pass
        return (self.hostname)
    #-----------------------------------------------------------------------------
    def set_debug_state(self, state: bool):

        if not isinstance(state, bool):
            print ("[ERROR] 'state' parameter must be a bool like True or False")
            return None

        msg = "<94"+str(state)+">"
        self.web_socket_send(msg)
    #-----------------------------------------------------------------------------
    def get_global_trame(self):
        """
        Get the global trame of ilo
        """
        self.web_socket_send("<0/10/11/12/>")
        time.sleep(0.1)
        return (self.global_trame)
    
    def del_global_trame(self):
        """
        Stop the global trame
        """
        self.web_socket_send("<00>")
    #-----------------------------------------------------------------------------