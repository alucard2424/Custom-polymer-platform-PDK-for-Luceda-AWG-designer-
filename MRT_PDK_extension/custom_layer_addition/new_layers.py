import si_fab.all as pdk  # noqa: F401
import ipkiss3.all as i3
from ipkiss.process import ProcessLayer, ProcessPurposeLayer
from ipkiss.visualisation.display_style import DisplayStyle
from ipkiss.visualisation.color import Color

TECH = pdk.TECH
TECH.name = "CUSTOMIZED TECHNOLOGY SAMPLE"

# Define the layers which are drawn in a GDS
# PPLayers are drawn in a GDS

TECH.PROCESS.MAT1 = ProcessLayer(name="MAT1", extension='MAT1')
TECH.PPLAYER.MAT1 = ProcessPurposeLayer(
    process=TECH.PROCESS.MAT1,
    purpose=TECH.PURPOSE.DRAWING,
    name="MAT1",
)

TECH.PROCESS.MAT2 = ProcessLayer(name="MAT2", extension='MAT2')
TECH.PPLAYER.MAT2 = ProcessPurposeLayer(
    process=TECH.PROCESS.MAT2,
    purpose=TECH.PURPOSE.DRAWING,
    name="MAT2",
)

# Associate the PPLayers with GDS layer number pairs

TECH.GDSII.LAYERTABLE[(TECH.PROCESS.MAT1, TECH.PURPOSE.DRAWING)] = (30, 0)
TECH.GDSII.LAYERTABLE[(TECH.PROCESS.MAT2, TECH.PURPOSE.DRAWING)] = (31, 0)

# Associate a color and pattern to custom layers in IPKISS visualizer

COLOR_MAT1 = Color(name="Baby blue", red=0.78, green=0.84, blue=0.91)
COLOR_MAT2 = Color(name="Ugly pink", red=0.82, green=0.59, blue=0.58)

DISPLAY_MAT1 = DisplayStyle(color=COLOR_MAT1)
DISPLAY_MAT2 = DisplayStyle(color=COLOR_MAT2)

TECH.DISPLAY.DEFAULT_DISPLAY_STYLE_SET.append((TECH.PPLAYER.MAT2, DISPLAY_MAT2))
TECH.DISPLAY.DEFAULT_DISPLAY_STYLE_SET.append((TECH.PPLAYER.MAT1, DISPLAY_MAT1))
