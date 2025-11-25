#!/usr/bin/env python3
"""Convenience wrapper to generate ~2000 examples per intent from the latest specs.

This script simply forwards the arguments to ``Chatbot/tools/generate_nlu.py``
with sensible defaults so you do not have to remember the long command. By
default it will:

- read specs from ``Chatbot/data/specs``
- create ``Chatbot/data/generated/nlu_generated.yml``
- request ``2000`` examples per intent

Optionally, pass ``--update-nlu`` to overwrite ``Chatbot/data/nlu.yml`` with the
resulting dataset after it is generated.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def resolve_path(root: Path, value: Path | None, default_relative: str) -> Path:
    """Resolve a user argument to an absolute path inside the repo."""

    if value is None:
        return (root / default_relative).resolve()
    if value.is_absolute():
        return value
    return (root / value).resolve()


def parse_args(root: Path) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a large NLU dataset from specs.")
    parser.add_argument(
        "--spec-dir",
        type=Path,
        default=None,
        help="Directory with *.yml specs (default: Chatbot/data/specs).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination NLU file (default: Chatbot/data/generated/nlu_generated.yml).",
    )
    parser.add_argument(
        "--per-intent",
        type=int,
        default=2000,
        help="Number of examples to request per intent (default: 2000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1337,
        help="Seed forwarded to the generator (default: 1337).",
    )
    parser.add_argument(
        "--min-ratio",
        type=float,
        default=0.5,
        help="Minimum ratio forwarded to the generator (default: 0.5).",
    )
    parser.add_argument(
        "--python-bin",
        type=str,
        default=sys.executable,
        help="Python interpreter to run the generator (default: current python).",
    )
    parser.add_argument(
        "--update-nlu",
        action="store_true",
        help="Copy the generated file over Chatbot/data/nlu.yml once finished.",
    )

    args = parser.parse_args()
    args.spec_dir = resolve_path(root, args.spec_dir, "Chatbot/data/specs")
    args.output = resolve_path(root, args.output, "Chatbot/data/generated/nlu_generated.yml")
    return args


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    generator = repo_root / "Chatbot" / "tools" / "generate_nlu.py"
    if not generator.exists():
        print(f"[x] No se encontro el script base en {generator}", file=sys.stderr)
        return 1

    args = parse_args(repo_root)

    command = [
        args.python_bin,
        str(generator),
        "--spec-dir",
        str(args.spec_dir),
        "--output",
        str(args.output),
        "--per-intent",
        str(args.per_intent),
        "--seed",
        str(args.seed),
        "--min-ratio",
        str(args.min_ratio),
    ]

    print("[i] Generando dataset NLU...", flush=True)
    print("    ", " ".join(command), flush=True)
    subprocess.run(command, check=True, cwd=repo_root / "Chatbot")

    if args.update_nlu:
        target = repo_root / "Chatbot" / "data" / "nlu.yml"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.output, target)
        print(f"[✓] data/nlu.yml actualizado con {args.output}", flush=True)
    else:
        print(f"[✓] Dataset listo en {args.output}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
