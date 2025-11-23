#!/usr/bin/python3
import matplotlib.pyplot as plt
import numpy as np
from sys import argv

Fs = 250

# Czytanie danych z pliku
data = []
with open(argv[1], 'r') as f:
    for i, line in enumerate(f):
        parts = line.strip().split(',')
        if len(parts) != 8:
            print(f"Bad row at", i, "skipping")
            continue
        try:
            row = [float(x) for x in parts]#[:8]
            data.append(row)
        except ValueError:
            print(f"Non-numeric data at row", i, "skipping")

if not data:
    print("Brak poprawnych danych.")
    exit()

# Transponowanie danych
data_array = np.transpose(data)

# Wybieramy sygnał z 3. kolumny (index 2)
signal = data_array[0]

# Zastosowanie filtra górnoprzepustowego (HP) w dziedzinie częstotliwości - od 0.5 Hz
N = len(signal)
fft_raw = np.fft.fft(signal)
fft_freqs = np.fft.fftfreq(N, 1/Fs)
hp_cutoff = 0.5  # Hz
hp_mask = np.abs(fft_freqs) >= hp_cutoff
fft_filtered = fft_raw * hp_mask
signal_hp = np.fft.ifft(fft_filtered).real

# Użyjemy sygnału przefiltrowanego do dalszych analiz (i też pokażemy oryginał)
filtered_signal = signal_hp

# Obliczenie FFT sygnału przefiltrowanego
fft_vals = np.fft.fft(filtered_signal)

# Rysowanie wykresów
fig, axs = plt.subplots(8, 1, figsize=(10, 8))

# Wykres sygnału w czasie (oryginał vs przefiltrowany)
# Oś czasu w sekundach
t = np.arange(N) / Fs
axs[2].plot(t, signal, color='0.7', label='Oryginał')
axs[2].plot(t, filtered_signal, color='C0', label='HP 0.5 Hz')
axs[2].set_title("Sygnał w czasie (kolumna 3) - oryginał vs filtr")
axs[2].set_xlabel("Czas [s]")
axs[2].set_ylabel("Wartość")
axs[2].legend()

# Wykres FFT (tylko dodatnie częstotliwości) — widmo sygnału przefiltrowanego
pos_mask = fft_freqs >= 0
axs[3].plot(fft_freqs[pos_mask], np.abs(fft_vals[pos_mask]))
axs[3].set_title("Widmo FFT sygnału przefiltrowanego (HP 0.5 Hz)")
axs[3].set_xlabel("Częstotliwość [Hz]")
axs[3].set_ylabel("Amplituda")

# Pozostałe wykresy ukrywamy
for i in range(8):
    if i not in [2, 3]:
        axs[i].axis('off')

plt.tight_layout()
plt.show()
