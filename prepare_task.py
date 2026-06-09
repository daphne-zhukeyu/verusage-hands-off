#!/usr/bin/env python3
"""Prepare an isolated Verus task directory for hands-off agent repair."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
from pathlib import Path


RUNTIME_FILES = [
    ".vstd-fingerprint",
    "cargo-verus",
    "libverus_builtin.rlib",
    "libverus_builtin_macros.so",
    "libverus_state_machines_macros.so",
    "libvstd.rlib",
    "rust_verify",
    "version.json",
    "version.txt",
    "verus-root",
    "vstd.vir",
    "z3",
]

RUNTIME_DIRS = [
    "builtin",
    "builtin_macros",
    "state_machines_macros",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a self-contained task folder containing X.rs, vstd, "
            "Verus, verus-checker, and a prompt for a generic coding agent."
        )
    )
    parser.add_argument("input", type=Path, help="Path to the unverified .rs file")
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Directory to create. Defaults to ./task_<input stem>",
    )
    parser.add_argument(
        "--verus",
        type=Path,
        default=Path("../verus/verus"),
        help="Path to the Verus executable. Default: ../verus/verus",
    )
    parser.add_argument(
        "--checker",
        type=Path,
        required=True,
        help="Path to the verus-checker executable or lynette binary",
    )
    parser.add_argument(
        "--checker-kind",
        choices=["verus-checker", "lynette-additions"],
        default="verus-checker",
        help=(
            "Checker interface. Use 'lynette-additions' to wrap a raw lynette "
            "binary as ./verus-checker <changed-file>."
        ),
    )
    parser.add_argument(
        "--vstd",
        type=Path,
        help="Path to vstd. Defaults to <verus executable parent>/vstd",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of symlinking Verus/vstd/checker assets",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing output directory",
    )
    return parser.parse_args()


def resolve_existing(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise SystemExit(f"{label} does not exist: {resolved}")
    return resolved


def copy_or_link(src: Path, dst: Path, copy: bool) -> None:
    if dst.exists() or dst.is_symlink():
        if dst.is_dir() and not dst.is_symlink():
            shutil.rmtree(dst)
        else:
            dst.unlink()

    if copy:
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    else:
        os.symlink(src, dst, target_is_directory=src.is_dir())


def ensure_executable(path: Path) -> None:
    if path.is_symlink():
        return
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_prompt(task_dir: Path, input_name: str, checker_name: str) -> None:
    verified_name = f"{Path(input_name).stem}_verified.rs"
    prompt = f"""The file {input_name} cannot be verified by Verus yet.

Please add proof annotations to {input_name} so that Verus verifies it, and write the result to {verified_name}.

You may inspect the vstd folder.

Run Verus until there are no errors.

Do not change preconditions or postconditions.
Do not change executable Rust code.
Do not use assume(...) or admit().
Do not add axiom, external_body, or other shortcut annotations that bypass proof obligations.

Before finishing, run:

./{checker_name} {verified_name}

The task is complete only when Verus verifies {verified_name} and verus-checker accepts it.
"""
    (task_dir / "HANDS_OFF_PROMPT.md").write_text(prompt, encoding="utf-8")


def write_lynette_checker_wrapper(task_dir: Path, input_name: str, lynette_name: str) -> None:
    wrapper = f"""#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: ./verus-checker <changed-file>" >&2
  exit 2
fi

DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
exec "$DIR/{lynette_name}" additions "$DIR/{input_name}" "$1"
"""
    wrapper_path = task_dir / "verus-checker"
    wrapper_path.write_text(wrapper, encoding="utf-8")
    ensure_executable(wrapper_path)


def main() -> None:
    args = parse_args()
    input_file = resolve_existing(args.input, "input file")
    verus = resolve_existing(args.verus, "Verus executable")
    checker = resolve_existing(args.checker, "verus-checker executable")
    vstd = resolve_existing(args.vstd or verus.parent / "vstd", "vstd directory")

    if input_file.suffix != ".rs":
        raise SystemExit(f"input file must be a .rs file: {input_file}")
    if not vstd.is_dir():
        raise SystemExit(f"vstd must be a directory: {vstd}")

    task_dir = (args.out_dir or Path(f"task_{input_file.stem}")).expanduser()
    task_dir = task_dir.resolve()
    if task_dir.exists():
        if not args.force:
            raise SystemExit(f"output directory already exists: {task_dir}")
        shutil.rmtree(task_dir)
    task_dir.mkdir(parents=True)

    shutil.copy2(input_file, task_dir / input_file.name)

    verus_name = "verus.exe" if verus.name.endswith(".exe") else "verus"
    checker_name = "verus-checker.exe" if checker.name.endswith(".exe") else "verus-checker"
    copy_or_link(verus, task_dir / verus_name, args.copy)
    if args.checker_kind == "lynette-additions":
        lynette_name = "lynette.exe" if checker.name.endswith(".exe") else "lynette"
        copy_or_link(checker, task_dir / lynette_name, args.copy)
        if checker.name.endswith(".exe"):
            raise SystemExit("lynette-additions wrapper is currently supported for WSL/Linux")
        write_lynette_checker_wrapper(task_dir, input_file.name, lynette_name)
    else:
        copy_or_link(checker, task_dir / checker_name, args.copy)
    copy_or_link(vstd, task_dir / "vstd", args.copy)

    for name in RUNTIME_FILES:
        src = verus.parent / name
        if src.exists():
            copy_or_link(src, task_dir / name, args.copy)
    for name in RUNTIME_DIRS:
        src = verus.parent / name
        if src.exists():
            copy_or_link(src, task_dir / name, args.copy)

    ensure_executable(task_dir / verus_name)
    ensure_executable(task_dir / checker_name)
    write_prompt(task_dir, input_file.name, checker_name)

    print(f"Created {task_dir}")
    print(f"Input: {task_dir / input_file.name}")
    print(f"Prompt: {task_dir / 'HANDS_OFF_PROMPT.md'}")
    print()
    print("Next:")
    print(f"  cd {task_dir}")
    print(f"  ./{verus_name} {input_file.name}")
    print(f"  ./{checker_name} {input_file.name}")
    print("  codex --ask-for-approval never --sandbox workspace-write")
    print("  paste HANDS_OFF_PROMPT.md")


if __name__ == "__main__":
    main()
