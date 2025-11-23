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
        if len(parts) != 1:
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
# Change: Create only 2 rows instead of 8. 
# You can adjust figsize (width, height) as preferred.
fig, axs = plt.subplots(2, 1, figsize=(10, 8))

# Wykres sygnału w czasie (oryginał vs przefiltrowany)
# Oś czasu w sekundach
t = np.arange(N) / Fs

# Change: Use index [0] (the top plot)
axs[0].plot(t, signal, color='0.7', label='Original')
axs[0].plot(t, filtered_signal, color='C0', label='HP 0.5 Hz')
axs[0].set_title("Signal in time (column 3) - original vs filter")
axs[0].set_xlabel("Time [s]")
axs[0].set_ylabel("Value")
axs[0].legend(loc='upper right') # Added loc to prevent covering data

# Wykres FFT (tylko dodatnie częstotliwości) — widmo sygnału przefiltrowanego
pos_mask = fft_freqs >= 0

# Change: Use index [1] (the bottom plot)
axs[1].plot(fft_freqs[pos_mask], np.abs(fft_vals[pos_mask]))
axs[1].set_title("FFT spectrum of the filtered signal (HP 0.5 Hz)")
axs[1].set_xlabel("Frequency [Hz]")
axs[1].set_ylabel("Magnitude")

# We removed the loop that hid the other axes because there are no empty axes left.
plt.tight_layout()
plt.show()