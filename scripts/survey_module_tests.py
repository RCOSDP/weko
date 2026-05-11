#!/usr/bin/env python3
"""Run module tox commands and write a reusable status report."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_ci_test_inventory import WORKFLOW_PATH, parse_unit_test_matrix

DEFAULT_JSON = ROOT / "docs" / "ci_test_status.json"
DEFAULT_MD = ROOT / "docs" / "ci_test_status.md"
COMPOSE_FILE = ROOT / "docker-compose2.yml"
DEFAULT_WORKSPACE_ROOT = ROOT / ".codex_tmp" / "weko-module-survey-workspace"


@dataclass
class ModuleResult:
    module: str
    status: str
    exit_code: int | None
    duration_seconds: float
    command: str
    summary: str


def prepare_workspace(workspace_root: Path) -> Path:
    modules_src = ROOT / "modules"
    modules_dst = workspace_root / "modules"

    shutil.rmtree(workspace_root, ignore_errors=True)
    modules_dst.mkdir(parents=True, exist_ok=True)

    for module_dir in sorted(modules_src.iterdir()):
        if not module_dir.is_dir():
            continue
        shutil.copytree(
            module_dir,
            modules_dst / module_dir.name,
            ignore=shutil.ignore_patterns("__pycache__", ".tox"),
        )

    for root, dirs, files in os.walk(workspace_root):
        os.chmod(root, 0o777)
        for dirname in dirs:
            os.chmod(Path(root) / dirname, 0o777)
        for filename in files:
            os.chmod(Path(root) / filename, 0o666)

    return workspace_root


def container_path(path: Path) -> str:
    return str(path.resolve()).replace(str(ROOT), "/code", 1)


def build_command(module: str, tox_env: str | None, workspace_root: Path) -> List[str]:
    tox_cmd = ["tox"]
    if tox_env:
        tox_cmd.extend(["-e", tox_env])

    inner = (
        "if ! python -m pip show tox >/dev/null 2>&1; then "
        "python -m pip install --user --upgrade pip && "
        "python -m pip install --user tox tox-setuptools-version pytest-timeout; "
        "fi && "
        "cd {workspace_root}/modules/{module} && "
        "{command}"
    ).format(
        workspace_root=container_path(workspace_root),
        module=module,
        command=" ".join(tox_cmd),
    )
    return [
        "docker",
        "compose",
        "-f",
        str(COMPOSE_FILE),
        "exec",
        "-T",
        "web",
        "bash",
        "-lc",
        inner,
    ]


def short_summary(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return "No output captured."
    return lines[-1][:400]


def ensure_text(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def run_module(
    module: str,
    tox_env: str | None,
    timeout_seconds: int,
    workspace_root: Path,
) -> ModuleResult:
    command = build_command(module, tox_env, workspace_root)
    started = time.monotonic()

    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        duration = time.monotonic() - started
        combined_output = "\n".join(
            part for part in (completed.stdout, completed.stderr) if part
        )
        status = "passed" if completed.returncode == 0 else "failed"
        return ModuleResult(
            module=module,
            status=status,
            exit_code=completed.returncode,
            duration_seconds=round(duration, 2),
            command=" ".join(command),
            summary=short_summary(combined_output),
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        output_parts = []
        if exc.stdout:
            output_parts.append(ensure_text(exc.stdout))
        if exc.stderr:
            output_parts.append(ensure_text(exc.stderr))
        return ModuleResult(
            module=module,
            status="timeout",
            exit_code=None,
            duration_seconds=round(duration, 2),
            command=" ".join(command),
            summary=short_summary("\n".join(output_parts)),
        )


def write_json(path: Path, results: Sequence[ModuleResult]) -> None:
    payload = {
        "generated_at_epoch": int(time.time()),
        "module_count": len(results),
        "passed": sum(result.status == "passed" for result in results),
        "failed": sum(result.status == "failed" for result in results),
        "timeout": sum(result.status == "timeout" for result in results),
        "results": [asdict(result) for result in results],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, results: Sequence[ModuleResult], tox_env: str | None) -> None:
    lines = [
        "# CI Test Status",
        "",
        "<!-- This file is generated by `python3 scripts/survey_module_tests.py`. -->",
        "",
        "This page records the latest module-by-module tox execution survey against the running WEKO Docker environment.",
        "",
        "## Summary",
        "",
        f"- Modules surveyed: {len(results)}",
        f"- Passed: {sum(result.status == 'passed' for result in results)}",
        f"- Failed: {sum(result.status == 'failed' for result in results)}",
        f"- Timed out: {sum(result.status == 'timeout' for result in results)}",
        f"- Tox environment: `{tox_env}`" if tox_env else "- Tox environment: default",
        "",
        "## Module Results",
        "",
        "| Module | Status | Exit Code | Duration (s) | Summary |",
        "|--------|--------|-----------|--------------|---------|",
    ]

    for result in results:
        exit_code = "" if result.exit_code is None else str(result.exit_code)
        summary = result.summary.replace("|", "\\|")
        lines.append(
            f"| {result.module} | {result.status} | {exit_code} | {result.duration_seconds} | {summary} |"
        )

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--module",
        action="append",
        dest="modules",
        help="Run only the specified module. Can be passed multiple times.",
    )
    parser.add_argument(
        "--tox-env",
        default=None,
        help="Optional tox env name, for example c1.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=1800,
        help="Per-module timeout in seconds.",
    )
    parser.add_argument(
        "--json-output",
        default=str(DEFAULT_JSON),
        help="Path for machine-readable output.",
    )
    parser.add_argument(
        "--markdown-output",
        default=str(DEFAULT_MD),
        help="Path for Markdown summary output.",
    )
    parser.add_argument(
        "--workspace-root",
        default=str(DEFAULT_WORKSPACE_ROOT),
        help="Writable temp directory used to stage the module workspace for tox.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    modules = args.modules or parse_unit_test_matrix(WORKFLOW_PATH)
    workspace_base = Path(args.workspace_root)
    workspace_root = prepare_workspace(
        workspace_base.parent
        / f"{workspace_base.name}-{int(time.time())}-{os.getpid()}"
    )
    results = [
        run_module(module, args.tox_env, args.timeout_seconds, workspace_root)
        for module in modules
    ]

    json_path = Path(args.json_output)
    markdown_path = Path(args.markdown_output)
    write_json(json_path, results)
    write_markdown(markdown_path, results, args.tox_env)
    print(f"Generated {json_path.relative_to(ROOT)}")
    print(f"Generated {markdown_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
