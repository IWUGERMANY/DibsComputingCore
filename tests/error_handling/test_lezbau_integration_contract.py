"""D-EH9 tests for host integrations such as Lezbau/DataSourceDjango.

These tests intentionally use a tiny stateful DataSource double. That mirrors
DataSourceCSV and DataSourceDjango without importing either implementation.
"""

import ast
from pathlib import Path

import pytest

import dibs_computing_core.iso_simulator.exceptions as exceptions
from dibs_computing_core.iso_simulator.dibs.dibs import DIBS
from dibs_computing_core.iso_simulator.exceptions import (
    DIBSDataSourceError,
    DIBSError,
)


PACKAGE_ROOT = Path(__file__).parents[2] / "src" / "dibs_computing_core"

EXPECTED_PUBLIC_ERRORS = {
    "BuildingNotHeatedError",
    "DIBSConfigurationError",
    "DIBSDataSourceError",
    "DIBSError",
    "DIBSInputError",
    "DIBSResultError",
    "DIBSSimulationError",
    "GHGEmissionError",
    "HkOrUkNotFoundError",
    "PLZNotFoundError",
    "SimulationStateError",
    "ThermalCalculationError",
    "UnsupportedSystemError",
    "UsageTimeError",
}

EXPECTED_ERROR_CODES = {
    "DIBS_BUILDING_NOT_HEATED",
    "DIBS_CONFIGURATION_ERROR",
    "DIBS_DATASOURCE_ERROR",
    "DIBS_ERROR",
    "DIBS_GHG_CALCULATION_FAILED",
    "DIBS_INVALID_INPUT",
    "DIBS_INVALID_SIMULATION_STATE",
    "DIBS_POSTCODE_NOT_FOUND",
    "DIBS_RESULT_ERROR",
    "DIBS_SIMULATION_ERROR",
    "DIBS_THERMAL_CALCULATION_FAILED",
    "DIBS_UNSUPPORTED_SYSTEM",
    "DIBS_USAGE_TIME_NOT_FOUND",
    "DIBS_USAGE_TYPE_NOT_FOUND",
}


class MinimalFailingDataSource:
    """Small stateful DataSource double for host integration error tests."""

    profile_from_norm = "din18599"
    gains_from_group_values = "mid"
    usage_from_norm = "sia2024"
    weather_period = "2004-2018"
    building = None
    epw_file = None
    epw_pe_factors = None

    def get_user_building(self):
        raise DIBSDataSourceError(
            "building not available",
            context={"source": "minimal"},
        )

    def get_epw_pe_factors(self):
        raise AssertionError("must not continue after get_user_building failure")

    def get_epw_file(self):
        raise AssertionError("must not continue after get_user_building failure")


def iter_package_imports():
    for path in PACKAGE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    yield path, alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                yield path, node.module


def test_public_exception_imports_are_stable_for_host_apps():
    for name in EXPECTED_PUBLIC_ERRORS:
        error_type = getattr(exceptions, name)
        assert issubclass(error_type, DIBSError)


def test_public_error_codes_are_stable_for_host_apps():
    public_codes = {
        getattr(getattr(exceptions, name), "code")
        for name in EXPECTED_PUBLIC_ERRORS
    }

    assert public_codes == EXPECTED_ERROR_CODES


def test_minimal_stateful_datasource_error_reaches_host_boundary():
    dibs = DIBS(MinimalFailingDataSource())

    with pytest.raises(DIBSDataSourceError) as raised:
        dibs.calculate_result_of_one_building()

    assert raised.value.code == "DIBS_DATASOURCE_ERROR"
    assert raised.value.phase == "initialize_data"
    assert raised.value.context == {"source": "minimal"}


def test_core_has_no_django_or_graphql_import_dependency():
    forbidden_roots = {"django", "graphene", "graphql"}
    violations = []

    for path, module_name in iter_package_imports():
        root_name = module_name.split(".", 1)[0]
        if root_name in forbidden_roots:
            violations.append(f"{path}:{module_name}")

    assert violations == []
