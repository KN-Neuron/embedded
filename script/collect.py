#!/usr/bin/python3
from serial import Serial
from sys import argv
from sys import platform
from glob import glob
from datetime import datetime

filename = argv[1] if (len(argv) > 1) else datetime.now().strftime("Data_%d-%m-%y_%H%M%S") + ".csv"

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

# Otwarcie pliku do zapisu danych
print("Collecting data...")
with open(filename, 'w') as f:
    while True:
        try:
            # Czytanie danych z portu
            ser_bytes = ser.readline()
            # Dekodowanie danych z Latin-1
            decoded_data = ser_bytes.decode('latin-1')
            # Sprawdzanie, czy dane rozpoczynają się od 'ADS:'
            if decoded_data.startswith('ADS:'):
                # Rozdzielenie danych separatorami ','
                data_fields = decoded_data.strip().split(':')[1][1:]#.split(',')
                # print(data_fields)
                # Zapisanie danych do pliku
                f.write(data_fields + '\n')
                # print(f"Zapisano dane: {data_fields}")
        except KeyboardInterrupt:
            print("Data collection stopped by user.")
            break
        except Exception as e:
            print(f"Błąd: {e}")