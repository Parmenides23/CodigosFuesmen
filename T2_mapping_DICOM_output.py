import pydicom
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tkinter import Tk
from tkinter.filedialog import askdirectory

def exp_decay(TE, S0, T2):
    return S0 * np.exp(-TE / T2)

root = Tk()
root.withdraw()
dicom_folder = askdirectory(title="Seleccionar carpeta con imágenes DICOM")

if not dicom_folder:
    print("No se seleccionó ninguna carpeta.")
else:
    dicom_files = sorted([f for f in os.listdir(dicom_folder) if f.endswith('.dcm')])
    dicom_files = dicom_files[:16]
    print(f"Se procesarán las primeras {len(dicom_files)} imágenes DICOM.")

    images = []
    TE_values = []
    for dicom_file in dicom_files:
        dicom_path = os.path.join(dicom_folder, dicom_file)
        ds = pydicom.dcmread(dicom_path)
        images.append(ds.pixel_array)
        TE_values.append(float(ds[0x0018, 0x0081].value))
    
    print(f"Se leyeron {len(images)} imágenes DICOM.")
    images_array = np.array(images)
    T2_map = np.zeros_like(images_array[0], dtype=np.float32)

    total_pixels = images_array.shape[1] * images_array.shape[2]
    processed_pixels = 0
    print("Comenzando el ajuste exponencial para cada píxel...")

    for i in range(images_array.shape[1]):
        for j in range(images_array.shape[2]):
            signal_values = images_array[:, i, j]
            if np.max(signal_values) < 10:
                T2_map[i, j] = np.nan
                continue
            try:
                S0_init = np.max(signal_values)
                T2_init = 40
                popt, _ = curve_fit(exp_decay, TE_values, signal_values, p0=(S0_init, T2_init), bounds=([0, 10], [np.inf, 200]))
                T2_map[i, j] = popt[1]
            except Exception:
                T2_map[i, j] = np.nan
            
            processed_pixels += 1
            if processed_pixels % (total_pixels // 10) == 0:
                progress = (processed_pixels / total_pixels) * 100
                print(f"Progreso: {progress:.1f}%")
    
    if np.isnan(T2_map).all():
        print("Todos los valores del mapa T2 son NaN.")
    else:
        print(f"El mapa T2 contiene valores válidos.")
        min_T2, max_T2 = np.nanmin(T2_map), np.nanmax(T2_map)
        print(f"Rango de T2: {min_T2:.2f} - {max_T2:.2f} ms")
        
        plt.figure(figsize=(6, 5))
        plt.hist(T2_map.flatten(), bins=100, color='blue', alpha=0.7)
        plt.title('Histograma de valores T2')
        plt.xlabel('Tiempo T2 (ms)')
        plt.ylabel('Frecuencia')
        hist_path = os.path.join(dicom_folder, "histograma_T2.jpg")
        plt.savefig(hist_path, dpi=300)
        plt.close()
        print(f"Histograma guardado en: {hist_path}")
        
        ref_dicom_path = os.path.join(dicom_folder, dicom_files[0])
        ref_ds = pydicom.dcmread(ref_dicom_path)
        new_ds = ref_ds.copy()
        
        if new_ds.file_meta.TransferSyntaxUID not in [
            pydicom.uid.ExplicitVRLittleEndian, pydicom.uid.ImplicitVRLittleEndian
        ]:
            print("Cambiando la sintaxis de transferencia a Explicit VR Little Endian...")
            new_ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        
        # Normalizar valores de T2 con ventana de visualización
        window_min, window_max = 10, 200  # Ajusta estos valores según sea necesario
        T2_map_clipped = np.clip(T2_map, window_min, window_max)
        T2_map_normalized = (T2_map_clipped - window_min) / (window_max - window_min) * 65535
        T2_map_normalized = np.nan_to_num(T2_map_normalized, nan=0).astype(np.uint16)

        # Crear nuevo archivo DICOM
        new_ds.PixelData = T2_map_normalized.tobytes()
        new_ds.Rows, new_ds.Columns = T2_map_normalized.shape
        new_ds.BitsAllocated = 16
        new_ds.BitsStored = 16
        new_ds.HighBit = 15
        new_ds.PixelRepresentation = 0

        output_dicom_path = os.path.join(dicom_folder, "T2_map.dcm")
        pydicom.dcmwrite(output_dicom_path, new_ds)
        print(f"Mapa T2 guardado en: {output_dicom_path}")