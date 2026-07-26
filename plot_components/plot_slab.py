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
import numpy as np

# Define the slab template as Mat1SlabTemplate (defined in custom_awg_components/slab.py)
slab = cc.Mat1SlabTemplate()

# Visualize the slab cross section
slab.Layout().cross_section().visualize()

# Calculate and visualize slab mode effective indices using CAMFR
slab_modes = slab.SlabModesFromCamfr(
    wavelengths=np.linspace(1.5, 1.6, 201),
    process_flow=pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM
)
slab_modes.visualize(wavelengths=np.linspace(1.5, 1.6, 21))
