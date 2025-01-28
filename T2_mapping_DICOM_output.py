import pydicom
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tkinter import Tk
from tkinter.filedialog import askdirectory
from pydicom.uid import ImplicitVRLittleEndian

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

            try:
                # Establecer parámetros iniciales
                S0_init = np.max(signal_values)
                T2_init = 1000  # Valor de T2 inicial (ajústalo según tus datos)

                # Establecer límites para el ajuste
                popt, _ = curve_fit(exp_decay, TE_values, signal_values, p0=(S0_init, T2_init), bounds=([0, 10], [np.inf, 3000]))

                # Almacenar el valor de T2 ajustado
                T2_map[i, j] = popt[1]  # El segundo parámetro es T2
            except Exception as e:
                T2_map[i, j] = np.nan  # Si el ajuste falla, asignar NaN
                print(f"Error en el ajuste para el píxel ({i}, {j}): {e}")

            # Actualizar el progreso cada vez que se procesan un 10% de los píxeles
            processed_pixels += 1
            if processed_pixels % (total_pixels // 10) == 0:
                progress = (processed_pixels / total_pixels) * 100
                print(f"Progreso: {progress:.1f}%")

    # Verificar si el mapa T2 contiene valores válidos
    if np.isnan(T2_map).all():
        print("Todos los valores del mapa T2 son NaN.")
    else:
        print(f"El mapa T2 contiene valores válidos. Creando el archivo DICOM...")

        # Crear un nuevo objeto DICOM para almacenar el mapa T2
        dicom_path = os.path.join(dicom_folder, dicom_files[0])
        ds = pydicom.dcmread(dicom_path)

        # Crear un nuevo archivo DICOM con los datos del mapa T2
        new_dicom = ds
        new_dicom.PixelData = T2_map.tobytes()  # Asignar el mapa T2 como datos de píxeles
        new_dicom.Rows, new_dicom.Columns = T2_map.shape  # Establecer las dimensiones de la imagen
        new_dicom.SamplesPerPixel = 1  # Imágenes en escala de grises
        new_dicom.PhotometricInterpretation = 'MONOCHROME2'  # Escala de grises

        # Crear el objeto FileMetaDataset para los metadatos del archivo DICOM
        file_meta = pydicom.dataset.FileMetaDataset()
        file_meta.TransferSyntaxUID = ImplicitVRLittleEndian  # Eliminar la compresión

        # Añadir los metadatos a la instancia DICOM
        new_dicom.file_meta = file_meta
        new_dicom.is_implicit_VR = True
        new_dicom.is_little_endian = True

        # Cambiar el nombre del archivo DICOM
        output_path = os.path.join(dicom_folder, 'T2_map.dcm')
        
        # Guardar el nuevo archivo DICOM
        new_dicom.save_as(output_path)
        print(f"Archivo DICOM guardado en: {output_path}")

        # Imprimir valor medio del mapa T2 para verificar
        print(f"Valor medio del mapa T2: {np.nanmean(T2_map)}")
