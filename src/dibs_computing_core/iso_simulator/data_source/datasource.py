from abc import ABC, abstractmethod

from ..model.building import Building
from ..model.epw_file import EPWFile
from ..model.primary_energy_and_emission_factors import PrimaryEnergyAndEmissionFactor
from ..model.schedule_name import ScheduleName
from ..model.weather_data import WeatherData


class DataSource(ABC):
    """Interface for simulation data supplied by a host application."""

    @abstractmethod
    def get_user_building(self) -> None:
        """Load the building and assign it to ``self.building``."""

    @abstractmethod
    def get_user_buildings(self) -> None:
        """Load all buildings and assign them to ``self.buildings``."""

    @abstractmethod
    def get_epw_pe_factors(self) -> None:
        """Load factors and assign them to ``self.epw_pe_factors``."""

    @abstractmethod
    def get_schedule(self) -> tuple[list[ScheduleName], str, float]:
        """Return the occupancy schedule for the building usage type.

        Raises:
            HkOrUkNotFoundError: If the HK/UK usage type cannot be resolved.
        """

    @abstractmethod
    def get_tek(self) -> tuple[float, str]:
        """Return the TEK value and name for the building usage type.

        Raises:
            HkOrUkNotFoundError: If the HK/UK usage type cannot be resolved.
        """

    @abstractmethod
    def choose_and_get_the_right_weather_data_from_path(self) -> list[WeatherData]:
        """Return weather data selected for the current building."""

    @abstractmethod
    def get_epw_file(self) -> None:
        """Select an EPW file and assign it to ``self.epw_file``.

        Raises:
            PLZNotFoundError: If no location can be resolved for the postcode.
        """

    @abstractmethod
    def get_usage_time(self) -> tuple[int, int]:
        """Return the start and end hour of building usage.

        Raises:
            UsageTimeError: If no valid usage time can be resolved.
        """

    @abstractmethod
    def get_gains(self) -> tuple[tuple[float, str], float]:
        """Return person-related and appliance gains."""
