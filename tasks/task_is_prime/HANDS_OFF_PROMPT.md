The file is_prime.rs cannot be verified by Verus yet.

Please add proof annotations to is_prime.rs so that Verus verifies it, and write the result to is_prime_verified.rs.

You may inspect the vstd folder.

Run Verus until there are no errors.

Do not change preconditions or postconditions.
Do not change executable Rust code.
Do not use assume(...) or admit().
Do not add axiom, external_body, or other shortcut annotations that bypass proof obligations.

Before finishing, run:

./verus-checker is_prime_verified.rs

The task is complete only when Verus verifies is_prime_verified.rs and verus-checker accepts it.
