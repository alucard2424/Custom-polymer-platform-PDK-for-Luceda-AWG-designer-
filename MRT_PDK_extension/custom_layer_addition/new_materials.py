import si_fab.all as pdk
import ipkiss3.all as i3
from ipkiss.visualisation.color import Color
from pysics.basics.material.material_stack import MaterialStack
from pysics.basics.material.material import Material
from pysics.basics.environment import DEFAULT_ENVIRONMENT
from ipkiss.visualisation.display_style import DisplayStyle
from ipkiss.visualisation import color
import os
import numpy as np
from scipy.interpolate import interp1d


COLOR_MAT1 = Color(name="Baby blue", red=0.78, green=0.84, blue=0.91)
COLOR_MAT2 = Color(name="Ugly pink", red=0.82, green=0.59, blue=0.58)


class OpticalMaterial(Material):
    def get_epsilon(self, environment=DEFAULT_ENVIRONMENT):
        return self.get_n(environment) ** 2

    def get_n(self, environment=DEFAULT_ENVIRONMENT):
        raise NotImplementedError("You need to implement the dispersive function")


class Mat1(OpticalMaterial):
    def __init__(self, name="Mat1", **kwargs):
        super().__init__(name=name, **kwargs)

        data_path = os.path.join(os.path.dirname(__file__), "MRT_ormocere_core_core_0.03_data.txt")
        data = np.loadtxt(data_path, usecols=(0, 1))
        wavelengths = data[:, 0]
        n_values = data[:, 1]

        self._n_interp = interp1d(
            wavelengths,
            n_values,
            kind='cubic',
            bounds_error=False,
            fill_value="extrapolate"
        )

    def get_n(self, environment=DEFAULT_ENVIRONMENT):
        return float(self._n_interp(environment.wavelength))


class Mat2(OpticalMaterial):
    def __init__(self, name="Mat2", **kwargs):
        super().__init__(name=name, **kwargs)

        data_path = os.path.join(os.path.dirname(__file__), "MRT_ormocere_cladding_data.txt")
        data = np.loadtxt(data_path, usecols=(0, 1))
        wavelengths = data[:, 0]
        n_values = data[:, 1]

        self._n_interp = interp1d(
            wavelengths,
            n_values,
            kind='cubic',
            bounds_error=False,
            fill_value="extrapolate"
        )

    def get_n(self, environment=DEFAULT_ENVIRONMENT):
        return float(self._n_interp(environment.wavelength))


class Air(Material):
    def get_n(self, environment=DEFAULT_ENVIRONMENT):
        return 1.0


TECH = pdk.TECH
TECH.overwrite_allowed.append("MATERIALS")
TECH.MATERIALS.AIR = Air(name="air", display_style=DisplayStyle(color=color.COLOR_BLUE_CRAYOLA, alpha=0.1), solid=False)
TECH.MATERIALS.MAT1 = Mat1(name="Material 1", display_style=DisplayStyle(color=COLOR_MAT1))
TECH.MATERIALS.MAT2 = Mat2(name="Material 2", display_style=DisplayStyle(color=COLOR_MAT2))


####################################################################
# MATERIALS STACKS
####################################################################

TECH.overwrite_allowed.append("MATERIAL_STACKS")

# Thicknesses of the different layers

MSTACK_MAT1_HEIGHT = 3.2  # um
MSTACK_MAT2_HEIGHT = 10.00  # um


# Material stacks with Material 1 and 2, where Mat1 is a core, and mat2 is a cladding
TECH.MATERIAL_STACKS.MSTACK_CUSTOM_INVALID = MaterialStack(
    name="INVALID_CUSTOM",
    materials_heights=[
        (TECH.MATERIALS.AIR, MSTACK_MAT2_HEIGHT),
        (TECH.MATERIALS.AIR, MSTACK_MAT1_HEIGHT),
        (TECH.MATERIALS.AIR, MSTACK_MAT2_HEIGHT),
    ],
    display_style=DisplayStyle(color=color.COLOR_WHITE),
)

TECH.MATERIAL_STACKS.MSTACK_MAT2 = MaterialStack(
    name="Mat2",
    materials_heights=[
        (TECH.MATERIALS.MAT2, MSTACK_MAT2_HEIGHT),
        (TECH.MATERIALS.MAT2, MSTACK_MAT1_HEIGHT),
        (TECH.MATERIALS.MAT2, MSTACK_MAT2_HEIGHT),
    ],
    display_style=DisplayStyle(color=COLOR_MAT2),
)

TECH.MATERIAL_STACKS.MSTACK_MAT1 = MaterialStack(
    name='Mat1_slab',
    materials_heights=[
        (TECH.MATERIALS.MAT2, MSTACK_MAT2_HEIGHT),
        (TECH.MATERIALS.MAT1, MSTACK_MAT1_HEIGHT),
        (TECH.MATERIALS.MAT2, MSTACK_MAT2_HEIGHT),
    ],
    display_style=DisplayStyle(color=COLOR_MAT1),
)


# Add the material stacks to a virtual fabrication flow

# then compose a process flow

# TECH.VFABRICATION.overwrite_allowed.append("PROCESS_FLOW_CUSTOM")
TECH.VFABRICATION.PROCESS_FLOW_CUSTOM = i3.VFabricationProcessFlow(
    active_processes=[TECH.PROCESS.MAT1, TECH.PROCESS.MAT2],
    process_layer_map={
        TECH.PROCESS.MAT1: TECH.PPLAYER.MAT1,
        TECH.PROCESS.MAT2: TECH.PPLAYER.MAT2,
    },
    process_to_material_stack_map=[
        ((0, 0), TECH.MATERIAL_STACKS.MSTACK_MAT2),
        ((0, 1), TECH.MATERIAL_STACKS.MSTACK_MAT2),
        ((1, 0), TECH.MATERIAL_STACKS.MSTACK_MAT1),
        ((1, 1), TECH.MATERIAL_STACKS.MSTACK_MAT1),
    ],
)
