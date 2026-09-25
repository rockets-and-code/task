"""Proof that the harness works. Delete or rewrite these as you like.

They assert nothing about pricing -- that is your job.
"""


def test_consumption_loads(consumption_rows):
    assert len(consumption_rows) > 17_000
    assert set(consumption_rows[0]) == {
        "mpan",
        "settlement_date",
        "settlement_period",
        "kwh",
        "reading_type",
    }


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
