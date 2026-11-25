"""Old SQLite builds (HostPapa Training Centre: 3.26.0) have FTS5 but not 'remove_diacritics 2' (3.27+).

Released migrations are never edited, so app/sqlite_runtime.py swaps in pysqlite3 when the system SQLite is too old.
The runtime FTS probe must also report 'not supported' on a build without the tokenizer option (LIKE fallback)."""

import sqlite3
import types

from app.services.documents.fts import fts5_supported_on
from app.sqlite_runtime import prefer_modern_sqlite


class _Old326Connection:
    def __init__(self):
        self._c = sqlite3.connect(":memory:")

    def exec_driver_sql(self, sql, *a):
        if "remove_diacritics 2" in sql:
            raise sqlite3.OperationalError("error in tokenizer constructor")
        return self._c.execute(sql)


def test_runtime_probe_rejects_a_build_without_the_tokenizer_option():
    assert fts5_supported_on(_Old326Connection()) is False


def test_nothing_changes_when_the_system_sqlite_is_new_enough():
    modules = {}
    assert prefer_modern_sqlite(modules, minimum=(3, 0, 0)) is False
    assert modules == {}


def test_nothing_changes_when_sqlite_is_old_and_pysqlite3_is_absent():
    modules = {}
    assert prefer_modern_sqlite(modules, minimum=(99, 0, 0)) is False  # pysqlite3 is not installed here
    assert modules == {}


def test_pysqlite3_replaces_sqlite3_when_the_system_one_is_older(monkeypatch):
    fake = types.ModuleType("pysqlite3")
    fake.sqlite_version_info = (3, 45, 0)
    fake.dbapi2 = types.ModuleType("pysqlite3.dbapi2")
    monkeypatch.setitem(__import__("sys").modules, "pysqlite3", fake)
    monkeypatch.setitem(__import__("sys").modules, "pysqlite3.dbapi2", fake.dbapi2)
    modules = {}
    assert prefer_modern_sqlite(modules, minimum=(3, 27, 0)) is (tuple(sqlite3.sqlite_version_info) < (3, 27, 0))
    modules = {}
    assert prefer_modern_sqlite(modules, minimum=(99, 0, 0)) is False  # fake is 3.45, below 99: not used
    assert modules == {}
