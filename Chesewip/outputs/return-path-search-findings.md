# Direct return-path search: progress and current limit

**The Noita eye cipher remains unsolved. This round found no plaintext, key, newly excluded rotation, or authenticated cipher mechanism.**

The useful advance is computational: a previously inconclusive return-path search now produces independently verified assignments for 195 return intervals across all nine messages. These cover every consecutive recurrence with a gap of at most 20 symbols, for the tested rotation 9 in the unit-neighbor three-card model.

Rotation 9 was retained as a benchmark from earlier work. It was not selected by a successful comparison against the other 81 rotations and is not identified as the actual rotation.

## What was tested

The model has an 83-card deck. Each plaintext position selects one of the 82 non-top positions, cycles its card, its neighbor, and the top card, then rotates the bottom ring by a fixed amount. The ciphertext is the selected card. The initial deck is unknown.

The repeated-plaintext assumptions are the ten previously recorded isomorphic passages, with their first symbol omitted, plus the shared body-prefix hypothesis. These remain assumptions, not decrypted text. No English alphabet or numerical header interpretation is imposed.

### Repeated-passage support test

Equal plaintext updates preserve the correspondence between paired decks. I contracted the observations that those equalities force to share one correspondence, then bounded the entry changes between contracted blocks.

The scan covered 50 relevant message/offset alignments for each of three trimming conventions. No version excluded support five. The strongest local requirement was only two mandatory entry changes per available differing-input position, below the five-entry limit for anchored three-card updates.

This test does not establish an actual small-shuffle realization. It simply failed to produce an exclusion.

### Coarse return-displacement test

If a card appears at output indices r and t, with no appearance in between, its position before the next appearance is tightly related to the plaintext selection at r+1. In zero-based bottom-ring coordinates:

`p[t] = p[r+1] + 1 + (t-r-1)*b - k  (mod 82)`

Here b is the rotation and k counts predecessor hits, with `0 <= k <= t-r-2`.

This interval condition discards the exact circumstances that cause each hit. All **82 rotations** satisfy that relaxation under the stated repeated-plaintext assumptions. It therefore does not narrow the rotation.

Generated controls caught an initial off-by-one in the rotation count before the real scan. The corrected formula is the one above and in the saved scripts.

## Making exact return constraints tractable

The more exact test tracks whether every intermediate selection hits the position immediately before the card, and forbids an early reappearance. The original combined bit-vector scan timed out at every rotation when restricted to gaps of twelve and given one second per solver call. A combined integer encoding also timed out at six sampled rotations with three-second limits. These timeouts are not exclusions.

Two changes improved the search:

1. **Solve independent groups separately.** If two sets of return constraints share no plaintext-selection variable, their solutions can be combined for this relaxation. At gap twelve there are 44 groups, with at most 26 variables in any group.
2. **Remove selectors used only once.** When an intermediate selector appears nowhere else in the active constraints, either a predecessor hit or a non-hit can be chosen freely. The search retains that choice and reconstructs the selector afterward. This elimination is valid without an alphabet restriction; it would need revisiting if selection positions were restricted to a small alphabet.

The resulting outcomes at rotation 9 are:

| Maximum return gap | Return intervals included | Result |
|---|---:|---|
| 12 | 126 | All groups satisfiable |
| 16 | 162 | All groups satisfiable |
| 18 | 188 | All groups satisfiable; saved assignments independently verified |
| 20 | 195 | All groups satisfiable; saved assignments independently verified |
| 24 | 227 | Inconclusive: the largest group timed out |

At gap 24, the difficult group contains 193 return intervals and 515 remaining selection variables. It timed out with a 15-second solver limit. Seeding a subsequent 30-second run with the gap-20 assignment also timed out. Seeds supplied initial guesses only; they did not fix those variables or narrow the allowed solutions.

## What the saved assignments prove

`verify_component_assignments.py` does not invoke the solver. It assembles all saved component assignments, checks that shared plaintext classes receive consistent values, and simulates an explicit physical deck for each return interval.

It verifies:

- 188 returns and 1,811 physical updates at gap 18.
- 195 returns and 1,948 physical updates at gap 20.
- The tracked card returns at the required output and never earlier within the interval.

These are assignments to internal selection positions, not letters or words. They do **not** establish that one common initial deck produces the entire ciphertext. They also leave longer returns and other global consistency conditions unchecked. Independent component shifts are legitimate for the return relaxation but need not remain free once the common initial key is imposed.

## Calibration

The new methods passed twelve generated full-return fixtures with known selectors, 51 unpinned component checks, and 4,861 independent physical card-return checks. The contracted-support calculation passed twelve shared-passage fixtures and 1,200 comparisons against an independently implemented window dynamic program.

The known-selector fixtures verify the equations, not recovery of a hidden key. The unpinned component tests verify that the reduced search can recover compatible return assignments without those known selectors.

## Implication for the investigation

This round improves the search method rather than increasing confidence in a deck cipher. A selected return subsystem can be satisfied; it has not yet been connected to a single historical key or meaningful plaintext. The prior lower bound of eighteen East1/West1 plaintext differences in the common-initial-deck anchored-three-card model remains unchanged.

The next discriminating work is to connect the return assignments to common initial-card positions and extend the constraints beyond twenty-symbol returns. Failure or success on that stronger system must again be distinguished from a solver timeout and from an arbitrary model fit.

## Reproduction

No build is required. Run directly from the extracted bundle directory:

```powershell
python shared_update_support.py
python return_displacement.py --controls
python return_displacement.py
python verify_return_methods.py
python component_return_paths.py --gap 18 --rotation 9 --timeout 15000 --eliminate-free
python component_return_paths.py --gap 20 --rotation 9 --timeout 15000 --eliminate-free
python verify_component_assignments.py
```

For the unresolved extension:

```powershell
python component_return_paths.py --gap 24 --rotation 9 --timeout 15000 --eliminate-free
python warm_return_paths.py
```

`checked_component_assignments.json` and `checked_return_methods.json` summarize verification. The gap-18 and gap-20 component files contain the concrete assignments. All text deliverables use CRLF.
