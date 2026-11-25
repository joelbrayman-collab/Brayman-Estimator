"""Use a modern SQLite where the operating system's is too old (25 Nov 2026).

The HostPapa Training Centre's Python is linked to SQLite 3.26.0. The released documents migration creates its
search table with the FTS5 tokenizer option ``remove_diacritics 2`` (SQLite 3.27+), so on 3.26 it failed. Released
migration files are never edited, so the older SQLite is replaced instead: when the interpreter's SQLite is older than
3.27 and the ``pysqlite3`` package (the training server installs ``pysqlite3-binary``) is present, it stands in for the
standard ``sqlite3`` module. Render (Production) and the office Mac already have a newer SQLite, so nothing changes there.
"""

from __future__ import annotations

import sys

MINIMUM = (3, 27, 0)


def prefer_modern_sqlite(modules=None, minimum=MINIMUM) -> bool:
    """Swap in pysqlite3 when the built-in SQLite is older than ``minimum``. Returns True when it did."""
    modules = sys.modules if modules is None else modules
    try:
        import sqlite3 as builtin
    except ImportError:  # pragma: no cover
        return False
    if tuple(builtin.sqlite_version_info) >= tuple(minimum):
        return False
    try:
        import pysqlite3
        import pysqlite3.dbapi2
    except ImportError:
        return False
    if tuple(pysqlite3.sqlite_version_info) < tuple(minimum):
        return False
    modules["sqlite3"] = pysqlite3
    modules["sqlite3.dbapi2"] = pysqlite3.dbapi2
    return True
