"""Energy-demand helpers for ``Building``.

The functions in this module keep the existing stateful ``Building`` behaviour:
they receive a Building instance, mutate the same fields as the original methods,
and intentionally do not change formulas or call order.
"""

from ..exceptions import SimulationStateError, ThermalCalculationError

def _demand_flags(t_air_rounded, t_set_heating, t_set_cooling):
    """Return heating/cooling demand flags with the original heating priority."""
    has_heating = t_air_rounded < t_set_heating
    has_cooling = (not has_heating) and t_air_rounded > t_set_cooling
    return has_heating, has_cooling


def _is_within_available_power(building):
    """Return whether unrestricted demand fits available heating/cooling power."""
    return (
        building.max_cooling_energy
        <= building.energy_demand_unrestricted
        <= building.max_heating_energy
    )


def solve_building_energy(building, internal_gains, solar_gains, t_out, t_m_prev):
    """Calculate heating and cooling consumption for one timestep."""
    self = building

    # Updates has_heating_demand and has_cooling_demand for this timestep.
    self.has_demand(internal_gains, solar_gains, t_out, t_m_prev)
    has_heating = self.has_heating_demand
    has_cooling = self.has_cooling_demand

    if not has_heating and not has_cooling:
        # No active heating or cooling is required for this timestep.
        self.energy_demand = 0

        self.heating_demand = 0  # Energy required by the zone
        self.cooling_demand = 0  # Energy surplus of the zone
        # Energy (in electricity) required by the supply system to provide
        # HeatingDemand
        self.heating_sys_electricity = 0
        # Energy (in fossil fuel) required by the supply system to provide
        # HeatingDemand
        self.heating_sys_fossils = 0
        # Energy (in electricity) required by the supply system to get rid
        # of CoolingDemand
        self.cooling_sys_electricity = 0
        # Energy (in fossil fuel) required by the supply system to get rid
        # of CoolingDemand
        self.cooling_sys_fossils = 0
        # Electricity produced by the supply system (e.g. CHP)
        self.electricity_out = 0
        # Set COP to nan if no heating or cooling is required
        self.cop = float("nan")

    else:
        self.calc_energy_demand(internal_gains, solar_gains, t_out, t_m_prev)

        supply_director = self._supply_director

        if has_heating:
            my_system = self._heating_supply_cls(
                load=self.energy_demand,
                t_out=t_out,
                heating_supply_temperature=self.heating_supply_temperature,
                cooling_supply_temperature=self.cooling_supply_temperature,
                has_heating_demand=has_heating,
                has_cooling_demand=has_cooling,
            )
            supply_director.set_builder(my_system)
            supplyOut = supply_director.calc_system()
            self.heating_demand = self.energy_demand
            self.heating_sys_electricity = supplyOut.electricity_in
            self.heating_sys_fossils = supplyOut.fossils_in
            self.cooling_demand = 0
            self.cooling_sys_electricity = 0
            self.cooling_sys_fossils = 0
            self.electricity_out = supplyOut.electricity_out

        elif has_cooling:
            my_system = self._cooling_supply_cls(
                load=self.energy_demand * (-1),
                t_out=t_out,
                heating_supply_temperature=self.heating_supply_temperature,
                cooling_supply_temperature=self.cooling_supply_temperature,
                has_heating_demand=has_heating,
                has_cooling_demand=has_cooling,
            )
            supply_director.set_builder(my_system)
            supplyOut = supply_director.calc_system()
            self.heating_demand = 0
            self.heating_sys_electricity = 0
            self.heating_sys_fossils = 0
            self.cooling_demand = self.energy_demand
            self.cooling_sys_electricity = supplyOut.electricity_in
            self.cooling_sys_fossils = supplyOut.fossils_in
            self.electricity_out = supplyOut.electricity_out

        self.cop = supplyOut.cop

    self.sys_total_energy = (
        self.heating_sys_electricity
        + self.heating_sys_fossils
        + self.cooling_sys_electricity
        + self.cooling_sys_fossils
    )
    self.heating_energy = self.heating_sys_electricity + self.heating_sys_fossils
    self.cooling_energy = self.cooling_sys_electricity + self.cooling_sys_fossils

def has_demand(building, internal_gains, solar_gains, t_out, t_m_prev):
    """Determine whether the building requires heating or cooling."""
    self = building

    # set energy demand to 0 and see if temperatures are within the comfort
    # range
    energy_demand = 0
    # Solve for the internal temperature t_Air
    self.calc_temperatures_crank_nicolson(
        energy_demand, internal_gains, solar_gains, t_out, t_m_prev
    )
    t_air = self.t_air
    self._last_no_demand_temperature_context = (
        internal_gains,
        solar_gains,
        t_out,
        t_m_prev,
        t_air,
    )

    # If the air temperature is less or greater than the set temperature,
    # there is a heating/cooling load.
    self.has_heating_demand, self.has_cooling_demand = _demand_flags(
        round(t_air, 1), self.t_set_heating, self.t_set_cooling
    )

def calc_energy_demand(building, internal_gains, solar_gains, t_out, t_m_prev):
    """Calculate required heating/cooling energy when demand is active."""
    self = building

    # Reuse the no-demand temperature from has_demand(), which runs immediately
    # before this function in solve_building_energy(). If calc_energy_demand() is
    # called directly, fall back to the original calculation.
    no_demand_context = getattr(self, "_last_no_demand_temperature_context", None)
    current_context = (internal_gains, solar_gains, t_out, t_m_prev)
    if no_demand_context is not None and no_demand_context[:4] == current_context:
        t_air_0 = no_demand_context[4]
    else:
        energy_demand_0 = 0
        t_air_0 = self.calc_temperatures_crank_nicolson(
            energy_demand_0, internal_gains, solar_gains, t_out, t_m_prev
        )[1]
    # Step 2: Calculate the unrestricted heating/cooling required

    # Select the active comfort setpoint according to the demand determined above.

    if self.has_heating_demand:
        t_air_set = self.t_set_heating
    elif self.has_cooling_demand:
        t_air_set = self.t_set_cooling
    else:
        raise SimulationStateError(
            "Energy-demand calculation called without heating or cooling demand",
            phase="simulate_hours",
            context={
                "has_heating_demand": self.has_heating_demand,
                "has_cooling_demand": self.has_cooling_demand,
            },
        )

    # Reference case: 10 W/m2 multiplied by the energy reference area.
    energy_floorAx10 = self._energy_floor_ax10

    # Air temperature for the reference case.
    t_air_10 = self.calc_temperatures_crank_nicolson(
        energy_floorAx10, internal_gains, solar_gains, t_out, t_m_prev
    )[1]

    # Determine unrestricted heating/cooling demand.
    self.calc_energy_demand_unrestricted(
        energy_floorAx10, t_air_set, t_air_0, t_air_10
    )

    # Use unrestricted demand if it fits within available system power.
    if _is_within_available_power(self):
        self.energy_demand = self.energy_demand_unrestricted
        self.t_air_ac = t_air_set

    # Otherwise clamp demand to the available heating/cooling power.
    elif self.energy_demand_unrestricted > self.max_heating_energy:
        self.energy_demand = self.max_heating_energy

    elif self.energy_demand_unrestricted < self.max_cooling_energy:
        self.energy_demand = self.max_cooling_energy

    else:
        self.energy_demand = 0
        raise ThermalCalculationError(
            "Unknown radiative heating/cooling system status",
            phase="simulate_hours",
            context={
                "energy_demand_unrestricted": self.energy_demand_unrestricted,
                "max_heating_energy": self.max_heating_energy,
                "max_cooling_energy": self.max_cooling_energy,
            },
        )

    # calculate system temperatures for Step 3/Step 4
    self.calc_temperatures_crank_nicolson(
        self.energy_demand, internal_gains, solar_gains, t_out, t_m_prev
    )

def calc_energy_demand_unrestricted(
    building, energy_floorAx10, t_air_set, t_air_0, t_air_10
):
    """Calculate unrestricted energy demand from the 10 W/m2 reference case."""
    building.energy_demand_unrestricted = (
        energy_floorAx10 * (t_air_set - t_air_0) / (t_air_10 - t_air_0)
    )
