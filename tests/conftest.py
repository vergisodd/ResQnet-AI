from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.settings import settings


@pytest.fixture(autouse=True)
def isolated_sqlite_db(tmp_path):
    object.__setattr__(settings, "database_url", None)
    object.__setattr__(settings, "database_path", str(tmp_path / "resqnet_test.db"))
    yield
