import os
import shutil
import pydicom
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog

def seleccionar_carpeta(titulo="Seleccionar Carpeta"):
    """Abre un cuadro de diálogo para seleccionar una carpeta."""
    carpeta = filedialog.askdirectory(title=titulo)
    return carpeta

def identificar_secuencias(dicom_folder):
    """
    Identifica las secuencias en la carpeta DICOM.

    Parameters:
        dicom_folder (str): Ruta de la carpeta con archivos DICOM.

    Returns:
        dict: Diccionario con SeriesNumber como clave y una lista de diccionarios con detalles de archivos como valor.
    """
    secuencias = {}
    for root, _, files in os.walk(dicom_folder):
        for file in files:
            if file.lower().endswith(".dcm"):
                file_path = os.path.join(root, file)
                try:
                    dicom_data = pydicom.dcmread(file_path)
                    series_number = dicom_data.get("SeriesNumber", "Desconocido")
                    series_description = dicom_data.get("SeriesDescription", "Desconocido")
                    if series_number not in secuencias:
                        secuencias[series_number] = {
                            "description": series_description,
                            "files": []
                        }
                    secuencias[series_number]["files"].append(file_path)
                except Exception as e:
                    print(f"Error leyendo el archivo {file_path}: {e}")
    return secuencias

def seleccionar_secuencia(secuencias):
    """
    Permite al usuario seleccionar una secuencia de una lista.

    Parameters:
        secuencias (dict): Diccionario de secuencias identificadas.

    Returns:
        int: El número de serie seleccionado, o None si no se selecciona.
    """
    opciones = "\n".join([f"{serie}: {detalles['description']} ({len(detalles['files'])} archivos)" for serie, detalles in secuencias.items()])
    mensaje = f"Selecciona una secuencia ingresando su número de serie:\n{opciones}"
    seleccion = simpledialog.askstring("Seleccionar Secuencia", mensaje)
    if seleccion and seleccion.isdigit():
        seleccion = int(seleccion)
        if seleccion in secuencias:
            return seleccion
    print("Selección inválida o cancelada.")
    return None

def agrupar_imagenes_por_posicion(file_paths, output_folder):
    """
    Agrupa imágenes DICOM por ImagePositionPatient.

    Parameters:
        file_paths (list): Lista de rutas de archivos DICOM.
        output_folder (str): Ruta de la carpeta de salida para las imágenes agrupadas.
    """
    for file_path in file_paths:
        try:
            # Leer el archivo DICOM
            dicom_data = pydicom.dcmread(file_path)

            # Obtener ImagePositionPatient
            position = dicom_data.get("ImagePositionPatient", "Desconocida")

            # Verificar que position sea válida
            if position != "Desconocida":
                position_str = "_".join(map(str, position))
            else:
                position_str = "Desconocida"

            # Crear carpetas de salida organizadas
            position_folder = os.path.join(output_folder, f"Posicion_{position_str}")
            os.makedirs(position_folder, exist_ok=True)

            # Copiar archivo a la carpeta correspondiente
            shutil.copy(file_path, position_folder)
        except Exception as e:
            print(f"Error procesando {file_path}: {e}")

if __name__ == "__main__":
    # Crear una ventana oculta para los cuadros de diálogo
    root = tk.Tk()
    root.withdraw()

    # Seleccionar carpeta de entrada y salida
    carpeta_entrada = seleccionar_carpeta("Selecciona la carpeta de entrada de los archivos DICOM")
    carpeta_salida = seleccionar_carpeta("Selecciona la carpeta de salida para agrupar las imágenes")

    if carpeta_entrada and carpeta_salida:
        # Identificar secuencias
        secuencias_identificadas = identificar_secuencias(carpeta_entrada)

        # Seleccionar una secuencia
        secuencia_seleccionada = seleccionar_secuencia(secuencias_identificadas)

        if secuencia_seleccionada is not None:
            # Agrupar imágenes por posición
            agrupar_imagenes_por_posicion(secuencias_identificadas[secuencia_seleccionada]["files"], carpeta_salida)
            print("Imágenes agrupadas exitosamente.")
        else:
            print("No se seleccionó ninguna secuencia.")
    else:
        print("No se seleccionaron carpetas de entrada o salida.")
