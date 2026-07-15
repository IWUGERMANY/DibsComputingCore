"""Occupancy, appliance and internal-gain calculations."""


class OccupancyAndGainsCalculator:
    """Calculate occupancy and internal gains for one building."""

    def __init__(self, building) -> None:
        self.building = building

    def calc_occupancy(self, occupancy_schedule, hour: int) -> float:
        """Calculate number of people for one simulation hour."""
        return occupancy_schedule[hour].People * self.building.max_occupancy

    def calc_gains_from_occupancy_and_appliances(
            self,
            occupancy_schedule,
            occupancy: float,
            gain_per_person: float,
            appliance_gains: float,
            hour: int,
    ) -> float:
        """Calculate internal gains from people, appliances and lighting."""
        return (
                occupancy * gain_per_person
                + appliance_gains
                * occupancy_schedule[hour].Appliances
                * self.building.energy_ref_area
                + self.building.lighting_demand
        )

    def calc_appliance_gains_demand(
            self, occupancy_schedule, appliance_gains: float, hour: int
    ) -> float:
        """Calculate appliance gains demand for one simulation hour."""
        return (
                appliance_gains
                * occupancy_schedule[hour].Appliances
                * self.building.energy_ref_area
        )

    def get_appliance_gains_elt_demand(
            self, occupancy_schedule, appliance_gains: float, hour: int
    ) -> float:
        """Calculate electric appliance demand, including negative gain handling."""
        appliance_gains_elt = (
            -1 * appliance_gains / 2 if appliance_gains < 0 else appliance_gains
        )
        return (
                appliance_gains_elt
                * occupancy_schedule[hour].Appliances
                * self.building.energy_ref_area
        )
