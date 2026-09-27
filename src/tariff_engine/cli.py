"""Command-line entry point. `make run` calls this.

Print a ranking, cheapest first, with the cost components broken out.
"""

from __future__ import annotations

import sys

from .loaders import load_duos_calendar, load_rate_cards, read_consumption_rows
from .pricing import price_all_tariffs


def main(argv: list[str] | None = None) -> int:
    rows = list(read_consumption_rows())
    cards = load_rate_cards()
    calendar = load_duos_calendar()

    print(f"loaded {len(rows):,} consumption rows")
    print(f"loaded {len(cards)} rate cards: {', '.join(c['name'] for c in cards)}")
    print(f"loaded DUoS calendar with {len(calendar['bank_holidays'])} bank holidays")
    print()

    ranked_results, warnings = price_all_tariffs(rows, cards, calendar)

    if warnings:
        print("Data quality warnings:")
        for warning in warnings[:10]:
            print(f"  - {warning}")
        print()

    header = f"{'Rank':>4} {'Tariff':<24} {'Annual (ex VAT)':>14} {'Standing':>12} {'Energy':>12} {'CCL':>12}"
    print(header)
    print("-" * len(header))

    for rank, result in enumerate(ranked_results, start=1):
        print(
            f"{rank:>4} {result.tariff_name:<24} "
            f"£{result.total_gbp:>12,.2f} "
            f"£{result.standing_charge_gbp:>10,.2f} "
            f"£{result.energy_gbp:>10,.2f} "
            f"£{result.ccl_gbp:>10,.2f}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
