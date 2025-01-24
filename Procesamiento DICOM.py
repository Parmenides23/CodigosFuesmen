import os
import shutil
import pydicom
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
import threading

def mostrar_Instrucciones():
    # Crear una ventana emergente con un tamaño más ancho
    ventana_instrucciones = tk.Toplevel()
    ventana_instrucciones.title("Instrucciones")
    ventana_instrucciones.geometry("600x400")  # Ajusta el tamaño aquí (ancho x alto)

    # Crear un widget de texto para mostrar las instrucciones
    texto_instrucciones = tk.Text(ventana_instrucciones, wrap=tk.WORD, height=600, width=900)
    texto_instrucciones.pack(padx=10, pady=10)

    # Definir el contenido de las instrucciones
    Instrucciones = """
    1 Selecciona la Carpeta de Entrada: Elige la carpeta que contiene los archivos DICOM.

    2 Selecciona la Carpeta de Salida: Define la carpeta donde se copiarán los archivos procesados.

    3 Revisa la Información de las Secuencias: Se mostrará una ventana con detalles de las secuencias. 
    ¡¡Desplázate con la rueda del mouse para ver toda la información!!

    4 Selecciona el Criterio de Búsqueda: Elige entre "Descripción de Secuencia" o "Número de Serie".

    5 Ingresa el Valor de Criterio: Introduce el valor que deseas buscar (ej. nombre de la secuencia o número de serie).

    6 Copiado de Archivos: Los archivos que coincidan con el criterio seleccionado serán copiados a la carpeta de salida.
    """

    # Insertar las instrucciones en el widget de texto
    texto_instrucciones.insert(tk.END, Instrucciones)
    texto_instrucciones.config(state=tk.DISABLED)  # Hacer el cuadro de texto solo lectura

    

def identificar_secuencia_dicom(dicom_folder):
    secuencias = {}
    for root, _, files in os.walk(dicom_folder):
        for file in files:
            if file.lower().endswith(".dcm"):  # Verifica que sea un archivo DICOM
                file_path = os.path.join(root, file)
                try:
                    dicom_data = pydicom.dcmread(file_path)
                    series_description = dicom_data.get("SeriesDescription", "Desconocida")
                    protocol_name = dicom_data.get("ProtocolName", "Desconocido")
                    numero_serie = dicom_data.get("SeriesNumber", "Desconocido")
                    device_name = dicom_data.get("DeviceSerialNumber", "Desconocido")
                    secuencia_info = {
                        "SeriesDescription": series_description,
                        "ProtocolName": protocol_name,
                        "FilePath": file_path,
                        "SeriesNumber": numero_serie,
                        "DeviceName": device_name,
                    }
                    secuencias.setdefault(series_description, []).append(secuencia_info)
                except Exception as e:
                    print(f"Error leyendo el archivo {file_path}: {e}")
    return secuencias

def copiar_secuencia(secuencias, criterio, valor, destino):
    seleccionadas = [
        detalles for key, detalles in secuencias.items()
        if any(item[criterio] == valor for item in detalles)
    ]
    
    if not seleccionadas:
        print(f"No se encontraron secuencias con {criterio} = {valor}")
        return
    
    if not os.path.exists(destino):
        os.makedirs(destino)
    
    for detalles in seleccionadas:
        for item in detalles:
            origen = item["FilePath"]
            archivo_nombre = os.path.basename(origen)
            destino_final = os.path.join(destino, archivo_nombre)
            shutil.copy(origen, destino_final)
            print(f"Copiado: {origen} -> {destino_final}")
    print(f"¡Secuencia/protocolo copiado exitosamente a {destino}!")

def seleccionar_carpeta(titulo="Seleccionar Carpeta"):
    carpeta = filedialog.askdirectory(title=titulo)
    return carpeta

def mostrar_info_secuencias(secuencias_identificadas):
    info_ventana = tk.Toplevel()
    info_ventana.title("Información de las secuencias")
    
    # No permitir que el tamaño del frame cambie con el contenido
    frame = tk.Frame(info_ventana)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    # Crear el widget de texto que se expandirá para ajustar el contenido
    texto_info = tk.Text(frame, wrap=tk.WORD)
    texto_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Configurar texto sin necesidad de barra deslizadora
    info_secuencias = ""
    for secuencia, detalles in secuencias_identificadas.items():
        info_secuencias += f"Secuencia: {secuencia}\n"
        for detalle in detalles[:1]:  # Mostrar solo una entrada por secuencia
            info_secuencias += f"  - Número de Serie: {detalle['SeriesNumber']}\n"
            info_secuencias += f"  - Protocolo: {detalle['ProtocolName']}\n"
            info_secuencias += f"  - Nombre del equipo: {detalle['DeviceName']}\n"
        info_secuencias += "\n"

    texto_info.insert(tk.END, info_secuencias)
    texto_info.config(state=tk.DISABLED)  # Hacer el cuadro de texto solo lectura

def seleccionar_criterio():
    criterio_seleccionado = simpledialog.askstring("Seleccionar criterio", 
                                                   "¿Quieres buscar por 'SeriesDescription' o 'SeriesNumber'?")
    if criterio_seleccionado and criterio_seleccionado in ['SeriesDescription', 'SeriesNumber']:
        valor = simpledialog.askstring("Ingresar valor", f"Ingrese el valor de {criterio_seleccionado}:")
        if valor:
            return criterio_seleccionado.strip(), valor.strip()
    return None, None

def ejecutar_seleccion_criterio():
    criterio, valor = seleccionar_criterio()
    if criterio and valor:
        copiar_secuencia(secuencias_identificadas, criterio, valor, carpeta_salida)
    else:
        print("No se ingresó un valor o criterio válido.")

# Crear una ventana principal oculta (no la mostramos)
root = tk.Tk()
root.withdraw()

# Mostrar las instrucciones
mostrar_Instrucciones()

# Selección de la carpeta de entrada y salida
carpeta_entrada = seleccionar_carpeta("Selecciona la carpeta de entrada de los archivos DICOM")
carpeta_salida = seleccionar_carpeta("Selecciona la carpeta de salida para guardar los archivos")

# Identificar secuencias
secuencias_identificadas = identificar_secuencia_dicom(carpeta_entrada)

# Mostrar la información obtenida en una ventana emergente
mostrar_info_secuencias(secuencias_identificadas)

# Ejecutar la selección del criterio en el hilo principal
ejecutar_seleccion_criterio()
