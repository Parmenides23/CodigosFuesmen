import pydicom
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tkinter import Tk
from tkinter.filedialog import askdirectory

def exp_decay(TE, S0, T2):
    """Modelo de decaimiento exponencial para el ajuste de T2."""
    return S0 * np.exp(-TE / T2)

# Seleccionar carpeta con imágenes DICOM
root = Tk()
root.withdraw()
dicom_folder = askdirectory(title="Seleccionar carpeta con imágenes DICOM")

if not dicom_folder:
    print("No se seleccionó ninguna carpeta.")
    exit()

# Seleccionar carpeta de salida
output_folder = askdirectory(title="Seleccionar carpeta para guardar resultados")

if not output_folder:
    print("No se seleccionó carpeta de salida. Se usará la misma carpeta de origen.")
    output_folder = dicom_folder

dicom_files = sorted([f for f in os.listdir(dicom_folder) if f.endswith('.dcm')])[:16]
if not dicom_files:
    print("No se encontraron archivos DICOM en la carpeta.")
    exit()

print(f"Se procesarán las primeras {len(dicom_files)} imágenes DICOM.")

# Cargar imágenes y valores TE
images = []
TE_values = []
for dicom_file in dicom_files:
    dicom_path = os.path.join(dicom_folder, dicom_file)
    ds = pydicom.dcmread(dicom_path)
    images.append(ds.pixel_array)
    TE_values.append(float(ds[0x0018, 0x0081].value))  # Echo Time (TE)

print(f"Se leyeron {len(images)} imágenes DICOM.")

# Convertir a array numpy
images_array = np.array(images)
T2_map = np.zeros_like(images_array[0], dtype=np.float32)

# Ajuste exponencial pixel a pixel
total_pixels = images_array.shape[1] * images_array.shape[2]
processed_pixels = 0

print("Comenzando el ajuste exponencial para cada píxel...")

for i in range(images_array.shape[1]):
    for j in range(images_array.shape[2]):
        signal_values = images_array[:, i, j]
        
        if np.max(signal_values) < 10:  # Filtrar valores muy bajos
            T2_map[i, j] = np.nan
            continue

        try:
            S0_init = np.max(signal_values)
            T2_init = 40  # Estimación inicial
            popt, _ = curve_fit(exp_decay, TE_values, signal_values, p0=(S0_init, T2_init), 
                                bounds=([0, 10], [np.inf, 200]))
            T2_map[i, j] = popt[1]  # Extraer T2
        except Exception:
            T2_map[i, j] = np.nan
        
        processed_pixels += 1
        if processed_pixels % (total_pixels // 10) == 0:
            progress = (processed_pixels / total_pixels) * 100
            print(f"Progreso: {progress:.1f}%")

# Si todos los valores son NaN, no generar imagen
if np.isnan(T2_map).all():
    print("Todos los valores del mapa T2 son NaN.")
    exit()

# Rango dinámico basado en percentiles
window_min = np.nanpercentile(T2_map, 1)  # Percentil 1
window_max = np.nanpercentile(T2_map, 99)  # Percentil 99

print(f"Rango dinámico de T2: {window_min:.2f} - {window_max:.2f} ms")

# Guardar histograma en carpeta seleccionada
plt.figure(figsize=(6, 5))
plt.hist(T2_map.flatten(), bins=100, color='blue', alpha=0.7)
plt.title('Histograma de valores T2')
plt.xlabel('Tiempo T2 (ms)')
plt.ylabel('Frecuencia')
hist_path = os.path.join(output_folder, "histograma_T2.jpg")
plt.savefig(hist_path, dpi=300)
plt.close()
print(f"Histograma guardado en: {hist_path}")

# Cargar la imagen de referencia para el DICOM de salida
ref_dicom_path = os.path.join(dicom_folder, dicom_files[0])
ref_ds = pydicom.dcmread(ref_dicom_path)
new_ds = ref_ds.copy()

# Ajustar sintaxis de transferencia
if new_ds.file_meta.TransferSyntaxUID not in [
    pydicom.uid.ExplicitVRLittleEndian, pydicom.uid.ImplicitVRLittleEndian
]:
    print("Cambiando la sintaxis de transferencia a Explicit VR Little Endian...")
    new_ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

# Aplicar normalización con rango dinámico
T2_map_clipped = np.clip(T2_map, window_min, window_max)

# Normalización estándar a 120 bits (4095)
T2_map_normalized = ((T2_map_clipped - window_min) / (window_max - window_min)) * 4096

# Alternativa: Normalización logarítmica (mejor contraste)
apply_log_transform = False  # Cambia a False si no deseas aplicar logaritmo
if apply_log_transform:
    T2_map_log = np.log1p(T2_map_clipped - window_min)  # Log(1 + valor)
    T2_map_log = (T2_map_log / np.max(T2_map_log)) * 4095
    T2_map_normalized = T2_map_log

# Convertir a formato de imagen de 12 bits
T2_map_normalized = np.nan_to_num(T2_map_normalized, nan=0).astype(np.uint16)

# Configurar nuevo DICOM
new_ds.PixelData = T2_map_normalized.tobytes()
new_ds.Rows, new_ds.Columns = T2_map_normalized.shape
new_ds.BitsAllocated = 16
new_ds.BitsStored = 16
new_ds.HighBit = 15
new_ds.PixelRepresentation = 0

# Guardar DICOM en la carpeta seleccionada
output_dicom_path = os.path.join(output_folder, "T2_map.dcm")
pydicom.dcmwrite(output_dicom_path, new_ds)
print(f"Mapa T2 guardado en: {output_dicom_path}")
