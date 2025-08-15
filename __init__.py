"""
Python backend for the Emergency Shelter API.

This package provides a small Flask application that exposes endpoints to:
 - List shelters
 - Find nearest shelters from latitude/longitude
 - Find nearest shelters from a Japanese postal code (requires Google API key)

Data is loaded from CSV files shipped in the repository (e.g. `mergeFromCity_2.csv` or `13121_2.csv`).
"""

__all__ = []

