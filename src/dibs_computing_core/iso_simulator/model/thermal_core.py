"""Thermal 5R1C core calculations used by Building.

This module intentionally contains only the pure Crank-Nicolson thermal core
and its optional numba-compiled variant. Moving it out of ``building.py`` keeps
``Building`` focused on orchestration/state without changing formulas.
"""

try:
    from numba import njit  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    njit = None


def _thermal_core_py(
    c_m,
    h_tr_em,
    h_tr_ms,
    h_tr_is,
    h_tr_w,
    h_ve_adj,
    phi_m,
    phi_st,
    phi_ia,
    t_out,
    t_m_prev,
):
    h_tr_1 = 1.0 / (1.0 / h_ve_adj + 1.0 / h_tr_is)
    h_tr_2 = h_tr_1 + h_tr_w
    h_tr_3 = 1.0 / (1.0 / h_tr_2 + 1.0 / h_tr_ms)

    phi_m_tot = (
        phi_m
        + h_tr_em * t_out
        + h_tr_3
        * (
            phi_st
            + h_tr_w * t_out
            + h_tr_1 * ((phi_ia / h_ve_adj) + t_out)
        )
        / h_tr_2
    )

    act_val1 = (
        (t_m_prev * ((c_m / 3600.0) - 0.5 * (h_tr_3 + h_tr_em)))
        + phi_m_tot
    )
    act_val2 = (c_m / 3600.0) + 0.5 * (h_tr_3 + h_tr_em)
    t_m_next = act_val1 / act_val2
    t_m = (t_m_next + t_m_prev) / 2.0
    t_s = (
        h_tr_ms * t_m
        + phi_st
        + h_tr_w * t_out
        + h_tr_1 * (t_out + phi_ia / h_ve_adj)
    ) / (h_tr_ms + h_tr_w + h_tr_1)
    t_air = (h_tr_is * t_s + h_ve_adj * t_out + phi_ia) / (h_tr_is + h_ve_adj)
    return phi_m_tot, t_m_next, t_m, t_s, t_air


if njit is not None:
    _thermal_core_numba = njit(cache=True)(_thermal_core_py)
else:  # pragma: no cover - optional dependency
    _thermal_core_numba = None