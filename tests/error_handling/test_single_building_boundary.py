"""Tests for the single-building public error boundary introduced in D-EH7."""

from types import SimpleNamespace

import pytest

import dibs_computing_core.iso_simulator.dibs.dibs as dibs_module
from dibs_computing_core.iso_simulator.dibs.dibs import DIBS
from dibs_computing_core.iso_simulator.exceptions import (
    DIBSDataSourceError,
    DIBSError,
)


def make_dibs() -> DIBS:
    datasource = SimpleNamespace(
        profile_from_norm=True,
        gains_from_group_values=True,
        usage_from_norm=True,
        weather_period="TMY",
        building=object(),
        epw_file=object(),
        epw_pe_factors=[object()],
    )
    return DIBS(datasource)


def raise_error(error):
    def operation(*args):
        raise error

    return operation


def test_initialize_data_error_receives_missing_phase(monkeypatch):
    dibs = make_dibs()
    error = DIBSDataSourceError("building missing")
    monkeypatch.setattr(dibs, "initialize_data", raise_error(error))

    with pytest.raises(DIBSDataSourceError) as raised:
        dibs.calculate_result_of_one_building()

    assert raised.value is error
    assert raised.value.phase == "initialize_data"


def test_existing_error_phase_is_not_overwritten(monkeypatch):
    dibs = make_dibs()
    error = DIBSError("weather missing", phase="load_weather")
    monkeypatch.setattr(dibs, "initialize_data", raise_error(error))

    with pytest.raises(DIBSError) as raised:
        dibs.calculate_result_of_one_building()

    assert raised.value.phase == "load_weather"


def test_simulator_initialization_error_receives_phase(monkeypatch):
    dibs = make_dibs()
    monkeypatch.setattr(dibs, "initialize_data", lambda: None)
    monkeypatch.setattr(
        dibs_module, "BuildingSimulator", raise_error(DIBSError("invalid simulator"))
    )

    with pytest.raises(DIBSError) as raised:
        dibs.calculate_result_of_one_building()

    assert raised.value.phase == "simulator_init"


def test_simulation_error_receives_phase(monkeypatch):
    dibs = make_dibs()
    simulator = SimpleNamespace(
        datasource=SimpleNamespace(building=SimpleNamespace(t_set_heating=20.0))
    )
    monkeypatch.setattr(dibs, "initialize_data", lambda: None)
    monkeypatch.setattr(dibs_module, "BuildingSimulator", lambda datasource: simulator)
    monkeypatch.setattr(
        dibs_module,
        "extracted_method_to_simulate_one_building",
        raise_error(DIBSError("hourly simulation failed")),
    )

    with pytest.raises(DIBSError) as raised:
        dibs.calculate_result_of_one_building()

    assert raised.value.phase == "simulate_hours"


def test_summary_error_receives_phase(monkeypatch):
    dibs = make_dibs()
    simulator = SimpleNamespace(
        datasource=SimpleNamespace(building=SimpleNamespace(t_set_heating=20.0))
    )
    monkeypatch.setattr(dibs, "initialize_data", lambda: None)
    monkeypatch.setattr(dibs_module, "BuildingSimulator", lambda datasource: simulator)
    monkeypatch.setattr(
        dibs_module,
        "extracted_method_to_simulate_one_building",
        lambda simulator, temperature: ("result", "output"),
    )
    monkeypatch.setattr(
        dibs_module, "SummaryResult", raise_error(DIBSError("summary failed"))
    )

    with pytest.raises(DIBSError) as raised:
        dibs.calculate_result_of_one_building()

    assert raised.value.phase == "summary_wrap"


def test_unknown_programming_error_is_not_wrapped(monkeypatch):
    dibs = make_dibs()
    error = ValueError("programming failure")
    monkeypatch.setattr(dibs, "initialize_data", raise_error(error))

    with pytest.raises(ValueError) as raised:
        dibs.calculate_result_of_one_building()

    assert raised.value is error


def test_complete_datasource_state_is_accepted():
    dibs = make_dibs()

    dibs._validate_datasource_state()


@pytest.mark.parametrize("missing_field", ["building", "epw_file", "epw_pe_factors"])
def test_missing_datasource_state_is_reported(missing_field):
    dibs = make_dibs()
    setattr(dibs.datasource, missing_field, None)

    with pytest.raises(DIBSDataSourceError) as raised:
        dibs._validate_datasource_state()

    assert raised.value.phase == "initialize_data"
    assert raised.value.context == {"missing_fields": [missing_field]}


def test_absent_datasource_attributes_are_reported_together():
    dibs = make_dibs()
    del dibs.datasource.building
    del dibs.datasource.epw_file

    with pytest.raises(DIBSDataSourceError) as raised:
        dibs._validate_datasource_state()

    assert raised.value.context == {"missing_fields": ["building", "epw_file"]}
