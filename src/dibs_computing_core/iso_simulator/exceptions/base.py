"""Common exception contract for the DIBS computing core."""

from collections.abc import Mapping
from typing import Any


class DIBSError(Exception):
    """Base class for expected, host-visible DIBS failures."""

    code = "DIBS_ERROR"

    def __init__(
        self,
        message: str | None = None,
        *,
        phase: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        self.phase = phase
        self.context = dict(context or {})
        super().__init__(message or self.code)


class DIBSInputError(DIBSError):
    """Input supplied to DIBS is missing or invalid."""

    code = "DIBS_INVALID_INPUT"


class DIBSDataSourceError(DIBSError):
    """A data source cannot provide data required by DIBS."""

    code = "DIBS_DATASOURCE_ERROR"


class DIBSConfigurationError(DIBSError):
    """The building or simulation configuration is unsupported."""

    code = "DIBS_CONFIGURATION_ERROR"


class DIBSSimulationError(DIBSError):
    """The simulation cannot produce a valid result."""

    code = "DIBS_SIMULATION_ERROR"


class DIBSResultError(DIBSError):
    """A derived result cannot be calculated reliably."""

    code = "DIBS_RESULT_ERROR"


class UnsupportedSystemError(DIBSConfigurationError):
    """A configured heating or cooling system is unsupported."""

    code = "DIBS_UNSUPPORTED_SYSTEM"


class SimulationStateError(DIBSSimulationError):
    """The simulation reached an invalid internal state."""

    code = "DIBS_INVALID_SIMULATION_STATE"


class ThermalCalculationError(DIBSSimulationError):
    """The thermal calculation cannot produce a valid state."""

    code = "DIBS_THERMAL_CALCULATION_FAILED"