"""Proof that the harness works. Delete or rewrite these as you like.

They assert nothing about pricing -- that is your job.
"""

from decimal import Decimal

from tariff_engine.loaders import ConsumptionRecord
from tariff_engine.pricing import DuoSTariffStrategy, exact_pence_to_pounds, price_site


def test_consumption_loads(consumption_rows):
    assert len(consumption_rows) > 17_000
    first = consumption_rows[0]
    assert first.date
    assert isinstance(first.period, int)
    assert isinstance(first.kwh, Decimal)
    assert first.kwh == Decimal(str(first.kwh))


def test_duos_strategy_maps_extra_periods_to_nearest_defined_band():
    calendar = {
        "season_months": {"winter": [11, 12, 1, 2], "summer": [3, 4, 5, 6, 7, 8, 9, 10]},
        "bank_holidays": [],
        "day_types": {
            "winter_weekday": {
                "green": list(range(1, 21)),
                "amber": list(range(21, 36)),
                "red": list(range(36, 49)),
            }
        },
    }
    rate_card = {
        "name": "Test DUoS",
        "band_scheme": "duos",
        "unit_rates_p_per_kwh": {"green": "10", "amber": "20", "red": "30"},
    }

    strategy = DuoSTariffStrategy(rate_card, calendar)
    reading = ConsumptionRecord(date="2025-11-10", period=49, kwh=Decimal("1"))

    assert strategy.resolve_band(reading) == "red"


def test_exact_pence_to_pounds_rounds_half_up():
    assert exact_pence_to_pounds(Decimal("1.550")) == Decimal("0.02")
    assert exact_pence_to_pounds(Decimal("12.345")) == Decimal("0.12")


def test_flat_tariff_calculates_total_cost_in_exact_decimal_pence():
    rate_card = {
        "name": "Test Flat",
        "band_scheme": "flat",
        "standing_charge_p_per_day": "100",
        "unit_rates_p_per_kwh": {"standard": "20"},
    }
    readings = [
        ConsumptionRecord(date="2025-04-01", period=1, kwh=Decimal("2")),
        ConsumptionRecord(date="2025-04-01", period=2, kwh=Decimal("0.5")),
    ]

    result = price_site(readings, rate_card, {})

    assert result.standing_charge_p == Decimal("100")
    assert result.energy_p == Decimal("50")
    assert result.ccl_p == Decimal("1.9375")
    assert result.total_p == Decimal("151.9375")
    assert result.total_gbp == Decimal("1.52")


def test_day_night_tariff_uses_night_and_day_rates():
    rate_card = {
        "name": "Test Day Night",
        "band_scheme": "day_night",
        "standing_charge_p_per_day": "50",
        "night_window": {"start": "00:00", "end": "01:00"},
        "unit_rates_p_per_kwh": {"night": "10", "day": "20"},
    }
    readings = [
        ConsumptionRecord(date="2025-04-01", period=1, kwh=Decimal("1")),
        ConsumptionRecord(date="2025-04-01", period=5, kwh=Decimal("2")),
    ]

    result = price_site(readings, rate_card, {})

    assert result.band_breakdown_p["night"] == Decimal("10")
    assert result.band_breakdown_p["day"] == Decimal("40")
    assert result.energy_p == Decimal("50")
    assert result.ccl_p == Decimal("2.325")
    assert result.total_p == Decimal("102.325")
    assert result.total_gbp == Decimal("1.02")


def test_every_rate_card_has_a_band_scheme(rate_cards):
    assert len(rate_cards) == 3
    for card in rate_cards:
        assert card["band_scheme"] in {"flat", "day_night", "duos"}
        assert card["unit_rates_p_per_kwh"]


def test_duos_calendar_covers_three_day_types(duos_calendar):
    assert set(duos_calendar["day_types"]) == {
        "winter_weekday",
        "summer_weekday",
        "weekend",
    }
