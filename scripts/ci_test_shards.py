#!/usr/bin/env python3
"""Compute deterministic module shards for CI test execution."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SUPPORTED_PREFIXES = ("invenio-", "weko-")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, required=True)
    return parser.parse_args()


def discover_modules() -> List[str]:
    modules_root = ROOT / "modules"
    return sorted(
        module_dir.name
        for module_dir in modules_root.iterdir()
        if module_dir.is_dir()
        and module_dir.name.startswith(SUPPORTED_PREFIXES)
        and (module_dir / "tests").is_dir()
    )


def shard_modules(modules: List[str], shard_index: int, shard_count: int) -> List[str]:
    if shard_count <= 0:
        raise ValueError("shard-count must be positive")
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError("shard-index must be within the shard-count range")
    return modules[shard_index::shard_count]


def main() -> None:
    args = parse_args()
    modules = discover_modules()
    print(" ".join(shard_modules(modules, args.shard_index, args.shard_count)))


if __name__ == "__main__":
    main()
