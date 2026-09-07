# From return-path assignments to common-deck searches

**Unsolved. No meaningful plaintext, historical key, or newly excluded cipher family.**

This continuation identifies a concrete flaw in the previously saved return-path assignments, adds the missing negative constraints, and moves to direct searches over complete initial decks. A common-key fit was found for all nine 24-symbol prefixes. It does not extend to a verified full solution and does not identify a rotation.

## 1. The earlier assignments cannot be complete deck solutions

The gap-18 and gap-20 assignments passed their selected return constraints, as reported. However, they also predict additional card reappearances that are absent from the ciphertext. Some contradictions occur entirely within one independently solved component, so changing the relative rotation of components cannot repair them.

A three-symbol counterexample is enough to reject the saved gap-20 assignment:

- East1 positions **51, 52, 53**, counting from 1, are **72, 31, 5**.
- The saved assignment selects physical bottom positions **63** and **73** at inputs 52 and 53, with rotation 9.
- After input 52, the preceding top card, 72, moves to the selected position's neighbor, 64, then rotates to position 73.
- Input 53 therefore selects card **72**, although the real ciphertext requires **5**.

The selection difference is 10, equal to rotation + 1, so rotating this component's coordinate system preserves the contradiction.

This rejects that particular assignment, not the unit-neighbor three-card cipher model. The earlier report explicitly described its return assignments as incomplete; this audit now shows an actual reason they cannot extend to a complete key.

## 2. Adding forbidden returns and checking whole stretches

The revised solver takes an assignment, checks complete stretches whose input selections are known, and adds a constraint whenever it predicts a forbidden reappearance or misses a required one. It then searches again. This process continues until the stretches have consistent ciphertext equality patterns, the search times out, or the configured round limit is reached.

For one smaller component, the solver repaired its assignment after adding twelve constraints to the original five returns. Two West1 stretches now have exact physical-deck replays:

- Positions 55 through 60: six symbols.
- Positions 85 through 102: eighteen symbols.

Each stretch has its own explicit starting deck. Those separate decks are not a common message reset key, and the selections are not meaningful text. All 24 outputs were independently replayed.

The largest component still timed out at its initial search with a fifteen-second solver limit. It was not excluded.

The terminal-return and terminal-non-return equations passed 120 direct physical checks, including 52 satisfiable and 68 deliberately incompatible cases.

## 3. A direct common-initial-deck formulation

I also encoded the whole deck as an array, shared by all messages at reset. Unlike the isolated return equations, a satisfying result from this formulation has an actual common initial key, and every output is replayed physically afterward.

The solver found a three-symbol prefix fit for all nine messages. Its twelve-symbol search timed out. That timeout is demonstrably a search limitation: direct decoding with the identity deck already satisfies the assumed plaintext equalities through sixteen symbols of every message.

Generated fixtures on decks of sizes 7, 19, and 83 passed both unknown-key/unknown-selector and known-selector/unknown-key tests. Altering an output while fixing the true key and selectors produced the expected contradictions.

These small prefix fits calibrate the formulation; they do not identify the historical cipher or its key.

## 4. Scoring all rotations from one complete key replay

A more practical search operates directly on candidate initial decks. For any candidate key, the ciphertext determines its sequence of selected positions. The key is scored by whether all hypothesized occurrences of the same plaintext symbol select the same physical position.

In the rotating coordinate frame, replaying the deck is independent of the rotation amount. If two equal-plaintext occurrences are at times u and v, their selected frame positions must satisfy:

`(position[v] - position[u]) + (v - u) * rotation = 0 (mod 82)`

Each comparison therefore contributes to a small set of compatible rotations. This permits all 82 rotation settings to be scored from one replay of a candidate deck, rather than replaying the deck 82 times.

The objective uses 256 representative equality comparisons from the stated repeated-passage and shared-prefix assumptions. It imposes no language or small-alphabet condition. Zero disagreements is required to fit those assumptions; even that would need further authentication as plaintext.

### Calibration and real-data outcome

| Search | Remaining equality disagreements | Interpretation |
|---|---:|---|
| Generated control, after five random swaps of its true key | **0** | Recovered the planted plaintext selections and rotation exactly |
| Generated control, random start followed by refinement | **100** | Failed to recover a known solution |
| Real full corpus, initial search | **97** | Incomplete candidate |
| Real full corpus, refined search | **84** | Still incomplete |

The real refined candidate selected rotation 42, whereas the control recovered rotation 9 from the nearby start. The real result does not establish rotation 42: the search has not passed random-start recovery calibration, and the candidate still violates 84 required equalities.

Every valid initial deck can be used to decode this ciphertext in the model's full selection alphabet. Re-encrypting that decoded sequence is therefore an implementation check, not evidence for a decryption. The equality constraints and eventual linguistic/global checks supply the discrimination.

## 5. Exact short-prefix fit and a failed extension

The direct key search found a **single common initial deck** satisfying all 107 active equality comparisons across the first **24 symbols of every message**, with all 216 outputs replayed exactly.

All 82 rotations fit these prefixes with that same key and their corresponding selection sequences. This prefix result cannot distinguish the rotation. Its reported rotation-0 continuation fails 144 of the full corpus's 256 equality comparisons.

Extending to 32 symbols introduces additional comparisons. The initial search left three of 124 comparisons unsatisfied; a longer refinement reduced that to two. A targeted two-swap search examined 17,015 second-move candidates and reduced it to one. A further 10,209-candidate search did not remove the last failure.

The remaining comparison is between West2 input position 25 and East3 input position 31, counting from 1. The candidate selects positions 36 and 48, respectively, though the hypothesis requires equality. This is a concrete failure, not a near-decryption.

The two-swap scan was bounded: its first move had to repair an originally failed comparison and obey a recorded error threshold. It was not an exhaustive search over all pairs of swaps. None of these failures excludes the cipher family or proves that the repeated-plaintext assumption is wrong.

## Verification and next discriminating work

Independent checks include 410 all-rotation score comparisons, 30 fixed-rotation profile comparisons, physical replay of the full-corpus and prefix candidates, the 216-output common-prefix fit, the nine array-solver calibration cases, and the negative-return tests described above.

The previous eighteen-difference lower bound for East1/West1 remains unchanged. This round improves how candidate keys are tested; it does not increase confidence in a particular historical key or rotation.

The useful remaining routes are to strengthen direct key-search recovery on random-start controls and to combine the forbidden-return refinement with common-reset constraints. A candidate must satisfy the complete structural system before its selection sequence is treated as a plaintext candidate.

## Reproduction

No project build is used. From the extracted bundle directory:

```powershell
python return_assignment_key_audit.py
python refine_return_paths.py --gap 20 --component 8 --timeout 5000 --rounds 15
python verify_nonreturn_refinement.py
python verify_common_deck_array.py
python identity_prefix_check.py
python rotation_vote_search.py --control --near --steps 30
python rotation_vote_search.py --control --steps 80 --restarts 2
python rotation_vote_search.py --steps 80 --restarts 2
python refine_rotation_vote.py --control
python refine_rotation_vote.py
python common_key_prefix_ladder.py
python refine_common_prefix.py
python two_swap_prefix_repair.py
python two_swap_prefix_repair.py --source two_swap_prefix_repair.json --output two_swap_prefix_repair_round2.json
python verify_direct_key_search.py
python verify_prefix_rotation_ambiguity.py
```

Useful result files are `return_assignment_key_audit.json`, `checked_nonreturn_refinement.json`, `checked_direct_key_search.json`, `common_key_prefix_ladder.json`, and `two_swap_prefix_repair.json`. Full-corpus candidate files explicitly retain their nonzero disagreement counts.
