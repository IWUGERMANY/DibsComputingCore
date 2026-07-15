"""Tests for the corrected DataSource contracts introduced in D-EH6."""

from typing import get_type_hints

from dibs_computing_core.iso_simulator.building_simulator.simulator import BuildingSimulator
from dibs_computing_core.iso_simulator.data_source.datasource import DataSource


def annotation_contains_exception(annotation) -> bool:
    """Return whether an annotation contains an exception class."""
    if isinstance(annotation, type) and issubclass(annotation, BaseException):
        return True
    return any(
        annotation_contains_exception(arg)
        for arg in getattr(annotation, "__args__", ())
    )


def test_datasource_success_types_do_not_contain_exceptions():
    for method_name in ("get_schedule", "get_tek", "get_usage_time"):
        return_type = get_type_hints(getattr(DataSource, method_name))["return"]
        assert not annotation_contains_exception(return_type)


def test_simulator_wrapper_success_types_do_not_contain_exceptions():
    for method_name in ("get_schedule", "get_tek"):
        return_type = get_type_hints(getattr(BuildingSimulator, method_name))["return"]
        assert not annotation_contains_exception(return_type)


def test_datasource_documents_expected_errors():
    assert "HkOrUkNotFoundError" in DataSource.get_schedule.__doc__
    assert "HkOrUkNotFoundError" in DataSource.get_tek.__doc__
    assert "UsageTimeError" in DataSource.get_usage_time.__doc__
    assert "PLZNotFoundError" in DataSource.get_epw_file.__doc__