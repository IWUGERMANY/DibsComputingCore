from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator
from dibs_computing_core.iso_simulator.model.hours_result import Result
from dibs_computing_core.iso_simulator.model.ResultOutput import ResultOutput


def build_heating_period_mask_and_metrics(
        weather_data,
        threshold_temperature: float = 12.0,
        reference_room_temperature: float = 20.0,
) -> tuple[list[bool], dict]:
    """
    Classify heating days from daily mean outdoor temperatures and derive annual metrics.
    """
    mask = [False] * len(weather_data)
    grouped_day_indices = {}
    grouped_day_temperatures = {}

    for hour_index, hour_weather in enumerate(weather_data):
        day_key = (hour_weather.year, hour_weather.month, hour_weather.day)
        grouped_day_indices.setdefault(day_key, []).append(hour_index)
        grouped_day_temperatures.setdefault(day_key, []).append(hour_weather.drybulb_C)

    heating_days = 0
    heating_degree_days = 0.0
    room_heating_degree_days = 0.0

    for day_key, day_temperatures in grouped_day_temperatures.items():
        daily_mean_temperature = sum(day_temperatures) / len(day_temperatures)
        is_heating_day = daily_mean_temperature < threshold_temperature
        if is_heating_day:
            heating_days += 1
            heating_degree_days += threshold_temperature - daily_mean_temperature
            room_heating_degree_days += (
                    reference_room_temperature - daily_mean_temperature
            )
            for hour_index in grouped_day_indices[day_key]:
                mask[hour_index] = True

    heating_period_weather_data = [
        hour_weather
        for hour_weather, is_heating_hour in zip(weather_data, mask)
        if is_heating_hour
    ]

    def sum_radiation(values, attr_name: str) -> float:
        return sum(getattr(value, attr_name) for value in values) * 0.001

    def mean(values, attr_name: str) -> float:
        if not values:
            return 0.0
        return sum(getattr(value, attr_name) for value in values) / len(values)

    return mask, {
        "HeatingDays": heating_days,
        "HeatingDegreeDays": heating_degree_days,
        "RoomHeatingDegreeDays": room_heating_degree_days,
        "GlobalHorizontalRadiationTotal_sum": sum_radiation(
            weather_data, "glohorrad_Whm2"
        ),
        "DirectNormalRadiationTotal_sum": sum_radiation(
            weather_data, "dirnorrad_Whm2"
        ),
        "DiffuseHorizontalRadiationTotal_sum": sum_radiation(
            weather_data, "difhorrad_Whm2"
        ),
        "HeatingPeriodGlobalHorizontalRadiationTotal_sum": sum_radiation(
            heating_period_weather_data, "glohorrad_Whm2"
        ),
        "HeatingPeriodDirectNormalRadiationTotal_sum": sum_radiation(
            heating_period_weather_data, "dirnorrad_Whm2"
        ),
        "HeatingPeriodDiffuseHorizontalRadiationTotal_sum": sum_radiation(
            heating_period_weather_data, "difhorrad_Whm2"
        ),
        "GlobalHorizontalRadiation_mean": mean(weather_data, "glohorrad_Whm2"),
        "DirectNormalRadiation_mean": mean(weather_data, "dirnorrad_Whm2"),
        "DiffuseHorizontalRadiation_mean": mean(weather_data, "difhorrad_Whm2"),
        "HeatingPeriodGlobalHorizontalRadiation_mean": mean(
            heating_period_weather_data, "glohorrad_Whm2"
        ),
        "HeatingPeriodDirectNormalRadiation_mean": mean(
            heating_period_weather_data, "dirnorrad_Whm2"
        ),
        "HeatingPeriodDiffuseHorizontalRadiation_mean": mean(
            heating_period_weather_data, "difhorrad_Whm2"
        ),
        "DrybulbTemperature_mean": mean(weather_data, "drybulb_C"),
        "HeatingPeriodDrybulbTemperature_mean": mean(
            heating_period_weather_data, "drybulb_C"
        ),
    }


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

    calc_altitude_and_azimuth = simulator.calc_altitude_and_azimuth
    set_t_air_based_on_hour = simulator.set_t_air_based_on_hour
    calc_window_gains_and_illuminance = simulator.calc_window_gains_and_illuminance_for_all_windows
    calc_energy_demand_for_time_step = simulator.calc_energy_demand_for_time_step
    calc_hot_water_usage = simulator.calc_hot_water_usage
    all_windows = simulator.all_windows
    heating_period_mask, heating_period_metrics = build_heating_period_mask_and_metrics(
        simulator.weather_data
    )
    # A2 hot-path optimization: bind target list-appends once and append directly
    # instead of calling Result.append_results(...) 8760 times.
    append_heating_demand = result.heating_demand.append
    append_heating_energy = result.heating_energy.append
    append_heating_sys_electricity = result.heating_sys_electricity.append
    append_heating_sys_fossils = result.heating_sys_fossils.append
    append_cooling_demand = result.cooling_demand.append
    append_cooling_energy = result.cooling_energy.append
    append_cooling_sys_electricity = result.cooling_sys_electricity.append
    append_cooling_sys_fossils = result.cooling_sys_fossils.append
    append_all_hot_water_demand = result.all_hot_water_demand.append
    append_all_hot_water_energy = result.all_hot_water_energy.append
    append_hot_water_sys_electricity = result.hot_water_sys_electricity.append
    append_hot_water_sys_fossils = result.hot_water_sys_fossils.append
    append_temp_air = result.temp_air.append
    append_outside_temp = result.outside_temp.append
    append_lighting_demand = result.lighting_demand.append
    append_internal_gains = result.internal_gains.append
    append_solar_gains_south_window = result.solar_gains_south_window.append
    append_solar_gains_east_window = result.solar_gains_east_window.append
    append_solar_gains_west_window = result.solar_gains_west_window.append
    append_solar_gains_north_window = result.solar_gains_north_window.append
    append_solar_gains_total = result.solar_gains_total.append
    append_day_time = result.DayTime.append
    append_appliance_gains_demand = result.appliance_gains_demand.append
    append_appliance_gains_elt_demand = result.appliance_gains_elt_demand.append
    append_transmission_loss = result.transmission_loss.append
    append_thermal_bridging_loss = result.thermal_bridging_loss.append
    append_ventilation_loss = result.ventilation_loss.append
    append_is_heating_period_hour = result.is_heating_period_hour.append
    append_occupancy_profile_people = result.occupancy_profile_people.append
    append_appliance_profile_factor = result.appliance_profile_factor.append
    append_air_change_rate_effective = result.air_change_rate_effective.append
    append_air_flow_rate_effective = result.air_flow_rate_effective.append
    append_electricity_demand_total = result.electricity_demand_total.append
    append_drybulb_temperature = result.drybulb_temperature.append
    append_global_horizontal_radiation = result.global_horizontal_radiation.append
    append_direct_normal_radiation = result.direct_normal_radiation.append
    append_diffuse_horizontal_radiation = result.diffuse_horizontal_radiation.append
    calc_h_ve_adj = building.calc_h_ve_adj
    solve_building_lighting = building.solve_building_lighting
    calc_hot_water_usage_with_schedule = calc_hot_water_usage
    occupancy_schedule_local = occupancy_schedule
    tek_dhw_per_hour = tek_dhw_per_occupancy_full_usage_hour
    window_south = all_windows[0]
    window_east = all_windows[1]
    window_west = all_windows[2]
    window_north = all_windows[3]
    has_dhw = building.dhw_system not in ["NoDHW", " -"]
    central_heating_or_dhw = simulator.check_if_central_heating_or_central_dhw()
    heat_pump_air_or_ground = simulator.check_if_heat_pump_air_or_ground_source()

    for hour in range(8760):
        schedule_hour = occupancy_schedule_local[hour]
        people = schedule_hour.People
        appliances = schedule_hour.Appliances
        hour_weather = simulator.weather_data[hour]
        t_out = hour_weather.drybulb_C
        global_horizontal_radiation = hour_weather.glohorrad_Whm2
        direct_normal_radiation = hour_weather.dirnorrad_Whm2
        diffuse_horizontal_radiation = hour_weather.difhorrad_Whm2

        altitude, azimuth = calc_altitude_and_azimuth(hour)

        building.h_ve_adj = (
            calc_h_ve_adj(
                hour, t_out, usage_start, usage_end
            )
        )

        t_air = set_t_air_based_on_hour(hour)

        solar_gains_all_windows, transmitted_illuminance_sum = calc_window_gains_and_illuminance(
            altitude, azimuth, t_air, hour, people > 0
        )

        solve_building_lighting(
            transmitted_illuminance_sum, people
        )
        appliance_gains_demand = appliance_gains_area_factor * appliances
        internal_gains = (
                people * people_heat_gain_factor
                + appliance_gains_demand
                + building.lighting_demand
        )

        """
        Calculate appliance_gains as part of the internal_gains
        """
        """
        Appliance_gains equal the electric energy that appliances use, except for negative appliance_gains of refrigerated counters in trade buildings for food!
        The assumption is: negative appliance_gains come from referigerated counters with heat pumps for which we assume a COP = 2.
        """
        appliance_gains_demand_elt = appliance_gains_elt_area_factor * appliances
        """
        Calculate energy demand for the time step
        """
        calc_energy_demand_for_time_step(
            internal_gains, t_out, t_m_prev, solar_gains_all_windows
        )
        """
        Calculate hot water usage of the building for the time step with (BuildingInstance.heating_energy
         / BuildingInstance.heating_demand) represents the Efficiency of the heat generation in the building
        """

        (
            hot_water_demand,
            hot_water_energy,
            hot_water_sys_electricity,
            hot_water_sys_fossils,
        ) = calc_hot_water_usage_with_schedule(
            occupancy_schedule_local,
            tek_dhw_per_hour,
            hour,
            people,
            has_dhw,
            central_heating_or_dhw,
            heat_pump_air_or_ground,
        )

        """
        Set the previous temperature for the next time step
        """
        t_m_prev = building.t_m_next
        air_change_rate_effective = 0.0
        if building.building_vol:
            air_change_rate_effective = (
                    building.h_ve_adj * 3600 / (1200 * building.building_vol)
            )
        air_flow_rate_effective = air_change_rate_effective * building.building_vol
        thermal_bridging_loss = max(
            0.0, building.h_tr_tb * (building.t_air - t_out)
        )
        transmission_loss = max(
            0.0, (building.h_tr_op + building.h_tr_direct) * (building.t_air - t_out)
        )
        ventilation_loss = max(0.0, building.h_ve_adj * (building.t_air - t_out))
        electricity_demand_total = (
                building.heating_sys_electricity
                + hot_water_sys_electricity
                + building.cooling_sys_electricity
                + building.lighting_demand
                + appliance_gains_demand_elt
        )
        """
        Append results to the created lists 
        """
        append_heating_demand(building.heating_demand)
        append_heating_energy(building.heating_energy)
        append_heating_sys_electricity(building.heating_sys_electricity)
        append_heating_sys_fossils(building.heating_sys_fossils)
        append_cooling_demand(building.cooling_demand)
        append_cooling_energy(building.cooling_energy)
        append_cooling_sys_electricity(building.cooling_sys_electricity)
        append_cooling_sys_fossils(building.cooling_sys_fossils)
        append_all_hot_water_demand(hot_water_demand)
        append_all_hot_water_energy(hot_water_energy)
        append_hot_water_sys_electricity(hot_water_sys_electricity)
        append_hot_water_sys_fossils(hot_water_sys_fossils)
        append_temp_air(building.t_air)
        append_outside_temp(t_out)
        append_lighting_demand(building.lighting_demand)
        append_internal_gains(internal_gains)
        append_solar_gains_south_window(window_south.solar_gains)
        append_solar_gains_east_window(window_east.solar_gains)
        append_solar_gains_west_window(window_west.solar_gains)
        append_solar_gains_north_window(window_north.solar_gains)
        append_solar_gains_total(solar_gains_all_windows)
        append_day_time(hour % 24)
        append_appliance_gains_demand(appliance_gains_demand)
        append_appliance_gains_elt_demand(appliance_gains_demand_elt)
        append_transmission_loss(transmission_loss)
        append_thermal_bridging_loss(thermal_bridging_loss)
        append_ventilation_loss(ventilation_loss)
        append_is_heating_period_hour(heating_period_mask[hour])
        append_occupancy_profile_people(people)
        append_appliance_profile_factor(appliances)
        append_air_change_rate_effective(air_change_rate_effective)
        append_air_flow_rate_effective(air_flow_rate_effective)
        append_electricity_demand_total(electricity_demand_total)
        append_drybulb_temperature(t_out)
        append_global_horizontal_radiation(global_horizontal_radiation)
        append_direct_normal_radiation(direct_normal_radiation)
        append_diffuse_horizontal_radiation(diffuse_horizontal_radiation)
        """
        Some calculations used for the console prints
        """
    sum_of_all_results = result.calc_sum_of_results(heating_period_metrics)
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
    # if type(f_hs_hi) is type(None):
    #     print(f'bd_id: {simulator.datasource.building.scr_gebaeude_id} and f_hs_hi: {f_hs_hi}')
    (
        heating_sys_electricity_hi_sum,
        heating_sys_carbon_sum,
        heating_sys_pe_sum,
        heating_sys_fossils_hi_sum,
    ) = simulator.check_heating_sys_electricity_sum(
        sum_of_all_results, f_hs_hi, f_ghg, f_pe
    )
    heating_sys_hi_sum = simulator.sys_electricity_folssils_sum(
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
    hot_water_energy_hi_sum = simulator.sys_electricity_folssils_sum(
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
    ) = simulator.check_cooling_system_elctricity_sum(
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
    fuel_type = "Electricity grid mix"
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
