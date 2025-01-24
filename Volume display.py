import os
import matplotlib.pyplot as plt
import pydicom
import numpy as np
import tkinter as tk
from tkinter import Button
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Paso 1: Cargar todas las imágenes DICOM de una carpeta ---
def cargar_imagenes_dicom(dicom_dir):
    slices = []
    
    for f in os.listdir(dicom_dir):
        if f.endswith(".dcm"):
            dicom_path = os.path.join(dicom_dir, f)
            ds = pydicom.dcmread(dicom_path)
            slices.append(ds)
    
    slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))  # Ordenar según la posición en z
    
    return slices

# --- Paso 2: Crear un volumen 3D apilando las imágenes ---
def crear_volumen(slices):
    # Apilar las imágenes en un volumen 3D (eje z)
    volumen_3d = np.stack([s.pixel_array for s in slices], axis=-1)
    return volumen_3d

# --- Paso 3: Visualizar una "rebanada" del volumen 3D ---
def visualizar_imagen(volumen_3d, slice_index, canvas, fig, ax):
    ax.clear()  # Limpiar el eje
    ax.imshow(volumen_3d[:, :, slice_index], cmap="gray")
    ax.set_title(f"Slice {slice_index+1}")
    canvas.draw()

# --- Paso 4: Función para avanzar a la siguiente imagen ---
def siguiente_imagen(volumen_3d, slice_index, canvas, fig, ax):
    if slice_index < volumen_3d.shape[2] - 1:
        slice_index += 1
        visualizar_imagen(volumen_3d, slice_index, canvas, fig, ax)
    return slice_index

# --- Función principal que crea la ventana de Tkinter ---
def main(dicom_dir):
    slices = cargar_imagenes_dicom(dicom_dir)
    
    if not slices:
        print("No se encontraron imágenes DICOM en la carpeta.")
        return
    
    # Crear el volumen 3D
    volumen_3d = crear_volumen(slices)
    
    slice_index = [0]  # Utilizamos una lista para que sea mutable

    # Crear la ventana principal de Tkinter
    root = tk.Tk()
    root.title("Visor de Volumen DICOM 3D")
    
    # Crear el gráfico de Matplotlib para incrustar en Tkinter
    fig, ax = plt.subplots(figsize=(6, 6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack()
    
    # Mostrar la primera imagen
    visualizar_imagen(volumen_3d, slice_index[0], canvas, fig, ax)
    
    # Crear botón para avanzar a la siguiente imagen
    def avanzar():
        slice_index[0] = siguiente_imagen(volumen_3d, slice_index[0], canvas, fig, ax)
    
    btn_siguiente = Button(root, text="Siguiente Imagen", command=avanzar)
    btn_siguiente.pack()

    # Ejecutar la ventana de Tkinter
    root.mainloop()

# --- Uso del código ---
dicom_dir = r"C:\Users\Claudia\Desktop\FUESMEN\HIGADO PACIENTE 1\T2W_TSE_COR"  # Ruta a la carpeta que contiene las imágenes DICOM
main(dicom_dir)
