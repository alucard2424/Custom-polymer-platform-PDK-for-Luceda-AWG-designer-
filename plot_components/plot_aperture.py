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

import si_fab.all as pdk  # noqa: F401
import ipkiss3.all as i3
import MRT_PDK_extension.all as cc
import numpy as np

# Define simulation wavelength range
wavelengths = np.linspace(1.5, 1.6, 100)
center_wavelength = 1.55

# Define the slab template. This relates to the FPR with which the aperture interfaces
slab_tmpl = cc.Mat1SlabTemplate()
slab_tmpl.SlabModesFromCamfr(wavelengths=wavelengths,
                             process_flow=pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM)

# Instantiate the aperture object
ap = cc.ExitAperture()
ap_lay = ap.Layout()
ap_lay.visualize(annotate=True)
# ap_lay.visualize_2d(process_flow=pdk.TECH.VFABRICATION.PROCESS_FLOW_CUSTOM)

# Calculate the fields within the aperture using Camfr
fieldmodel = ap.FieldModelFromCamfr()
env = i3.Environment(wavelength=center_wavelength)

# Field profile at the aperture exit
fields = fieldmodel.get_fields(mode=0, environment=env)
fields.visualize()

# Field propagated from input to the aperture exit
fields_2d = fieldmodel.get_aperture_fields2d(mode=0, environment=env)
fields_2d.visualize()


# Far field of the aperture
fields_ff = fieldmodel.get_far_field(mode=0, environment=env)
divergence_angle = fields_ff.divergence_angle(slab_mode="TE0", method="e_sq")
fields_ff.visualize()

# camfr_expression = i3.device_sim.camfr_stack_expr_for_structure(
#     structure=ap_lay,
#     discretisation_resolution=int(1.0/grid),
#     environment=env,
#     material_stack_to_material_map=mater
# )
