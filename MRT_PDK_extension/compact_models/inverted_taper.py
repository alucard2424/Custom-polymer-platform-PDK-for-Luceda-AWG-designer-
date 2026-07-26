from ipkiss3.pcell.model import CompactModel
from ipkiss3.pcell.photonics.term import OpticalTerm

from math import sqrt, exp, log


class InvertedTaperModel(CompactModel):
    """
    Inverted taper model with Gaussian wavelength dependence.
    """

    parameters = [
        "center_wavelength",  # nm or µm (match your env.wavelength units)
        "bandwidth_1dB",  # 1 dB bandwidth
        "peak_IL_dB",  # insertion loss at center wavelength
    ]

    terms = [
        OpticalTerm(name="in"),
        OpticalTerm(name="out"),
    ]

    def calculate_smatrix(parameters, env, S):
        # Compute Gaussian-like transmission around center_wavelength
        sigma = parameters.bandwidth_1dB / 2.0 * sqrt(10 / (2 * log(10)))
        peak_transmission = 10 ** (-parameters.peak_IL_dB / 10.0)

        power_S = peak_transmission * exp(
            -((env.wavelength - parameters.center_wavelength) ** 2) / (2.0 * sigma ** 2)
        )

        # Field transmission is sqrt of power transmission
        S["in", "out"] = S["out", "in"] = sqrt(power_S)
