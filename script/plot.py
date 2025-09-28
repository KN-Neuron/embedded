import matplotlib.pyplot as plt
import numpy as np
from sys import argv

# Czytanie danych z pliku
data = []
with open(argv[1], 'r') as f:
    for i, line in enumerate(f):
        parts = line.strip().split(',')  # Pomijamy pierwszy element
        if len(parts) < 8:
            print(f"Bad row at {i}, skipping")
            continue
        try:
            row = [float(x) for x in parts]
            data.append(row)
        except ValueError:
            print(f"Non-numeric data at row {i}, skipping")

# Sprawdzenie czy mamy dane
if not data:
    print("Brak poprawnych danych.")
    exit()

# Transponowanie danych
data_array = np.transpose(data)

# Rysowanie 2 wykresów
fig, axs = plt.subplots(8, 1, figsize=(10, 8))
for i in range(8):
    if i < len(data_array):
        axs[i].plot(data_array[i])
        axs[i].set_title(f"Wykres {i+1}")
        axs[i].set_xlabel("Czas")
        axs[i].set_ylabel("Wartość")
    else:
        axs[i].axis('off')

plt.tight_layout()
plt.show()
