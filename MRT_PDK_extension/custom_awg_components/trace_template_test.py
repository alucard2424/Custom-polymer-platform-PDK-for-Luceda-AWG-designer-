from ipkiss3.pcell.trace.window.window import PathTraceWindow
from ipkiss.technology import get_technology
from ipcore.properties.predefined import NonNegativeNumberProperty, PositiveNumberProperty
from ipkiss.primitives.layer import LayerProperty
from ipkiss3.pcell.photonics.rounded_waveguide import RoundedWaveguide
import numpy as np
import MRT_PDK_extension.custom_layer_addition.new_rules
from ipkiss3.technology import TechValue
from MRT_PDK_extension.custom_components.Waveguides.generic.trace import GenericWaveguideTemplate
import os
import si_fab.all as pdk

import ipkiss3.all as i3



TECH = get_technology()


class MRTWaveguideTemplate(i3.WindowWaveguideTemplate):
    _name_prefix = "MRT_FAB_WIRE_WGTEMPLATE"

    class Layout(GenericWaveguideTemplate.Layout):
        cladding_width = PositiveNumberProperty()
        cladding_layer = LayerProperty()

        def _default_core_layer(self):
            return pdk.TECH.PPLAYER.MAT1

        def _default_cladding_layer(self):
            return pdk.TECH.PPLAYER.MAT2

        def _default_core_width(self):
            assigned_core_width = pdk.TECH.MRTWG.CORE_WIDTH
            return assigned_core_width

        def _default_cladding_width(self):
            assigned_cladding_width =pdk.TECH.MRTWG.CLADDING_WIDTH
            return assigned_cladding_width

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

    class CircuitModel(i3.WindowWaveguideTemplate.CircuitModel):
        """
        CircuitModel view for MySlotWgTemplate, defining simulation parameters.
        """
        n_eff = i3.PositiveNumberProperty(doc="Effective index of the slot waveguide")

        def _default_n_eff(self):
            """
            Sets a constant effective index for this trace template.
            This value can be adapted manually.
            """
            return 1.42635  # Example constant effective index

        def _default_loss_dB_m(self):
            """
            Sets a constant loss for this trace template
            """
            return 80


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

class RoundedMRTWaveguide(RoundedWaveguide):
    def _default_trace_template(self):
        return MRTWG3200()

    class Layout(RoundedWaveguide.Layout):
        def _default_bend_radius(self):
            return pdk.TECH.MRTWG.BEND_RADIUS


if __name__ == "__main__":
    tt_new = MRTWaveguideTemplate()
    # Define the shape of the waveguide
    shape = i3.Shape([(0, 0), (1500, 0), (1500, 1500)])

    # Define a waveguide class, and pass in the shape and cross section
    wg = i3.RoundedWaveguide(trace_template=tt_new)
    wg_lo = wg.Layout(
        shape=shape,
        bend_radius=pdk.TECH.MRTWG.BEND_RADIUS,
    )
    print(pdk.TECH.MRTWG.BEND_RADIUS)
    wg_lo.visualize()
    wg_lo.write_gdsii('custom_wg_trace.gds')
    wg_lo.cross_section(
        cross_section_path=i3.Shape([(10, -10), (10, 10)]),
        process_flow=pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM,
    ).visualize()
    wg_lo.visualize_2d(process_flow=pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM)

    wg_cm = wg.CircuitModel()
    wavelengths = np.linspace(1.5, 1.6, 201)
    S = wg_cm.get_smatrix(wavelengths=wavelengths)
    S.visualize()

