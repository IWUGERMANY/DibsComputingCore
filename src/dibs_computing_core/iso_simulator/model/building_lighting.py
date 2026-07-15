"""Lighting-demand helper for ``Building``.

The function in this module keeps the existing stateful ``Building`` behaviour:
it receives a Building instance, mutates ``lighting_demand`` exactly as the
original method did, and intentionally does not change formulas or call order.
"""


def solve_building_lighting(building, illuminance, occupancy):
    """Calculate lighting demand for one timestep."""
    lux = (
        illuminance
        * building.lighting_utilisation_factor
        * building.lighting_maintenance_factor
    ) / building.net_room_area  # [Lux]

    if lux < building.lighting_control and occupancy > 0:
        # Lighting demand for the hour
        building.lighting_demand = building.lighting_load * building.net_room_area * occupancy
    else:
        building.lighting_demand = 0