"""Heat-flow helpers for ``Building``.

The function in this module keeps the existing stateful ``Building`` behaviour:
it receives a Building instance, mutates the same fields as the original method,
and intentionally does not change formulas or call order.
"""


def calc_heat_flow(building, t_out, internal_gains, solar_gains, energy_demand):
    """Calculate heat-flow distribution and emission-system temperatures."""
    self = building

    # Calculates the heat flows to various points of the building based on the breakdown in section C.2, formulas C.1-C.3
    # Heat flow to the air node
    self.phi_ia = 0.5 * internal_gains
    # Heat flow to the surface node
    self.phi_st = (
        1 - (self.mass_area / self.A_t) - (self.h_tr_w / (9.1 * self.A_t))
    ) * (0.5 * internal_gains + solar_gains)
    # Heatflow to the thermal mass node
    self.phi_m = (self.mass_area / self.A_t) * (0.5 * internal_gains + solar_gains)

    # We call the EmissionDirector to modify these flows depending on the
    # system and the energy demand
    emDirector = self._emission_director

    # Set the emission system to the type specified by the user
    if energy_demand > 0:
        my_system = self._heating_emission_cls(energy_demand)
        emDirector.set_builder(my_system)
        # emDirector.set_builder(self.heating_emission_system(
        #     energy_demand=energy_demand))
    else:
        my_system = self._cooling_emission_cls(energy_demand)
        emDirector.set_builder(my_system)
        # emDirector.set_builder(self.cooling_emission_system(
        #     energy_demand=energy_demand))
    # Calculate the new flows to each node based on the heating/cooling system
    flows = emDirector.calc_flows()
    # Set modified flows to building object

    self.phi_ia += flows.phi_ia_plus
    self.phi_st += flows.phi_st_plus
    self.phi_m += flows.phi_m_plus

    # Set supply temperature to building object
    self.heating_supply_temperature = flows.heating_supply_temperature
    self.cooling_supply_temperature = flows.cooling_supply_temperature