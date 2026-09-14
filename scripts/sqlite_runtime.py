"""Process-local SQLite selection for the repository's Python launcher.

Prefer the standard library. Only a failed JSON/FTS5 capability probe permits
the optional, pinned pysqlite3-binary dependency to replace sqlite3 in this
one process, before application imports. No installation, UDF, SQL rewrite,
database connection override, or user/global Python customization occurs.
"""
from __future__ import annotations

import importlib
import json
import os
import runpy
import sys
import types


class SQLiteRuntimeError(RuntimeError):
    """Neither available driver satisfies the unmodified database contract."""


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def probe_runtime(driver):
    """Probe actual SQL behavior, not just the reported SQLite version."""
    features = {"json_roundtrip": False, "json_set": False, "fts5": False}
    connection = None
    try:
        connection = driver.connect(":memory:")
        # Same contract as sqlite_catalog_fidelity._probe_json, intentionally
        # duplicated here so no business module imports sqlite3 too early.
        value = {"a\".x": [None, True, False],
                 "large": 123456789012345678901234567890, "null": None}
        original = _canonical(value)
        try:
            restored = connection.execute(
                "SELECT json_group_object(key,json(? -> fullkey)) FROM json_each(?)",
                (original, original),
            ).fetchone()[0]
            features["json_roundtrip"] = _canonical(json.loads(restored)) == original
            updated = connection.execute(
                "SELECT json_set(?, '$.extra', json('[true,false,null]'))", (original,),
            ).fetchone()[0]
            features["json_set"] = _canonical(json.loads(updated)) == _canonical(
                {**value, "extra": [True, False, None]})
        except Exception:
            pass
        try:
            connection.execute("CREATE VIRTUAL TABLE runtime_fts USING fts5(body)")
            connection.execute("INSERT INTO runtime_fts(body) VALUES ('robot evidence')")
            features["fts5"] = connection.execute(
                "SELECT count(*) FROM runtime_fts WHERE runtime_fts MATCH 'robot'",
            ).fetchone()[0] == 1
        except Exception:
            pass
    except Exception:
        pass
    finally:
        if connection is not None:
            connection.close()
    return {"sqlite_version": getattr(driver, "sqlite_version", "unknown"),
            "features": features, "available": all(features.values())}


def ensure_sqlite_runtime(importer=None, module_registry=None):
    """Select an adequate driver before executing any repository code."""
    importer = importer or importlib.import_module
    module_registry = sys.modules if module_registry is None else module_registry
    standard = importer("sqlite3")
    report = probe_runtime(standard)
    if report["available"]:
        return {"driver": "sqlite3", **report}
    try:
        replacement = importer("pysqlite3")
        replacement_report = probe_runtime(replacement)
        if replacement_report["available"]:
            dbapi = importer("pysqlite3.dbapi2")
            module_registry["sqlite3"] = replacement
            module_registry["sqlite3.dbapi2"] = dbapi
            return {"driver": "pysqlite3", **replacement_report}
    except ImportError:
        pass
    raise SQLiteRuntimeError(
        "SQLite runtime lacks required lossless JSON and FTS5 features. "
        "Install requirements-v3.txt in the selected project Python environment "
        "(Linux x86_64), or use a Python runtime whose SQLite passes the feature probe. "
        "The database schema and fidelity checks have not been weakened.")


def _target_import_path(entry):
    bootstrap_directory = os.path.dirname(os.path.abspath(__file__))
    if sys.path and os.path.abspath(sys.path[0]) == bootstrap_directory:
        sys.path.pop(0)
    if not getattr(sys.flags, "safe_path", False):
        sys.path.insert(0, entry)


def _execute_text(source, filename, arguments):
    sys.argv = ["-c" if filename == "<string>" else "-", *arguments]
    _target_import_path("")
    module = types.ModuleType("__main__")
    if filename == "<stdin>":
        module.__file__ = filename
    sys.modules["__main__"] = module
    exec(compile(source, filename, "exec"), module.__dict__)


def main(arguments=None):
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    if arguments[:1] == ["--"]:
        arguments.pop(0)
    if arguments[:1] == ["--"]:
        arguments.pop(0)  # Python's explicit end-of-options before a file.
    if not arguments:
        raise SystemExit("A Python script, -m module, -c command, or - stdin is required.")
    try:
        ensure_sqlite_runtime()
    except SQLiteRuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    target, *rest = arguments
    if target in {"-c", "-m"} and not rest:
        raise SystemExit(f"{target} requires an argument")
    if target == "-c":
        _execute_text(rest[0], "<string>", rest[1:])
    elif target == "-":
        _execute_text(sys.stdin.read(), "<stdin>", rest)
    elif target == "-m":
        _target_import_path(os.getcwd())
        sys.argv = [rest[0], *rest[1:]]
        runpy.run_module(rest[0], run_name="__main__", alter_sys=True)
    else:
        _target_import_path(os.path.dirname(os.path.abspath(target)))
        sys.argv = [target, *rest]
        runpy.run_path(target, run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
