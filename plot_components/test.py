import si_fab.all as pdk
import numpy as np


trace_template = pdk.NWG1000()

fc = pdk.SiNInvertedTaper()
fc_lv = fc.Layout(
    shallow_taper_start_width=0.75,
    shallow_taper_end_width=1.0,
    shallow_taper_length=45,
    shallow_straight_section_length=1,
    deep_straight_section_length=5,
    deep_taper_start_width=0.6,
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