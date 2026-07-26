# import os
# import si_fab.all as pdk
# from ipkiss.technology import get_technology
# import custom_awg_components.layer_addition
# #from . import layer_addition
# import custom_awg_components.layer_addition.new_rules
# from ipcore.properties.predefined import NonNegativeNumberProperty, PositiveNumberProperty
# from ipkiss3.technology import TechValue
# import numpy as np
# from custom_awg_components.generic.trace import GenericWaveguideTemplate
# import custom_awg_components.all as cc
#
#
#
#
#
# print("Core Width", pdk.TECH.MRTWG.CORE_WIDTH)
# print("Cladding Width", pdk.TECH.MRTWG.CLADDING_WIDTH)
# print("Bend Radius", pdk.TECH.MRTWG.BEND_RADIUS)
#
# center_wavelength = PositiveNumberProperty(
#             default=1.55, doc="Center wavelength for which n_eff and n_g are defined"
#         )
#
# print(center_wavelength)
#
# wavs = np.arange(1.5, 1.6, 0.01)
#
# print(wavs)




import numpy as np
from ipkiss3 import all as i3


# Converts a list of x, y coordinates into a list of waypoints (tuples of x, y positions)
def allxy_2_waypoints(all_xy):
    n_points = len(all_xy) / 2
    way_points = []
    for n in range(n_points):
        way_points.append((all_xy[2 * n], all_xy[2 * n + 1]))

    return way_points


# Converts a list of waypoints back into a flattened list of x, y coordinates
def waypoints_2_allxy(waypoints):
    all_xy = []
    for p in waypoints:
        all_xy.extend([p[0], p[1]])
    return all_xy

# Generates a smooth waveguide shape between a start and end port with optional waypoints
def get_waveguide_shape(
    start_port, end_port, way_points=[], distance_straight=10.0, discretisation=1
):
    original_points = [
        start_port.position,
        start_port.move_polar_copy(distance_straight, start_port.angle).position,
    ]
    original_points.extend(way_points)
    original_points.extend(
        [
            end_port.move_polar_copy(distance_straight, end_port.angle).position,
            end_port.position,
        ]
    )
    original_shape = i3.Shape(
        points=original_points,
        start_face_angle=start_port.angle,
        end_face_angle=end_port.angle + 180.0,
    )
    s2 = i3.ShapeFitClampedCubicSpline(
        original_shape=original_shape, discretisation=discretisation
    )
    return s2

# from scipy.optimize import minimize, brentq

def get_waveguide_shape_fixed_length(
    start_port,
    end_port,
    initial_way_points=[],
    distance_straight=20.0,
    length=None,
    min_y=None,
    max_error=1e-2,
    discretisation=1.0,
    length_discretisation=0.2,
    max_bracket_probe=5000.0,
    bracket_steps=101,
):
    """
    Robustly find a waveguide shape whose length matches `length` by
    optimizing the y-coordinate of a single waypoint (initial_way_points[0]).
    - We first try a smooth bounded minimization of squared error.
    - If that doesn't reach tolerance, we sample y in [min_y, min_y + max_bracket_probe]
      to attempt to bracket the root and then use brentq.
    - length_discretisation: used for more accurate length evaluation during search.
    """

    if length is None:
        raise ValueError("length must be specified for fixed-length waveform generation")

    if not initial_way_points or len(initial_way_points) == 0:
        raise ValueError("initial_way_points must contain at least one waypoint (x,y)")

    # Helper to get length at a given y (use finer discretisation for length evaluations)
    def shape_len_for_y(y, use_discretisation=length_discretisation):
        way_points = [(initial_way_points[0][0], float(y))]
        shape = get_waveguide_shape(
            start_port=start_port,
            end_port=end_port,
            way_points=way_points,
            distance_straight=distance_straight,
            discretisation=use_discretisation,
        )
        return shape.length()

    # Objective: squared error (smooth)
    def obj_squared(y_arr):
        y = float(y_arr[0])
        L = shape_len_for_y(y, use_discretisation=length_discretisation)
        return (L - length) ** 2

    # Initial guess
    y0 = np.asarray([initial_way_points[0][1]])

    # Bounded minimization (allow y >= min_y)
    bounds = [(min_y, min_y + 1e6)]  # keep an upper bound but very large
    try:
        res = minimize(
            obj_squared,
            x0=y0,
            bounds=bounds,
            method="L-BFGS-B",
            options={"ftol": 1e-6, "maxiter": 200},
        )
    except Exception:
        # fallback to Powell if L-BFGS-B fails for some reason
        res = minimize(
            obj_squared,
            x0=y0,
            bounds=bounds,
            method="Powell",
            options={"xtol": 1e-3, "maxiter": 200},
        )

    y_opt = float(res.x[0])
    # Build final shape with requested discretisation
    waypoints_final = [(initial_way_points[0][0], y_opt)]
    shape_final = get_waveguide_shape(
        start_port=start_port,
        end_port=end_port,
        way_points=waypoints_final,
        distance_straight=distance_straight,
        discretisation=discretisation,
    )

    # If we are within tolerance, return
    if abs(shape_final.length() - length) <= max_error:
        return shape_final

    # --- fallback: try to bracket and use root finding ---
    # We attempt to find y_lo, y_hi such that f(y) = shape_len(y) - length changes sign.
    def f_scalar(y):
        return shape_len_for_y(y, use_discretisation=length_discretisation) - length

    # sample candidate ys up to max_bracket_probe
    ys = np.linspace(min_y, min_y + max_bracket_probe, bracket_steps)
    vals = [f_scalar(y) for y in ys]

    bracket = None
    for i in range(len(vals) - 1):
        if vals[i] == 0.0:
            bracket = (ys[i], ys[i])
            break
        if vals[i] * vals[i + 1] < 0:
            bracket = (ys[i], ys[i + 1])
            break

    if bracket is not None:
        a, b = bracket
        try:
            y_root = brentq(f_scalar, a, b, xtol=1e-6, maxiter=200)
            waypoints_final = [(initial_way_points[0][0], float(y_root))]
            shape_final = get_waveguide_shape(
                start_port=start_port,
                end_port=end_port,
                way_points=waypoints_final,
                distance_straight=distance_straight,
                discretisation=discretisation,
            )
            if abs(shape_final.length() - length) <= max_error:
                return shape_final
        except Exception:
            pass

    # If still not within tolerance, warn with diagnostics
    import warnings

    warnings.warn(
        "A smooth connector of length {} could not be made. The real length is {}. "
        "Optimization result: x={} fun={} message={}".format(
            length, shape_final.length(), res.x, getattr(res, "fun", None), getattr(res, "message", "")
        )
    )
    return shape_final






# Generates a set of waveguide shapes forming a bundle
def get_bundle_shapes(start_ports, end_ports, delay_lengths, start_y=0.0):
    shapes = []
    wp = (0.5 * (start_ports[0].position + end_ports[0].position)).move_copy(
        (0.0, start_y)
    )
    min_y = wp[1]
    for pl, pr, d in zip(start_ports, end_ports, delay_lengths):
        s = get_waveguide_shape_fixed_length(
            start_port=pl,
            end_port=pr,
            min_y=min_y,
            length=d,
            initial_way_points=[wp],
            discretisation=1.0,
        )
        shapes.append(s)
        max_y = s.size_info.north
        min_y = max_y
        wp = (wp[0], max_y + 0.2)
    return shapes


# Generates a bundle of waveguides based on the computed shapes
def get_bundle(start_ports, end_ports, delay_lengths, trace_template, start_y=0.0):
    shapes = get_bundle_shapes(
        start_ports=start_ports,
        end_ports=end_ports,
        delay_lengths=delay_lengths,
        start_y=start_y,
    )
    waveguides = [
        i3.Waveguide(trace_template=trace_template).Layout(shape=shape)
        for shape in shapes
    ]
    return waveguides

# Computes the minimum vertical spacing between waveguides in a bundle
def get_min_spacing_bundle(shapes):
    y_maxs = [s.size_info.north for s in shapes]
    return min(np.abs(np.diff(y_maxs)))

from scipy import interpolate

# Computes the curvature at each point of a waveguide shape
def get_curvature_with_spline(shape):
    """
    Returns the curvature (1/bend_radius) of the shape for each point in the shape.
    :param: shape
    :return: list of bend radii as a function of lengths.
    """

    if hasattr(shape, "_get_spline_tck_u"):
        tck, ucontrol, usample = shape._get_spline_tck_u()
    else:
        shape2 = i3.ShapeFitNaturalCubicSpline(original_shape=shape)
        tck, ucontrol, usample = shape2._get_spline_tck_u()

    dt = interpolate.splev(usample, tck, 1)
    ddt = interpolate.splev(usample, tck, 2)
    curvature = (
        np.abs(dt[0] * ddt[1] - ddt[0] * dt[1]) / (dt[0] * dt[0] + dt[1] * dt[1]) ** 1.5
    )
    return curvature

# Computes the maximum curvature across all waveguides in a bundle
def get_max_curvature_bundle(shapes):
    max_curv = max([max(get_curvature_with_spline(shape=s)) for s in shapes])
    return max_curv
