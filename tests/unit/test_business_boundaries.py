"""Prevent framework dependencies from returning to business modules."""
import ast
from pathlib import Path
import subprocess
import sys


def test_domain_and_services_import_only_business_dependencies():
    root = Path(__file__).resolve().parents[2] / "app"
    forbidden = ("fastapi", "pydantic", "sqlalchemy", "app.models", "app.schemas",
                 "app.repositories", "app.api", "app.db", "app.core.config", "app.core.security")
    for folder in (root / "domain", root / "services"):
        for path in folder.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                modules = [alias.name for alias in node.names] if isinstance(node, ast.Import) else (
                    [node.module or ""] if isinstance(node, ast.ImportFrom) else []
                )
                assert not any(module == prefix or module.startswith(prefix + ".")
                               for module in modules for prefix in forbidden), path


def test_services_import_without_loading_frameworks_or_settings():
    code = """
import importlib, sys
for name in ('auth', 'booking', 'movie', 'showtime', 'seat_hold', 'payment'):
    importlib.import_module('app.services.' + name + '_service')
for name in ('fastapi', 'pydantic', 'sqlalchemy', 'app.core.config', 'app.core.security'):
    assert name not in sys.modules, name
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
