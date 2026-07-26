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
import ipkiss3.all as i3
import MRT_PDK_extension.all as cc

# Define the trace template (waveguide cross section)
tt_new = cc.MRTWaveguideTemplate()   # Start from the simple wire waveguide template in SiFab
tt_new_lo = tt_new.Layout(               # Change the default core and cladding layers to custom ones
    core_layer=pdk.TECH.PPLAYER.MAT1,
    cladding_layer=pdk.TECH.PPLAYER.MAT2,
                          )

# Define the shape of the waveguide
shape = i3.Shape([(0, 0), (100, 0), (100, 100)])

# Define a waveguide class, and pass in the shape and cross section
wg = i3.RoundedWaveguide(trace_template=tt_new)
wg_lo = wg.Layout(
    shape=shape,
)

# Visualize the waveguide, write it to GDS. Note that custom GDS layer numbers are exported
wg_lo.visualize()
wg_lo.write_gdsii('wg_example.gds')

# Visualize the material stacks across the layout
wg_lo.visualize_2d(process_flow=pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM)

# Visualize the cross section of the waveguide with the custom materials
wg_lo.cross_section(
     cross_section_path=i3.Shape([(5, -5), (5, 5)]),
     process_flow=pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM,
 ).visualize()
