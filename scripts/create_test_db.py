"""
scripts/create_test_db.py
=========================
Ensures the test PostgreSQL database exists and is reachable.

Usage
-----
    python scripts/create_test_db.py

Environment
-----------
Reads TEST_DATABASE_URL from the environment or from a .env.test file in the
project root.  The script will FAIL FAST if TEST_DATABASE_URL is absent or
empty — it never falls back to DATABASE_URL or any production connection.

Safety rules
------------
* The database name must contain the word "test".  This prevents accidental
  runs against a production database whose URL happened to be set in the env.
* The script never drops or truncates any database.
* If the database already exists the script exits cleanly (idempotent).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse


def _load_env_test() -> None:
    """Parse key=value pairs from .env.test and inject them into os.environ.

    This is a minimal implementation so the script has no extra dependencies.
    Lines beginning with # and blank lines are ignored.
    Values are NOT overridden if already set in the environment.
    """
    env_file = Path(__file__).parent.parent / ".env.test"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _get_test_url() -> str:
    """Return TEST_DATABASE_URL or abort with a clear error message."""
    url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not url:
        print(
            "\n[ERROR] TEST_DATABASE_URL is not set.\n"
            "  Copy .env.test.example to .env.test and fill in your credentials.\n"
            "  This script will NOT fall back to DATABASE_URL.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return url


def _assert_test_database(url: str) -> None:
    """Abort if the database name does not contain 'test'.

    This is a safety guardrail against accidentally pointing at production.
    """
    parsed = urlparse(url)
    db_name = parsed.path.lstrip("/")
    if "test" not in db_name.lower():
        print(
            f"\n[ERROR] Safety check failed.\n"
            f"  Database name '{db_name}' does not contain 'test'.\n"
            f"  Refusing to proceed — verify TEST_DATABASE_URL.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return db_name


def _admin_url(test_url: str) -> str:
    """Build an admin-level URL pointing at the 'postgres' maintenance DB.

    This is used to issue CREATE DATABASE when the target DB doesn't exist yet.
    """
    parsed = urlparse(test_url)
    admin = parsed._replace(path="/postgres")
    return admin.geturl()


def ensure_database_exists(test_url: str, db_name: str) -> None:
    """Create the test database if it does not already exist."""
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        print("[ERROR] SQLAlchemy is not installed.", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(test_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[OK] Connected to test database '{db_name}' — it already exists.")
        engine.dispose()
        return
    except Exception:
        # Database probably doesn't exist yet; fall through to create it.
        engine.dispose()

    admin_url = _admin_url(test_url)
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            row = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).fetchone()
            if row is None:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"[OK] Created test database '{db_name}'.")
            else:
                print(f"[OK] Test database '{db_name}' already exists.")
    except Exception as exc:
        print(
            f"\n[ERROR] Could not create database '{db_name}'.\n"
            f"  {exc}\n"
            f"  Check that the PostgreSQL user has CREATEDB privilege.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    finally:
        admin_engine.dispose()


def verify_connection(test_url: str, db_name: str) -> None:
    """Final connection smoke-test on the (now existing) test database."""
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        sys.exit(1)

    engine = create_engine(test_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[OK] Final connection check passed for '{db_name}'.")
    except Exception as exc:
        print(
            f"\n[ERROR] Could not connect to test database '{db_name}' after creation.\n"
            f"  {exc}\n",
            file=sys.stderr,
        )
        sys.exit(1)
    finally:
        engine.dispose()


def main() -> None:
    _load_env_test()
    test_url = _get_test_url()
    db_name = _assert_test_database(test_url)
    print(f"[INFO] Target test database: '{db_name}'")
    ensure_database_exists(test_url, db_name)
    verify_connection(test_url, db_name)
    print("\n[DONE] Test database is ready.")


if __name__ == "__main__":
    main()
