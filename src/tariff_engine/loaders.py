"""Reading the input files off disk.

These helpers do the boring part — opening files and parsing them — and
deliberately stop there. They do no validation, no deduplication and no type
coercion beyond what `csv` and `json` give you. Those decisions are yours.

You are free to rewrite or delete any of this.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterator

from . import DATA_DIR


def read_consumption_rows(path: Path | None = None) -> Iterator[dict[str, str]]:
    path = path or DATA_DIR / "site_consumption.csv"
    with path.open(newline="") as fh:
        yield from csv.DictReader(fh)


def load_rate_cards(directory: Path | None = None) -> list[dict[str, Any]]:
    directory = directory or DATA_DIR / "rate_cards"
    return [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))]


def load_duos_calendar(path: Path | None = None) -> dict[str, Any]:
    path = path or DATA_DIR / "duos_calendar.json"
    return json.loads(path.read_text())
