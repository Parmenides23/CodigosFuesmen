import pydicom
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from tkinter import Tk, filedialog

def load_dicom_image(path):
    dicom_data = pydicom.dcmread(path)
    image = dicom_data.pixel_array.astype(np.float32)
    return image

def compute_pearson(image1, image2):
    if image1.shape != image2.shape:
        raise ValueError("Las imágenes deben tener las mismas dimensiones")
    
    flat1 = image1.flatten()
    flat2 = image2.flatten()
#TRANSFORMA LA MATRIZ EN UN VECTOR FILA PARA PODER CALCULAR LA CORRELACIÓN DE PEARSON
    
    correlation, _ = pearsonr(flat1, flat2)
    return correlation, flat1, flat2

def plot_scatter(flat1, flat2, correlation):
    plt.figure(figsize=(8, 6))
    plt.scatter(flat1, flat2, alpha=0.5, s=1)
    plt.xlabel("Intensidad de píxeles - Imagen 1")
    plt.ylabel("Intensidad de píxeles - Imagen 2")
    plt.title(f"Coeficiente de Pearson: {correlation:.4f}")
    plt.grid()
    plt.show()

def select_file():
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Seleccionar imagen DICOM", filetypes=[("DICOM files", "*.dcm")])
    return file_path

def main():
    path1 = select_file()
    path2 = select_file()
    
    if not path1 or not path2:
        print("Selección de archivos cancelada.")
        return
    
    image1 = load_dicom_image(path1)
    image2 = load_dicom_image(path2)
    
    correlation, flat1, flat2 = compute_pearson(image1, image2)
    print(f"Coeficiente de correlación de Pearson: {correlation:.4f}")
    
    plot_scatter(flat1, flat2, correlation)

if __name__ == "__main__":
    main()