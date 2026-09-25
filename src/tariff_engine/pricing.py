"""The pricing engine. This is the part you write.

Nothing here is prescriptive. The names below are one plausible shape; replace
them with whatever you think fits. What we care about is:

  - money handled exactly, with a rounding policy you can defend
  - tariff rules kept out of the consumption-handling code, so a fourth rate
    card needs no change here
  - anything you cannot price surfaced rather than silently priced as zero

Climate Change Levy is 0.775 p/kWh on all consumption.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

CCL_P_PER_KWH = Decimal("0.775")


def price_site(
    readings: Any,
    rate_card: dict[str, Any],
    duos_calendar: dict[str, Any],
) -> Any:
    """Return the annual cost of one site on one rate card.

    Break the result into standing charge, energy and CCL at minimum, so a human
    can check the arithmetic by hand.
    """
    raise NotImplementedError("Part A")
