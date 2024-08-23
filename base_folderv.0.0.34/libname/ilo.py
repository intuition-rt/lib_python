# This python scrip is the library for using the robot ilo with python command on WiFi
# INTUITION ROBOTIQUE ET TECHNOLOGIES ALL RIGHT RESERVED
# 06/08/2024
# code work with 1.2.7 version of c++
#-----------------------------------------------------------------------------
version = "0.34"
print("ilo robot library version ", version)
print("For more information about the library use ilo.info() command line")
print("For any help or support contact us on our website, ilorobot.com")
#-----------------------------------------------------------------------------
import socket, time, keyboard, subprocess, platform, websocket
from prettytable import PrettyTable

tab_IP = []

#-----------------------------------------------------------------------------
def info():
    """
    Print info about ilorobot
    :return:
    """
    print("ilo robot is an education robot controlable by direct python command")
    print("To know every fonction available with ilo,  use ilo.list_function() command line")
    print("You are using the version ", version)
#-----------------------------------------------------------------------------
def list_function():
    print("info()                                        -> print info about ilorobot")
    print(" ")
    print("connection()                                  -> connection your machine to ilorobot")
    print(" ")
    print("stop()                                        -> stop the robot")
    print("")
    print("step(direction)                               -> move by step ilorobot with selected direction during 2 seconds")
    print("                                                 direction is a string and should be (front, back, left, right, rot_trigo or rot_clock)")
    print(" ")
    print("move(direction, speed)                        -> move ilorobot with selected direction speed and time control")
    print("                                                 direction is a string and should be (front, back, left or right)")
    print("                                                 speed is an integer from 0 to 100 as a pourcentage ")
    print(" ")
    print("direct_contol(axial, radial, rotation)        -> control ilorobot with full control ")
    print("                                                 axial, radial and roation are 3 integer from 0 to 255")
    print("                                                 value from 0 to 128 are negative, value from 128 to 255 are positve")
    print(" ")
    print("list_order(ilo_list)                          -> ilo will execute a list of successive displacment define in ilo_list")
    print("                                                 example of list ['front', 'left', 'front', 'rot_trigo', 'back'] ")
    print("                                                 value of ilo_list are a string")
    print(" ")
    print("game()                                        -> control ilo using arrow or numb pad of your keyboard")
    print("                                                 available keyboard touch: 8,2,4,6,1,3   space = stop    esc = quit")
    print("")
    print("get_color_rgb()                               -> return RGB color under the robot with list form as [color_left, color_middle, color_right]")
    print("")
    print("get_color_clear()                             -> return lightness under the robot with list from as [light_left, light_middle, light_right]")
    print("")
    print("get_line()                                    -> detects whether the robot is on a line or not and return a list from as [line_left, line_center, line_right]")
    print("")
    print("set_line_threshold_value()                    -> set the threshold value for the line detector")
    print("")
    print("get_distance()                                -> return distance around the robot with list from as [front, right, back, left]")
    print("")
    print("get_angle()                                   -> return angle of the robot with list from as [roll, pitch, yaw]")
    print("")
    print("reset_angle()                                 -> reset the angle of the robot")
    print("")
    print("get_imu()                                     -> return info about the imu with list from as [gyroX, gyroY, gyroZ, accelX, accelY, accelZ] ")
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
    print("drive_single_motor(id, value)                 -> control only one motor at a time")
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
def socket_send(ws, msg):
    #print(msg)
    try:
        ws.send(msg)
        #time.sleep(0.1)
        return True
    except Exception as e:
        print(f'Error of connection with ilo to send message: {e}')
        return False
    '''
    global s
    try:
        s = socket.socket()
        s.connect((IP, Port))
        s.send(msg.encode())
        #deviceIP = s.getsockname()[0]     # IP of the machine
        #print('device_control_IP', deviceIP)
        time.sleep(0.1)           #  10Hz
        return True
    except:
        print('Error of connection with ilo to send message')
        return False'''
#-----------------------------------------------------------------------------
def socket_read(ws):
    #print(msg)
    global s
    try:
        data = ws.recv()  # Lecture des donnees via WebSocket
        data = data[1:]  # Suppression du premier caractere si necessaire
        
        print(data)
        time.sleep(0.05)  # 20Hz
        return data
    except websocket.WebSocketException as e:
        print(f'Error of connection with ilo to receive message: {e}')
        return False
#-----------------------------------------------------------------------------
def classification(trame, ws):
    try: 
        global s
        socket_send(trame, ws)
        #print('trame envoyée: ', trame)
        data = ws.recv()[2:]

        #data = socket_read(IP, Port)
        #print ('data reçu:   ', data)
        #print ('data indice: ', data[2])
        #print (str(data[2:4]))
        if data[2:4] == "10":
            red_color   = data[data.find('r')+1 : data.find('g')]
            green_color = data[data.find('g')+1 : data.find('b')]
            blue_color  = data[data.find('b')+1 : data.find('>')]
            return red_color, green_color, blue_color

        if data[2:4] == "11":
            clear_left   = int(data[data.find('l')+1 : data.find('m')])
            clear_center = int(data[data.find('m')+1 : data.find('r')])
            clear_right  = int(data[data.find('r')+1 : data.find('>')])
            return clear_left, clear_center, clear_right
        
        if data[2:4] == "12":
            line_left   = int(data[data.find('l')+1 : data.find('m')])
            line_center = int(data[data.find('m')+1 : data.find('r')])
            line_right  = int(data[data.find('r')+1 : data.find('>')])
            return line_left, line_center, line_right

        if data[2:4] == "14" :
            line_threshold_value = int(data[data.find('t')+1 : data.find('>')])
            return line_threshold_value

        if data[2:4] == "20":
            distance_front = data[data.find('f')+1 : data.find('r')]
            distance_right = data[data.find('r')+1 : data.find('b')]
            distance_back  = data[data.find('b')+1 : data.find('l')]
            distance_left  = data[data.find('l')+1 : data.find('>')]
            return distance_front, distance_right, distance_back, distance_left
            
        if data[2:4] == "32":
            roll  = int(data[data.find('r')+1 : data.find('p')])
            pitch = int(data[data.find('p')+1 : data.find('y')])
            yaw   = int(data[data.find('y')+1 : data.find('>')])
            return roll, pitch, yaw
            
        '''if data[2:4] == "32":
            accelX  = int(data[data.find('x')+1 : data.find('y')])
            accelY  = int(data[data.find('y')+1 : data.find('z')])
            accelZ  = int(data[data.find('z')+1 : data.find('t')])
            gyroX   = int(data[data.find('t')+1 : data.find('r')])
            gyroY   = int(data[data.find('r')+1 : data.find('l')])
            gyroZ   = int(data[data.find('l')+1 : data.find('>')])
            return accelX, accelY, accelZ, gyroX, gyroY, gyroZ'''

        if data[2:4] == "40":
            status_battery      = int(data[data.find('s')+1 : data.find('p')])
            pourcentage_battery = int(data[data.find('p')+1 : data.find('>')]) 
            return status_battery, pourcentage_battery
        
        if data[2:4] == "50":
            red_led   = int(data[data.find('r')+1 : data.find('g')])
            green_led = int(data[data.find('g')+1 : data.find('b')])
            blue_led  = int(data[data.find('b')+1 : data.find('>')])
            return red_led, green_led, blue_led
        
        if data[2:4] == "60":
            acc_motor  = int(data[data.find('a')+1 : data.find('>')])
            return acc_motor
        
        if data[2:4] == "91":
            ssid     = str(data[data.find('s')+1 : data.find('p')])
            password = str(data[data.find('p')+1 : data.find('>')])
            return ssid, password
        
        if data[2:4] == "92":
            hostname = str(data[data.find('n')+1 : data.find('>')])
            return hostname
        
    except:
        print('Communication Err: classification')
        return -1
#-----------------------------------------------------------------------------
def check_robot_on_network():

    try:
        print("Looking for ilo on your network ...")
        global tab_IP
        tab_IP = []

        global ws
        
        # Check if we are using ilo on AP
        ilo_AP = False
        
        try:
            ws_url = "ws://192.168.4.1:4583"
            print(ws_url)
            ws = websocket.create_connection(ws_url)
            print("WebSocket connection opened")
            if socket_send(ws, "ilo"):
                tab_IP.append(["192.168.4.1", 1])
                ilo_AP = True
                ws.close()
        except:
            pass
        
        if not ilo_AP:
            base_ip = "192.168.1."
            ilo_ID  = 1
            c = 5                             # checking 5 more IP address after

            try:
                for i in range(100, 200):         # between 192.168.1.100 and 192.168.1.200
                    ip_check = f"{base_ip}{i}"
                    IP = ip_check
                    ws_url = f"ws://{IP}:4583"
                    print(ws_url)
                    ws = websocket.create_connection(ws_url)
                    print("WebSocket connection opened")
                    if (socket_send(ws, "<<>>")):
                        tab_IP.append([IP, ilo_ID])
                        ilo_ID +=1
                    else:
                        c -=1
                        if c==0:
                            break
                    ws.close()
            except:
                print("error connection with ilo on LAN")

        #display the IP and ID
        #print(tab_IP)
        table = PrettyTable()
        table.field_names = ["IP Address", "ID of ilo"]
        for row in tab_IP:
            table.add_row(row)
        
        if len(tab_IP) != 0:
            print(table)
            print("")
            print("Use for exemple: my_ilo = ilo.robot(1) to created object my_ilo with the ID = 1")
        else:
            print("Unfornutaly no one ilo is present on your current network, check you connection.")

    except Exception as e:
        print(f"WebSocket error: {e}")
#-----------------------------------------------------------------------------   
def get_IP_from_ID(ID):
    for item in tab_IP:
        if item[1] == ID:
            return item[0]
    return None
#-----------------------------------------------------------------------------
#exemple of creation of object robot
#my_ilo = ilo.robot(1)

class robot(object):
    
    def __init__(self, ID):
        self.ID = ID
        self.Port = 4583
        self.ws = None
        self.connect = False
        self.IP = get_IP_from_ID(self.ID)
        if self.ID:
            print(self.IP)
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
            return

        else:
            print('Connecting...')
            try:
                self.ws = websocket.create_connection(f"ws://{self.IP}:{self.Port}")
                socket_send(self.ws, "ilo")
                print('Connected')
                self.connect = True
                '''
                ping = socket.socket()
                ping.connect((self.ws))
                
                msg = "ilo"
                ping.send(msg.encode())
                ping.close()

                inform = socket.socket()
                inform.bind((deviceIP, self.Port))

                time.sleep(1)

                s = socket.socket()
                msg = "io"
                s.connect((self.ws))
                s.send(msg.encode())
                '''

            except:
                print("Error connection: you have to be connect to the ilo wifi network")
                print(" --> If the disfonction continu, switch off and switch on ilo")
    #-----------------------------------------------------------------------------
    def test_connection(self):
        """
        Test the connection to the robot via a try of stop method
        :return: True or False 
        """
        try:
            self.stop()
            return True
        except:
            print("Error connection to the robot")
            return False
    #-----------------------------------------------------------------------------    
    def stop(self):
        """
        Stop the robot
        :return:
        """
        socket_send(self.ws, "<<>>")
    #-----------------------------------------------------------------------------
    def pause(self):
        self.direct_control(128,128,128)
    #-----------------------------------------------------------------------------
    def step(self, direction):
        """
        Move by step ilorobot with selected direction during 2 seconds
        :param direction:
        :return: Is a string and should be (front, back, left, right, rot_trigo or rot_clock)
        """
        #ilo.step('front')
        if self.connect == True:
            if not isinstance(direction, str):
                print ('Direction should be an string as front, back, left, rot_trigo, rot_clock, stop')
                return None

            if direction == 'front':
                socket_send(self.ws, "<<avpx110yr>>")
            elif direction == 'back':
                socket_send(self.ws, "<<avpx010yr>>")
            elif direction == 'left':
                socket_send(self.ws, "<<avpxy010r>>")
            elif direction == 'right':
                socket_send(self.ws, "<<avpxy110r>>")
            elif direction == 'rot_trigo':
                socket_send(self.ws, "<<avpxyr090>>")
            elif direction == 'rot_clock':
                socket_send(self.ws, "<<avpxyr190>>")
            elif direction == 'stop':
                self.stop()
            else:
                print('direction name is not correct')
        else:
            print("You are not connected !")
    #-----------------------------------------------------------------------------
    def list_order(self, ilo_list):
        """
        ilo will execute a list of successive displacment define in ilo_list
        :param ilo_list: example : ['front', 'left', 'front', 'rot_trigo', 'back'] (value of ilo_list are a string)
        :return: 
        """
        if isinstance(ilo_list, list) == False:
            print ('the variable should be a list, with inside string as front, back, left, rot_trigo, rot_clock')
            return None

        for i in range(len(ilo_list)):
            self.step(ilo_list[i])
    #-----------------------------------------------------------------------------
    def correction_command(self, list_course):

        #convert a list of 3 elements to a sendable string

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
        Move ilorobot with selected direction, speed and time control
        :param direction: is a string and should be (front, back, left, right, rot_trigo or rot_clock)
        :param speed: is an integer from 0 to 100, as a pourcentage
        :return:
        """

        #ilo.move('front', 50)

        #global preview_stop
        #preview_stop = True

        if not isinstance(direction, str):
            print ("Error : the 'direction' parameter must be a string as front, back, left, rot_trigo or rot_clock")
            return None
        if not isinstance(speed, int):
            print ("Error : the 'speed' parameter must be a integer")
            return None     
        if speed> 100 or speed<0:
            print ("Error : 'speed' parameter must be include between 0 and 100")
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
            print('direction is not correct')
            return None

        corrected_command = self.correction_command(command)
        socket_send(self.ws, corrected_command)
    #-----------------------------------------------------------------------------
    def direct_control(self, axial: int, radial: int, rotation: int):
        """
        Control ilorobot with full control
        :param axial, radial, rotation: is an integer from 0 to 255. Value from 0 to 128 are negative and value from 128 to 255 are positive
        :return:
        """

        if not isinstance(axial, int):
            print ("Error : the 'axial' parameter must be a int")
            return None
        if axial> 255 or axial<0:
            print ("Error : 'axial' parameter must be include between 0 and 255")
            return None
        if not isinstance(radial, int):
            print ("Error : the 'radial' parameter must be a int")
            return None
        if radial> 255 or radial<0:
            print ("Error : 'radial' parameter must be include between 0 and 255")
            return None
        if not isinstance(rotation, int):
            print ("Error : the 'rotation' parameter must be a int")
            return None
        if rotation> 255 or rotation<0:
            print ("Error : 'rotation' parameter must be include between 0 and 255")
            return None

        command = [axial, radial, rotation]
        corrected_command = self.correction_command(command)
        socket_send(self.ws, corrected_command)
    #-----------------------------------------------------------------------------
    def game(self):
        """
        Control ilo using arrow or numb pad of your keyboard. \n
        Available keyboard touch: 8,2,4,6,1,3 | space = stop | esc = quit
        :return:
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
    def set_name(self, name: str):

        if not isinstance(name, str):
            print ("Error : the 'name' parameter must be a string")
            return None
        
        msg = "<0n"+str(name)+">"
        socket_send(self.ws, msg)
        
    def get_name(self):
        return classification(self.ws, "<92>")
    #-----------------------------------------------------------------------------
    def get_color_rgb(self):
        return classification(self.ws, "<10>")
    #-----------------------------------------------------------------------------
    def get_color_clear(self):
        return classification(self.ws, "<11>")
    
    def get_color_clear_left(self):
        return self.get_color_clear()[0]
    
    def get_color_clear_center(self):
        return self.get_color_clear()[1]

    def get_color_clear_right(self):
        return self.get_color_clear()[2]
    #-----------------------------------------------------------------------------
    def get_line(self):
        return classification(self.ws, "<<12>>")

    def get_line_left(self):
        return self.get_line()[0]
    
    def get_line_center(self):
        return self.get_line()[1]

    def get_line_right(self):
        return self.get_line()[2]

    def set_line_threshold_value(self, value: int):

        if not isinstance(value, int):
            print ("Error : the 'value' parameter must be a int")
            return None

        msg = "<<13t"+str(value)+">>"
        socket_send(self.ws, msg)
        
    def get_line_threshold_value(self):
        return classification(self.ws, "<<14>>")
    #-----------------------------------------------------------------------------
    def get_distance(self):
        return classification(self.ws, "<<20>>")
    
    def get_distance_front(self):
        result = self.get_distance()
        
        # Vérifiez que result est un tuple (ou une liste)
        if isinstance(result, (tuple, list)):
            distance_front, _, _, _ = result
            return int(distance_front)
        else:
            # Si ce n'est pas un tuple ou une liste, gérer l'erreur
            print("Erreur : get_distance() n'a pas retourné un tuple ou une liste")
            distance_front = 600
            return distance_front
   
    def get_distance_right(self):
        result = self.get_distance()
        
        # Vérifiez que result est un tuple (ou une liste)
        if isinstance(result, (tuple, list)):
            _, distance_right, _, _ = result
            return int(distance_right)
        else:
            print("Erreur : get_distance() n'a pas retourné un tuple ou une liste")
            distance_right = 600
            return distance_right
    
    def get_distance_back(self):
        # return self.get_distance()[2]
        result = self.get_distance()
        
        # Vérifiez que result est un tuple (ou une liste)
        if isinstance(result, (tuple, list)):
            _, _, distance_back, _ = result
            return int(distance_back)
        else:
            print("Erreur : get_distance() n'a pas retourné un tuple ou une liste")
            distance_back = 600
            return distance_back
    
    def get_distance_left(self):
        result = self.get_distance()
        
        # Vérifiez que result est un tuple (ou une liste)
        if isinstance(result, (tuple, list)):
            _, _, _, distance_left = result
            return int(distance_left)
        else:
            print("Erreur : get_distance() n'a pas retourné un tuple ou une liste")
            distance_left = 600
            return distance_left
    #-----------------------------------------------------------------------------
    def get_angle(self):
        return classification(self.ws, "<<30>>")

    def reset_angle(self):
        socket_send(self.ws, "<<31>>")

    def get_imu(self):
        return classification(self.ws, "<<32>>")
    #-----------------------------------------------------------------------------
    def get_battery(self):
        return classification(self.ws, "<<40>>")
    #-----------------------------------------------------------------------------
    def get_led_color(self):
        return classification(self.ws, "<<50>>")
            
    def set_led_color(self,red: int, green: int, blue : int):
        # make integer test and test min and max value

        if not isinstance(red, int):
            print ("Error : 'red' parameter must be a int")
            return None
        if red>255 or red<0:
            print ("Error : 'red' parameter must be include between 0 and 255")
            return None
        if not isinstance(green, int):
            print ("Error : 'green' parameter must be a int")
            return None
        if green> 255 or green<0:
            print ("Error : 'green' parameter must be include between 0 and 255")
            return None
        if not isinstance(blue, int):
            print ("Error : 'blue' parameter must be a int")
            return None
        if blue> 255 or blue<0:
            print ("Error : 'blue' parameter must be include between 0 and 255")
            return None
        
        msg = "<<51r"+str(red)+"g"+str(green)+"b"+str(blue)+">>"
        socket_send(self.ws, msg)    

    def set_led_shape(self, value: str):

        if not isinstance(value, str):
            print ("Error : 'value' parameter must be a string")
            return None

        msg = "<<52v"+str(value)+">>"
        socket_send(self.ws, msg) 
        
    def set_led_anim(self,value: str):

        if not isinstance(value, str):
            print ("Error : 'value' parameter must be a string")
            return None


        msg = "<<53v"+str(value)+">>"
        socket_send(self.ws, msg) 

    def set_led_single(self, type: str, id: int, red: int, green: int, blue: int):

        if not isinstance(type, str):
            print ("Error : 'type' parameter must be a string")
            return None
        if type != "center" and type != "circle":
            print ("Error : 'type' parameter must be center or circle")
            return None
        if not isinstance(id, int):
            print ("Error : 'id' parameter must be a int")
            return None
        
        if not isinstance(red, int):
            print ("Error : 'red' parameter must be a int")
            return None
        if red> 255 or red<0:
            print ("Error : 'red' parameter must be include between 0 and 255")
            return None
        if not isinstance(green, int):
            print ("Error : 'green' parameter must be a int")
            return None
        if green> 255 or green<0:
            print ("Error : 'green' parameter must be include between 0 and 255")
            return None
        if not isinstance(blue, int):
            print ("Error : 'blue' parameter must be a int")
            return None
        if blue> 255 or blue<0:
            print ("Error : 'blue' parameter must be include between 0 and 255")
            return None
        
        if type == "center":
            type = True
        if type == "circle":
            type = False
        msg = "<<55t"+str(type)+"d"+str(id)+"r"+str(red)+"g"+str(green)+"b"+str(blue)+">>"
        socket_send(self.ws, msg)

    def set_led_captor(self,state: bool):

        if not isinstance(state, bool):
            print ("Error : 'state' parameter must be a bool")
            return None

        if (state == True):
            msg = "<<54l1>>"
        elif (state == False) :
            msg = "<<54l0>>"
        socket_send(self.ws, msg) 
    #-----------------------------------------------------------------------------
    def get_acc_motor(self):
        return classification(self.ws, "<<60>>")
    
    def set_acc_motor(self, value: int):
        # make integer test and test min and max value

        if not isinstance(value, int):
            print ("Error : 'value' parameter must be a int")
            return None
        if value> 100 or value<10:
            print ("Error : 'value' parameter must be include between 10 and 100")
            return None

        if value < 10 : value = 10
        elif value > 100 : value = 100
        msg = "<<61a"+str(value)+">>"
        socket_send(self.ws, msg) 

    def drive_single_motor(self, id: int, value: int):        # à mettre en pourcentage

        if not isinstance(id, int):
            print ("Error : 'id' parameter must be a int")
            return None
        if id> 255 or id<0:
            print ("Error : 'id' parameter must be include between 0 and 255")
            return None
        if not isinstance(value, int):
            print ("Error : 'value' parameter must be a int")
            return None
        if value> 100 or value<-100:
            print ("Error : 'value' parameter must be include between -100 and 100")
            return None
        if id < 0 : id = 0
        elif id > 255 : id = 255
        if value < -100 : value = -100
        elif value > 100 : value = 100
        value = value * 70
        msg = "<<70d"+str(id)+"v"+str(value)+">>"
        socket_send(self.ws, msg) 

    def set_autonomous_mode(self, value: str):

        if not isinstance(value, str):
            print ("Error : 'value' parameter must be a string")
            return None

        msg = "<<80"+str(value)+">>"
        socket_send(self.ws, msg) 
        
    def set_autonomous_led(self, value: str):
        
        if not isinstance(value, str):
            print ("Error : 'value' parameter must be a string")
            return None
        
        msg = "<<81"+str(value)+">>"
        socket_send(self.ws, msg)

    def control_single_motor_front_left(self, value: int):  # de -100 à 100
        
        if not isinstance(value, int):
            print ("Error : 'value' parameter must be a int")
            return None
        
        self.drive_single_motor(1,value)
        
        # if isinstance(pourcentage, int) == False:
        #     print ('value should be an integer between -100 to 100')
        # pass

    def control_single_motor_front_right(self, value: int):
        
        if not isinstance(value, int):
            print ("Error : 'value' parameter must be a int")
            return None
        
        self.drive_single_motor(2,value)

    def control_single_motor_back_left(self, value: int):
        
        if not isinstance(value, int):
            print ("Error : 'value' parameter must be a int")
            return None
        
        self.drive_single_motor(4, value)

    def control_single_motor_back_right(self, value: int):

        if not isinstance(value, int):
            print ("Error : 'value' parameter must be a int")
            return None
        
        self.drive_single_motor(3, value)

    def get_vmax():
        pass

    def set_vmax(vmax):
        pass 
    
    def set_mode_motor():
        #between position or wheel mode
        pass

    def free_motor():
        #to disconnected power on engine
        pass
    #-----------------------------------------------------------------------------
    def set_wifi_credentials(self, ssid: str, password: str):

        if not isinstance(ssid, str): 
            print ("Error : 'ssid' parameter must be a string")
            return None
            
        if not isinstance(password, str):
            print("Error : 'password' parameter must be a string")
            return none
        
        msg = "<90s"+str(ssid)+">"
        socket_send(self.ws, msg)

        msg = "<91p"+str(password)+">"
        socket_send(self.ws, msg)

    def get_wifi_credentials(self):
        return classification(self.ws, "<92>")
    #---------------------------------------------------------------------------------   
    def set_debug_state(self, state: bool):

        if not isinstance(state, bool):
            print ("Error : 'state' parameter must be a bool like True or False")
            return None

        msg = "<94"+str(state)+">"
        socket_send(self.ws, msg)
#---------------------------------------------------------------------------------
    