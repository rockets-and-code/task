"""Tariff comparison engine."""

__all__ = ["DATA_DIR"]

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
