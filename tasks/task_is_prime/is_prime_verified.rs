use vstd::prelude::*;

fn main() {}
verus! {

spec fn divides(factor: nat, candidate: nat) -> bool {
    candidate % factor == 0
}

spec fn is_prime(candidate: nat) -> bool {
    &&& 1 < candidate
    &&& forall|factor: nat| 1 < factor && factor < candidate ==> !divides(factor, candidate)
}

fn test_prime(candidate: u64) -> (result: bool)
    requires
        1 < candidate,
    ensures
        result == is_prime(candidate as nat),
{
    let mut factor: u64 = 2;
    while factor < candidate
        invariant
            2 <= factor <= candidate,
            forall|f: nat| 1 < f && f < factor ==> !divides(f, candidate as nat),
        decreases candidate - factor
    {
        if candidate % factor == 0 {
            assert(divides(factor as nat, candidate as nat));
            assert(!is_prime(candidate as nat));
            return false;
        }
        assert(!divides(factor as nat, candidate as nat));
        factor = factor + 1;
    }
    assert(forall|f: nat| 1 < f && f < candidate ==> !divides(f, candidate as nat));
    true
}

} // verus!
