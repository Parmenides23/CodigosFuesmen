import pydicom
import matplotlib.pyplot as plt
import os
from PIL import Image  # Asegúrate de importar PIL para trabajar con imágenes

# Leer archivo DICOM
file_path = r"C:\Users\Claudia\Desktop\FUESMEN\Imagenes de prueba\1.dcm"
dicom_data = pydicom.dcmread(file_path)

# Extraer datos
birth_date = dicom_data.PatientBirthDate  # Fecha en formato AAAAMMDD

# Separar año, mes y día
birth_year = birth_date[:4]  # Primeros 4 dígitos
birth_month = birth_date[4:6]  # Dígitos 5 y 6
birth_day = birth_date[6:]  # Últimos 2 dígitos

patient_data = {
    "Nombre": dicom_data.PatientName,
    "ID": dicom_data.PatientID,
    "Año de nacimiento": birth_year,
    "Mes de nacimiento": birth_month,
    "Día de nacimiento": birth_day,
    "Sexo": dicom_data.PatientSex
}

# Mostrar en consola
for key, value in patient_data.items():
    print(f"{key}: {value}")

# Extraer imagen
image = dicom_data.pixel_array  # Obtener la matriz de píxeles de la imagen

# Normalizar los valores de píxeles para asegurarse de que estén en el rango de 0-255 (formato compatible con JPEG)
image_normalized = (image - image.min()) / (image.max() - image.min()) * 255
image_normalized = image_normalized.astype('uint8')  # Convertir a enteros de 8 bits

# Crear el nuevo nombre del archivo
carpeta_original = os.path.dirname(file_path)  # Carpeta donde está el archivo DICOM
nombre_original = os.path.basename(file_path).split(".")[0]  # Nombre sin la extensión
new_name = f"{nombre_original}j.jpg"  # Nuevo nombre con "j" al final y extensión .jpg
output_path = os.path.join(carpeta_original, new_name)  # Ruta completa para guardar

# Guardar la imagen como JPEG
image_pil = Image.fromarray(image_normalized)  # Crear una imagen PIL desde el array
image_pil.save(output_path, format='JPEG')  # Guardar como JPEG

# Mostrar la imagen
plt.imshow(image, cmap='gray')  # cmap='gray' para escala de grises
plt.title(dicom_data.PatientName)
plt.axis('off')  # Ocultar los ejes
plt.show()

# Confirmación de que la imagen se guardó
print(f"Imagen guardada como: {output_path}")
