from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator
from dibs_computing_core.iso_simulator.model.hours_result import Result
from dibs_computing_core.iso_simulator.model.ResultOutput import ResultOutput
from dibs_computing_core.iso_simulator.building_simulator.system_enums import (
    EnergyCarrier,
    system_key,
)
from dibs_computing_core.iso_simulator.building_simulator.system_fuel_mappings import (
    DHW_NO_SYSTEM_TYPES,
)
import os


# def simulate_one_building(datasource: DataSourceCSV):
#     """
#     This method simulates the building which located in the given path
#     Args:
#     Returns:
#
#     """
#     dibs = DIBS(datasource)
#     time_begin = time.time()
#
#     simulator = BuildingSimulator(dibs.datasource)
#     simulator.datasource.get_user_building()
#     simulator.datasource.get_epw_file()
#
#     t_set_heating_temp = simulator.datasource.building.t_set_heating
#
#     result, result_output = extracted_method_to_simulate_one_building(
#         simulator, t_set_heating_temp
#     )
#     simulation_time = time.time() - time_begin
#
#     # TODO: result muss ausgegeben und in dibs cli in funktion map_result_to_dataframe implementiert werden
#     # result_data_frame = simulator.datasource.result_to_pandas_dataframe(
#     #     result_output, user_arguments
#     # )
#     excel_file_name = simulator.building_object.scr_gebaeude_id + ".xlsx"
#
#     start_time = time.time()
#     excel_file_path = os.path.join(folder_path, excel_file_name)
#     result_data_frame.to_excel(excel_file_path)
#     end_time = time.time()
#     excel_time = end_time - start_time
#
#     start_time = time.time()
#     csv_file_name = simulator.datasource.result_of_all_hours_to_excel(
#         folder_path, result, simulator.building_object
#     )
#     end_time = time.time()
#     csv_time = end_time - start_time
#
#     return (
#         result_data_frame,
#         simulator.building_object.scr_gebaeude_id,
#         simulation_time,
#         excel_time,
#         csv_time,
#         excel_file_name,
#         csv_file_name,
#     )


def extracted_method_to_simulate_one_building(simulator: BuildingSimulator, t_set_heating_temp) -> \
        tuple[Result, ResultOutput]:
    """

    Parameters
        simulator: object that contains the methods needed to simulate one building
        t_set_heating_temp: Thermal heating set point [C]

    Returns
        (result, result_output)
    Return type
        tuple[Result, ResultOutput]

    """
    result = Result()
    hours = 8760

    simulator.check_energy_area_and_heating()
    gain_person_and_typ_norm, appliance_gains = simulator.datasource.get_gains()
    gain_per_person, typ_norm = gain_person_and_typ_norm
    usage_start, usage_end = simulator.get_usage_start_and_end()
    (
        occupancy_schedule,
        schedule_name,
        occupancy_full_usage_hours,
    ) = simulator.get_schedule()
    tek_dhw, tek_name = simulator.get_tek()
    tek_dhw_per_occupancy_full_usage_hour = tek_dhw / occupancy_full_usage_hours
    t_m_prev = simulator.datasource.building.t_start
    building = simulator.datasource.building
    max_occupancy = building.max_occupancy
    energy_ref_area = building.energy_ref_area
    appliance_gains_elt = -1 * appliance_gains / 2 if appliance_gains < 0 else appliance_gains
    people_heat_gain_factor = max_occupancy * gain_per_person
    appliance_gains_area_factor = appliance_gains * energy_ref_area
    appliance_gains_elt_area_factor = appliance_gains_elt * energy_ref_area

    building.t_set_heating = t_set_heating_temp

    extract_outdoor_temperature = simulator.extract_outdoor_temperature
    calc_altitude_and_azimuth = simulator.calc_altitude_and_azimuth
    set_t_air_based_on_hour = simulator.set_t_air_based_on_hour
    calc_window_gains_and_illuminance = simulator.calc_window_gains_and_illuminance_for_all_windows
    calc_energy_demand_for_time_step = simulator.calc_energy_demand_for_time_step
    calc_hot_water_usage = simulator.calc_hot_water_usage
    all_windows = simulator.all_windows
    use_prealloc = os.getenv("DIBS_USE_PREALLOC_RESULTS", "1").lower() in {
        "1",
        "true",
        "yes",
    }
    # P1 hot-path optimization: preallocate fixed-size result buffers and assign by index.
    # Can be switched off for A/B benchmarking via DIBS_USE_PREALLOC_RESULTS=0.
    heating_demand = [0.0] * hours
    heating_energy = [0.0] * hours
    heating_sys_electricity = [0.0] * hours
    heating_sys_fossils = [0.0] * hours
    cooling_demand = [0.0] * hours
    cooling_energy = [0.0] * hours
    cooling_sys_electricity = [0.0] * hours
    cooling_sys_fossils = [0.0] * hours
    all_hot_water_demand = [0.0] * hours
    all_hot_water_energy = [0.0] * hours
    hot_water_sys_electricity = [0.0] * hours
    hot_water_sys_fossils = [0.0] * hours
    temp_air = [0.0] * hours
    outside_temp = [0.0] * hours
    lighting_demand = [0.0] * hours
    internal_gains_values = [0.0] * hours
    solar_gains_south_window = [0.0] * hours
    solar_gains_east_window = [0.0] * hours
    solar_gains_west_window = [0.0] * hours
    solar_gains_north_window = [0.0] * hours
    solar_gains_total = [0.0] * hours
    day_time = [0] * hours
    appliance_gains_demand_values = [0.0] * hours
    appliance_gains_elt_demand_values = [0.0] * hours
    calc_h_ve_adj = building.calc_h_ve_adj
    solve_building_lighting = building.solve_building_lighting
    calc_hot_water_usage_with_schedule = calc_hot_water_usage
    occupancy_schedule_local = occupancy_schedule
    tek_dhw_per_hour = tek_dhw_per_occupancy_full_usage_hour
    window_south = all_windows[0]
    window_east = all_windows[1]
    window_west = all_windows[2]
    window_north = all_windows[3]
    has_dhw = system_key(building.dhw_system) not in DHW_NO_SYSTEM_TYPES
    central_heating_or_dhw = simulator.check_if_central_heating_or_central_dhw()
    heat_pump_air_or_ground = simulator.check_if_heat_pump_air_or_ground_source()

    day_clock = 0
    if use_prealloc:
        for hour in range(hours):
            schedule_hour = occupancy_schedule_local[hour]
            people = schedule_hour.People
            appliances = schedule_hour.Appliances

            t_out = extract_outdoor_temperature(hour)
            altitude, azimuth = calc_altitude_and_azimuth(hour)
            building.h_ve_adj = calc_h_ve_adj(hour, t_out, usage_start, usage_end)
            t_air = set_t_air_based_on_hour(hour)

            window_gains = calc_window_gains_and_illuminance(
                altitude, azimuth, t_air, hour, people > 0
            )
            solar_gains_all_windows = window_gains.solar_gains_total
            transmitted_illuminance_sum = window_gains.transmitted_illuminance_total
            solve_building_lighting(transmitted_illuminance_sum, people)

            appliance_gains_demand = appliance_gains_area_factor * appliances
            internal_gains = (
                people * people_heat_gain_factor
                + appliance_gains_demand
                + building.lighting_demand
            )
            appliance_gains_demand_elt = appliance_gains_elt_area_factor * appliances

            calc_energy_demand_for_time_step(
                internal_gains, t_out, t_m_prev, solar_gains_all_windows
            )

            (
                hot_water_demand,
                hot_water_energy,
                hot_water_sys_electricity_value,
                hot_water_sys_fossils_value,
            ) = calc_hot_water_usage_with_schedule(
                occupancy_schedule_local,
                tek_dhw_per_hour,
                hour,
                people,
                has_dhw,
                central_heating_or_dhw,
                heat_pump_air_or_ground,
            )

            t_m_prev = building.t_m_next

            heating_demand[hour] = building.heating_demand
            heating_energy[hour] = building.heating_energy
            heating_sys_electricity[hour] = building.heating_sys_electricity
            heating_sys_fossils[hour] = building.heating_sys_fossils
            cooling_demand[hour] = building.cooling_demand
            cooling_energy[hour] = building.cooling_energy
            cooling_sys_electricity[hour] = building.cooling_sys_electricity
            cooling_sys_fossils[hour] = building.cooling_sys_fossils
            all_hot_water_demand[hour] = hot_water_demand
            all_hot_water_energy[hour] = hot_water_energy
            hot_water_sys_electricity[hour] = hot_water_sys_electricity_value
            hot_water_sys_fossils[hour] = hot_water_sys_fossils_value
            temp_air[hour] = building.t_air
            outside_temp[hour] = t_out
            lighting_demand[hour] = building.lighting_demand
            internal_gains_values[hour] = internal_gains
            solar_gains_south_window[hour] = window_south.solar_gains
            solar_gains_east_window[hour] = window_east.solar_gains
            solar_gains_west_window[hour] = window_west.solar_gains
            solar_gains_north_window[hour] = window_north.solar_gains
            solar_gains_total[hour] = solar_gains_all_windows
            day_time[hour] = day_clock
            appliance_gains_demand_values[hour] = appliance_gains_demand
            appliance_gains_elt_demand_values[hour] = appliance_gains_demand_elt

            day_clock += 1
            if day_clock == 24:
                day_clock = 0
    else:
        for hour in range(hours):
            schedule_hour = occupancy_schedule_local[hour]
            people = schedule_hour.People
            appliances = schedule_hour.Appliances

            t_out = extract_outdoor_temperature(hour)
            altitude, azimuth = calc_altitude_and_azimuth(hour)
            building.h_ve_adj = calc_h_ve_adj(hour, t_out, usage_start, usage_end)
            t_air = set_t_air_based_on_hour(hour)

            window_gains = calc_window_gains_and_illuminance(
                altitude, azimuth, t_air, hour, people > 0
            )
            solar_gains_all_windows = window_gains.solar_gains_total
            transmitted_illuminance_sum = window_gains.transmitted_illuminance_total
            solve_building_lighting(transmitted_illuminance_sum, people)

            appliance_gains_demand = appliance_gains_area_factor * appliances
            internal_gains = (
                people * people_heat_gain_factor
                + appliance_gains_demand
                + building.lighting_demand
            )
            appliance_gains_demand_elt = appliance_gains_elt_area_factor * appliances

            calc_energy_demand_for_time_step(
                internal_gains, t_out, t_m_prev, solar_gains_all_windows
            )

            (
                hot_water_demand,
                hot_water_energy,
                hot_water_sys_electricity_value,
                hot_water_sys_fossils_value,
            ) = calc_hot_water_usage_with_schedule(
                occupancy_schedule_local,
                tek_dhw_per_hour,
                hour,
                people,
                has_dhw,
                central_heating_or_dhw,
                heat_pump_air_or_ground,
            )

            t_m_prev = building.t_m_next

            result.heating_demand.append(building.heating_demand)
            result.heating_energy.append(building.heating_energy)
            result.heating_sys_electricity.append(building.heating_sys_electricity)
            result.heating_sys_fossils.append(building.heating_sys_fossils)
            result.cooling_demand.append(building.cooling_demand)
            result.cooling_energy.append(building.cooling_energy)
            result.cooling_sys_electricity.append(building.cooling_sys_electricity)
            result.cooling_sys_fossils.append(building.cooling_sys_fossils)
            result.all_hot_water_demand.append(hot_water_demand)
            result.all_hot_water_energy.append(hot_water_energy)
            result.hot_water_sys_electricity.append(hot_water_sys_electricity_value)
            result.hot_water_sys_fossils.append(hot_water_sys_fossils_value)
            result.temp_air.append(building.t_air)
            result.outside_temp.append(t_out)
            result.lighting_demand.append(building.lighting_demand)
            result.internal_gains.append(internal_gains)
            result.solar_gains_south_window.append(window_south.solar_gains)
            result.solar_gains_east_window.append(window_east.solar_gains)
            result.solar_gains_west_window.append(window_west.solar_gains)
            result.solar_gains_north_window.append(window_north.solar_gains)
            result.solar_gains_total.append(solar_gains_all_windows)
            result.DayTime.append(day_clock)
            result.appliance_gains_demand.append(appliance_gains_demand)
            result.appliance_gains_elt_demand.append(appliance_gains_demand_elt)

            day_clock += 1
            if day_clock == 24:
                day_clock = 0
    """
    Some calculations used for the console prints
    """
    if use_prealloc:
        result.heating_demand = heating_demand
        result.heating_energy = heating_energy
        result.heating_sys_electricity = heating_sys_electricity
        result.heating_sys_fossils = heating_sys_fossils
        result.cooling_demand = cooling_demand
        result.cooling_energy = cooling_energy
        result.cooling_sys_electricity = cooling_sys_electricity
        result.cooling_sys_fossils = cooling_sys_fossils
        result.all_hot_water_demand = all_hot_water_demand
        result.all_hot_water_energy = all_hot_water_energy
        result.hot_water_sys_electricity = hot_water_sys_electricity
        result.hot_water_sys_fossils = hot_water_sys_fossils
        result.temp_air = temp_air
        result.outside_temp = outside_temp
        result.lighting_demand = lighting_demand
        result.internal_gains = internal_gains_values
        result.solar_gains_south_window = solar_gains_south_window
        result.solar_gains_east_window = solar_gains_east_window
        result.solar_gains_west_window = solar_gains_west_window
        result.solar_gains_north_window = solar_gains_north_window
        result.solar_gains_total = solar_gains_total
        result.DayTime = day_time
        result.appliance_gains_demand = appliance_gains_demand_values
        result.appliance_gains_elt_demand = appliance_gains_elt_demand_values

    sum_of_all_results = result.calc_sum_of_results()
    """
        the fuel-related final energy sums, f.i. HeatingEnergy_sum, are calculated based upon the superior heating value
        Hs since the corresponding expenditure factors from TEK 9.24 represent the ration of Hs-related final energy to 
        useful energy.
         --- Calculation  related to HEATING and Hotwater energy ---
        """
    fuel_type = simulator.choose_the_fuel_type()
    """
        Heating:
            - GHG-Factor Heating
            - PE-Factor Heating
            - Umrechnungsfaktor von Brennwert (Hs) zu Heizwert (Hi) einlesen
        """
    f_ghg, f_pe, f_hs_hi, fuel_type = simulator.get_ghg_pe_conversion_factors(
        fuel_type
    )
    (
        heating_sys_electricity_hi_sum,
        heating_sys_carbon_sum,
        heating_sys_pe_sum,
        heating_sys_fossils_hi_sum,
    ) = simulator.check_heating_sys_electricity_sum(
        sum_of_all_results, f_hs_hi, f_ghg, f_pe
    )
    heating_sys_hi_sum = simulator.sys_electricity_fossils_sum(
        heating_sys_electricity_hi_sum, heating_sys_fossils_hi_sum
    )
    heating_fuel_type = fuel_type
    heating_f_ghg = f_ghg
    heating_f_pe = f_pe
    heating_f_hs_hi = f_hs_hi
    """
        HOT WATER
        Assumption: Central DHW-Systems use the same Fuel_type as Heating-Systems, only decentral DHW-Systems might have
        another Fuel-Type.
        """
    fuel_type = simulator.check_if_central_dhw_use_same_fuel_type_as_heating_system(
        heating_fuel_type
    )
    f_ghg, f_pe, f_hs_hi, fuel_type = simulator.get_ghg_pe_conversion_factors(
        fuel_type
    )
    (
        hot_water_sys_electricity_hi_sum,
        hot_water_sys_pe_sum,
        hot_water_sys_carbon_sum,
        hot_water_sys_fossils_hi_sum,
    ) = simulator.check_hotwater_sys_electricity_sum(
        sum_of_all_results, f_hs_hi, f_ghg, f_pe
    )
    hot_water_energy_hi_sum = simulator.sys_electricity_fossils_sum(
        hot_water_sys_electricity_hi_sum, hot_water_sys_fossils_hi_sum
    )
    hot_water_fuel_type = fuel_type
    hot_water_f_ghg = f_ghg
    hot_water_f_pe = f_pe
    hot_water_f_hs_hi = f_hs_hi
    """
        Cooling energy
        """
    fuel_type = simulator.choose_cooling_energy_fuel_type()
    f_ghg, f_pe, f_hs_hi, fuel_type = simulator.get_ghg_pe_conversion_factors(
        fuel_type
    )
    (
        cooling_sys_electricity_hi_sum,
        cooling_sys_carbon_sum,
        cooling_sys_pe_sum,
        cooling_sys_fossils_hi_sum,
    ) = simulator.check_cooling_system_electricity_sum(
        sum_of_all_results, f_hs_hi, f_ghg, f_pe
    )
    cooling_sys_hi_sum = simulator.cooling_sys_hi_sum(
        cooling_sys_electricity_hi_sum, cooling_sys_fossils_hi_sum
    )
    cooling_fuel_type = fuel_type
    cooling_f_ghg = f_ghg
    cooling_f_pe = f_pe
    cooling_f_hs_hi = f_hs_hi
    """
        remaining Electric energy (LightingDemand_sum + Appliance_gains_elt_demand_sum)
        Lighting
        electrical energy for lighting
        """
    fuel_type = EnergyCarrier.ELECTRICITY_GRID_MIX.value
    f_ghg, f_pe, f_hs_hi, fuel_type = simulator.get_ghg_pe_conversion_factors(
        fuel_type
    )
    lighting_demand_hi_sum = (
            sum_of_all_results.LightingDemand_sum / f_hs_hi
    )  # for kWhHi Final Energy Demand
    lighting_demand_carbon_sum = (
                                         lighting_demand_hi_sum * f_ghg
                                 ) / 1000  # for kg CO2eq
    lighting_demand_pe_sum = (
            lighting_demand_hi_sum * f_pe
    )  # for kWhHs Primary Energy Demand
    appliance_gains_demand_hi_sum = (
            sum_of_all_results.Appliance_gains_elt_demand_sum / f_hs_hi
    )  # for kWhHi Final Energy Demand
    appliance_gains_demand_pe_sum = (
            appliance_gains_demand_hi_sum * f_pe
    )  # for kWhHs Primary Energy Demand
    appliance_gains_demand_carbon_sum = (
                                                appliance_gains_demand_hi_sum * f_ghg
                                        ) / 1000  # for kg CO2eq
    light_appl_fuel_type = fuel_type
    light_appl_f_ghg = f_ghg
    light_appl_f_pe = f_pe
    light_appl_f_hs_hi = f_hs_hi
    """
            Calculation of Carbon Emission related to the entire energy consumption (Heating_Sys_Carbon_sum + 
            Cooling_Sys_Carbon_sum + LightingDemand_Carbon_sum + Appliance_gains_demand_Carbon_sum)
            """
    carbon_sum = (
            heating_sys_carbon_sum
            + cooling_sys_carbon_sum
            + lighting_demand_carbon_sum
            + appliance_gains_demand_carbon_sum
            + hot_water_sys_carbon_sum
    )
    """
            Calculation of Primary Energy Demand related to the entire energy consumption (Heating_Sys_PE_sum +
             Cooling_Sys_PE_sum + LightingDemand_PE_sum + Appliance_gains_demand_PE_sum + HotWater_Sys_PE_sum)
            """
    pe_sum = (
            heating_sys_pe_sum
            + cooling_sys_pe_sum
            + lighting_demand_pe_sum
            + appliance_gains_demand_pe_sum
            + hot_water_sys_pe_sum
    )
    """
            Calculation of Final Energy Hi Demand related to the entire energy consumption
            """
    fe_hi_sum = (
            heating_sys_hi_sum
            + cooling_sys_hi_sum
            + lighting_demand_hi_sum
            + appliance_gains_demand_hi_sum
            + hot_water_energy_hi_sum
    )
    """
            Build Results of a building
            """
    result_output = save_result_output_object(
        appliance_gains_demand_carbon_sum,
        appliance_gains_demand_pe_sum,
        carbon_sum,
        cooling_f_ghg,
        cooling_f_hs_hi,
        cooling_f_pe,
        cooling_fuel_type,
        cooling_sys_carbon_sum,
        cooling_sys_pe_sum,
        fe_hi_sum,
        heating_f_ghg,
        heating_f_hs_hi,
        heating_f_pe,
        heating_fuel_type,
        heating_sys_carbon_sum,
        heating_sys_electricity_hi_sum,
        heating_sys_fossils_hi_sum,
        heating_sys_hi_sum,
        heating_sys_pe_sum,
        hot_water_energy_hi_sum,
        hot_water_f_ghg,
        hot_water_f_hs_hi,
        hot_water_f_pe,
        hot_water_fuel_type,
        hot_water_sys_carbon_sum,
        hot_water_sys_pe_sum,
        light_appl_f_ghg,
        light_appl_f_hs_hi,
        light_appl_f_pe,
        light_appl_fuel_type,
        lighting_demand_carbon_sum,
        lighting_demand_pe_sum,
        pe_sum,
        schedule_name,
        simulator,
        sum_of_all_results,
        typ_norm,
    )
    return result, result_output


def save_result_output_object(
        appliance_gains_demand_carbon_sum,
        appliance_gains_demand_pe_sum,
        carbon_sum,
        cooling_f_ghg,
        cooling_f_hs_hi,
        cooling_f_pe,
        cooling_fuel_type,
        cooling_sys_carbon_sum,
        cooling_sys_pe_sum,
        fe_hi_sum,
        heating_f_ghg,
        heating_f_hs_hi,
        heating_f_pe,
        heating_fuel_type,
        heating_sys_carbon_sum,
        heating_sys_electricity_hi_sum,
        heating_sys_fossils_hi_sum,
        heating_sys_hi_sum,
        heating_sys_pe_sum,
        hot_water_energy_hi_sum,
        hot_water_f_ghg,
        hot_water_f_hs_hi,
        hot_water_f_pe,
        hot_water_fuel_type,
        hot_water_sys_carbon_sum,
        hot_water_sys_pe_sum,
        light_appl_f_ghg,
        light_appl_f_hs_hi,
        light_appl_f_pe,
        light_appl_fuel_type,
        lighting_demand_carbon_sum,
        lighting_demand_pe_sum,
        pe_sum,
        schedule_name,
        simulator,
        sum_of_all_results,
        typ_norm,
):
    result_output = ResultOutput(
        simulator.datasource.building,
        sum_of_all_results,
        heating_sys_hi_sum,
        heating_sys_electricity_hi_sum,
        heating_sys_fossils_hi_sum,
        heating_sys_carbon_sum,
        heating_sys_pe_sum,
        cooling_sys_carbon_sum,
        cooling_sys_pe_sum,
        hot_water_energy_hi_sum,
        heating_fuel_type,
        heating_f_ghg,
        heating_f_pe,
        heating_f_hs_hi,
        hot_water_fuel_type,
        hot_water_f_ghg,
        hot_water_f_pe,
        hot_water_f_hs_hi,
        cooling_fuel_type,
        cooling_f_ghg,
        cooling_f_pe,
        cooling_f_hs_hi,
        light_appl_fuel_type,
        light_appl_f_ghg,
        light_appl_f_pe,
        light_appl_f_hs_hi,
        hot_water_sys_carbon_sum,
        hot_water_sys_pe_sum,
        lighting_demand_carbon_sum,
        lighting_demand_pe_sum,
        appliance_gains_demand_carbon_sum,
        appliance_gains_demand_pe_sum,
        carbon_sum,
        pe_sum,
        fe_hi_sum,
        schedule_name,
        typ_norm,
        simulator.datasource.epw_file.file_name,
    )
    return result_output


def unpack_results(results) -> tuple[Result: list[Result], list[ResultOutput]]:
    """
    Unpacks the results and calculates the runtime
    Parameters
        results: contains result of all simulated hours and the end result

    Returns
        unpack_time, result, result_output

    Return type
        tuple[float, float, : List[Result], List[ResultOutput]]

    """
    result, result_output = zip(*results)
    return result, result_output
