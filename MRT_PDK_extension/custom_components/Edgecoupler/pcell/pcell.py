import ipkiss3.all as i3
from MRT_PDK_extension.custom_components.Waveguides.generic.trace import GenericWaveguideTemplate
from MRT_PDK_extension.custom_components.Waveguides.MRT_d_03_WG.MRT_WG_trace import MRTWG3200, MRTWaveguideTemplate
from MRT_PDK_extension.compact_models.all import InvertedTaperModel
import MRT_PDK_extension.custom_layer_addition.new_rules
import si_fab.all as pdk




class MRTInvertedTaper(i3.PCell):
    """Inverted taper on an SiN platform. Its layout and default dimensions were taken from this paper:
    https://ietresearch.onlinelibrary.wiley.com/doi/epdf/10.1049/iet-opt.2018.5065
    """

    trace_template = i3.TraceTemplateProperty(doc="The trace template of the waveguide port")

    def _default_trace_template(self):
        return MRTWG3200()

    class Layout(i3.LayoutView):
        taper_start_width = i3.PositiveNumberProperty(
            default=6, doc="The start width of the shallow tapered section (fibre end)"
        )
        taper_end_width = i3.PositiveNumberProperty(
            default=3.2, doc="The end width of the tapered section"
        )
        taper_length = i3.PositiveNumberProperty(default=350, doc="The length of the tapered section")
        straight_section_length = i3.PositiveNumberProperty(
            default=4.0, doc="The length of the intermediate straight section"
        )
        extra_cladding_width = i3.PositiveNumberProperty(
            default=pdk.TECH.MRTWG.CLADDING_WIDTH, doc="The width of cladding section"
        )

        def generate(self, layout):
            taper_start_width = self.taper_start_width
            taper_end_width = self.taper_end_width
            taper_length = self.taper_length
            straight_section_length = self.straight_section_length
            extra_cladding_width = self.extra_cladding_width


            total_length = taper_length + straight_section_length


            start_trace_template = MRTWaveguideTemplate()
            start_trace_template.Layout(core_width=self.taper_start_width)


            layout += i3.Wedge(
                layer=pdk.TECH.PPLAYER.MAT1,
                begin_coord=(0, 0),
                end_coord=(taper_length, 0),
                begin_width=taper_start_width,
                end_width=taper_end_width,
            )
            layout += i3.Wedge(
                layer=pdk.TECH.PPLAYER.MAT2,
                begin_coord=(0, 0),
                end_coord=(taper_length, 0),
                begin_width=taper_start_width+10,
                end_width=taper_end_width+extra_cladding_width,
            )

            layout += i3.Rectangle(
                layer=pdk.TECH.PPLAYER.MAT1,
                center=(taper_length + 0.5 * straight_section_length, 0),
                box_size=(straight_section_length, taper_end_width),

            )
            layout += i3.Rectangle(
                layer=pdk.TECH.PPLAYER.MAT2,
                center=(taper_length + 0.5 * straight_section_length, 0),
                box_size=(straight_section_length, taper_end_width+extra_cladding_width),
            )



            layout += i3.OpticalPort(
                name="in",
                trace_template=start_trace_template,
                position=(0, 0),
                angle=180,
            )

            layout += i3.OpticalPort(
                name="out",
                trace_template=start_trace_template,
                position=(total_length, 0),
                angle=0,
            )

            return layout

    class Netlist(i3.NetlistFromLayout):
        pass

    class CircuitModel(i3.CircuitModelView):
        center_wavelength = i3.PositiveNumberProperty(doc="center wavelength (um)")
        bandwidth_1dB = i3.PositiveNumberProperty(doc="1dB bandwidth (um)")
        peak_IL_dB = i3.NonNegativeNumberProperty(doc="peak insertion loss (dB)")

        def _default_center_wavelength(self):
            raise NotImplementedError("Please specify center_wavelength")

        def _default_bandwidth_1dB(self):
            raise NotImplementedError("Please specify bandwidth_1dB")

        def _default_peak_IL_dB(self):
            raise NotImplementedError("Please specify peak_IL_dB")

        def _generate_model(self):
            return InvertedTaperModel(
                center_wavelength=self.center_wavelength,
                bandwidth_1dB=self.bandwidth_1dB,
                peak_IL_dB=self.peak_IL_dB,
            )




@i3.lock_properties()
class MRT_FC_TE_1550(MRTInvertedTaper):

    def _default_name(self):
        return "MRT_FC_TE_1550"


    class CircuitModel(MRTInvertedTaper.CircuitModel):
        def _default_center_wavelength(self):
            return 1.55

        def _default_bandwidth_1dB(self):
            return 0.0248

        def _default_peak_IL_dB(self):
            return 2.39
