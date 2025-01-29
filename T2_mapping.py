import pydicom
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tkinter import Tk
from tkinter.filedialog import askdirectory

# Función de decaimiento exponencial (modelo T2)
def exp_decay(TE, S0, T2):
    return S0 * np.exp(-TE / T2)

# Crear una ventana de Tkinter para seleccionar la carpeta
root = Tk()
root.withdraw()
dicom_folder = askdirectory(title="Seleccionar carpeta con imágenes DICOM")

if not dicom_folder:
    print("No se seleccionó ninguna carpeta.")
else:
    # Listar los archivos DICOM en la carpeta y ordenarlos
    dicom_files = sorted([f for f in os.listdir(dicom_folder) if f.endswith('.dcm')])

    # Limitar a las primeras 16 imágenes
    dicom_files = dicom_files[:16]
    print(f"Se procesarán las primeras {len(dicom_files)} imágenes DICOM.")

    # Leer las imágenes DICOM
    images = []
    TE_values = []  # Lista para almacenar los tiempos de eco (TE)
    for dicom_file in dicom_files:
        dicom_path = os.path.join(dicom_folder, dicom_file)
        ds = pydicom.dcmread(dicom_path)
        images.append(ds.pixel_array)
        TE_values.append(float(ds[0x0018, 0x0081].value))  # Obtener el tiempo de eco (TE) del DICOM

    print(f"Se leyeron {len(images)} imágenes DICOM.")

    # Convertir las imágenes en un array de numpy
    images_array = np.array(images)

    # Crear un mapa T2 para cada píxel
    T2_map = np.zeros_like(images_array[0], dtype=np.float32)

    # Ajustar exponencialmente para cada píxel
    total_pixels = images_array.shape[1] * images_array.shape[2]
    processed_pixels = 0
    print("Comenzando el ajuste exponencial para cada píxel...")

    for i in range(images_array.shape[1]):  # Iterar sobre columnas
        for j in range(images_array.shape[2]):  # Iterar sobre filas
            signal_values = images_array[:, i, j]  # Valores de señal para el píxel (i, j)

            # Filtrar valores de señal muy bajos para evitar ruido
            if np.max(signal_values) < 10:  # Umbral ajustable
                T2_map[i, j] = np.nan
                continue

            try:
                # Establecer parámetros iniciales
                S0_init = np.max(signal_values)
                T2_init = 40  # Valor de T2 inicial ajustado para hígado

                # Establecer límites para el ajuste
                popt, _ = curve_fit(
                    exp_decay,
                    TE_values,
                    signal_values,
                    p0=(S0_init, T2_init),
                    bounds=([0, 10], [np.inf, 200])
                )

                # Almacenar el valor de T2 ajustado
                T2_map[i, j] = popt[1]  # El segundo parámetro es T2
            except Exception as e:
                T2_map[i, j] = np.nan  # Si el ajuste falla, asignar NaN

            # Actualizar el progreso cada vez que se procesan un 10% de los píxeles
            processed_pixels += 1
            if processed_pixels % (total_pixels // 10) == 0:
                progress = (processed_pixels / total_pixels) * 100
                print(f"Progreso: {progress:.1f}%")

    # Verificar si el mapa T2 contiene valores válidos
    if np.isnan(T2_map).all():
        print("Todos los valores del mapa T2 son NaN.")
    else:
        print(f"El mapa T2 contiene valores válidos. Mostrando resultados...")

        # Verificar el rango de valores de T2
        min_T2, max_T2 = np.nanmin(T2_map), np.nanmax(T2_map)
        print(f"Rango de T2: {min_T2:.2f} - {max_T2:.2f} ms")

        # Normalizar el mapa T2 para que los valores estén entre 0 y 255 (escala de grises)
        T2_map_normalized = np.clip(T2_map, 10, 100)  # Limitar a un rango razonable para hígado
        T2_map_normalized = (
            (T2_map_normalized - np.nanmin(T2_map_normalized)) /
            (np.nanmax(T2_map_normalized) - np.nanmin(T2_map_normalized)) * 255
        )

        # Mostrar el mapa T2 en escala de grises
        plt.figure(figsize=(10, 5))

        plt.subplot(1, 2, 1)
        plt.imshow(T2_map_normalized, cmap='gray', interpolation='nearest')
        plt.colorbar(label='Tiempo T2 (ms)')
        plt.title('Mapa T2 (Escala de grises)')

        # Mostrar el histograma de valores T2
        plt.subplot(1, 2, 2)
        plt.hist(T2_map.flatten(), bins=100, color='blue', alpha=0.7)
        plt.title('Histograma de valores T2')
        plt.xlabel('Tiempo T2 (ms)')
        plt.ylabel('Frecuencia')

        plt.tight_layout()
        plt.show()
