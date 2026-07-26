from ipkiss.technology import get_technology
from ipkiss.technology.technology import TechnologyTree
from ipkiss.geometry.shapes.basic import ShapeRectangle

TECH = get_technology()


TECH.METRICS.GRID = 1e-9  # Default manufacturing grid, in m
TECH.METRICS.ANGLE_STEP = 1.0  # Default angle step used in curve discretisation, in degrees


TECH.MRTWG = TechnologyTree()
TECH.MRTWG.CORE_WIDTH = 3.2
TECH.MRTWG.CLADDING_WIDTH = 10
TECH.MRTWG.BEND_RADIUS = 1500.0
TECH.MRTWG.SPACING = 10.0

#Aperture Parameters
TECH.MRTAPERTURE = TechnologyTree()
#Input aperture
TECH.MRTAPERTURE.INPUT_AP_START_WIDTH = 3.2
TECH.MRTAPERTURE.INPUT_AP_END_WIDTH = 7
TECH.MRTAPERTURE.INPUT_AP_TAPER_LEN = 266
TECH.MRTAPERTURE.INPUT_AP_START_STRAIGHT_LEN = 4
TECH.MRTAPERTURE.INPUT_AP_END_STRAIGHT_LEN = 0 #can't see any on the mask


#exit aperture
TECH.MRTAPERTURE.EXIT_AP_START_WIDTH = 3.2
TECH.MRTAPERTURE.EXIT_AP_END_WIDTH = 6
TECH.MRTAPERTURE.EXIT_AP_TAPER_LEN = 196
TECH.MRTAPERTURE.EXIT_AP_START_STRAIGHT_LEN = 4
TECH.MRTAPERTURE.EXIT_AP_END_STRAIGHT_LEN = 0
