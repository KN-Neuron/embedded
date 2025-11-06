import serial
from sys import argv

# Otwarcie portu
ser = serial.Serial('COM6', baudrate=115200)
# Otwarcie pliku do zapisu danych
with open(argv[1], 'w') as f:
    while True:
        try:
            print("Oczekiwanie na dane...", end='\t')
            # Czytanie danych z portu
            ser_bytes = ser.readline()
            # Dekodowanie danych z Latin-1
            decoded_data = ser_bytes.decode('latin-1')
            # Sprawdzanie, czy dane rozpoczynają się od 'ADS:'
            if decoded_data.startswith('ADS:'):
                # Rozdzielenie danych separatorami ','
                data_fields = decoded_data.strip().split(':')[1].split(',')
                # Zapisanie danych do pliku
                f.write(','.join(data_fields) + '\n')
                print(f"Zapisano dane: {data_fields}")
        except Exception as e:
            print(f"Błąd: {e}")
