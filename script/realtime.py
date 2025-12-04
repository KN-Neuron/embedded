#!/usr/bin/python3
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

port = 'COM54'
s = Serial(port, baudrate=115200, timeout=1.0)
if s.is_open:
    ser = s
    print(f"connected to {port}")

if ser is None:
    print("STM32 not found")
    exit(1)

# === buffers ===
max_len = 200
num_channels = 1
data_buffers = [deque([0]*max_len, maxlen=max_len) for _ in range(num_channels)]
x_vals = np.arange(max_len)

# === figure ===
fig, axs = plt.subplots(num_channels, 1, figsize=(10, 20))
# When `num_channels == 1`, `plt.subplots` returns a single Axes object
# instead of an array. Make sure `axs` is always indexable the same way.
if num_channels == 1:
    axs = [axs]
lines = []

for i in range(num_channels):
    l, = axs[i].plot(x_vals, data_buffers[i], lw=1.5)
    axs[i].set_xlim(0, max_len - 1)
    axs[i].set_ylim(-0.5, 0.5)   # set something sane; update later if needed
    axs[i].set_title(f"Channel {i+1}")
    lines.append(l)

plt.subplots_adjust(hspace=0.3)


### decoding starts
def process_data(binary_data):
    """
    Converts 24 bytes of raw data into 8 integers (3 bytes each).
    """
    numbers = []

    # Iterate from 0 to 24, stepping 3 bytes at a time
    for i in range(0, 24, 3):
        # 1. Slice out the 3-byte chunk
        chunk = binary_data[i : i+3]

        # 'byteorder' determines if the first byte is the smallest (little)
        # or largest (big) part of the number.
        value = int.from_bytes(chunk, byteorder='little', signed=True)

        numbers.append(value)

    return numbers

# === animation ===
def update(frame):
    try:
        ser.reset_input_buffer()
        header = ser.read(1)
        
        # 2. Check if the byte is the Header 'A'
        if header == b'A':
            # 3. If header matches, read the remaining 24 bytes
            payload = ser.read(24)
            
            # Verify we actually got all 24 bytes (didn't time out)
            if len(payload) == 24:
                vals = process_data(payload)
                # print(vals)
            else:
                print("Incomplete packet received.")
                return lines

            for i in range(num_channels):
            # data_buffers[i].append((vals[i] / (2**24)) * 10)
                data_buffers[i].append((vals[i] / (2**24)))
                lines[i].set_ydata(data_buffers[i])
    except Exception as e:
        print("Error:", e)
        breakpoint()

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
