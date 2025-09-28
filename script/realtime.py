from collections import deque
from glob import glob
from serial import Serial
from sys import platform

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

# === Serial Port Setup ===
if platform.startswith('win'):
    ports = [f'COM{i+1}' for i in range(256)]
elif platform.startswith('linux'):
    ports = glob('/dev/ttyACM*') + glob('/dev/ttyUSB*')
elif platform.startswith('darwin'):
    ports = glob('/dev/tty.usbmodem*') + glob('/dev/tty.usbserial*')
else:
    raise EnvironmentError(f'Unsupported platform: {platform}')

ser = None

for port in ports:
    try:
        ser = Serial(port, baudrate=115200, timeout=0.01)
        print(f"Found STM32 on port: {port}...", end=' ')
        if (ser.isOpen()):
            print("Connected!")
            break
        print("But the port is closed. Trying another...")
    except (OSError):
        print(f"Could not open port {port}")
        continue

if not ser:
    print("STM32 not found!")
    exit(1)

# === Data Buffers ===
max_len = 200
num_channels = 8
data_buffers = [deque([0]*max_len, maxlen=max_len) for _ in range(num_channels)]

# === Precomputed X values ===
x_vals = np.arange(max_len)

# === Figure Setup ===
fig, axs = plt.subplots(num_channels, 1, figsize=(10, 20))
lines = []

for i in range(num_channels):
    line, = axs[i].plot(x_vals, [0]*max_len, lw=1.5)
    lines.append(line)
    axs[i].set_xlim(0, max_len - 1)
    axs[i].set_title(f"Channel {i+1}")
    axs[i].set_xlabel("Time")
    axs[i].set_ylabel("Value")

plt.subplots_adjust(hspace=0.4)

# === Animation Update Function ===
def update_plot(frame):
    try:
        line = ser.readline().decode('latin-1').strip()
        if not line.startswith('ADS:'):
            return lines

        _, raw_values = line.split(':', 1)
        values = raw_values.split(',')

        if len(values) < num_channels:
            return lines

        print(values)
        for i in range(num_channels):
            data_buffers[i].append(float(values[i]))
            axs[i].relim()
            axs[i].autoscale_view()

        for i, line in enumerate(lines):
            line.set_ydata(data_buffers[i])

    except Exception as e:
        print(f"Serial read error: {e}")
    return lines

# === Run Animation ===
ani = animation.FuncAnimation(
    fig, update_plot, interval=10, blit=True, cache_frame_data=False
)

try:
    plt.show()
except KeyboardInterrupt:
    print("Interrupted by user")

# === Cleanup ===
ser.close()
