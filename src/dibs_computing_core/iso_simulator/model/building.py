"""
Physics required to calculate sensible space heating and space cooling loads, and space lighting loads (DIN EN ISO 13970:2008)

The equations presented here is this code are derived from ISO 13790 Annex C, Methods are listed in order of apperance in the Annex


Portions of this software are copyright of their respective authors and released under the MIT license:
RC_BuildingSimulator, Copyright 2016 Architecture and Building Systems, ETH Zurich

author: "Julian Bischof, Simon Knoll, Michael Hörner "
copyright: "Copyright 2023, Institut Wohnen und Umwelt"
license: "MIT"

"""
__author__ = "Julian Bischof, Simon Knoll, Michael Hörner "
__copyright__ = "Copyright 2023, Institut Wohnen und Umwelt"
__license__ = "MIT"

from ..emission_system import *

from ..supply_system import *

import os

from .building_energy import (
    calc_energy_demand as _calc_energy_demand,
    calc_energy_demand_unrestricted as _calc_energy_demand_unrestricted,
    has_demand as _has_demand,
    solve_building_energy as _solve_building_energy,
)
from .building_heat_flow import calc_heat_flow as _calc_heat_flow
from .building_lighting import solve_building_lighting as _solve_building_lighting
from .building_ventilation import (
    calc_h_ve_adj as _calc_h_ve_adj,
    check_night_flushing as _check_night_flushing,
)
from .thermal_core import _thermal_core_numba
from dibs_computing_core.iso_simulator.building_simulator.system_enums import system_key
from .building_system_mappings import (
    BUILDING_EMISSION_SYSTEM_MAPPING,
    BUILDING_SUPPLY_SYSTEM_MAPPING,
)

class Building(object):
    """
    Sets the parameters of the building.

    INPUT PARAMETER DEFINITION
    scr_gebaeude_id: Building Screening-ID
    plz: Zipcode of building location
    hk_geb: Usage type (main category)
    uk_geb: Usage type (subcategory)
    max_occupancy: Max. number of persons
    wall_area_og: Area of all walls above ground in contact with the outside [m2]
    wall_area_ug: Area of all walls below ground in contact with soil [m2]
    window_area_north: Area of the glazed surface in contact with the outside facing north [m2]
    window_area_east: Area of the glazed surface in contact with the outside facing east [m2]
    window_area_south: Area of the glazed surface in contact with the outside facing south [m2]
    window_area_west: Area of the glazed surface in contact with the outside facing west [m2]
    roof_area: Area of the roof in contact with the outside [m2]
    net_room_area: Area of all floor areas from usable rooms including all floor plan levels of the building (Refers to "Netto-Raumfläche", DIN 277-1:2016-01)
    base_area: Area for the calculation of transmission heat losses to the soil. Also used to calculate the building's volume.
    energy_ref_area: Energy reference area of the building
    building_height: Mean height of the building [m]
    lighting_load: Lighting Load [W/m2]
    lighting_control: Lux threshold at which the lights turn on [Lx]
    lighting_utilisation_factor: A factor that determines how much natural solar lumminace is effectively utilised in the space
    lighting_maintenance_factor: A factor based on how dirty the windows area
    glass_solar_transmittance: Solar radiation passing through the window (g-value)
    glass_solar_shading_transmittance: Solar radiation passing through the window with active shading devices
    glass_light_transmittance: Solar illuminance passing through the window
    u_windows: U value of glazed surfaces [W/m2K]
    u_walls: U value of external walls  [W/m2K]
    u_roof: U value of the roof [W/m2K]
    u_base: U value of the floor [W/m2K]
    temp_adj_base: Temperature adjustment factor for the floor
    temp_adj_walls_ug: Temperature adjustment factor for walls below ground
    ach_inf: Air changes per hour through infiltration [Air Changes Per Hour]
    ach_win: Air changes per hour through opened windows [Air Changes Per Hour]
    ach_vent: Air changes per hour through ventilation [Air Changes Per Hour]
    ventilation_efficiency: Efficiency of the heat recovery system for ventilation. Set to 0 if there is no heat recovery
    night_flushing_flow: Air changes per hour through night flushing [Air Changes Per Hour]
    thermal_capacitance: Thermal capacitance of the building [J/m2K]
    t_set_heating : Thermal heating set point [C]
    t_set_cooling: Thermal cooling set point [C]
    max_cooling_energy_per_floor_area: Maximum cooling load. Set to -np.inf for unrestricted cooling [C]
    max_heating_energy_per_floor_area: Maximum heating load per floor area. Set to no.inf for unrestricted heating [C]
    heating_supply_system: The type of heating system
    cooling_supply_system: The type of cooling system
    heating_emission_system: How the heat is distributed to the building
    cooling_emission_system: How the cooling energy is distributed to the building


    VARIABLE DEFINITION

    internal_gains: Internal Heat Gains [W]
    solar_gains: Solar Heat Gains after transmitting through the window [W]
    t_out: Outdoor air temperature [C]
    t_m_prev: Thermal mass temperature from the previous time step
    ill: Illuminance transmitting through the window [lumen]
    occupancy: Occupancy [people]

    t_m_next: Medium temperature of the next time step [C]
    t_m: Average between the previous and current time-step of the bulk temperature [C]

    Inputs to the 5R1C model:
    c_m: Thermal Capacitance of the medium [J/K]
    h_tr_is: Conductance between the air node and the inside surface node [W/K]
    h_tr_w: Heat transfer coefficient from the outside through windows, doors [W/K]
    h_tr_op: Heat transfer coefficient from the outside through opaque elements [W/K]
    h_tr_em: Conductance between outside node and mass node [W/K]
    h_tr_ms: Conductance between mass node and internal surface node [W/K]
    h_ve_adj: Ventilation heat transmission coefficient [W/K]

    phi_m_tot: see formula for the calculation, eq C.5 in standard [W]
    phi_m: Combination of internal and solar gains directly to the medium [W]
    phi_st: combination of internal and solar gains directly to the internal surface [W]
    phi_ia: combination of internal and solar gains to the air [W]
    energy_demand: Heating and Cooling of the Supply air [W]

    h_tr_1: combined heat conductance, see function for definition [W/K]
    h_tr_2: combined heat conductance, see function for definition [W/K]
    h_tr_3: combined heat conductance, see function for definition [W/K]
    """

    def __init__(
            self,
            scr_gebaeude_id: str,
            plz: str,
            hk_geb: str,
            uk_geb: str,
            max_occupancy: int,
            wall_area_og: float,
            wall_area_ug: float,
            window_area_north: float,
            window_area_east: float,
            window_area_south: float,
            window_area_west: float,
            roof_area: float,
            net_room_area: float,
            energy_ref_area: float,
            base_area: float,
            gross_base_area: float,
            building_height: float,
            net_volume: float,
            gross_volume: float,
            envelope_area: float,
            lighting_load: float,
            lighting_control: int,
            lighting_utilisation_factor: float,
            lighting_maintenance_factor: float,
            aw_construction: int,
            shading_device: int,
            shading_solar_transmittance: float,
            glass_solar_transmittance: float,
            glass_solar_shading_transmittance: float,
            glass_light_transmittance: float,
            u_windows: float,
            u_walls: float,
            u_roof: float,
            u_base: float,
            temp_adj_base: float,
            temp_adj_walls_ug: float,
            ach_inf: float,
            ach_win: float,
            ach_vent: float,
            heat_recovery_efficiency: int,
            thermal_capacitance: int,
            t_set_heating: int,
            t_start: int,
            t_set_cooling: int,
            night_flushing_flow: int,
            max_heating_energy_per_floor_area: float,
            max_cooling_energy_per_floor_area: float,
            heating_supply_system: str,
            cooling_supply_system: str,
            heating_emission_system: str,
            cooling_emission_system: str,
            dhw_system,
    ):
        self.dhw_system = dhw_system
        self.scr_gebaeude_id = scr_gebaeude_id

        ## Dimensions
        # area of all windows
        self.window_area_north = window_area_north
        self.window_area_east = window_area_east
        self.window_area_south = window_area_south
        self.window_area_west = window_area_west
        self.window_area = (
                window_area_north + window_area_east + window_area_south + window_area_west
        )
        # net room area
        self.net_room_area = net_room_area
        # energy reference area
        self.energy_ref_area = energy_ref_area

        ## Fenestration and Lighting Properties
        self.glass_solar_transmittance = glass_solar_transmittance
        self.glass_light_transmittance = glass_light_transmittance
        self.glass_solar_shading_transmittance = glass_solar_shading_transmittance
        # lighting load
        self.lighting_load = lighting_load
        # Lighting set point
        self.lighting_control = lighting_control
        # How the light entering the window is transmitted to the working plane
        self.lighting_utilisation_factor = lighting_utilisation_factor
        # How dirty the window is. Section 2.2.3.1 Environmental Science Handbook
        self.lighting_maintenance_factor = lighting_maintenance_factor

        ## Constants of the building
        self.plz = plz
        self.hk_geb = hk_geb
        self.uk_geb = uk_geb
        self.max_occupancy = max_occupancy

        # Night flushing
        self.night_flushing_flow = night_flushing_flow

        ## Calculated Properties
        # [m2] Effective mass area (See p. 81, Table 12)
        if thermal_capacitance <= 165000:
            self.mass_area = energy_ref_area * 2.5

        elif 165000 < thermal_capacitance <= 260000:
            self.mass_area = energy_ref_area * 3

        elif thermal_capacitance > 260000:
            self.mass_area = energy_ref_area * 3.5

        # [m3] Calculate building volume
        self.building_vol = base_area * building_height
        # Calculate internal area (See 7.2.2.2, p. 35/36)
        self.total_internal_area = energy_ref_area * 4.5
        self.A_t = self.total_internal_area

        # Single Capacitance  5 conductance Model Parameters
        # [kWh/K] Room Capacitance. Default based on ISO standard 12.3.1.2 for medium heavy buildings
        # p. 81, Table 12
        self.c_m = thermal_capacitance * energy_ref_area

        # Conductance of opaque surfaces to exterior [W/K]
        # p. 44, Eq. 18 --> H_x = A_i * U_i
        self.h_tr_op = (
                (u_walls * wall_area_og)
                + (u_roof * roof_area)
                + (base_area * u_base * temp_adj_base)
                + (wall_area_ug * u_walls * temp_adj_walls_ug)
        )
        # Conductance to exterior through glazed surfaces [W/K], based on
        # U-wert of 1W/m2K
        self.h_tr_w = u_windows * self.window_area

        ## Determine the ventilation conductance
        self.ach_inf = ach_inf
        self.ach_win = ach_win
        self.ach_vent = ach_vent
        self.ach_tot = ach_inf + ach_win + ach_vent
        # Total Air Changes Per Hour
        # temperature adjustment factor taking ventilation and infiltration
        # p. 53, Eq. 27
        self.b_ek = 1 - (ach_vent / (self.ach_tot)) * heat_recovery_efficiency
        # Conductance through ventilation [W/M]
        # transmittance from the internal air to the thermal mass of the building
        # p. 79, Eq. 64
        self.h_tr_ms = 9.1 * self.mass_area
        # Conductance from the conditioned air to interior building surface
        # p. 35, Eq. 9
        self.h_tr_is = self.total_internal_area * 3.45
        self.h_tr_em = max(0, (1 / ((1 / self.h_tr_op) - (1 / self.h_tr_ms))))

        ## Thermal set points and starting temperature
        self.t_set_heating = t_set_heating
        self.t_set_cooling = t_set_cooling
        self.t_start = t_start

        ## Thermal Properties
        # Boolean for if heating is required
        self.has_heating_demand = False
        # Boolean for if cooling is required
        self.has_cooling_demand = False
        # max cooling load (W/m2)
        self.max_cooling_energy = max_cooling_energy_per_floor_area * energy_ref_area
        # max heating load (W/m2)
        self.max_heating_energy = max_heating_energy_per_floor_area * energy_ref_area
        self._energy_floor_ax10 = 10 * energy_ref_area

        ## Building System Properties
        self.heating_supply_system = heating_supply_system
        self.cooling_supply_system = cooling_supply_system
        self.heating_emission_system = heating_emission_system
        self.cooling_emission_system = cooling_emission_system
        self._use_numba_thermal = (
                os.getenv("LBBD_ENABLE_NUMBA_THERMAL", "").lower() in {"1", "true", "yes"}
                and _thermal_core_numba is not None
        )
        # Hot-loop helpers: directors are stateless apart from the current builder,
        # so one instance per Building avoids repeated allocation in hourly calls.
        self._emission_director = EmissionDirector()
        self._supply_director = SupplyDirector()
        self._heating_emission_cls = BUILDING_EMISSION_SYSTEM_MAPPING[
            system_key(self.heating_emission_system)
        ]
        self._cooling_emission_cls = BUILDING_EMISSION_SYSTEM_MAPPING[
            system_key(self.cooling_emission_system)
        ]
        self._heating_supply_cls = BUILDING_SUPPLY_SYSTEM_MAPPING[
            system_key(self.heating_supply_system)
        ]
        self._cooling_supply_cls = BUILDING_SUPPLY_SYSTEM_MAPPING[
            system_key(self.cooling_supply_system)
        ]

    @property
    def h_tr_1(self):
        """
        Definition to simplify calc_phi_m_tot
        # (C.6) in [C.3 ISO 13790]
        """
        return 1.0 / (1.0 / self.h_ve_adj + 1.0 / self.h_tr_is)

    @property
    def h_tr_2(self):
        """
        Definition to simplify calc_phi_m_tot
        # (C.7) in [C.3 ISO 13790]
        """
        return self.h_tr_1 + self.h_tr_w

    @property
    def h_tr_3(self):
        """
        Definition to simplify calc_phi_m_tot
        # (C.8) in [C.3 ISO 13790]
        """
        return 1.0 / (1.0 / self.h_tr_2 + 1.0 / self.h_tr_ms)

    @property
    def t_opperative(self):
        """
        The opperative temperature is a weighted average of the air and mean radiant temperatures.
        It is not used in any further calculation at this stage
        # (C.12) in [C.3 ISO 13790]
        """
        return 0.3 * self.t_air + 0.7 * self.t_s

    # Public Building API: these methods intentionally remain on Building and
    # delegate to focused helper modules. This keeps existing callers and
    # profiling method names stable while reducing this file's responsibilities.

    def calc_h_ve_adj(self, hour, t_out, usage_start, usage_end):
        """
        Calculates h_ve_adj depending on the building's usage time.
        """
        return _calc_h_ve_adj(self, hour, t_out, usage_start, usage_end)

    def check_night_flushing(self, hour, t_out):
        """
        Checks if night flushing is on/off.
        """
        return _check_night_flushing(self, hour, t_out)

    def solve_building_lighting(self, illuminance, occupancy):
        """
        Calculates the lighting demand for a set timestep.
        """
        return _solve_building_lighting(self, illuminance, occupancy)

    def solve_building_energy(self, internal_gains, solar_gains, t_out, t_m_prev):
        """
        Calculates the heating and cooling consumption of a building for a set timestep.
        """
        return _solve_building_energy(
            self, internal_gains, solar_gains, t_out, t_m_prev
        )

    def has_demand(self, internal_gains, solar_gains, t_out, t_m_prev):
        """
        Determines whether the building requires heating or cooling.
        """
        return _has_demand(self, internal_gains, solar_gains, t_out, t_m_prev)

    def calc_temperatures_crank_nicolson(
            self, energy_demand, internal_gains, solar_gains, t_out, t_m_prev
    ):
        """
        Determines node temperatures (t_air, t_m, t_s) and computes derivation to determine the new node temperatures
        Used in: has_demand(), solve_building_energy(), calc_energy_demand()
        # section C.3 in [C.3 ISO 13790]
        """
        # Eq. C.1 - C.3
        self.calc_heat_flow(t_out, internal_gains, solar_gains, energy_demand)
        # Eq. C.5
        if self._use_numba_thermal:
            (
                self.phi_m_tot,
                self.t_m_next,
                self.t_m,
                self.t_s,
                self.t_air,
            ) = _thermal_core_numba(
                self.c_m,
                self.h_tr_em,
                self.h_tr_ms,
                self.h_tr_is,
                self.h_tr_w,
                self.h_ve_adj,
                self.phi_m,
                self.phi_st,
                self.phi_ia,
                t_out,
                t_m_prev,
            )
        else:
            # Fast Python path: inline thermal core math to avoid repeated
            # method/property dispatch overhead in the hot loop.
            h_ve_adj = self.h_ve_adj
            h_tr_is = self.h_tr_is
            h_tr_w = self.h_tr_w
            h_tr_ms = self.h_tr_ms
            h_tr_em = self.h_tr_em
            c_m = self.c_m
            phi_m = self.phi_m
            phi_st = self.phi_st
            phi_ia = self.phi_ia

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
            t_m_next = (
                (t_m_prev * ((c_m / 3600.0) - 0.5 * (h_tr_3 + h_tr_em)))
                + phi_m_tot
            ) / ((c_m / 3600.0) + 0.5 * (h_tr_3 + h_tr_em))
            t_m = (t_m_next + t_m_prev) / 2.0
            t_s = (
                h_tr_ms * t_m
                + phi_st
                + h_tr_w * t_out
                + h_tr_1 * (t_out + phi_ia / h_ve_adj)
            ) / (h_tr_ms + h_tr_w + h_tr_1)
            t_air = (
                h_tr_is * t_s + h_ve_adj * t_out + phi_ia
            ) / (h_tr_is + h_ve_adj)

            self.phi_m_tot = phi_m_tot
            self.t_m_next = t_m_next
            self.t_m = t_m
            self.t_s = t_s
            self.t_air = t_air

        return self.t_m, self.t_air, self.t_opperative

    def calc_energy_demand(self, internal_gains, solar_gains, t_out, t_m_prev):
        """
        Calculates the energy demand of the space if heating/cooling is active.
        """
        return _calc_energy_demand(
            self, internal_gains, solar_gains, t_out, t_m_prev
        )

    def calc_energy_demand_unrestricted(
            self, energy_floorAx10, t_air_set, t_air_0, t_air_10
    ):
        """
        Calculates unrestricted heating/cooling demand.
        """
        return _calc_energy_demand_unrestricted(
            self, energy_floorAx10, t_air_set, t_air_0, t_air_10
        )
    def calc_heat_flow(self, t_out, internal_gains, solar_gains, energy_demand):
        """
        Calculates heat flow from solar gains, internal gains and heating/cooling emission.
        """
        return _calc_heat_flow(
            self, t_out, internal_gains, solar_gains, energy_demand
        )
    # Legacy thermal formula helpers retained for compatibility. The active
    # hourly path in calc_temperatures_crank_nicolson uses inline thermal math.
    def calc_t_m_next(self, t_m_prev):
        """
        Primary Equation, calculates the temperature of the next time step
        # (C.4) in [C.3 ISO 13790]
        """
        act_val1 = (
                (t_m_prev * ((self.c_m / 3600.0) - 0.5 * (self.h_tr_3 + self.h_tr_em)))
                + self.phi_m_tot
        )

        act_val2 = ((self.c_m / 3600.0) + 0.5 * (self.h_tr_3 + self.h_tr_em))

        self.t_m_next = act_val1 / act_val2

        # self.t_m_next = (
        #                         (t_m_prev * ((self.c_m / 3600.0) - 0.5 * (self.h_tr_3 + self.h_tr_em)))
        #                         + self.phi_m_tot
        #                 ) / ((self.c_m / 3600.0) + 0.5 * (self.h_tr_3 + self.h_tr_em))

    def calc_phi_m_tot(self, t_out):
        """
        Calculates a global heat transfer. This is a definition used to simplify equation
        calc_t_m_next so it's not so long to write out
        # (C.5) in [C.3 ISO 13790]
        # h_ve = h_ve_adj and t_supply = t_out [9.3.2 ISO 13790]
        """

        t_supply = t_out  # ASSUMPTION: Supply air comes straight from the outside air

        self.phi_m_tot = (
                self.phi_m
                + self.h_tr_em * t_out
                + self.h_tr_3
                * (
                        self.phi_st
                        + self.h_tr_w * t_out
                        + self.h_tr_1 * ((self.phi_ia / self.h_ve_adj) + t_supply)
                )
                / self.h_tr_2
        )

    def calc_t_m(self, t_m_prev):
        """
        Temperature used for the calculations, average between newly calculated and previous bulk temperature
        # (C.9) in [C.3 ISO 13790]
        """
        self.t_m = (self.t_m_next + t_m_prev) / 2.0

    def calc_t_s(self, t_out):
        """
        Calculate the temperature of the inside room surfaces.
        Consists of the air temperature and the average radiation temperature
        # (C.10) in [C.3 ISO 13790]
        # h_ve = h_ve_adj and t_supply = t_out [9.3.2 ISO 13790]
        """

        t_supply = t_out  # ASSUMPTION: Supply air comes straight from the outside air

        self.t_s = (
                           self.h_tr_ms * self.t_m
                           + self.phi_st
                           + self.h_tr_w * t_out
                           + self.h_tr_1 * (t_supply + self.phi_ia / self.h_ve_adj)
                   ) / (self.h_tr_ms + self.h_tr_w + self.h_tr_1)

    def calc_t_air(self, t_out):
        """
        Calculate the temperature of the air node
        # (C.11) in [C.3 ISO 13790]
        # h_ve = h_ve_adj and t_supply = t_out [9.3.2 ISO 13790]
        """

        t_supply = t_out

        # Calculate the temperature of the inside air
        self.t_air = (
                             self.h_tr_is * self.t_s + self.h_ve_adj * t_supply + self.phi_ia
                     ) / (self.h_tr_is + self.h_ve_adj)
