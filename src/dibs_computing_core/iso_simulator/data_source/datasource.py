from abc import ABC, abstractmethod
from ..model.building import Building
from ..model.schedule_name import ScheduleName
from ..model.primary_energy_and_emission_factors import PrimaryEnergyAndEmissionFactor
from ..model.weather_data import WeatherData
from ..model.epw_file import EPWFile

from ..exceptions.uk_or_hk_exception import HkOrUkNotFoundError
from ..exceptions.usage_time_exception import UsageTimeError


class DataSource(ABC):
    """
    This interface provides several methods that can be implemented in other classes
    """

    @abstractmethod
    def get_user_building(self) -> Building:
        """
        This method retrieves the building to be simulated.
        Args:

        Returns:
            building
        """

    @abstractmethod
    def get_user_buildings(self) -> list[Building]:
        """
        This method retrieves all the building to be simulated.
        Args:

        Returns:
            building
        """

    @abstractmethod
    def get_epw_pe_factors(self) -> list[PrimaryEnergyAndEmissionFactor]:
        """
        This method retrieves all primary energy and emission factors
        Returns:
            epw_pe_factors
        """
        pass

    @abstractmethod
    def get_schedule(self) -> tuple[list[ScheduleName], str, float] | HkOrUkNotFoundError:
        """
        Find occupancy schedule from SIA2024, depending on hk_geb, uk_geb
        Args:

        Returns:
            schedule_name_list, schedule_name or throws an error
        """
        pass

    @abstractmethod
    def get_tek(self) -> tuple[float, str] | HkOrUkNotFoundError:
        """
        Find TEK values from Partial energy parameters to build the comparative values in accordance with the
        announcement  of 15.04.2021 on the Building Energy Act (GEG) of 2020, depending on hk_geb, uk_geb
        Args:

        Returns:
            tek_dhw, tek_name or throws an error
        """
        pass

    @abstractmethod
    def choose_and_get_the_right_weather_data_from_path(self) -> list[WeatherData]:
        """
        This method retrieves the right weather data
        Args:
        Returns:
            weather_data_objects
        """
        pass

    @abstractmethod
    def get_epw_file(self) -> EPWFile:
        """
        Function finds the epw file depending on building location, Pick latitude and longitude from plz_data and put
        values into a list and Calculate minimum distance to next weather station
        Args:


        Returns:
            epw_file object
        """
        pass

    @abstractmethod
    def get_usage_time(self) -> tuple[int, int] | UsageTimeError:
        """
        Find building's usage time DIN 18599-10 or SIA2024
        Args:

        Returns:
            usage_start, usage_end or throws error
        """
        pass

    @abstractmethod
    def get_gains(self) -> tuple[tuple[float, str], float]:
        """
        Find data from DIN V 18599-10 or SIA2024
        Args:

        Returns:
            gain_person_and_typ_norm, appliance_gains
        """
        pass
