"""Tariff pricing engine and strategy scaffolding.

This module keeps pricing policy separate from reading ingestion. Each tariff
scheme is represented by its own strategy subclass, and all money uses Decimal
with the rounding policy defined in SUBMISSION.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Iterator

from .loaders import ConsumptionRecord

CCL_P_PER_KWH = Decimal("0.775")

def exact_pence_to_pounds(value_pence: Decimal) -> Decimal:
    """Convert exact pence to pounds and round to 2 decimal places.

    This matches the documented rounding policy: invoice components are summed in
    pence, converted to pounds, and then quantized using ROUND_HALF_UP.
    """
    PENCE_PER_POUND = Decimal("100")
    POUNDS_QUANT = Decimal("0.01")

    return (value_pence / PENCE_PER_POUND).quantize(POUNDS_QUANT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class CalculationResult:
    """Exact calculation for one site on one tariff, in pence and pounds."""

    tariff_name: str
    standing_charge_p: Decimal
    energy_p: Decimal
    ccl_p: Decimal
    total_p: Decimal
    band_breakdown_p: dict[str, Decimal] = field(default_factory=dict)

    @property # makes it read-only from the outside
    def standing_charge_gbp(self) -> Decimal:
        return exact_pence_to_pounds(self.standing_charge_p) #converts the pence to pounds and returns a Decimal

    @property
    def energy_gbp(self) -> Decimal:
        return exact_pence_to_pounds(self.energy_p)

    @property
    def ccl_gbp(self) -> Decimal:
        return exact_pence_to_pounds(self.ccl_p)

    @property
    def total_gbp(self) -> Decimal:
        return exact_pence_to_pounds(self.total_p)


class BaseTariffStrategy(ABC):
    """Base tariff strategy used to price a site against one rate card."""

    def __init__(self, rate_card: dict[str, Any], duos_calendar: dict[str, Any] | None = None):
        self.rate_card = rate_card
        self.duos_calendar = duos_calendar or {}
        self.name = str(rate_card.get("name", "unknown_tariff"))

    @property
    def standing_charge_p_per_day(self) -> Decimal:
        return Decimal(str(self.rate_card["standing_charge_p_per_day"]))

    @property
    def unit_rates_p_per_kwh(self) -> dict[str, Decimal]:
        return {band: Decimal(str(rate)) for band, rate in self.rate_card["unit_rates_p_per_kwh"].items()}

    @abstractmethod
    def resolve_band(self, record: ConsumptionRecord) -> str:
        """Map one reading to a tariff band."""

    def calculate(self, readings: Iterable[ConsumptionRecord]) -> CalculationResult:
        """Price one site against the strategy.

        Rounding policy:
        - all intermediate calculations remain exact in pence using Decimal
        - invoice components are rounded only when converting to pounds for output
        """
        readings = list(readings)
        if not readings:
            raise ValueError(f"No readings supplied for tariff {self.name!r}")

        total_energy_p = Decimal("0")
        band_breakdown_p: dict[str, Decimal] = {}

        for record in readings:
            band = self.resolve_band(record)
            unit_rate_p_per_kwh = self.unit_rates_p_per_kwh[band]
            period_cost_p = (record.kwh * unit_rate_p_per_kwh)
            total_energy_p += period_cost_p #accumulate the total energy cost in pence
            band_breakdown_p[band] = band_breakdown_p.get(band, Decimal("0")) + period_cost_p #each band accumulates the total cost for that band across all readings

        ccl_p = sum((record.kwh * CCL_P_PER_KWH) for record in readings) #calculate the Climate Change Levy (CCL) for each reading and sum them up
        number_of_days = len({record.date for record in readings})
        standing_charge_p = self.standing_charge_p_per_day * Decimal(number_of_days) #calculate the total standing charge based on the number of unique days in the readings - this is a flat daily charge that applies regardless of consumption
        total_p = standing_charge_p + total_energy_p + ccl_p #calculate the total cost by summing the standing charge, total energy cost, and CCL

        return CalculationResult(
            tariff_name=self.name,
            standing_charge_p=standing_charge_p,
            energy_p=total_energy_p,
            ccl_p=ccl_p,
            total_p=total_p,
            band_breakdown_p=band_breakdown_p,
        )


class FlatTariffStrategy(BaseTariffStrategy):
    """Flat-rate tariff: every reading uses the single standard band."""

    def resolve_band(self, record: ConsumptionRecord) -> str:
        return next(iter(self.unit_rates_p_per_kwh)) # only change from AbstractTariffStrategy is that it returns the first (and only) band from the unit_rates_p_per_kwh dictionary, which represents a flat-rate tariff where all readings are charged at the same rate.


class DayNightTariffStrategy(BaseTariffStrategy):
    """Economy 7 style tariff: split by day and night period windows."""

    def resolve_band(self, record: ConsumptionRecord) -> str:
        night_window = self.rate_card.get("night_window", {"start": "00:00", "end": "07:00"})
        start_period = self._time_to_period(night_window.get("start", "00:00"))
        end_period = self._time_to_period(night_window.get("end", "07:00"))

        if start_period <= record.period <= end_period:
            return "night"
        return "day"

    @staticmethod
    def _time_to_period(value: str) -> int:
        # Settlement periods are 30-minute slots in a 48-slot day for most dates,
        # but DST changes create short/long days with 46 or 50 periods. We therefore
        # convert the wall-clock time to a slot index without clamping to 48, so the
        # time-of-use logic still maps correctly on DST transition dates.
        # Should work because we read the date from the CSV and use that to determine the day type, so we can handle DST correctly.
        hour, minute = value.split(":")
        total_minutes = (int(hour) * 60) + int(minute)
        return (total_minutes // 30) + 1


class DuoSTariffStrategy(BaseTariffStrategy):
    """DUoS tariff: resolve the period to a season/day-type band."""

    def resolve_band(self, record: ConsumptionRecord) -> str:
        month = self._month_for_date(record.date)
        self._season_for_month(month)
        day_type = self._day_type_for_date(record.date)
        periods_by_band = self.duos_calendar.get("day_types", {}).get(day_type, {})

        # Build a lookup from settlement period to its DUoS band so we can figure out which band rate we apply. 
        # This is required because DST causes a few dates to have 46 or 50 periods instead of the usual 48. 
        # We cannot assume every day is a fixed-length 48-slot schedule.
        period_to_band: dict[int, str] = {}
        for band_name, periods in periods_by_band.items():
            for period in periods:
                period_to_band[period] = band_name

        # If the settlement period is defined in the DUoS calendar, return its band.
        if record.period in period_to_band:
            return period_to_band[record.period]

        # order the defined periods so we can find the nearest one to the current settlement period
        defined_periods = sorted(period_to_band)
        if not defined_periods:
            return "green"

        # find the nearest defined period that is less than or equal to the current settlement period. If there are any, return the band for the maximum of those previous periods.
        previous_periods = [period for period in defined_periods if period <= record.period]
        if previous_periods:
            return period_to_band[max(previous_periods)]
        
        # If there are no previous periods, return the band for the nearest defined period after the current one.
        return period_to_band[min(defined_periods)]

    def _month_for_date(self, settlement_date: str) -> int:
        return date.fromisoformat(settlement_date).month

    # Determine the season for a given month based on the DUoS calendar. If the month is in the winter months, return "winter"; otherwise, return "summer".
    def _season_for_month(self, month: int) -> str:
        winter = set(self.duos_calendar.get("season_months", {}).get("winter", []))
        return "winter" if month in winter else "summer"

    # Determine the day type for a given settlement date based on the DUoS calendar. If the date is a bank holiday, return "weekend". If the date falls on a Saturday or Sunday, return "weekend". Otherwise, determine the season for the month and return "{season}_weekday".
    def _day_type_for_date(self, settlement_date: str) -> str:
        holiday_dates = {d for d in self.duos_calendar.get("bank_holidays", [])}
        if settlement_date in holiday_dates:
            return "weekend"

        day_name = date.fromisoformat(settlement_date).strftime("%A")
        if day_name in {"Saturday", "Sunday"}:
            return "weekend"

        month = self._month_for_date(settlement_date)
        season = self._season_for_month(month)
        return f"{season}_weekday"


def build_tariff_strategy(rate_card: dict[str, Any], duos_calendar: dict[str, Any] | None = None) -> BaseTariffStrategy:
    """
    Factory function to create the appropriate tariff strategy based on the band scheme specified in the rate card.
    If the band scheme is "flat", it returns a FlatTariffStrategy.
    If the band scheme is "day_night", it returns a DayNightTariffStrategy.
    If the band scheme is "duos", it returns a DuoSTariffStrategy.
    If the band scheme is not recognized, it raises a ValueError.
    """
    scheme = rate_card.get("band_scheme")
    calendar = duos_calendar or {}

    if scheme == "flat":
        return FlatTariffStrategy(rate_card, calendar)
    if scheme == "day_night":
        return DayNightTariffStrategy(rate_card, calendar)
    if scheme == "duos":
        return DuoSTariffStrategy(rate_card, calendar)

    raise ValueError(f"Unsupported band scheme: {scheme!r}")


def price_site(
    readings: Iterable[ConsumptionRecord],
    rate_card: dict[str, Any],
    duos_calendar: dict[str, Any],
) -> CalculationResult:
    """Return the annual cost of one site on one rate card.

    This is the main public loop for Part A and is intentionally isolated from the
    raw CSV loader so new tariff cards can be added without changing this function.
    """
    strategy = build_tariff_strategy(rate_card, duos_calendar)
    return strategy.calculate(readings)
