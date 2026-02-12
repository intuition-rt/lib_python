
<p align="center">
  <img alt="Ilo robot" src="https://images.squarespace-cdn.com/content/v1/6312fe2115db3003bd2ec2f1/546df043-e044-4003-867b-802738eb1332/LOGO+ILO+PYTHON.png" width="400">
</p>

# ilo

![Python](https://img.shields.io/pypi/pyversions/ilo.svg?style=for-the-badge&color=%233776AB&)
[![PyPI](https://img.shields.io/pypi/v/ilo.svg?style=for-the-badge&color=%23FFD343&)](https://pypi.org/project/ilo/)
[![Downloads](https://img.shields.io/pypi/dm/ilo.svg?style=for-the-badge&color=%2328A745&)](https://pypi.org/project/ilo/)
[![License](https://img.shields.io/pypi/l/ilo.svg?style=for-the-badge&color=%234A75A0)](https://github.com/marinchl/ilo/blob/main/LICENSE)

---

**ilo** is a powerful Python package to control **ilo** the new **educational robot** directly from your computer.  
It allows you to move the robot, read sensors, interact with LEDs, and create autonomous behaviors — all in just a few lines of Python.

---

## Features

- Move the robot in multiple directions with Python commands  
- Create complex **movement loops**  
- Draw and animate using the robot's **LED matrix**  
- Play with the robot **in real time** using your keyboard  
- Use **colored cards** to trigger autonomous modes  
- Control and read sensors over **Wi-Fi** or **Bluetooth**

---

## Installation

```bash
pip install ilo
```

To update:
```bash
pip install ilo --upgrade
```

---

## Quick Example

Here’s a simple example to get started:

```python
import ilo, time

ilo.check_robot_on_bluetooth()
# ilo.check_robot_on_wifi()  # Make sure you are connected to the robot's Wi-Fi AP

my_ilo = ilo.robot(1)

# Go forward until an obstacle is close
while my_ilo.get_distance_front() > 30:
    my_ilo.move("front", 10, 50) 
    time.sleep(0.1)

my_ilo.stop()  # Stop the robot
my_ilo.step("rot_clock")  # Rotate clockwise
my_ilo.set_led_color(25, 200, 25)
my_ilo.step("front", 0.5)
```

---

## Dependencies

All dependencies are **automatically installed** with `ilo`.  
Here’s what each one does:
- [`keyboard-crossplatform`](https://pypi.org/project/keyboard-crossplatform/) – cross-platform keyboard event listener (works on macOS, Windows, and Linux)
- [`prettytable`](https://pypi.org/project/prettytable/) – generate clean and easy-to-read tables in the terminal
- [`websocket-client`](https://pypi.org/project/websocket-client/) – communicate with the robot via WebSocket
- [`bleak`](https://pypi.org/project/bleak/) – Bluetooth Low Energy (BLE) client library for Python
- [`pyserial`](https://pypi.org/project/pyserial/) – serial communication support (UART)
- [`pyperclip`](https://pypi.org/project/pyperclip/) – cross-platform clipboard support
- [`requests`](https://pypi.org/project/requests/) – simple and powerful HTTP client
- [`numpy`](https://pypi.org/project/numpy/) – fundamental package for scientific computing
- [`matplotlib`](https://pypi.org/project/matplotlib/) – powerful plotting and visualization library

---

## Documentation

Full documentation and examples are available on `GitHub`. *(Comming soon)*

---

## Contributing

Bug reports, patches, and suggestions are welcome!

Questions? Contact us via [`our website`](https://ilorobot.com).

---

<p align="center">
  <a href="https://ilorobot.com">
    <img src="https://img.shields.io/badge/Powered_by-Intuition_RT-%234A75A0?style=for-the-badge&logo=python&logoColor=white" alt="Powered by Intuition RT">
  </a>
</p>
