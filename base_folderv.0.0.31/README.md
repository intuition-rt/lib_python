<picture align="center">
    <img alt="Ilo robot" src="https://images.squarespace-cdn.com/content/v1/6312fe2115db3003bd2ec2f1/546df043-e044-4003-867b-802738eb1332/LOGO+ILO+PYTHON.png">
</picture>

# ilo robot

A package that lets users control ilo the new educational robot using python command lines.

## Features

- Moves the robot in **many directions** with python commands line
- Creates **movement loops**
- Play with the robot in **real time** with your keyboard
- Use **colored plates** to make the robot move

## Where to get it ?

```
# with pip
pip install ilo
```

## Dependencies

- [Keyboard - Take full control of your keyboard with this small Python library. Hook global events, register hotkeys, simulate key presses and much more.](https://pypi.org/project/keyboard/)

- [PrettyTable - A simple Python library for easily displaying tabular data in a visually appealing ASCII table format.](https://pypi.org/project/prettytable/)

Don't worry, this dependency is automatically installed with the ilo library.

## Example

```
import ilo

ilo.connection()

print("ilo is connected")

ilo.set_led_color_rgb(200,0,0)      # color is red
ilo.set_led_color_rgb(0,0,200)      # color is blue

while true:

    print("Ilo moves forward")
    ilo.move("front", 100)
    
    while ilo.get_distance() > 20:
        pass
        
    ilo.stop()
    print("ilo has encountered an obstacle")
    
    if ilo.get_distance() > 20:
        ilo.move("right", 80)
        print("ilo moves to the right at 80% speed")
    
    else:
        ilo.move("left", 70)
        print("ilo moves to the left at 70% speed")
```

## About us

Find us on our [***website***](https://ilorobot.com) ;)
