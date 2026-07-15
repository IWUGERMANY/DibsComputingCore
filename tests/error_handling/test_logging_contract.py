"""Static logging-contract tests introduced in D-EH8."""

import ast
from pathlib import Path


PACKAGE_ROOT = Path(__file__).parents[2] / "src" / "dibs_computing_core"


def python_trees():
    for path in PACKAGE_ROOT.rglob("*.py"):
        yield path, ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def test_library_contains_no_active_print_calls():
    violations = []
    for path, tree in python_trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "print":
                    violations.append(f"{path}:{node.lineno}")

    assert violations == []


def test_library_does_not_configure_global_logging():
    violations = []
    for path, tree in python_trees():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr == "basicConfig":
                violations.append(f"{path}:{node.lineno}")

    assert violations == []


def test_error_boundary_does_not_log_expected_exceptions():
    dibs_path = (
        PACKAGE_ROOT / "iso_simulator" / "dibs" / "dibs.py"
    )
    tree = ast.parse(dibs_path.read_text(encoding="utf-8-sig"))
    helper = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_run_with_error_phase"
    )

    logged_methods = {
        node.func.attr
        for node in ast.walk(helper)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert logged_methods.isdisjoint({"debug", "info", "warning", "error", "exception"})


def test_performance_logging_remains_available_but_is_flag_gated():
    dibs_source = (
        PACKAGE_ROOT / "iso_simulator" / "dibs" / "dibs.py"
    ).read_text(encoding="utf-8-sig")

    assert "DIBS_PERF_LOG" in dibs_source
    assert "def _log_perf" in dibs_source
    assert "SIM_PERF dibs phase=%s duration_s=%.4f" in dibs_source
