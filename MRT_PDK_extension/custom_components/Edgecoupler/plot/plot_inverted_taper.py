from MRT_PDK_extension.all import MRTWG3200
from MRT_PDK_extension.custom_components.Edgecoupler.pcell.pcell import MRTInvertedTaper, MRT_FC_TE_1550
import numpy as np





# trace_template = MRTWG3200()
#
# fc = MRTInvertedTaper()
# fc_lv = fc.Layout(
#     taper_start_width=6,
#     taper_end_width=3.2,
#     taper_length=250,
#     straight_section_length=5,
# )
# fc_lv.visualize()
#
# fc_cm = fc.CircuitModel()
#
# wavelengths = np.linspace(1.55, 1.56, 1000)
# S = fc_cm.get_smatrix(wavelengths=wavelengths)
# S.visualize(
#     term_pairs=[("in", "out")],
#     scale="dB",
#     title="Power transmission",
# )



trace_template = MRTWG3200()

fc = MRT_FC_TE_1550()
fc_lv = fc.Layout(
)
fc_lv.visualize()

fc_cm = fc.CircuitModel()

wavelengths = np.linspace(1.55, 1.56, 1000)
S = fc_cm.get_smatrix(wavelengths=wavelengths)
S.visualize(
    term_pairs=[("in", "out")],
    scale="dB",
    title="Power transmission",
)
