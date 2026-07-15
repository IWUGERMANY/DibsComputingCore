"""Shared system-energy calculations for DIBS building simulations."""

from typing import NamedTuple


class SystemEnergyTotals(NamedTuple):
    """Energy, carbon and primary-energy totals for one technical system."""

    electricity_hi: float
    carbon: float
    primary_energy: float
    fossils_hi: float


class SystemEnergyCalculator:
    """Calculate Hi, GHG and PE totals for technical system energy streams."""

    def calculate(
            self,
            electricity_sum: float,
            fossils_sum: float,
            f_hs_hi: float,
            f_ghg: int,
            f_pe: float,
    ) -> SystemEnergyTotals:
        electricity_hi = 0
        fossils_hi = 0

        if electricity_sum > 0:
            electricity_hi = electricity_sum / f_hs_hi
            active_energy_hi = electricity_hi
        else:
            fossils_hi = fossils_sum / f_hs_hi
            active_energy_hi = fossils_hi

        carbon = (active_energy_hi * f_ghg) / 1000
        primary_energy = active_energy_hi * f_pe
        return SystemEnergyTotals(electricity_hi, carbon, primary_energy, fossils_hi)
