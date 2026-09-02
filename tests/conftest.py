"""Shared pytest configuration.

Tests are split into two suites that run with different commands:

* ``tests/unit``        - fast, no I/O, no external services (``pytest -m unit``)
* ``tests/integration`` - drives the FastAPI app against a real Postgres
  database with a deterministic (mocked) LLM (``pytest -m integration``)

Markers are applied automatically from the directory a test lives in, so test
functions do not need to be decorated by hand.
"""

from __future__ import annotations

import pytest

_SUITE_MARKERS = ("unit", "integration")


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    for item in items:
        parts = item.path.parts
        for marker in _SUITE_MARKERS:
            if marker in parts:
                item.add_marker(getattr(pytest.mark, marker))
                break
