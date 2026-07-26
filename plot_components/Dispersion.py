from MRT_PDK_extension.custom_layer_addition.new_materials import Mat1, Mat2
import matplotlib.pyplot as plt
import numpy as np
from pysics.basics.environment import Environment
import os


current_dir = os.path.dirname(__file__)
data_path_core = os.path.join(current_dir, "MRT_ormocere_core_core_0.03_data.txt")
data_path_cladding = os.path.join(current_dir, "MRT_ormocere_cladding_data.txt")


data_core = np.loadtxt(data_path_core, usecols=(0, 1))
data_cladding = np.loadtxt(data_path_cladding, usecols=(0, 1))
raw_wavelengths = data_core[:, 0]
raw_n = data_core[:, 1]

raw_wavelengths_cladding = data_cladding[:, 0]
raw_n_cladding = data_cladding[:, 1]


material_core = Mat1()
material_cladding = Mat2()


wavs = np.arange(0.4, 1.7, 0.01)
n_interp_core = np.array([
    material_core.get_n(Environment(wavelength=w)) for w in wavs
])

n_interp_cladding = np.array([
    material_cladding.get_n(Environment(wavelength=w)) for w in wavs
])


plt.figure(figsize=(8, 5))
plt.plot(raw_wavelengths, raw_n, "o", label="Raw data", markersize=4)
plt.plot(wavs, n_interp_core, "-", linewidth=2, label="Interpolated (Mat1)", alpha=0.8)
plt.xlabel("Wavelength [μm]")
plt.ylabel("Refractive Index n")
plt.title("Refractive Index of Mat1")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(raw_wavelengths_cladding, raw_n_cladding, "o", label="Raw data", markersize=4)
plt.plot(wavs, n_interp_cladding, "-", linewidth=2, label="Interpolated (Mat1)", alpha=0.8)
plt.xlabel("Wavelength [μm]")
plt.ylabel("Refractive Index n")
plt.title("Refractive Index of Mat2")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


plt.figure(figsize=(8, 5))
plt.plot(raw_wavelengths_cladding, raw_n-raw_n_cladding, "o", label="Raw data", markersize=4)
plt.plot(wavs, n_interp_core-n_interp_cladding, "-", linewidth=2, label="Interpolated", alpha=0.8)
plt.xlabel("Wavelength [μm]")
plt.ylabel(r"Index difference $\Delta$n")
plt.title("Index Contrast of Core and Cladding")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
