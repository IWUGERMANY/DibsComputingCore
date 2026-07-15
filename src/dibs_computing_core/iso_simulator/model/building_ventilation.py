"""Ventilation and night-flushing helpers for ``Building``.

The functions in this module keep the existing stateful ``Building`` behaviour:
they receive a Building instance, mutate the same fields as the original methods,
and intentionally do not change formulas or call order.
"""


def _is_usage_time(daytime, usage_start, usage_end):
    """Return whether ``daytime`` is inside the possibly overnight usage window."""
    if usage_start < usage_end:
        return usage_start <= daytime < usage_end
    return not usage_end <= daytime < usage_start


def _is_night_flushing_active(building, hour, t_out):
    """Return whether night flushing is allowed for the current timestep."""
    daytime = hour % 24
    cooling_season = 2169 < hour < 6561
    is_night_time = daytime < 6 or daytime > 23
    night_flushing_available = building.night_flushing_flow > 0

    if not (night_flushing_available and cooling_season and is_night_time):
        return False

    rounded_indoor_air = round(building.t_air, 1)
    indoor_air_is_warm = rounded_indoor_air > 21
    indoor_air_exceeds_outdoor_threshold = rounded_indoor_air > (t_out + 2)
    return indoor_air_is_warm and indoor_air_exceeds_outdoor_threshold


def _infiltration_h_ve(building):
    return 1200 * 1 * building.building_vol * (building.ach_inf / 3600)


def _usage_h_ve(building):
    return 1200 * (
        (building.b_ek * building.building_vol * (building.ach_vent / 3600))
        + (1 * building.building_vol * (building.ach_win / 3600))
    )


def _night_flushing_h_ve(building):
    return 1200 * 1 * building.building_vol * (building.night_flushing_flow / 3600)


def calc_h_ve_adj(building, hour, t_out, usage_start, usage_end):
    """Calculate ventilation heat transfer coefficient for one timestep."""
    self = building

    self.check_night_flushing(hour, t_out)

    no_mechanical_or_window_air_exchange = self.ach_vent == 0 and self.ach_win == 0
    if no_mechanical_or_window_air_exchange:
        self.h_ve_adj = _infiltration_h_ve(self)
        return self.h_ve_adj

    if self.night_flushing_on:
        self.h_ve_adj = _night_flushing_h_ve(self)
        # Prevent heating from counteracting active night flushing in this hour.
        self.t_set_heating = 0
        return self.h_ve_adj

    daytime = hour % 24
    if _is_usage_time(daytime, usage_start, usage_end):
        self.h_ve_adj = _usage_h_ve(self)
    else:
        self.h_ve_adj = _infiltration_h_ve(self)

    return self.h_ve_adj


def check_night_flushing(building, hour, t_out):
    """Check whether night flushing is active for one timestep."""
    building.night_flushing_on = _is_night_flushing_active(building, hour, t_out)
    return building.night_flushing_on