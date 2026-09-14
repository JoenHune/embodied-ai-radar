import importlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sqlite_runtime import SQLiteRuntimeError, ensure_sqlite_runtime, probe_runtime


class BrokenConnection:
    def __init__(self, *, corrupt_json=False, missing_fts=False):
        self.connection = sqlite3.connect(":memory:")
        self.corrupt_json = corrupt_json
        self.missing_fts = missing_fts

    def execute(self, statement, parameters=()):
        if self.corrupt_json and statement.startswith("SELECT json_group_object"):
            # Simulate an engine that accepts the operators but changes JSON
            # semantics: bool -> integer, rounded large integer, escaped key.
            damaged = {'a".x': [None, 1, 0], "large": 1.2345678901234568e29, "null": None}
            return types.SimpleNamespace(fetchone=lambda: (json.dumps(damaged),))
        if self.missing_fts and statement.startswith("CREATE VIRTUAL TABLE"):
            raise sqlite3.OperationalError("FTS5 unavailable in fixture")
        return self.connection.execute(statement, parameters)

    def close(self):
        self.connection.close()


def broken_driver(**options):
    return types.SimpleNamespace(sqlite_version="fixture", connect=lambda _: BrokenConnection(**options))


class SQLiteRuntimeTests(unittest.TestCase):
    def test_actual_selected_runtime_preserves_json_and_fts5(self):
        report = probe_runtime(sqlite3)
        self.assertTrue(report["available"], report)
        self.assertEqual(report["features"], {"json_roundtrip": True, "json_set": True, "fts5": True})

    def test_operator_presence_does_not_hide_lossy_json(self):
        report = probe_runtime(broken_driver(corrupt_json=True))
        self.assertFalse(report["available"])
        self.assertFalse(report["features"]["json_roundtrip"])
        self.assertTrue(report["features"]["fts5"])

    def test_fts5_is_required_even_when_json_passes(self):
        report = probe_runtime(broken_driver(missing_fts=True))
        self.assertFalse(report["available"])
        self.assertTrue(report["features"]["json_roundtrip"])
        self.assertFalse(report["features"]["fts5"])

    def test_good_standard_driver_never_imports_optional_package(self):
        imports = []
        registry = {}
        def importer(name):
            imports.append(name)
            if name != "sqlite3":
                self.fail("Unnecessary optional driver import")
            return sqlite3
        report = ensure_sqlite_runtime(importer, registry)
        self.assertEqual(imports, ["sqlite3"])
        self.assertEqual(registry, {})
        self.assertEqual(report["driver"], "sqlite3")

    def test_failed_standard_probe_selects_only_a_verified_replacement(self):
        old = broken_driver(corrupt_json=True)
        dbapi = importlib.import_module("sqlite3.dbapi2")
        modules = {"sqlite3": old, "pysqlite3": sqlite3, "pysqlite3.dbapi2": dbapi}
        registry = {"sqlite3": old}
        report = ensure_sqlite_runtime(modules.__getitem__, registry)
        self.assertEqual(report["driver"], "pysqlite3")
        self.assertIs(registry["sqlite3"], sqlite3)
        self.assertIs(registry["sqlite3.dbapi2"], dbapi)
        # Test injection must not replace the test process's global module.
        self.assertIs(sys.modules["sqlite3"], sqlite3)

    def test_bad_optional_driver_leaves_module_registry_unchanged(self):
        old = broken_driver(corrupt_json=True)
        bad = broken_driver(missing_fts=True)
        registry = {"sqlite3": old}
        with self.assertRaises(SQLiteRuntimeError):
            ensure_sqlite_runtime({"sqlite3": old, "pysqlite3": bad}.__getitem__, registry)
        self.assertEqual(registry, {"sqlite3": old})

    def test_missing_optional_package_fails_closed_with_actionable_message(self):
        old = broken_driver(corrupt_json=True)
        def importer(name):
            if name == "sqlite3":
                return old
            raise ImportError("fixture error detail must not be printed")
        with self.assertRaisesRegex(SQLiteRuntimeError, "requirements-v3.txt") as caught:
            ensure_sqlite_runtime(importer, {})
        self.assertNotIn("fixture error detail", str(caught.exception))

    def test_dependency_is_pinned_and_only_installed_for_linux_wheel_platform(self):
        requirement = next(line for line in (ROOT / "requirements-v3.txt").read_text().splitlines()
                           if line.startswith("pysqlite3-binary"))
        self.assertIn("pysqlite3-binary==0.5.4.post2", requirement)
        self.assertIn('sys_platform == "linux"', requirement)
        self.assertIn('platform_machine == "x86_64"', requirement)


@unittest.skipUnless(shutil.which("node"), "The project Node launcher is unavailable")
class PythonLauncherTests(unittest.TestCase):
    def launch(self, *arguments, input=None):
        env = {**os.environ, "V3_PYTHON": sys.executable}
        return subprocess.run([shutil.which("node"), str(ROOT / "scripts/run-python.mjs"), *arguments],
                              input=input, text=True, capture_output=True, cwd=ROOT, env=env, timeout=30)

    def test_command_mode_preserves_arguments_and_native_interpreter_flag(self):
        result = self.launch("-B", "-c", "import json,sys,sqlite3;print(json.dumps([sys.argv,sys.flags.dont_write_bytecode,sqlite3.sqlite_version]))", "alpha", "--target-option")
        self.assertEqual(result.returncode, 0, result.stderr)
        args, no_bytecode, version = json.loads(result.stdout)
        self.assertEqual(args, ["-c", "alpha", "--target-option"])
        self.assertEqual(no_bytecode, 1)
        self.assertTrue(version)

    def test_module_mode_keeps_stdin_and_standard_module_behavior(self):
        result = self.launch("-m", "json.tool", input='{"answer":42}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"answer": 42})

    def test_stdin_mode_preserves_arguments(self):
        result = self.launch("-", "alpha", input="import json,sys;print(json.dumps(sys.argv))")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ["-", "alpha"])

    def test_script_mode_retains_sibling_imports_and_target_arguments(self):
        with tempfile.TemporaryDirectory(prefix="radar-runtime-test-") as temporary:
            directory = Path(temporary)
            (directory / "sibling.py").write_text("VALUE = 42\n")
            script = directory / "entry.py"
            script.write_text("import json,sys,sqlite3,sibling\nprint(json.dumps([sys.argv,sibling.VALUE,sqlite3.sqlite_version]))\n")
            result = self.launch("-B", str(script), "-m", "target-argument")
            self.assertEqual(result.returncode, 0, result.stderr)
            args, value, version = json.loads(result.stdout)
            self.assertEqual(args, [str(script), "-m", "target-argument"])
            self.assertEqual(value, 42)
            self.assertTrue(version)
            self.assertFalse((directory / "__pycache__").exists())

    def test_exit_status_is_not_replaced_by_launcher_success(self):
        self.assertEqual(self.launch("-c", "raise SystemExit(7)").returncode, 7)

    def test_python_version_switch_remains_native(self):
        result = self.launch("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("Python "))


if __name__ == "__main__":
    unittest.main()
