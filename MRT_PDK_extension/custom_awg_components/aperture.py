import si_fab.all as pdk
import ipkiss3.all as i3
from MRT_PDK_extension import custom_layer_addition
from awg_designer.all import SingleAperture
from .slab import Mat1SlabTemplate
from MRT_PDK_extension.custom_components.Waveguides.MRT_d_03_WG.MRT_WG_trace  import MRTWaveguideTemplate
import MRT_PDK_extension.custom_layer_addition.new_rules
from ipkiss.technology import get_technology

TECH = get_technology()
class LinearAperture(SingleAperture):

    input_width = i3.PositiveNumberProperty(default=3.2, doc='Width of the core of the input waveguide')
    aperture_width = i3.PositiveNumberProperty(default=7, doc='Width of the core of the exit of aperture')



    def _default_trace_template(self):
        # Waveguide cross section at start of aperture
        tt_start = MRTWaveguideTemplate()
        tt_start_lo = tt_start.Layout(
            core_layer=pdk.TECH.PPLAYER.MAT1,
            cladding_layer=pdk.TECH.PPLAYER.MAT2,
            core_width=self.input_width
        )
        return tt_start

    def _default_aperture_trace_template(self):
        # Waveguide cross section at end of aperture
        tt_end = MRTWaveguideTemplate()
        tt_end_lo = tt_end.Layout(
            core_layer=pdk.TECH.PPLAYER.MAT1,
            cladding_layer=pdk.TECH.PPLAYER.MAT2,
            core_width=self.aperture_width
        )
        return tt_end

    def _default_slab_template(self):
        return Mat1SlabTemplate()

    class Layout(SingleAperture.Layout):
        core_layer = i3.LayerProperty(default=pdk.TECH.PPLAYER.MAT1)
        cladding_layer = i3.LayerProperty(default=pdk.TECH.PPLAYER.MAT2)
        taper_length = i3.NonNegativeNumberProperty(default=200, doc="Length of taper section")
        start_straight = i3.NonNegativeNumberProperty(default=20, doc="Straight waveguide length of input waveguide")
        end_straight = i3.NonNegativeNumberProperty(default=50, doc="Straight waveguide length of exit waveguide")

        def _generate_elements(self, elems):

            start_w = self.trace_template.core_width
            end_w   = self.aperture_trace_template.core_width
            core_layer = self.trace_template.core_layer
            cladding_layer = self.trace_template.cladding_layer

            elems += i3.Rectangle(
                layer=core_layer,
                box_size=(self.start_straight, start_w),
                center=(-(self.start_straight/2 + self.taper_length + self.end_straight), 0)
            )

            elems += i3.Wedge(
                layer=core_layer,
                begin_coord=(-self.end_straight-self.taper_length, 0),
                begin_width=start_w,
                end_coord=(-self.end_straight, 0),
                end_width=end_w,

            )

            elems += i3.Rectangle(
                layer=core_layer,
                box_size=(self.end_straight, end_w),
                center=(-self.end_straight/2, 0)
            )

            elems += i3.Rectangle(
                layer=cladding_layer,
                box_size=(self.start_straight+self.taper_length+self.end_straight, end_w + pdk.TECH.MRTWG.CLADDING_WIDTH),
                center=(-(self.start_straight + self.taper_length + self.end_straight) / 2, 0)
            )

            return elems

        def _generate_ports(self, ports):
            ports += i3.OpticalPort(
                name="in",
                position=(-(self.start_straight + self.taper_length + self.end_straight), 0),
                angle=180,
                trace_template=self.trace_template
            )

            ports += i3.OpticalPort(
                name="in_field",
                position=(0, 0),
                angle=0,
                trace_template=self.aperture_trace_template
            )
            return ports

    class FieldModelFromCamfr(SingleAperture.FieldModelFromCamfr):
        """Field model calculating the output fields from a CAMFR simulation.

        Propagates from the input port to the field port.
        """

        def _default_width(self):
            return self.aperture_width + pdk.TECH.MRTWG.CLADDING_WIDTH

        def _default_process_flow(self):
            # process flow to use for the virtual fabrication, select the waveguide-only process
            return pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM


class InputAperture(LinearAperture):
    def _default_input_width(self):
        return TECH.MRTAPERTURE.INPUT_AP_START_WIDTH

    def _default_aperture_width(self):
        return TECH.MRTAPERTURE.INPUT_AP_END_WIDTH

    class Layout(LinearAperture.Layout):

        def _default_taper_length(self):
            return TECH.MRTAPERTURE.INPUT_AP_TAPER_LEN

        def _default_start_straight(self):
            return TECH.MRTAPERTURE.INPUT_AP_START_STRAIGHT_LEN

        def _default_end_straight(self):
            return TECH.MRTAPERTURE.INPUT_AP_END_STRAIGHT_LEN


InputAperture.set_default_view(InputAperture.FieldModelFromCamfr)


class ExitAperture(LinearAperture):
    def _default_input_width(self):
        return TECH.MRTAPERTURE.EXIT_AP_START_WIDTH

    def _default_aperture_width(self):
        return TECH.MRTAPERTURE.EXIT_AP_END_WIDTH

    class Layout(LinearAperture.Layout):
        aperture_core_width = i3.PositiveNumberProperty(
            default=TECH.MRTAPERTURE.EXIT_AP_END_WIDTH
        )

        def _default_taper_length(self):
            return TECH.MRTAPERTURE.EXIT_AP_TAPER_LEN

        def _default_start_straight(self):
            return TECH.MRTAPERTURE.EXIT_AP_START_STRAIGHT_LEN

        def _default_end_straight(self):
            return TECH.MRTAPERTURE.EXIT_AP_END_STRAIGHT_LEN


ExitAperture.set_default_view(ExitAperture.FieldModelFromCamfr)
