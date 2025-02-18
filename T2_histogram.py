import pydicom
import numpy as np
import os
import matplotlib.pyplot as plt
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Función para mostrar coordenadas al mover el mouse
def on_hover(event):
    if event.xdata is not None and event.ydata is not None:
        plt.gca().set_title(f'Histograma de valores T2\nTiempo T2: {event.xdata:.2f} ms, Frecuencia: {event.ydata:.0f}')
        plt.draw()

root = Tk()
root.withdraw()
dicom_path = askopenfilename(title="Seleccionar archivo DICOM de mapa T2", filetypes=[("DICOM files", "*.dcm")])

if not dicom_path:
    print("No se seleccionó ningún archivo.")
else:
    ds = pydicom.dcmread(dicom_path)
    T2_map = ds.pixel_array.astype(np.float32)

    min_T2, max_T2 = np.min(T2_map), np.max(T2_map)
    print(f"Dimensiones del mapa T2: {T2_map.shape}")
    print(f"Rango de valores T2: {min_T2:.2f} - {max_T2:.2f} ms")

    fig, ax = plt.subplots(figsize=(10, 6))
    bins = np.linspace(min_T2, max_T2, 200)
    counts, _, _ = ax.hist(T2_map.flatten(), bins=bins, color='blue', alpha=0.7)
    ax.set_title('Histograma de valores T2')
    ax.set_xlabel('Tiempo T2 (ms)')
    ax.set_ylabel('Frecuencia')

    max_freq_index = np.argmax(counts)
    T2_max_freq = bins[max_freq_index]
    max_freq_value = counts[max_freq_index]
    print(f"El valor de T2 con máxima frecuencia es aproximadamente: {T2_max_freq:.2f} ms con una frecuencia de {max_freq_value}")

    # Conectar la función de interacción con el mouse
    fig.canvas.mpl_connect("motion_notify_event", on_hover)

    plt.show()

    hist_path = os.path.join(os.path.dirname(dicom_path), "histograma_T2.jpg")
    fig.savefig(hist_path, dpi=300)
    print(f"Histograma guardado en: {hist_path}")