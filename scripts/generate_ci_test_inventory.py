#!/usr/bin/env python3
"""Generate a compact CI test inventory for WEKO modules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Set


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "unit-tests.yml"
RUN_TESTS_PATH = ROOT / "run-tests.sh"
OUTPUT = ROOT / "docs" / "ci_test_inventory.md"

MODULE_NAME_RE = re.compile(r"^\s*-\s+([A-Za-z0-9_-]+)\s*$")
RUN_TESTS_PREFIX_RE = re.compile(r"^\s*if \[\[ \$\{module_path\} =~ \^modules/\(([^)]+)\)\.\+\$ \]\]")
SUPPORTED_PREFIXES = ("invenio-", "weko-")


@dataclass(frozen=True)
class ModuleRecord:
    """Aggregated test-related metadata for a module."""

    name: str
    has_tox: bool
    has_tests: bool
    in_unit_matrix: bool
    in_run_tests: bool

    @property
    def status(self) -> str:
        if self.in_unit_matrix and self.has_tox and self.has_tests:
            return "covered-by-unit-ci"
        if self.in_unit_matrix and self.has_tox and not self.has_tests:
            return "matrix-entry-without-tests"
        if self.has_tox and self.has_tests and not self.in_unit_matrix:
            return "missing-from-unit-ci"
        if self.has_tests and not self.has_tox:
            return "tests-without-tox"
        if self.has_tox and not self.has_tests:
            return "tox-without-tests"
        if self.in_run_tests and not self.in_unit_matrix:
            return "run-tests-only"
        return "out-of-scope"

    @property
    def note(self) -> str:
        if self.status == "covered-by-unit-ci":
            return "Included in the current unit-test workflow matrix."
        if self.status == "matrix-entry-without-tests":
            return "CI matrix should explicitly justify this module or remove it from unit scope."
        if self.status == "missing-from-unit-ci":
            return "Has tox and tests but is not listed in the current unit-test workflow."
        if self.status == "tests-without-tox":
            return "Has tests but no tox.ini, so CI standardization is incomplete."
        if self.status == "tox-without-tests":
            return "Has tox.ini but no tests/ directory."
        if self.status == "run-tests-only":
            return "Covered by run-tests.sh style discovery but not by the unit-test matrix."
        return "No current unit-test signal detected."


def relpath(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def parse_unit_test_matrix(path: Path) -> List[str]:
    modules: List[str] = []
    in_module_block = False

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "module:":
            in_module_block = True
            continue

        if not in_module_block:
            continue

        match = MODULE_NAME_RE.match(line)
        if match:
            modules.append(match.group(1))
            continue

        # Leave the block once indentation returns to a new key under matrix/strategy.
        if line.strip() and not line.startswith(" " * 10):
            break

    return modules


def parse_run_tests_prefixes(path: Path) -> Sequence[str]:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = RUN_TESTS_PREFIX_RE.match(line)
        if not match:
            continue
        return [part.strip() for part in match.group(1).split("|") if part.strip()]
    raise RuntimeError("Could not determine module prefixes from run-tests.sh")


def discover_modules() -> Set[str]:
    return {
        module_dir.name
        for module_dir in sorted((ROOT / "modules").iterdir())
        if module_dir.is_dir() and module_dir.name.startswith(SUPPORTED_PREFIXES)
    }


def modules_with_tox() -> Set[str]:
    return {
        path.parent.name
        for path in sorted((ROOT / "modules").glob("*/tox.ini"))
    }


def modules_with_tests() -> Set[str]:
    return {
        path.parent.name
        for path in sorted((ROOT / "modules").glob("*/tests"))
        if path.is_dir()
    }


def modules_in_run_tests(prefixes: Iterable[str], tests_modules: Set[str]) -> Set[str]:
    prefix_tuple = tuple(prefixes)
    return {name for name in tests_modules if name.startswith(prefix_tuple)}


def build_records() -> List[ModuleRecord]:
    all_modules = discover_modules()
    tox_modules = modules_with_tox()
    test_modules = modules_with_tests()
    unit_matrix_modules = set(parse_unit_test_matrix(WORKFLOW_PATH))
    run_test_modules = modules_in_run_tests(parse_run_tests_prefixes(RUN_TESTS_PATH), test_modules)

    return [
        ModuleRecord(
            name=module_name,
            has_tox=module_name in tox_modules,
            has_tests=module_name in test_modules,
            in_unit_matrix=module_name in unit_matrix_modules,
            in_run_tests=module_name in run_test_modules,
        )
        for module_name in sorted(all_modules)
    ]


def render_summary(records: Sequence[ModuleRecord]) -> List[str]:
    covered = [record for record in records if record.status == "covered-by-unit-ci"]
    missing = [record for record in records if record.status == "missing-from-unit-ci"]
    matrix_without_tests = [record for record in records if record.status == "matrix-entry-without-tests"]
    tox_without_tests = [record for record in records if record.status == "tox-without-tests"]
    tests_without_tox = [record for record in records if record.status == "tests-without-tox"]

    return [
        "## Summary",
        "",
        f"- Total modules under `modules/`: {len(records)}",
        f"- Modules with `tox.ini`: {sum(record.has_tox for record in records)}",
        f"- Modules with `tests/`: {sum(record.has_tests for record in records)}",
        f"- Modules in `.github/workflows/unit-tests.yml`: {sum(record.in_unit_matrix for record in records)}",
        f"- Modules selected by `run-tests.sh`: {sum(record.in_run_tests for record in records)}",
        f"- Unit CI covered modules (`tox.ini` + `tests/` + matrix entry): {len(covered)}",
        f"- Missing from unit CI despite `tox.ini` + `tests/`: {len(missing)}",
        f"- Matrix entries without `tests/`: {len(matrix_without_tests)}",
        f"- `tox.ini` without `tests/`: {len(tox_without_tests)}",
        f"- `tests/` without `tox.ini`: {len(tests_without_tox)}",
        "",
    ]


def render_named_section(title: str, records: Sequence[ModuleRecord]) -> List[str]:
    lines = [f"## {title}", ""]
    if not records:
        lines.extend(["- None", ""])
        return lines

    for record in records:
        lines.append(f"- `{record.name}`: {record.note}")
    lines.append("")
    return lines


def render_table(records: Sequence[ModuleRecord]) -> List[str]:
    lines = [
        "## Module Inventory",
        "",
        "| Module | tox.ini | tests/ | unit matrix | run-tests.sh | status |",
        "|--------|---------|--------|-------------|--------------|--------|",
    ]

    for record in records:
        lines.append(
            "| {name} | {has_tox} | {has_tests} | {in_unit_matrix} | {in_run_tests} | {status} |".format(
                name=record.name,
                has_tox="yes" if record.has_tox else "no",
                has_tests="yes" if record.has_tests else "no",
                in_unit_matrix="yes" if record.in_unit_matrix else "no",
                in_run_tests="yes" if record.in_run_tests else "no",
                status=record.status,
            )
        )

    lines.append("")
    return lines


def generate() -> None:
    records = build_records()
    missing = [record for record in records if record.status == "missing-from-unit-ci"]
    matrix_without_tests = [record for record in records if record.status == "matrix-entry-without-tests"]
    tests_without_tox = [record for record in records if record.status == "tests-without-tox"]

    lines: List[str] = [
        "# CI Test Inventory",
        "",
        "<!-- This file is generated by `python3 scripts/generate_ci_test_inventory.py`. -->",
        "",
        "This page compares the current unit-test workflow matrix with actual module test assets.",
        "Use it as the starting point when deciding what should run in CI and what still needs cleanup.",
        "",
    ]
    lines.extend(render_summary(records))
    lines.extend(render_named_section("Modules Missing From The Unit-Test Matrix", missing))
    lines.extend(render_named_section("Matrix Entries Without tests/", matrix_without_tests))
    lines.extend(render_named_section("Modules With tests/ But No tox.ini", tests_without_tox))
    lines.extend(render_table(records))

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {relpath(OUTPUT)}")


if __name__ == "__main__":
    generate()
