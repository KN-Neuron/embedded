from collections import deque
from glob import glob
from serial import Serial
from sys import platform

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

# === serial port scan ===
if platform.startswith('win'):
    ports = [f'COM{i+1}' for i in range(256)]
elif platform.startswith('linux'):
    ports = glob('/dev/ttyACM*') + glob('/dev/ttyUSB*')
elif platform.startswith('darwin'):
    ports = glob('/dev/tty.usbmodem*') + glob('/dev/tty.usbserial*')
else:
    raise EnvironmentError(f'unsupported platform: {platform}')

ser = None
for port in ports:
    try:
        s = Serial(port, baudrate=115200, timeout=0.01)
        if s.is_open:
            ser = s
            print(f"connected to {port}")
            break
    except OSError:
        continue

if ser is None:
    print("STM32 not found")
    exit(1)

# === buffers ===
max_len = 200
num_channels = 8
data_buffers = [deque([0]*max_len, maxlen=max_len) for _ in range(num_channels)]
x_vals = np.arange(max_len)

# === figure ===
fig, axs = plt.subplots(num_channels, 1, figsize=(10, 20))
lines = []

for i in range(num_channels):
    l, = axs[i].plot(x_vals, data_buffers[i], lw=1.5)
    axs[i].set_xlim(0, max_len - 1)
    axs[i].set_ylim(-5, 5)   # set something sane; update later if needed
    axs[i].set_title(f"channel {i+1}")
    lines.append(l)

plt.subplots_adjust(hspace=0.3)

# === animation ===
def update(frame):
    try:
        raw = ser.readline().decode('latin-1', errors='ignore').strip()
        if not raw.startswith("ADS:"):
            return lines

        parts = raw.split(':', 1)[1].split(',')
        if len(parts) < num_channels:
            return lines

        vals = [float(v) for v in parts[:num_channels]]

        for i in range(num_channels):
            data_buffers[i].append((vals[i] / (2**24)) * 10 - 5)
            lines[i].set_ydata(data_buffers[i])

    except Exception as e:
        print("err:", e)

    return lines

ani = animation.FuncAnimation(
    fig,
    update,
    interval=10,
    blit=True,
    cache_frame_data=False
)

plt.show()
ser.close()
