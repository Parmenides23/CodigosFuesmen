import os
import shutil
import pydicom
import tkinter as tk
from tkinter import filedialog

def identificar_secuencia_dicom(dicom_folder):
    secuencias = {}
    
    # Recorrer los archivos de la carpeta
    for root, _, files in os.walk(dicom_folder):
        for file in files:
            if file.lower().endswith(".dcm"):  # Verifica que sea un archivo DICOM
                file_path = os.path.join(root, file)
# os.walk : Recorre un directorio y sus subdirectorios: La función genera los nombres de los archivos 
# y directorios en el árbol de directorios de forma recursiva. IMPORTANTE: file.lower es para que no 
# existan discrepancias con archivos terminados en .dcm o .DCM y cambia todos los archivos a .dcm en minúscula 
# os.path.join(root, file) se utiliza para crear la ruta completa del archivo combinando el directorio actual (root) 
# con el nombre del archivo (file).
                
                try:
                    # Leer el archivo DICOM
                    dicom_data = pydicom.dcmread(file_path)
                    
                    # Extraer información de la secuencia
                    series_description = dicom_data.get("SeriesDescription", "Desconocida")
                    protocol_name = dicom_data.get("ProtocolName", "Desconocido")
                    numero_serie = dicom_data.get("SeriesNumber", "Desconocido")
                    device_name = dicom_data.get("DeviceSerialNumber", "Desconocido")  # Nombre del equipo
                    
                    # Guardar en el diccionario
                    secuencia_info = {
                        "SeriesDescription": series_description,
                        "ProtocolName": protocol_name,
                        "FilePath": file_path,
                        "SeriesNumber": numero_serie,
                        "DeviceName": device_name,
                    }
                    
                    # Usar la descripción de la serie como clave para agrupar
                    secuencias.setdefault(series_description, []).append(secuencia_info)
                
                except Exception as e:
                    print(f"Error leyendo el archivo {file_path}: {e}")
    
    return secuencias

def copiar_secuencia(secuencias, criterio, valor, destino):
    # Buscar secuencias que coincidan con el criterio y valor
    seleccionadas = [
        detalles for key, detalles in secuencias.items()
        if any(item[criterio] == valor for item in detalles)
    ]
    
    if not seleccionadas:
        print(f"No se encontraron secuencias con {criterio} = {valor}")
        return
    
    # Crear carpeta de destino si no existe
    if not os.path.exists(destino):
        os.makedirs(destino)
    
    # Copiar los archivos seleccionados
    for detalles in seleccionadas:
        for item in detalles:
            origen = item["FilePath"]
            archivo_nombre = os.path.basename(origen)
            destino_final = os.path.join(destino, archivo_nombre)
            shutil.copy(origen, destino_final)
            print(f"Copiado: {origen} -> {destino_final}")
    print(f"¡Secuencia/protocolo copiado exitosamente a {destino}!")

# Función para seleccionar las carpetas con una ventana emergente
def seleccionar_carpeta(titulo="Seleccionar Carpeta"):
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal
    carpeta = filedialog.askdirectory(title=titulo)
    return carpeta

# Selección de la carpeta de entrada y salida
carpeta_entrada = seleccionar_carpeta("Selecciona la carpeta de entrada de los archivos DICOM")
carpeta_salida = seleccionar_carpeta("Selecciona la carpeta de salida para guardar los archivos")

# Identificar secuencias
secuencias_identificadas = identificar_secuencia_dicom(carpeta_entrada)

# Imprimir las opciones disponibles
print("Opciones disponibles:")
for secuencia, detalles in secuencias_identificadas.items():
    print(f"Secuencia: {secuencia}")
    for detalle in detalles[:1]:  # Mostrar solo una entrada por secuencia
        print(f"  - Número de Serie: {detalle['SeriesNumber']}")
        print(f"  - Protocolo: {detalle['ProtocolName']}")
        print(f"  - Nombre del equipo: {detalle['DeviceName']}")
    print()

# Preguntar por el criterio de búsqueda
criterio = input("¿Quieres buscar por 'SeriesDescription' o 'SeriesNumber'? ").strip()
if criterio not in ['SeriesDescription', 'SeriesNumber']:
    print("Criterio no válido. Debe ser 'SeriesDescription' o 'SeriesNumber'.")
else:
    valor = input(f"Ingrese el valor de {criterio}: ").strip()
    # Copiar los archivos correspondientes
    copiar_secuencia(secuencias_identificadas, criterio, valor, carpeta_salida)
