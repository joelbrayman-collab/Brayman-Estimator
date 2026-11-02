"""Tests only: two caches that make the suite faster without changing what any test sees (faster gate, 2 Nov 2026).

1. Password checks. Every test that uses the HTTP client signs the office user in, and app.services.auth checks the
   password with Werkzeug's PBKDF2-SHA256 (1,000,000 iterations, about 0.3-0.7 s). check_password_hash is a pure
   function of (stored hash, password), so its result is memoised per exact pair: the same hash and password always
   give the same answer, a wrong password or a changed hash is a different pair and is checked for real. The office
   test user's own hash is made once per process by the real hash_password (tests/auth_fixtures.py), so it is a
   genuine pbkdf2:sha256 hash with the production parameters; only the salt is shared between test databases.

2. Schema. Most tests build a new app on ``sqlite:///:memory:`` and call ``db.create_all()``, which
issues ~1,000 DDL statements (234 tables, their indexes, the insert-only audit triggers and the FTS5 search table)
and costs about 0.45 s each time. The first such call in a test process runs the real ``create_all()`` and keeps a
byte-for-byte copy of the resulting, still empty database (SQLite online backup). Later calls on another fresh,
empty in-memory database restore that copy (about 5 ms), so every test still starts from exactly the database
``create_all()`` builds, with no rows.

The fast path is taken only when all of these hold, otherwise the real ``create_all()`` runs unchanged:
  * every bind (the default database only) is an in-memory SQLite engine on one shared connection (StaticPool);
  * the target database is completely empty (no table, index, trigger or view) and has no open transaction;
  * the model metadata is identical to the one the copy was made from (table, column, type, index, constraint and
    DDL-listener fingerprint), so a test that adds a table gets a fresh real ``create_all()``.
Set CALIBRAYTAI_TEST_CACHES=0 to turn both caches off (real create_all, real password hash and check every time).
"""

from __future__ import annotations

import functools
import os
import sqlite3
import types

from sqlalchemy.pool import StaticPool

ENV = "CALIBRAYTAI_TEST_CACHES"
_TEMPLATES: dict = {}
STATS = {"real": 0, "copied": 0}
_PASSWORD_HASHES: dict = {}


def enabled() -> bool:
    return os.environ.get(ENV, "1").strip() != "0"


def install_password_check_cache() -> None:
    """Memoise app.services.auth's check_password_hash per exact (hash, password) pair (tests only)."""
    from app.services import auth

    if not enabled() or getattr(auth.check_password_hash, "_test_memo", False):
        return
    memo = functools.lru_cache(maxsize=4096)(auth.check_password_hash)
    memo._test_memo = True
    auth.check_password_hash = memo


def office_password_hash(password: str) -> str:
    """A real hash_password() result, made once per password per process (test users only)."""
    from app.services.auth import hash_password

    if not enabled():
        return hash_password(password)
    if password not in _PASSWORD_HASHES:
        _PASSWORD_HASHES[password] = hash_password(password)
    return _PASSWORD_HASHES[password]


def _metadata_fingerprint(metadata) -> tuple:
    tables = []
    for table in metadata.sorted_tables:
        columns = tuple(
            (c.name, repr(c.type), c.nullable, c.primary_key, repr(c.server_default), bool(c.foreign_keys))
            for c in table.columns
        )
        indexes = tuple(sorted((i.name or "", tuple(col.name for col in i.columns), bool(i.unique))
                               for i in table.indexes))
        constraints = tuple(sorted(type(c).__name__ + ":" + str(c.name or "") for c in table.constraints))
        listeners = tuple(sorted(
            repr(fn) for name in ("before_create", "after_create")
            for fn in getattr(table.dispatch, name)))
        tables.append((table.name, columns, indexes, constraints, listeners))
    return (sqlite3.sqlite_version, tuple(tables))


def _in_memory_static(engine) -> bool:
    url = engine.url
    return (url.get_backend_name() == "sqlite" and url.database in (None, "", ":memory:")
            and isinstance(engine.pool, StaticPool))


def _empty_raw_connection(engine):
    """The engine's single DBAPI connection when its database is empty and idle; else None."""
    with engine.connect() as connection:
        raw = connection.connection.driver_connection
        if not isinstance(raw, sqlite3.Connection) or raw.in_transaction:
            return None
        if raw.execute("SELECT count(*) FROM sqlite_master").fetchone()[0] != 0:
            return None
        return raw


def install_schema_cache(db) -> None:
    """Wrap ``db.create_all`` on this Flask-SQLAlchemy instance (tests only)."""
    if not enabled() or getattr(db, "_schema_cache_installed", False):
        return
    real_create_all = db.create_all

    def create_all(self, bind_key="__all__"):
        if bind_key != "__all__" or list(self.metadatas) != [None]:
            STATS["real"] += 1
            return real_create_all(bind_key)
        engine = self.engines[None]
        if not _in_memory_static(engine):
            STATS["real"] += 1
            return real_create_all(bind_key)
        raw = _empty_raw_connection(engine)
        if raw is None:
            STATS["real"] += 1
            return real_create_all(bind_key)
        key = _metadata_fingerprint(self.metadatas[None])
        template = _TEMPLATES.get(key)
        if template is not None:
            template.backup(raw)
            STATS["copied"] += 1
            return None
        real_create_all(bind_key)
        STATS["real"] += 1
        copy = sqlite3.connect(":memory:", check_same_thread=False)
        raw.backup(copy)
        _TEMPLATES[key] = copy
        return None

    db.create_all = types.MethodType(create_all, db)
    db._schema_cache_installed = True
