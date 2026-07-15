"""Tests for the public DIBS exception contract introduced in D-EH2."""

import pytest

from dibs_computing_core.iso_simulator.exceptions import (
    BuildingNotHeatedError,
    DIBSConfigurationError,
    DIBSDataSourceError,
    DIBSError,
    DIBSInputError,
    DIBSResultError,
    DIBSSimulationError,
    GHGEmissionError,
    HkOrUkNotFoundError,
    PLZNotFoundError,
    SimulationStateError,
    ThermalCalculationError,
    UnsupportedSystemError,
    UsageTimeError,
)


@pytest.mark.parametrize(
    ("error_type", "parent_type", "code"),
    [
        (DIBSInputError, DIBSError, "DIBS_INVALID_INPUT"),
        (DIBSDataSourceError, DIBSError, "DIBS_DATASOURCE_ERROR"),
        (DIBSConfigurationError, DIBSError, "DIBS_CONFIGURATION_ERROR"),
        (DIBSSimulationError, DIBSError, "DIBS_SIMULATION_ERROR"),
        (DIBSResultError, DIBSError, "DIBS_RESULT_ERROR"),
        (BuildingNotHeatedError, DIBSConfigurationError, "DIBS_BUILDING_NOT_HEATED"),
        (GHGEmissionError, DIBSResultError, "DIBS_GHG_CALCULATION_FAILED"),
        (PLZNotFoundError, DIBSDataSourceError, "DIBS_POSTCODE_NOT_FOUND"),
        (HkOrUkNotFoundError, DIBSDataSourceError, "DIBS_USAGE_TYPE_NOT_FOUND"),
        (UsageTimeError, DIBSDataSourceError, "DIBS_USAGE_TIME_NOT_FOUND"),
        (UnsupportedSystemError, DIBSConfigurationError, "DIBS_UNSUPPORTED_SYSTEM"),
        (SimulationStateError, DIBSSimulationError, "DIBS_INVALID_SIMULATION_STATE"),
        (
            ThermalCalculationError,
            DIBSSimulationError,
            "DIBS_THERMAL_CALCULATION_FAILED",
        ),
    ],
)
def test_exception_hierarchy_and_codes(error_type, parent_type, code):
    assert issubclass(error_type, parent_type)
    assert error_type.code == code


def test_base_error_preserves_message_phase_and_context():
    source_context = {"building_id": 42}
    error = DIBSError(
        "simulation failed", phase="simulate_hours", context=source_context
    )
    source_context["building_id"] = 99

    assert str(error) == "simulation failed"
    assert error.phase == "simulate_hours"
    assert error.context == {"building_id": 42}


def test_default_message_is_stable_error_code():
    error = PLZNotFoundError()

    assert str(error) == "DIBS_POSTCODE_NOT_FOUND"
    assert error.phase is None
    assert error.context == {}


def test_all_domain_errors_can_be_caught_as_dibs_error():
    with pytest.raises(DIBSError):
        raise GHGEmissionError("unknown heating system")
@pytest.mark.parametrize(
    "error_type",
    [
        BuildingNotHeatedError,
        GHGEmissionError,
        PLZNotFoundError,
        HkOrUkNotFoundError,
        SimulationStateError,
    ThermalCalculationError,
    UnsupportedSystemError,
    UsageTimeError,
    ],
)
def test_domain_error_uses_uniform_constructor(error_type):
    error = error_type(
        "domain failure",
        phase="initialize_data",
        context={"building_id": 42},
    )

    assert str(error) == "domain failure"
    assert error.code == error_type.code
    assert error.phase == "initialize_data"
    assert error.context == {"building_id": 42}


