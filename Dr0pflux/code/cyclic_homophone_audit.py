"""Ciphertext-only audit of fixed cyclic homophonic substitution."""

from __future__ import annotations

from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
DATA_PATH = REPOSITORY / "Chesewip" / "outputs" / "ciphertext.json"
RESULT_PATH = Path(__file__).resolve().parents[1] / "results" / "cyclic_homophone_audit.json"
SOURCE_COMMIT = "d8ef5d825cbe8b09b1bbfbddc10ffdc064758569"


def pair_alternates(messages: list[list[int]], a: int, b: int) -> bool:
    """Return whether each message projected to {a,b} has no equal neighbors."""
    for message in messages:
        projected = [symbol for symbol in message if symbol == a or symbol == b]
        if any(left == right for left, right in zip(projected, projected[1:])):
            return False
    return True


def compatible_pairs(messages: list[list[int]], labels: list[int]) -> list[tuple[int, int]]:
    return [pair for pair in combinations(labels, 2) if pair_alternates(messages, *pair)]


def triangle_count(labels: list[int], edges: list[tuple[int, int]]) -> int:
    edge_set = {tuple(sorted(edge)) for edge in edges}
    return sum(
        (a, b) in edge_set and (a, c) in edge_set and (b, c) in edge_set
        for a, b, c in combinations(labels, 3)
    )


def maximum_matching(edges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Exact branch search; the observed graph is deliberately tiny."""
    best: list[tuple[int, int]] = []

    def visit(index: int, used: set[int], chosen: list[tuple[int, int]]) -> None:
        nonlocal best
        if len(chosen) + len(edges) - index <= len(best):
            return
        if index == len(edges):
            if len(chosen) > len(best):
                best = chosen.copy()
            return
        visit(index + 1, used, chosen)
        a, b = edges[index]
        if a not in used and b not in used:
            visit(index + 1, used | {a, b}, chosen + [(a, b)])

    visit(0, set(), [])
    return best


def generated_controls() -> dict[str, bool]:
    cycles = {0: [0, 1, 2], 1: [3, 4], 2: [5]}
    plaintexts = [
        [0, 1, 2, 0, 1, 0, 2, 1] * 8,
        [2, 0, 1, 0, 2, 1, 0, 1] * 8,
    ]
    phases = [{0: 0, 1: 1, 2: 0}, {0: 2, 1: 0, 2: 0}]
    controls: list[list[int]] = []
    for plaintext, initial in zip(plaintexts, phases):
        state = initial.copy()
        ciphertext = []
        for symbol in plaintext:
            cycle = cycles[symbol]
            ciphertext.append(cycle[state[symbol]])
            state[symbol] = (state[symbol] + 1) % len(cycle)
        controls.append(ciphertext)

    same_class_pairs_survive = all(
        pair_alternates(controls, a, b)
        for cycle in cycles.values()
        for a, b in combinations(cycle, 2)
    )
    deliberately_broken_pair_fails = not pair_alternates([[0, 0, 1]], 0, 1)
    return {
        "same_class_pairs_survive_with_message_specific_start_phases": same_class_pairs_survive,
        "deliberately_broken_pair_fails": deliberately_broken_pair_fails,
    }


def main() -> None:
    source = DATA_PATH.read_bytes()
    raw = json.loads(source)
    message_names = list(raw)
    messages = [raw[name][1:] for name in message_names]
    labels = sorted({symbol for message in messages for symbol in message})
    controls = generated_controls()
    assert all(controls.values())

    edges = compatible_pairs(messages, labels)
    triangles = triangle_count(labels, edges)
    matching = maximum_matching(edges)
    maximum_clique_size = 2 if edges and triangles == 0 else None
    minimum_classes = len(labels) - len(matching) if maximum_clique_size == 2 else None

    result = {
        "status": "conditional exclusion; no plaintext or key recovered",
        "model": (
            "Each plaintext class has one fixed cycle of distinct ciphertext labels; each label belongs "
            "to one class; class state advances once per occurrence; message-specific starting phases are allowed."
        ),
        "source": {
            "repository_commit": SOURCE_COMMIT,
            "path": "Chesewip/outputs/ciphertext.json",
            "sha256": sha256(source).hexdigest(),
            "message_order": message_names,
            "raw_lengths": [len(raw[name]) for name in message_names],
            "first_symbol_treatment": "removed independently from each message as a possible marker",
            "body_lengths": [len(message) for message in messages],
        },
        "labels_observed": labels,
        "label_count": len(labels),
        "pairs_tested": len(labels) * (len(labels) - 1) // 2,
        "compatible_pairs": [list(edge) for edge in edges],
        "compatible_pair_count": len(edges),
        "triangle_count": triangles,
        "maximum_compatible_clique_size": maximum_clique_size,
        "maximum_matching": [list(edge) for edge in matching],
        "maximum_matching_size": len(matching),
        "minimum_plaintext_classes_under_model": minimum_classes,
        "controls": controls,
    }
    assert len(labels) == 83
    assert len(edges) == 6
    assert triangles == 0
    assert len(matching) == 4
    assert minimum_classes == 79

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\r\n")
    print(json.dumps({
        "compatible_pairs": result["compatible_pairs"],
        "maximum_matching": result["maximum_matching"],
        "minimum_plaintext_classes_under_model": minimum_classes,
        "controls": controls,
    }, indent=2))


if __name__ == "__main__":
    main()
