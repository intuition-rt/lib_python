# Plottica

Plottica is a simple and lightweight Python library for quickly plotting data.  
It is specifically designed to work with ESP32 devices over Wi-Fi. You can easily visualize data streams from your ESP32 without complex configuration.

## 🔧 Installation

```bash
pip install plottica
```

## 🚀 Usage

```python
from plottica import draw_data

draw_data(lambda: my_ilo._distance_front, label="Distance (mm)")
```

## 📦 Features

- Fast rendering of simple plots  
- Light customization  
- Simple to use  
- Optimized for ESP32 communication over Wi-Fi  

## 💡 Ideal for :

- Educational projects  
- Real-time data debugging with ESP32  
- Quick scripts for IoT and robotics  
