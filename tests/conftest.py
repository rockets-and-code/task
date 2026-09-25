import pytest

from tariff_engine.loaders import load_duos_calendar, load_rate_cards, read_consumption_rows


@pytest.fixture(scope="session")
def consumption_rows():
    return list(read_consumption_rows())


@pytest.fixture(scope="session")
def rate_cards():
    return load_rate_cards()


@pytest.fixture(scope="session")
def duos_calendar():
    return load_duos_calendar()
