import warnings
from typing import Any, List, Tuple, Optional
import numpy as np
from scipy.optimize import minimize, brentq
from scipy import interpolate
from ipkiss3 import all as i3



def allxy_2_waypoints(all_xy: List[float]) -> List[Tuple[float, float]]:
    """Convert flattened [x0,y0,x1,y1,...] into [(x0,y0),(x1,y1),...]."""
    n_points = int(len(all_xy) / 2)
    way_points = []
    for n in range(n_points):
        way_points.append((all_xy[2 * n], all_xy[2 * n + 1]))
    return way_points


def waypoints_2_allxy(waypoints: List[Tuple[float, float]]) -> List[float]:
    """Convert list of waypoints into flattened list [x0,y0,x1,y1,...]."""
    all_xy = []
    for p in waypoints:
        all_xy.extend([p[0], p[1]])
    return all_xy



def get_waveguide_shape(
        start_port: Any,
        end_port: Any,
        way_points: List[Tuple[float, float]] = [],
        distance_straight: float = 10.0,
        discretisation: float = 1.0,
):
    """
    Build a smooth waveguide Shape between start_port and end_port,
    inserting short straight segments near the ports and fitting a clamped cubic spline.
    """
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



def get_curvature_with_spline(shape: Any) -> np.ndarray:
    """
    Compute curvature (1/R) along the shape using spline representation.
    Returns an array of curvature values sampled along the shape.
    """
    # Recreate/obtain spline tck,u sample used by IPKISS shape internals.
    if hasattr(shape, "_get_spline_tck_u"):
        tck, ucontrol, usample = shape._get_spline_tck_u()
    else:
        # fallback to a natural cubic spline fit if the shape doesn't expose tck directly
        shape2 = i3.ShapeFitNaturalCubicSpline(original_shape=shape)
        tck, ucontrol, usample = shape2._get_spline_tck_u()

    # first and second derivatives from spline
    dt = interpolate.splev(usample, tck, 1)  # [dx/du, dy/du]
    ddt = interpolate.splev(usample, tck, 2)  # [d2x/du2, d2y/du2]

    # curvature formula: |x' y'' - y' x''| / (x'^2 + y'^2)^(3/2)
    num = np.abs(dt[0] * ddt[1] - ddt[0] * dt[1])
    den = (dt[0] * dt[0] + dt[1] * dt[1]) ** 1.5
    # avoid division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        curvature = np.where(den > 0, num / den, 0.0)
    return curvature


def get_max_bend_radius(shape: Any) -> Tuple[float, float]:
    """
    Returns (max_curvature, min_bend_radius).
    - max_curvature is the maximum curvature along the shape (1/µm).
    - min_bend_radius = 1 / max_curvature (µm). If curvature == 0 returns inf.
    """
    curv = get_curvature_with_spline(shape)
    if curv.size == 0:
        return 0.0, float("inf")
    max_curv = float(np.max(curv))
    if max_curv <= 0.0:
        return max_curv, float("inf")
    return max_curv, 1.0 / max_curv



def get_waveguide_shape_fixed_length(
    start_port: Any,
    end_port: Any,
    initial_way_points: List[Tuple[float, float]] = [],
    distance_straight: float = 20.0,
    length: Optional[float] = None,
    min_y: Optional[float] = None,
    max_error: float = 1e-2,
    discretisation: float = 1.0,
    length_discretisation: float = 0.2,
    max_bracket_probe: float = 5000.0,
    bracket_steps: int = 101,
    # NEW: curvature enforcement options
    min_bend_radius: Optional[float] = 1500,         # µm; if None -> no bend constraint
    curvature_penalty_weight: float = 1e6,           # penalty weight for curvature violation
):
    """
    Find a single-waypoint smooth connector whose length matches `length` (µm)
    by adjusting the y of initial_way_points[0].
    """
    if length is None:
        raise ValueError("length must be specified for fixed-length waveform generation")

    if not initial_way_points or len(initial_way_points) == 0:
        raise ValueError("initial_way_points must contain at least one waypoint (x,y)")

    if min_y is None:
        raise ValueError("min_y must be provided to define feasible waypoint bounds")

    base_x = float(initial_way_points[0][0])

    def shape_len_for_y(y: float, use_discretisation: float = length_discretisation):
        wp = [(base_x, float(y))]
        shape = get_waveguide_shape(
            start_port=start_port,
            end_port=end_port,
            way_points=wp,
            distance_straight=distance_straight,
            discretisation=use_discretisation,
        )
        L = shape.length()
        max_curv, min_radius = get_max_bend_radius(shape)
        return L, max_curv, min_radius

    def obj_squared(y_arr: np.ndarray) -> float:
        y = float(y_arr[0])
        L, max_curv, _ = shape_len_for_y(y, use_discretisation=length_discretisation)
        err = (L - length) ** 2
        penalty = 0.0
        if min_bend_radius is not None:
            allowed_curv = 1.0 / float(min_bend_radius)
            excess = max(0.0, max_curv - allowed_curv)
            penalty = curvature_penalty_weight * (excess ** 2)
        return float(err + penalty)

    y0 = np.asarray([initial_way_points[0][1]], dtype=float)
    bounds = [(min_y, min_y + 1e6)]

    try:
        res = minimize(
            obj_squared,
            x0=y0,
            bounds=bounds,
            method="L-BFGS-B",
            options={"ftol": 1e-6, "maxiter": 400},
        )
    except Exception:
        res = minimize(
            obj_squared,
            x0=y0,
            bounds=bounds,
            method="Powell",
            options={"xtol": 1e-3, "maxiter": 400},
        )

    y_opt = float(res.x[0])
    waypoints_final = [(base_x, y_opt)]
    shape_final = get_waveguide_shape(
        start_port=start_port,
        end_port=end_port,
        way_points=waypoints_final,
        distance_straight=distance_straight,
        discretisation=discretisation,
    )

    if abs(shape_final.length() - length) <= max_error:
        # verify curvature constraint if requested
        if min_bend_radius is not None:
            max_curv_final, min_radius_final = get_max_bend_radius(shape_final)
            if max_curv_final > 1.0 / float(min_bend_radius):
                warnings.warn(
                    f"Shape meets length but violates bend radius: requested Rmin={min_bend_radius:.3f} µm, "
                    f"real min radius={min_radius_final:.3f} µm. Consider increasing penalty or relaxing target."
                )
        return shape_final

    def f_scalar_for_bracket(y: float) -> float:
        L, max_curv, _ = shape_len_for_y(y, use_discretisation=length_discretisation)
        if min_bend_radius is not None and max_curv > 1.0 / float(min_bend_radius):
            return np.nan
        return L - length

    ys = np.linspace(min_y, min_y + max_bracket_probe, bracket_steps)
    vals = []
    valid = []
    for y in ys:
        v = f_scalar_for_bracket(y)
        if np.isnan(v):
            vals.append(np.nan)
            valid.append(False)
        else:
            vals.append(float(v))
            valid.append(True)

    bracket = None
    for i in range(len(vals) - 1):
        if not (valid[i] and valid[i + 1]):
            continue
        if vals[i] == 0.0:
            bracket = (ys[i], ys[i])
            break
        if vals[i] * vals[i + 1] < 0:
            bracket = (ys[i], ys[i + 1])
            break

    if bracket is not None:
        a, b = bracket
        try:
            y_root = brentq(
                lambda y: shape_len_for_y(y, use_discretisation=length_discretisation)[0] - length,
                a,
                b,
                xtol=1e-6,
                maxiter=200,
            )
            waypoints_final = [(base_x, float(y_root))]
            shape_final = get_waveguide_shape(
                start_port=start_port,
                end_port=end_port,
                way_points=waypoints_final,
                distance_straight=distance_straight,
                discretisation=discretisation,
            )
            if min_bend_radius is not None:
                max_curv_final, min_radius_final = get_max_bend_radius(shape_final)
                if max_curv_final > 1.0 / float(min_bend_radius):
                    warnings.warn(
                        f"Brent root found but resulting shape violates Rmin: requested {min_bend_radius:.3f} µm, "
                        f"real min radius {min_radius_final:.3f} µm. Rejecting root."
                    )
                else:
                    if abs(shape_final.length() - length) <= max_error:
                        return shape_final
            else:
                if abs(shape_final.length() - length) <= max_error:
                    return shape_final
        except Exception:
            pass

    max_curv_final, min_radius_final = get_max_bend_radius(shape_final)
    warnings.warn(
        "A smooth connector of length {} could not be made. The real length is {:.6f}. "
        "Optimization result: x={} fun={} message={}. Max_curv={:.6e} (min_radius={:.3f} µm).".format(
            length,
            shape_final.length(),
            getattr(res, "x", None),
            getattr(res, "fun", None),
            getattr(res, "message", None),
            max_curv_final,
            min_radius_final,
        )
    )

    return shape_final




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


def get_min_spacing_bundle(shapes):
    y_maxs = [s.size_info.north for s in shapes]
    return min(np.abs(np.diff(y_maxs)))


def get_max_curvature_bundle(shapes):
    max_curv = max([max(get_curvature_with_spline(shape=s)) for s in shapes])
    return max_curv