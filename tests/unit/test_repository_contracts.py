"""Regression checks for repository ports and standalone test DB metadata."""
import importlib
import inspect
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.domain import ports


@pytest.mark.parametrize("name,module", [
    ("UserRepository", "user_repository"),
    ("MovieRepository", "movie_repository"),
    ("ShowtimeRepository", "showtime_repository"),
    ("BookingRepository", "booking_repository"),
    ("SeatHoldRepository", "seat_hold_repository"),
    ("PaymentRepository", "payment_repository"),
])
def test_adapters_accept_port_keyword_arguments(name, module):
    protocol = getattr(ports, name)
    adapter = getattr(importlib.import_module("app.repositories." + module), name)
    for method, contract in vars(protocol).items():
        if not inspect.iscoroutinefunction(contract):
            continue
        implementation = getattr(adapter, method)
        assert inspect.iscoroutinefunction(implementation)
        arguments = {
            key: object() for key, parameter in inspect.signature(contract).parameters.items()
            if key != "self" and parameter.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY
            )
        }
        # Binding raises TypeError if a port-supported keyword is rejected.
        inspect.signature(implementation).bind(object(), **arguments)


def test_conftest_registers_all_tables_without_importing_application():
    root = Path(__file__).resolve().parents[2]
    script = """
import runpy, sys
runpy.run_path('tests/conftest.py')
assert 'app.main' not in sys.modules
from app.db.database import Base
expected = {'users', 'movies', 'showtimes', 'bookings', 'seat_holds', 'seat_hold_seats', 'payments'}
assert expected <= set(Base.metadata.tables), expected - set(Base.metadata.tables)
"""
    env = os.environ.copy()
    # Only import fixture definitions: never instantiate an engine fixture or
    # connect to this deliberately non-production URL.
    env["TEST_DATABASE_URL"] = "postgresql+psycopg://test:test@127.0.0.1:65432/metadata_only"
    result = subprocess.run([sys.executable, "-c", script], cwd=root, env=env,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
