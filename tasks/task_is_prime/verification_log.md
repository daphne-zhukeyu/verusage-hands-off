# Verification Log

Source file: `is_prime.rs`

Generated verified file: `is_prime_verified.rs`

Summary:

- Added proof annotations to `is_prime_verified.rs` while preserving the existing executable Rust code and the original function preconditions/postconditions.
- Added loop invariants for the `test_prime` loop to track:
  - `factor` remains in the range `2 <= factor <= candidate`.
  - every already-tested factor does not divide `candidate`.
- Added a `decreases candidate - factor` clause for loop termination.
- Added proof assertions for the early `false` return showing the current `factor` witnesses that `candidate` is not prime.
- Added a final assertion establishing the universal no-divisor condition required by `is_prime`.
- Did not use `assume(...)`, `admit(...)`, new axioms, or `external_body`.

Verification commands run:

```text
./verus is_prime_verified.rs
```

Result:

```text
verification results:: 2 verified, 0 errors
```

Checker command run:

```text
./verus-checker is_prime_verified.rs
```

Result:

```text
passed with exit code 0
```

# Complete Workflow
The file X.rs cannot be verified by Verus, a veri
  fication tool for Rust programs, yet. Please add proof
  annotations to X.rs so that it can be successfully
  verified by Verus, and write the resulting code with
  proof into a new file, X_verified.rs. Please invoke
  Verus to check the proof annotation you added. The
  vstd folder in the current directory is a copy of
  Verus’ vstd definitions and helper lemmas; please feel
  free to check it when needed. You should KEEP editing
  your proof annotations until Verus shows there is no
  error. You should NOT change existing functions’ pre
  conditions or post-conditions; you should NOT change
  any executable Rust code; and you should NEVER use
  admit(...) or assume(...) in your code. You are also
  NOT allowed to create unimplemented, external-body
  lemma functions--- for any new lemma functions you
  add, you should provide complete proof. You are NOT
  allowed to create new axiom functions or change the
  pre/post conditions of existing axiom functions, and
  you should NEVER add external_body tag to any existing
  non-external-body functions. I have installed Verus
  locally; you can just run Verus. Before you are done,
  MAKE SURE to run verus-checker X_verified.rs to double
  check whether you have made any illegal changes to X.
  rs (fix those if you did)


• I’ll inspect the Rust file and the local Verus setup first, then create X_verified.rs as a proof-annotated copy
  and iterate with Verus plus verus-checker.

• Explored
  └ List ls -la
    Read X.rs

• Ran pwd && rg --files
  └ /home/dell/verus-proof-synthesis/hands-off/tasks/task_is_prime
    is_prime.rs
    HANDS_OFF_PROMPT.md
    verus-checker

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• There is no literal X.rs; this task’s source file is is_prime.rs, so I’m treating the requested output as
  is_prime_verified.rs. I’m reading the source now and will preserve executable code exactly.

• Explored
  └ Read is_prime.rs, HANDS_OFF_PROMPT.md, verus-checker

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• The proof shape is straightforward: the loop needs to remember that every factor already tested, from 2 up to the
  current factor, does not divide candidate. I’m going to add only loop invariants and proof assertions around that
  existing loop.

• Ran cp is_prime.rs is_prime_verified.rs && ./verus is_prime_verified.rs
  └ error: loop must have a decreases clause
      --> is_prime_verified.rs:22:5
    … +6 lines (ctrl + t to view transcript)
    error: aborting due to 1 previous error


────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• The first Verus failure is termination only, which confirms the functional proof obligations have not been exposed
  yet. I’m adding the loop invariant and a natural decreasing metric now.

• Edited is_prime_verified.rs (+8 -1)
    21      let mut factor: u64 = 2;
    22 -    while factor < candidate {
    22 +    while factor < candidate
    23 +        invariant
    24 +            2 <= factor <= candidate,
    25 +            forall|f: nat| 1 < f && f < factor ==> !divides(f, candidate as nat),
    26 +        decreases candidate - factor
    27 +    {
    28          if candidate % factor == 0 {
       ⋮
    30          }
    31 +        assert(!divides(factor as nat, candidate as nat));
    32          factor = factor + 1;
    33      }
    34 +    assert(forall|f: nat| 1 < f && f < candidate ==> !divides(f, candidate as nat));
    35      true

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• The annotations are in place. I’m running Verus now to see which arithmetic facts need to be made explicit.

• Ran ./verus is_prime_verified.rs
  └ error: postcondition not satisfied
      --> is_prime_verified.rs:19:9
    … +8 lines (ctrl + t to view transcript)
    error: aborting due to 1 previous error


────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• Verus now needs the early return justified: when the executable modulo test succeeds, the current factor witnesses
  that the candidate is not prime. I’m making that witness explicit inside the branch.

• Edited is_prime_verified.rs (+2 -0)
    28          if candidate % factor == 0 {
    29 +            assert(divides(factor as nat, candidate as nat));
    30 +            assert(!is_prime(candidate as nat));
    31              return false;

• Ran ./verus is_prime_verified.rs
  └ verification results:: 2 verified, 0 errors

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• ./verus is_prime_verified.rs passes. I’m running the required checker next to confirm the executable code and
  specs were not illegally changed.

• Ran ./verus-checker is_prime_verified.rs
  └ (no output)

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• Done. I created is_prime_verified.rs with loop invariants, a decreases clause, and proof assertions for the
  divisor witness.

  Verification passed:

  ./verus is_prime_verified.rs
  verification results:: 2 verified, 0 errors

  The required checker also passed:

  ./verus-checker is_prime_verified.rs
