"""Unit test configuration and fixtures.

Pytest marks used in this suite:
- ``integration``: Tests that make real HTTP calls or require external services.
  Skipped in normal CI; run manually with ``uv run pytest -m integration``.
- ``slow``: Tests with significant runtime (> 5 s). Excluded from fast feedback loops.
"""
