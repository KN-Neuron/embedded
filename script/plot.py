import matplotlib.pyplot as plt
import numpy as np
from sys import argv

# Czytanie danych z pliku
data = []
with open(argv[1], 'r') as f:
    for i, line in enumerate(f):
        parts = line.strip().split(',')
        if len(parts) < 8:
            print(f"Bad row at", i, "skipping")
            continue
        try:
            row = [float(x) for x in parts]
            data.append(row)
        except ValueError:
            print(f"Non-numeric data at row", i, "skipping")

if not data:
    print("Brak poprawnych danych.")
    exit()

# Transponowanie danych
data_array = np.transpose(data)

# Wybieramy sygnał z 3. kolumny (index 2)
signal = data_array[2]

# Obliczenie FFT
fft_vals = np.fft.fft(signal)
fft_freqs = np.fft.fftfreq(len(signal))

# Rysowanie wykresów
fig, axs = plt.subplots(8, 1, figsize=(10, 8))

# Wykres sygnału w czasie
axs[2].plot(signal)
axs[2].set_title("Sygnał w czasie (kolumna 3)")
axs[2].set_xlabel("Czas")
axs[2].set_ylabel("Wartość")

# Wykres FFT (tylko dodatnie częstotliwości)
pos_mask = fft_freqs >= 0
axs[3].plot(fft_freqs[pos_mask], np.abs(fft_vals[pos_mask]))
axs[3].set_title("Widmo FFT sygnału (kolumna 3)")
axs[3].set_xlabel("Częstotliwość [Hz]")
axs[3].set_ylabel("Amplituda")

# Pozostałe wykresy ukrywamy
for i in range(8):
    if i not in [2, 3]:
        axs[i].axis('off')

# plt.tight_layout()
plt.show()
