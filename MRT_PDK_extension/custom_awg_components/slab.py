# Copyright (C) 2020-2024 Luceda Photonics
# This version of Luceda Academy and related packages
# (hereafter referred to as Luceda Academy) is distributed under a proprietary License by Luceda
# It does allow you to develop and distribute add-ons or plug-ins, but does
# not allow redistribution of Luceda Academy  itself (in original or modified form).
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
#
# For the details of the licensing contract and the conditions under which
# you may use this software, we refer to the
# EULA which was distributed along with this program.
# It is located in the root of the distribution folder.

import si_fab.all as pdk
from MRT_PDK_extension import custom_layer_addition
from awg_designer.all import SlabTemplate
from ipkiss.technology import get_technology
import ipkiss3.all as i3

# TECH = get_technology()

__all__ = ["Mat1SlabTemplate"]


class Mat1SlabTemplate(SlabTemplate):
    """Silicon free propagation region slab waveguide template"""

    class Layout(SlabTemplate.Layout):
        slab_layers = i3.LockedProperty()

        def _default_slab_layers(self):
            return [pdk.TECH.PPLAYER.MAT1]

        def cross_section(self, process_flow=None):
            """Override method so we can specify the process flow.

            This cross section is used for visualization and for calculating the slab modes
            when using SlabModesFromCamfr.
            """
            if process_flow is None:
                process_flow = pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM
            return super(Mat1SlabTemplate.Layout, self).cross_section(process_flow)

    class SlabModesFromCamfr(SlabTemplate.SlabModesFromCamfr):
        # Slab modes are dynamically calculated using camfr
        # using the cross-section defined by the layout

        pass


# By default, calculate slabs from camfr
Mat1SlabTemplate.set_default_view("SlabModesFromCamfr")
