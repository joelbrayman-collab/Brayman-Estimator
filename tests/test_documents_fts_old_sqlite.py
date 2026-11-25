"""Old SQLite builds (HostPapa Training Centre: 3.26.0) have FTS5 but not 'remove_diacritics 2' (3.27+).
The probe must report 'not supported' there so the migration and the app use the LIKE fallback instead of failing."""

import importlib.util
import pathlib
import sqlite3

import pytest

from app.services.documents.fts import fts5_supported_on


class _Old326Connection:
    """Behaves like SQLite 3.26: FTS5 works, but the tokenizer option is rejected."""

    def __init__(self):
        self._c = sqlite3.connect(":memory:")

    def exec_driver_sql(self, sql, *a):
        if "remove_diacritics 2" in sql:
            raise sqlite3.OperationalError("error in tokenizer constructor")
        return self._c.execute(sql)


def _migration():
    path = pathlib.Path(__file__).resolve().parents[1] / "migrations/versions/t7a8b9c0d1e2_documents_and_equipment.py"
    spec = importlib.util.spec_from_file_location("t7_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_probe_rejects_a_build_without_the_tokenizer_option():
    assert fts5_supported_on(_Old326Connection()) is False


def test_migration_probe_rejects_a_build_without_the_tokenizer_option():
    assert _migration()._fts5_available(_Old326Connection()) is False


def test_probes_accept_this_build_when_it_supports_the_tokenizer():
    conn = sqlite3.connect(":memory:")

    class _C:
        def exec_driver_sql(self, sql, *a):
            return conn.execute(sql)

    if tuple(int(x) for x in sqlite3.sqlite_version.split(".")) < (3, 27, 0):
        pytest.skip("this SQLite is older than 3.27")
    assert fts5_supported_on(_C()) is True
    assert _migration()._fts5_available(_C()) is True
