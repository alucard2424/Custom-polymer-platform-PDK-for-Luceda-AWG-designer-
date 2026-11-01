from ipkiss.technology import get_technology
from ipkiss.technology.technology import TechnologyTree
from ipkiss.geometry.shapes.basic import ShapeRectangle

TECH = get_technology()


TECH.METRICS.GRID = 1e-9  # Default manufacturing grid, in m
TECH.METRICS.ANGLE_STEP = 1.0  # Default angle step used in curve discretisation, in degrees


TECH.MRTWG = TechnologyTree()
TECH.MRTWG.CORE_WIDTH = xx
TECH.MRTWG.CLADDING_WIDTH = xx
TECH.MRTWG.BEND_RADIUS = xx
TECH.MRTWG.SPACING = xx

#Aperture Parameters
TECH.MRTAPERTURE = TechnologyTree()
#Input aperture
TECH.MRTAPERTURE.INPUT_AP_START_WIDTH =xx
TECH.MRTAPERTURE.INPUT_AP_END_WIDTH = xx
TECH.MRTAPERTURE.INPUT_AP_TAPER_LEN =xx
TECH.MRTAPERTURE.INPUT_AP_START_STRAIGHT_LEN = xx
TECH.MRTAPERTURE.INPUT_AP_END_STRAIGHT_LEN = xx #can't see any on the mask


#exit aperture
TECH.MRTAPERTURE.EXIT_AP_START_WIDTH = xx
TECH.MRTAPERTURE.EXIT_AP_END_WIDTH = xx
TECH.MRTAPERTURE.EXIT_AP_TAPER_LEN = xx
TECH.MRTAPERTURE.EXIT_AP_START_STRAIGHT_LEN = xx
TECH.MRTAPERTURE.EXIT_AP_END_STRAIGHT_LEN = x
