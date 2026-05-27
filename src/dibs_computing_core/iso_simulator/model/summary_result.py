from .ResultOutput import ResultOutput


class SummaryResult:
    def __init__(self, result: ResultOutput, user_args: list):
        (
            profile_from_norm,
            gains_from_group_values,
            usage_from_norm,
            weather_period,
        ) = user_args

        def surface(value: float) -> float:
            if result.building.energy_ref_area == 0:
                return 0.0
            return value / result.building.energy_ref_area

        self.building_id = result.building.scr_gebaeude_id
        self.energy_ref_area = result.building.energy_ref_area

        self.heating_demand = result.sum_object.HeatingDemand_sum
        self.heating_demand_surface = result.calc_heating_demand()
        self.heating_energy = result.sum_object.HeatingEnergy_sum
        self.heating_energy_surface = result.calc_heating_energy()
        self.heating_energy_hi = result.heating_sys_hi_sum
        self.heating_sys_electricity = result.sum_object.Heating_Sys_Electricity_sum
        self.heating_sys_electricity_surface = result.calc_heating_sys_electricity()
        self.heating_sys_electricity_hi = result.heating_sys_electricity_hi_sum
        self.heating_sys_fossils = result.sum_object.Heating_Sys_Fossils_sum
        self.heating_sys_fossils_surface = result.calc_heating_sys_fossils()
        self.heating_sys_fossils_hi = result.heating_sys_fossils_hi_sum
        self.heating_sys_gwp = result.heating_sys_carbon_sum
        self.heating_sys_gwp_surface = result.calc_heating_sys_gwp()
        self.heating_sys_pe = result.heating_sys_pe_sum
        self.heating_sys_pe_surface = result.calc_heating_sys_pe()

        self.cooling_demand = result.sum_object.CoolingDemand_sum
        self.cooling_demand_surface = result.calc_cooling_demand()
        self.cooling_energy = result.sum_object.CoolingEnergy_sum
        self.cooling_energy_surface = result.calc_cooling_energy()
        self.cooling_sys_electricity = result.sum_object.Cooling_Sys_Electricity_sum
        self.cooling_sys_electricity_surface = result.calc_cooling_sys_electricity()
        self.cooling_sys_fossils = result.sum_object.Cooling_Sys_Fossils_sum
        self.cooling_sys_fossils_surface = result.calc_cooling_sys_fossils()
        self.cooling_sys_gwp = result.cooling_sys_carbon_sum
        self.cooling_sys_gwp_surface = result.calc_cooling_sys_gwp()
        self.cooling_sys_pe = result.cooling_sys_pe_sum
        self.cooling_sys_pe_surface = result.calc_cooling_sys_pe()

        self.hot_water_demand = result.sum_object.HotWaterDemand_sum
        self.hot_water_demand_surface = result.calc_hot_water_demand()
        self.hot_water_energy = result.sum_object.HotWaterEnergy_sum
        self.hot_water_energy_surface = result.calc_hot_water_energy()
        self.hot_water_energy_hi = result.hot_water_energy_hi_sum
        self.hot_water_sys_electricity = result.sum_object.HotWater_Sys_Electricity_sum
        self.hot_water_sys_fossils = result.sum_object.HotWater_Sys_Fossils_sum

        self.heating_supply_system = result.building.heating_supply_system
        self.cooling_supply_system = result.building.cooling_supply_system
        self.dhw_supply_system = result.building.dhw_system
        self.heating_fuel_type = result.heating_fuel_type
        self.heating_f_ghg = result.heating_f_ghg
        self.heating_f_pe = result.heating_f_pe
        self.heating_f_hs_hi = result.heating_f_hs_hi
        self.hotwater_fuel_type = result.hot_water_fuel_type
        self.hotwater_f_ghg = result.hot_water_f_ghg
        self.hotwater_f_pe = result.hot_water_f_pe
        self.hotwater_f_hs_hi = result.hot_water_f_hs_hi
        self.cooling_fuel_type = result.cooling_fuel_type
        self.cooling_f_ghg = result.cooling_f_ghg
        self.cooling_f_pe = result.cooling_f_pe
        self.cooling_f_hs_hi = result.cooling_f_hs_hi
        self.light_appl_fuel_type = result.light_appl_fuel_type
        self.light_appl_f_ghg = result.light_appl_f_ghg
        self.light_appl_f_pe = result.light_appl_f_pe
        self.light_appl_f_hs_hi = result.light_appl_f_hs_hi
        self.hotwater_sys_gwp = result.hot_water_sys_carbon_sum
        self.hotwater_sys_gwp_surface = result.calc_hot_water_sys_gwp()
        self.hotwater_sys_pe = result.hot_water_sys_pe_sum
        self.hotwater_sys_pe_surface = result.calc_hot_water_sys_pe()

        self.electricity_demand_total = result.calc_electricity_demand_total()
        self.electricity_demand_total_surface = result.calc_electricity_demand_total_ref()
        self.fossils_demand_total = result.calc_fossils_demand_total()
        self.fossils_demand_total_surface = result.calc_fossils_demand_total_ref()

        self.lighting_demand = result.sum_object.LightingDemand_sum
        self.lighting_demand_surface = surface(self.lighting_demand)
        self.lighting_demand_gwp = result.lighting_demand_carbon_sum
        self.lighting_demand_gwp_surface = result.calc_lighting_demand_gwp()
        self.lighting_demand_pe = result.lighting_demand_pe_sum
        self.lighting_demand_pe_surface = result.calc_lighting_demand_pe()

        self.appliance_gains_demand = result.sum_object.Appliance_gains_demand_sum
        self.appliance_gains_demand_surface = surface(self.appliance_gains_demand)
        self.appliance_gains_elt_demand = result.sum_object.Appliance_gains_elt_demand_sum
        self.appliance_gains_elt_demand_surface = surface(
            self.appliance_gains_elt_demand
        )
        self.appliance_gains_demand_gwp = result.appliance_gains_demand_carbon_sum
        self.appliance_gains_demand_gwp_surface = result.calc_appliance_gains_demand_gwp()
        self.appliance_gains_demand_pe = result.appliance_gains_demand_pe_sum
        self.appliance_gains_demand_pe_surface = result.calc_appliance_gains_demand_pe()

        self.gwp = result.carbon_sum
        self.gwp_surface = result.calc_gwp()
        self.pe = result.pe_sum
        self.pe_surface = result.calc_pe()
        self.final_energy_hi = result.fe_hi_sum

        self.internal_gains = result.sum_object.InternalGains_sum
        self.internal_gains_surface = surface(self.internal_gains)
        self.solar_gains_total = result.sum_object.SolarGainsTotal_sum
        self.solar_gains_total_surface = surface(self.solar_gains_total)
        self.solar_gains_south_window = result.sum_object.SolarGainsSouthWindow_sum
        self.solar_gains_east_window = result.sum_object.SolarGainsEastWindow_sum
        self.solar_gains_west_window = result.sum_object.SolarGainsWestWindow_sum
        self.solar_gains_north_window = result.sum_object.SolarGainsNorthWindow_sum
        self.transmission_loss = result.sum_object.TransmissionLoss_sum
        self.transmission_loss_surface = surface(self.transmission_loss)
        self.ventilation_loss = result.sum_object.VentilationLoss_sum
        self.ventilation_loss_surface = surface(self.ventilation_loss)

        self.heating_period_hours = result.sum_object.HeatingPeriodHours
        self.heating_days = result.sum_object.HeatingDays
        self.heating_degree_days = result.sum_object.HeatingDegreeDays
        self.room_heating_degree_days = result.sum_object.RoomHeatingDegreeDays
        self.global_horizontal_radiation_total = (
            result.sum_object.GlobalHorizontalRadiationTotal_sum
        )
        self.direct_normal_radiation_total = (
            result.sum_object.DirectNormalRadiationTotal_sum
        )
        self.diffuse_horizontal_radiation_total = (
            result.sum_object.DiffuseHorizontalRadiationTotal_sum
        )
        self.global_horizontal_radiation_mean_annual = (
            result.sum_object.GlobalHorizontalRadiation_mean
        )
        self.direct_normal_radiation_mean_annual = (
            result.sum_object.DirectNormalRadiation_mean
        )
        self.diffuse_horizontal_radiation_mean_annual = (
            result.sum_object.DiffuseHorizontalRadiation_mean
        )
        self.drybulb_temperature_mean_annual = (
            result.sum_object.DrybulbTemperature_mean
        )

        self.heating_period_heating_demand = result.sum_object.HeatingPeriodHeatingDemand_sum
        self.heating_period_heating_demand_surface = surface(
            self.heating_period_heating_demand
        )
        self.heating_period_cooling_demand = result.sum_object.HeatingPeriodCoolingDemand_sum
        self.heating_period_cooling_demand_surface = surface(
            self.heating_period_cooling_demand
        )
        self.heating_period_hot_water_demand = result.sum_object.HeatingPeriodHotWaterDemand_sum
        self.heating_period_hot_water_demand_surface = surface(
            self.heating_period_hot_water_demand
        )
        self.heating_period_hot_water_energy = result.sum_object.HeatingPeriodHotWaterEnergy_sum
        self.heating_period_hot_water_energy_surface = surface(
            self.heating_period_hot_water_energy
        )
        self.heating_period_electricity_demand_total = (
            result.sum_object.HeatingPeriodElectricityDemandTotal_sum
        )
        self.heating_period_electricity_demand_total_surface = surface(
            self.heating_period_electricity_demand_total
        )
        self.heating_period_internal_gains = result.sum_object.HeatingPeriodInternalGains_sum
        self.heating_period_internal_gains_surface = surface(
            self.heating_period_internal_gains
        )
        self.heating_period_lighting_demand = result.sum_object.HeatingPeriodLightingDemand_sum
        self.heating_period_lighting_demand_surface = surface(
            self.heating_period_lighting_demand
        )
        self.heating_period_appliance_gains_demand = (
            result.sum_object.HeatingPeriodAppliance_gains_demand_sum
        )
        self.heating_period_appliance_gains_demand_surface = surface(
            self.heating_period_appliance_gains_demand
        )
        self.heating_period_appliance_gains_elt_demand = (
            result.sum_object.HeatingPeriodAppliance_gains_elt_demand_sum
        )
        self.heating_period_appliance_gains_elt_demand_surface = surface(
            self.heating_period_appliance_gains_elt_demand
        )
        self.heating_period_solar_gains_total = result.sum_object.HeatingPeriodSolarGainsTotal_sum
        self.heating_period_solar_gains_total_surface = surface(
            self.heating_period_solar_gains_total
        )
        self.heating_period_solar_gains_south_window = (
            result.sum_object.HeatingPeriodSolarGainsSouthWindow_sum
        )
        self.heating_period_solar_gains_east_window = (
            result.sum_object.HeatingPeriodSolarGainsEastWindow_sum
        )
        self.heating_period_solar_gains_west_window = (
            result.sum_object.HeatingPeriodSolarGainsWestWindow_sum
        )
        self.heating_period_solar_gains_north_window = (
            result.sum_object.HeatingPeriodSolarGainsNorthWindow_sum
        )
        self.heating_period_transmission_loss = result.sum_object.HeatingPeriodTransmissionLoss_sum
        self.heating_period_transmission_loss_surface = surface(
            self.heating_period_transmission_loss
        )
        self.heating_period_ventilation_loss = result.sum_object.HeatingPeriodVentilationLoss_sum
        self.heating_period_ventilation_loss_surface = surface(
            self.heating_period_ventilation_loss
        )
        self.heating_period_global_horizontal_radiation_total = (
            result.sum_object.HeatingPeriodGlobalHorizontalRadiationTotal_sum
        )
        self.heating_period_direct_normal_radiation_total = (
            result.sum_object.HeatingPeriodDirectNormalRadiationTotal_sum
        )
        self.heating_period_diffuse_horizontal_radiation_total = (
            result.sum_object.HeatingPeriodDiffuseHorizontalRadiationTotal_sum
        )
        self.global_horizontal_radiation_mean_heating_period = (
            result.sum_object.HeatingPeriodGlobalHorizontalRadiation_mean
        )
        self.direct_normal_radiation_mean_heating_period = (
            result.sum_object.HeatingPeriodDirectNormalRadiation_mean
        )
        self.diffuse_horizontal_radiation_mean_heating_period = (
            result.sum_object.HeatingPeriodDiffuseHorizontalRadiation_mean
        )
        self.drybulb_temperature_mean_heating_period = (
            result.sum_object.HeatingPeriodDrybulbTemperature_mean
        )

        self.occupancy_profile_people_mean_annual = (
            result.sum_object.OccupancyProfilePeople_mean
        )
        self.occupancy_profile_people_mean_heating_period = (
            result.sum_object.HeatingPeriodOccupancyProfilePeople_mean
        )
        self.appliance_profile_factor_mean_annual = (
            result.sum_object.ApplianceProfileFactor_mean
        )
        self.appliance_profile_factor_mean_heating_period = (
            result.sum_object.HeatingPeriodApplianceProfileFactor_mean
        )
        self.air_change_rate_effective_mean_annual = (
            result.sum_object.AirChangeRateEffective_mean
        )
        self.air_change_rate_effective_mean_heating_period = (
            result.sum_object.HeatingPeriodAirChangeRateEffective_mean
        )
        self.air_flow_rate_effective_mean_annual = (
            result.sum_object.AirFlowRateEffective_mean
        )
        self.air_flow_rate_effective_mean_heating_period = (
            result.sum_object.HeatingPeriodAirFlowRateEffective_mean
        )

        self.building_function_main_category = result.building.hk_geb
        self.building_function_sub_category = result.building.uk_geb
        self.profile_sia_2024 = [result.schedule_name]
        self.profile_18599 = [result.typ_norm]
        self.epw_file = [result.epw_filename]
        self.profile_from_norm = profile_from_norm
        self.gains_from_group_values = gains_from_group_values
        self.usage_from_norm = usage_from_norm
        self.weather_period = weather_period

    def __str__(self):
        attrs = "\n".join([f"{key} = {getattr(self, key)}" for key in vars(self)])
        return f"SummaryResult of the simulation: {attrs}"
