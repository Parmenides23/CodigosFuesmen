import pydicom
import os

# Carpeta donde se encuentran los archivos DICOM
dicom_folder = r"C:\Users\Claudia\Desktop\FUESMEN\Secuencia con datos"

# Carpeta donde guardarás los archivos anonimizados
output_folder = r"C:\Users\Claudia\Desktop\FUESMEN\Axial T2"

# Crear la carpeta de salida si no existe
os.makedirs(output_folder, exist_ok=True)

# Recorrer todos los archivos en la carpeta DICOM
for filename in os.listdir(dicom_folder):
    if filename.endswith(".dcm"):  # Solo archivos DICOM
        file_path = os.path.join(dicom_folder, filename)
        dicom_data = pydicom.dcmread(file_path)

        # Anonimizar los campos de información personal
        dicom_data.PatientName = "Darth Vader"
        dicom_data.PatientID = ""
        dicom_data.PatientBirthDate = ""
        dicom_data.PatientSex = ""
        dicom_data.ReferringPhysicianName = "Lord Farquaad"  # Anonimizar nombre del médico referente
        
        # Guardar el archivo anonimizado en la carpeta de salida
        output_path = os.path.join(output_folder, filename)
        dicom_data.save_as(output_path)

        print(f"Archivo anonimizado guardado: {output_path}")