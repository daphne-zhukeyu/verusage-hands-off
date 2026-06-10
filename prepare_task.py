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
    prompt = f"""The file {input_name} cannot be verified by Verus, a verification tool for Rust programs, yet. Please add proof annotations to {input_name} so that it can be successfully verified by Verus, and write the resulting code with proof into a new file, {verified_name}. Please invoke Verus to check the proof annotation you added. The vstd folder in the current directory is a copy of Verus' vstd definitions and helper lemmas; please feel free to check it when needed. You should KEEP editing your proof annotations until Verus shows there is no error. You should NOT change existing functions' preconditions or post-conditions; you should NOT change any executable Rust code; and you should NEVER use admit(...) or assume(...) in your code. You are also NOT allowed to create unimplemented, external-body lemma functions--- for any new lemma functions you add, you should provide complete proof. You are NOT allowed to create new axiom functions or change the pre/post conditions of existing axiom functions, and you should NEVER add external_body tag to any existing non-external-body functions. I have installed Verus locally; you can just run Verus. Before you are done, MAKE SURE to run {checker_name} {verified_name} to double check whether you have made any illegal changes to {input_name} (fix those if you did).
"""
    (task_dir / "HANDS_OFF_PROMPT.md").write_text(prompt, encoding="utf-8")


def write_lynette_checker_wrapper(task_dir: Path, lynette_name: str) -> None:
    wrapper = f"""#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "usage: ./verus-checker <changed-file> [original-file]" >&2
  exit 2
fi

DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
CHANGED="$1"

if [ "$#" -eq 2 ]; then
  ORIGINAL="$2"
else
  CHANGED_BASENAME="$(basename "$CHANGED")"
  if [[ "$CHANGED_BASENAME" == *_verified.rs ]]; then
    ORIGINAL_BASENAME="${{CHANGED_BASENAME%_verified.rs}}.rs"
    ORIGINAL="$DIR/$ORIGINAL_BASENAME"
  else
    mapfile -t ORIGINAL_CANDIDATES < <(
      find "$DIR" -maxdepth 1 -type f -name '*.rs' ! -name '*_verified.rs' -printf '%p\\n'
    )
    if [ "${{#ORIGINAL_CANDIDATES[@]}}" -ne 1 ]; then
      echo "could not infer original file; pass it explicitly as the second argument" >&2
      exit 2
    fi
    ORIGINAL="${{ORIGINAL_CANDIDATES[0]}}"
  fi
fi

exec "$DIR/{lynette_name}" additions "$ORIGINAL" "$CHANGED"
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
        write_lynette_checker_wrapper(task_dir, lynette_name)
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
