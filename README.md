# Hands-Off Verus Repair

This directory supports the hands-off approach: give a generic coding agent one isolated task directory containing only the task file, Verus, vstd, and verus-checker, then let the agent independently produce `X_verified.rs`.

This is intentionally separate from VeruSAGE. Do not run `verusage/main.py` for this flow.

## Directory Shape

Each prepared task directory should look like this:

```text
task_X/
  X.rs
  HANDS_OFF_PROMPT.md
  vstd/
  verus
  verus-checker
```

The helper also links or copies the supporting Verus runtime files from the Verus installation when they exist, such as `z3`, `rust_verify`, `libvstd.rlib`, and Verus macro libraries. Those extra files make `./verus X.rs` work reliably from inside the task directory.

## Prepare One Task

From the repository root:

```bash
python hands-off/prepare_task.py \
  benchmarks/Verus-Bench/CloverBench/unverified/is_prime.rs \
  --verus ../verus/verus \
  --checker /path/to/verus-checker \
  --out-dir hands-off/tasks/task_is_prime
```

By default, large Verus assets are symlinked. Use `--copy` if the task directory must be physically self-contained:

```bash
python hands-off/prepare_task.py \
  benchmarks/Verus-Bench/CloverBench/unverified/is_prime.rs \
  --verus ../verus/verus \
  --checker /path/to/verus-checker \
  --out-dir hands-off/tasks/task_is_prime \
  --copy
```

If your checker backend is the raw `lynette` binary, use `--checker-kind lynette-additions`. The helper will place `lynette` in the task directory and generate a `verus-checker` wrapper that infers the original file from `<name>_verified.rs` and runs:

```bash
lynette additions <original-file> <changed-file>
```

If the wrapper cannot infer the original file, pass it explicitly:

```bash
./verus-checker <changed-file> <original-file>
```

For this workspace, after building `utils/lynette/source/target/release/lynette`, the command is:

```bash
python hands-off/prepare_task.py \
  benchmarks/Verus-Bench/CloverBench/unverified/is_prime.rs \
  --verus ../verus/verus \
  --checker utils/lynette/source/target/release/lynette \
  --checker-kind lynette-additions \
  --out-dir hands-off/tasks/task_is_prime
```

Use `--force` to replace an existing prepared task directory.

## Sanity Check The Task

Before starting the coding agent:

```bash
cd hands-off/tasks/task_is_prime
./verus is_prime.rs
./verus-checker is_prime.rs
```

Both commands are allowed to fail verification because the input is unverified. The important check is that the binaries execute and can find their dependencies.

## Run Codex Hands-Off

From inside the task directory:

```bash
codex --ask-for-approval never --sandbox workspace-write
```

Paste the contents of `HANDS_OFF_PROMPT.md`.

The agent should stop only after both commands succeed:

```bash
./verus is_prime_verified.rs
./verus-checker is_prime_verified.rs
```

## Prompt Template

`prompt_template.md` contains the generic prompt. `prepare_task.py` writes a task-specific `HANDS_OFF_PROMPT.md` that replaces `X.rs` and `X_verified.rs` with the actual filenames.

## Many Tasks

Recommended layout:

```text
hands-off/tasks/
  task_001/
    task_001.rs
    task_001_verified.rs
    HANDS_OFF_PROMPT.md
    vstd/
    verus
    verus-checker

  task_002/
    task_002.rs
    task_002_verified.rs
    HANDS_OFF_PROMPT.md
    vstd/
    verus
    verus-checker
```

Run Codex separately inside each task folder. This keeps the agent focused and prevents accidental cross-task edits.
