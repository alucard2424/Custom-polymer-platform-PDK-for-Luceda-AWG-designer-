

from ipkiss3.pcell.trace.window.window import PathTraceWindow
from ipkiss.technology import get_technology
from ipcore.properties.predefined import NonNegativeNumberProperty, PositiveNumberProperty
from ipkiss.primitives.layer import LayerProperty
from ipkiss3.pcell.photonics.rounded_waveguide import RoundedWaveguide
import numpy as np
import ipkiss3.all as i3

from ipkiss3.technology import TechValue
from MRT_PDK_extension.custom_components.Waveguides.generic.trace import GenericWaveguideTemplate
import os
import si_fab.all as pdk
import ipkiss3.all as i3

# Do not import ipkiss3.all here to avoid cyclic imports
# In this case, caused by loading i3, which loads the autotaperdatabase,
# which (due to a delayed init tree) imports this file.

#__all__ = ["MRTWaveguideTemplate", "MRTWG3200", "MRTWG3500", "MRTWG3000", "RoundedMRTWaveguide"]

TECH = get_technology()


class MRTWaveguideTemplate(GenericWaveguideTemplate):
    _name_prefix = "MRT_FAB_WIRE_WGTEMPLATE"

    class Layout(GenericWaveguideTemplate.Layout):
        cladding_width = PositiveNumberProperty()
        cladding_layer = LayerProperty()

        # def get_material_height(stack, material_name):
        #     for mat, h in stack.materials_heights:
        #         if mat.name == material_name:
        #             return h
        #     raise ValueError(f"Material {material_name} not found in stack.")

        def _default_core_layer(self):
            return pdk.TECH.PPLAYER.MAT1

        def _default_cladding_layer(self):
            return pdk.TECH.PPLAYER.MAT2

        def _default_core_width(self):
            core_width = pdk.TECH.MRTWG.CORE_WIDTH
            return core_width

        def _default_cladding_width(self):
            cladding_width =pdk.TECH.MRTWG.CORE_WIDTH+pdk.TECH.MRTWG.CLADDING_WIDTH
            return cladding_width

        def _default_cover_layers(self):
            return [self.cladding_layer]

        def _default_windows(self):
            windows = [
                PathTraceWindow(
                    layer=self.core_layer,
                    start_offset=-0.5 * self.core_width,
                    end_offset=0.5 * self.core_width,
                ),
                PathTraceWindow(
                    layer=self.cladding_layer,
                    start_offset=-0.5 * self.cladding_width,
                    end_offset=0.5 * self.cladding_width,
                ),
            ]
            return windows

    class CircuitModel(GenericWaveguideTemplate.CircuitModel):
        center_wavelength = PositiveNumberProperty(
            default=1.55, doc="Center wavelength for which n_eff and n_g are defined"
        )
        n_eff = PositiveNumberProperty(
            default=1.42635,
            doc="Effective index of the fundamental waveguide mode for the given center wavelength",
        )
        n_g = PositiveNumberProperty(
            default=1.46344,
            doc="Group index of the fundamental waveguide mode for the given center wavelength",
        )
        loss_dB_m = NonNegativeNumberProperty(default=TechValue("WG_DEFAULTS.LOSS_DB_PERM"), doc="Loss in dB/m")

        def _default_n_eff(self):
            return 1.42635

        def _default_n_eff_values(self):
            n_eff_values = np.loadtxt(os.path.join(os.path.dirname(__file__), "neff_MRT.txt"), delimiter=",")

            # Update the scattering loss to 0.8 dB/cm
            db_cm = 0.8
            loss_1cm = 10 ** (-db_cm / 20)  # Convert dB/cm to linear loss factor
            wav = 1.55  # Wavelength in microns
            imag_neff = -np.log(loss_1cm) * wav / 1e4 * 1 / (2 * np.pi)  # Imaginary part of neff due to scattering loss

            n_eff_values = n_eff_values + imag_neff * 1j  # Add loss as imaginary part

            return [n_eff_values]

        def _default_phase_error_width_deviation(self):
            return 0.000

        def _default_phase_error_correlation_length(self):
            return 0.0

        def _default_wavelengths(self):
            return np.arange(1.5, 1.60, 0.01)

        def _default_widths(self):
            return np.arange(3.0, 12.05, 0.05)


class MRTWG3200(MRTWaveguideTemplate):
    def _default_name(self):
        return "MRTWG3200"

    class Layout(MRTWaveguideTemplate.Layout):
        core_width = PositiveNumberProperty(locked=True)

        def _default_core_width(self):
            return 3.2

    class CircuitModel(MRTWaveguideTemplate.CircuitModel):
        def _default_n_eff(self):
            return 1.42635





# class MRTWG3000(MRTWaveguideTemplate):
#     def _default_name(self):
#         return "MRTWG3000"
#
#     class Layout(MRTWaveguideTemplate.Layout):
#         core_width = PositiveNumberProperty(locked=True)
#
#         def _default_core_width(self):
#             return 3.0
#
#     class CircuitModel(MRTWaveguideTemplate.CircuitModel):
#         def _default_n_eff(self):
#             return 1.42578
#
#
# class MRTWG3500(MRTWaveguideTemplate):
#     def _default_name(self):
#         return "MRTWG3500"
#
#     class Layout(MRTWaveguideTemplate.Layout):
#         core_width = PositiveNumberProperty(locked=True)
#
#         def _default_core_width(self):
#             return 3.5


class RoundedMRTWaveguide(RoundedWaveguide):
    def _default_trace_template(self):
        return MRTWG3200()

    class Layout(RoundedWaveguide.Layout):
        def _default_bend_radius(self):
            return pdk.TECH.MRTWG.BEND_RADIUS


if __name__ == "__main__":
    tt_new = MRTWaveguideTemplate()
    # Define the shape of the waveguide
    shape = i3.Shape([(0, 0), (1600, 0), (1600, 1600)])

    # Define a waveguide class, and pass in the shape and cross section
    wg = RoundedMRTWaveguide(trace_template=tt_new)
    wg_lo = wg.Layout(
        shape=shape
    )
    wg_lo.visualize()
    wg_lo.cross_section(
        cross_section_path=i3.Shape([(10, -10), (10, 10)]),
        process_flow=pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM,
    ).visualize()
    wg_lo.visualize_2d(process_flow=pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM)


    wg_cm = wg.CircuitModel()
    wavelengths = np.linspace(1.5, 1.6, 201)
    S = wg_cm.get_smatrix(wavelengths=wavelengths)



    import matplotlib.pyplot as plt

    T = S["in", "out"]
    phase = np.unwrap(np.angle(T))  # unwrap to remove 2π jumps
    plt.plot(wavelengths, phase)
    plt.xlabel("Wavelength (µm)")
    plt.ylabel("Phase (rad)")
    plt.title("Phase vs wavelength (in -> out)")
    plt.grid(True)
    plt.show()
    c = 299792458.0

    # wavelengths (µm) -> meters
    wl_m = wavelengths * 1e-6
    dphi_dwl = np.gradient(phase, wl_m)  # dφ/dλ (rad / m)
    tau_g = (wl_m ** 2) / (2 * np.pi * c) * dphi_dwl  # group delay (s)
    plt.figure()
    plt.plot(wavelengths, tau_g * 1e12)  # convert to ps
    plt.xlabel("Wavelength (µm)")
    plt.ylabel("Group delay (ps)")
    plt.title("Group delay vs wavelength")
    plt.grid(True)
    plt.show()


    S.visualize()