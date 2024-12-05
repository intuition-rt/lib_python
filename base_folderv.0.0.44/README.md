<picture align="center">
    <img alt="Ilo robot" src="https://images.squarespace-cdn.com/content/v1/6312fe2115db3003bd2ec2f1/546df043-e044-4003-867b-802738eb1332/LOGO+ILO+PYTHON.png">
</picture>

# ilo robot

A package that lets users control ilo the new educational robot using python command lines.

## Features

- Moves the robot in **many directions** with python commands line
- Creates **movement loops**
- Play with the robot in **real time** with your keyboard
- Use **colored plates** to make the robot move and many other **autonomous modes**

## Where to get it ?

```
# with pip
pip install ilo
```

## How to update it ?

```
# with pip
pip install ilo --upgrade
```

## Dependencies

- [Keyboard - Take full control of your keyboard with this small Python library. Hook global events, register hotkeys, simulate key presses and much more.](https://pypi.org/project/keyboard/)

- [PrettyTable - A simple Python library for easily displaying tabular data in a visually appealing ASCII table format.](https://pypi.org/project/prettytable/)

- [WebSocket-Client - websocket-client is a WebSocket client for Python. It provides access to low level APIs for WebSockets.](https://pypi.org/project/websocket-client/)

- [Python Serial Port Extension for Win32, OSX, Linux, BSD, Jython, IronPython.](https://pypi.org/project/pyserial/)

- [Pyperclip is a cross-platform Python module for copy and paste clipboard functions.](https://pypi.org/project/pyperclip/)

Don't worry, these dependencies are automatically installed with the ilo library.

## Example

```
import ilo

ilo.check_robot_on_network()

my_ilo = ilo.robot(1)

my_ilo.set_led_color(255,0,0)      # set the robot color to red

while true:

    print("Ilo moves forward")
    my_ilo.move("front", 100)
    
    while my_ilo.get_distance() > 20:
        pass
        
    my_ilo.stop()
    print("ilo has encountered an obstacle")
    
    if my_ilo.get_distance() > 20:
        my_ilo.move("right", 80)
        print("ilo moves to the right at 80% speed")
    
    else:
        my_ilo.move("left", 70)
        print("ilo moves to the left at 70% speed")
```

## What else? 

Bug reports, patches and suggestions are welcome!

Contact us through our [***website***](https://ilorobot.com) ;)
