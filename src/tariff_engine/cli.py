"""Command-line entry point. `make run` calls this.

Print a ranking, cheapest first, with the cost components broken out.
"""

from __future__ import annotations

import sys

from .loaders import load_duos_calendar, load_rate_cards, read_consumption_rows


def main(argv: list[str] | None = None) -> int:
    rows = list(read_consumption_rows())
    cards = load_rate_cards()
    calendar = load_duos_calendar()

    print(f"loaded {len(rows):,} consumption rows")
    print(f"loaded {len(cards)} rate cards: {', '.join(c['name'] for c in cards)}")
    print(f"loaded DUoS calendar with {len(calendar['bank_holidays'])} bank holidays")
    print()
    print("Now price them. See src/tariff_engine/pricing.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
