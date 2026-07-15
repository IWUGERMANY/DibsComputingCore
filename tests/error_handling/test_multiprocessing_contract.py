from types import SimpleNamespace

import pytest

import dibs_computing_core.iso_simulator.dibs.dibs as dibs_module
from dibs_computing_core.iso_simulator.dibs.dibs import DIBS
from dibs_computing_core.iso_simulator.exceptions import DIBSDataSourceError


class FakeAsyncResult:
    def __init__(self, value=None, error=None):
        self.value = value
        self.error = error
        self.get_calls = 0

    def get(self):
        self.get_calls += 1
        if self.error is not None:
            raise self.error
        return self.value


class FakePool:
    def __init__(self, queued_results):
        self.queued_results = list(queued_results)
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def apply_async(self, operation, args):
        self.calls.append((operation, args))
        return self.queued_results.pop(0)


class StockDataSource:
    def __init__(self, buildings):
        self.buildings = buildings
        self.building = None
        self.epw_pe_factors = None
        self.profile_from_norm = "din18599"
        self.gains_from_group_values = "mid"
        self.usage_from_norm = "sia2024"
        self.weather_period = "2004-2018"

    def get_user_buildings(self):
        return None

    def get_epw_pe_factors(self):
        self.epw_pe_factors = [object()]


def install_fake_pool(monkeypatch, queued_results):
    created = []

    def pool_factory(*, processes):
        pool = FakePool(queued_results)
        pool.processes = processes
        created.append(pool)
        return pool

    monkeypatch.setattr(dibs_module.multiprocessing, "Pool", pool_factory)
    monkeypatch.setattr(
        dibs_module,
        "unpack_results",
        lambda results: ([result[0] for result in results], [result[1] for result in results]),
    )
    monkeypatch.setattr(
        dibs_module, "SummaryResult", lambda result_output, user_args: result_output
    )
    return created


def test_multi_submits_one_building_per_worker_task(monkeypatch):
    buildings = [SimpleNamespace(scr_gebaeude_id=1), SimpleNamespace(scr_gebaeude_id=2)]
    datasource = StockDataSource(buildings)
    created = install_fake_pool(
        monkeypatch,
        [FakeAsyncResult(("hours-1", "summary-1")), FakeAsyncResult(("hours-2", "summary-2"))],
    )

    _, hourly, summaries = DIBS(datasource).multi()

    submitted = [call[1] for call in created[0].calls]
    assert [args[1] for args in submitted] == buildings
    assert all(args[0].buildings is None for args in submitted)
    assert created[0].processes == 2
    assert hourly == ["hours-1", "hours-2"]
    assert summaries == ["summary-1", "summary-2"]


def test_batch_does_not_reuse_external_async_results(monkeypatch):
    buildings = [SimpleNamespace(scr_gebaeude_id=1), SimpleNamespace(scr_gebaeude_id=2)]
    stale_result = FakeAsyncResult(error=AssertionError("stale result was evaluated"))
    created = install_fake_pool(
        monkeypatch, [FakeAsyncResult(("hours-2", "summary-2"))]
    )

    _, hourly, summaries = DIBS(StockDataSource(buildings)).multi_with_batches(
        ["din18599", "mid", "sia2024", "2004-2018"],
        buildings,
        1,
        2,
        [stale_result],
    )

    assert stale_result.get_calls == 0
    assert [call[1][1] for call in created[0].calls] == [buildings[1]]
    assert created[0].processes == 1
    assert hourly == ["hours-2"]
    assert summaries == ["summary-2"]


def test_worker_datasource_copy_does_not_retain_building_stock():
    buildings = [SimpleNamespace(scr_gebaeude_id=1)]
    datasource = StockDataSource(buildings)

    worker_datasource = DIBS(datasource)._worker_datasource_copy()

    assert worker_datasource is not datasource
    assert worker_datasource.building is None
    assert worker_datasource.buildings is None
    assert datasource.buildings is buildings


def test_worker_error_contains_building_and_phase():
    building = SimpleNamespace(scr_gebaeude_id="building-7", t_set_heating=20.0)

    class FailingDataSource:
        building = None

        def get_epw_file(self):
            raise DIBSDataSourceError("weather station missing")

    with pytest.raises(DIBSDataSourceError) as raised:
        dibs_module._simulate_building_worker(FailingDataSource(), building)

    assert raised.value.phase == "initialize_data"
    assert raised.value.context == {"building_id": "building-7"}
