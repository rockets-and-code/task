"""Proof that the harness works. Delete or rewrite these as you like.

They assert nothing about pricing -- that is your job.
"""

from decimal import Decimal

from tariff_engine.loaders import ConsumptionRecord
from tariff_engine.pricing import DuoSTariffStrategy


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
