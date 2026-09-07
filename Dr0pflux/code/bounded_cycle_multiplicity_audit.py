"""Audit cyclic homophony when a label may repeat within its class cycle."""

from __future__ import annotations

from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
DATA_PATH = REPOSITORY / "Chesewip" / "outputs" / "ciphertext.json"
RESULT_PATH = Path(__file__).resolve().parents[1] / "results" / "bounded_cycle_multiplicity.json"
SOURCE_COMMIT = "3e9e4f049e97988fa236a5c4b96b6ac67a9a1e0f"
EXPECTED = {
    1: (1, 6, 79),
    2: (5, 207, 60),
    3: (15, 831, 40),
    4: (43, 1515, 28),
    5: (119, 2131, 20),
}


def binary_necklaces(limit: int) -> list[tuple[int, ...]]:
    """Return rotation-canonical binary cycles with 1..limit of each bit."""
    necklaces: set[tuple[int, ...]] = set()
    for zero_count in range(1, limit + 1):
        for one_count in range(1, limit + 1):
            length = zero_count + one_count
            for zero_positions in combinations(range(length), zero_count):
                zero_set = set(zero_positions)
                word = tuple(0 if index in zero_set else 1 for index in range(length))
                rotations = [word[index:] + word[:index] for index in range(length)]
                necklaces.add(min(rotations))
    return sorted(necklaces)


def matches_periodic_word(sequence: list[int], word: tuple[int, ...]) -> bool:
    """Return whether a finite sequence occurs in an infinite repetition of word."""
    if not sequence:
        return True
    return any(
        all(value == word[(phase + index) % len(word)] for index, value in enumerate(sequence))
        for phase in range(len(word))
    )


def projected_pair(messages: list[list[int]], a: int, b: int) -> list[list[int]]:
    return [[0 if value == a else 1 for value in message if value == a or value == b] for message in messages]


def pair_compatible(
    messages: list[list[int]], a: int, b: int, necklaces: list[tuple[int, ...]]
) -> bool:
    projections = projected_pair(messages, a, b)
    return any(all(matches_periodic_word(sequence, word) for sequence in projections) for word in necklaces)


def compatibility_graph(
    messages: list[list[int]], labels: list[int], necklaces: list[tuple[int, ...]]
) -> list[set[int]]:
    adjacency = [set() for _ in labels]
    for a, b in combinations(labels, 2):
        if pair_compatible(messages, a, b, necklaces):
            adjacency[a].add(b)
            adjacency[b].add(a)
    return adjacency


def maximum_incompatible_set(adjacency: list[set[int]]) -> tuple[list[int], int]:
    """Find a maximum independent set by exact maximum-clique search on the complement."""
    vertices = set(range(len(adjacency)))
    complement = [vertices - {vertex} - adjacency[vertex] for vertex in vertices]
    best: list[int] = []
    nodes = 0

    def visit(chosen: list[int], candidates: set[int]) -> None:
        nonlocal best, nodes
        nodes += 1
        if len(chosen) + len(candidates) <= len(best):
            return
        if not candidates:
            if len(chosen) > len(best):
                best = chosen.copy()
            return
        pivot = max(sorted(candidates), key=lambda vertex: len(candidates & complement[vertex]))
        for vertex in sorted(candidates - complement[pivot]):
            visit(chosen + [vertex], candidates & complement[vertex])
            candidates.remove(vertex)
            if len(chosen) + len(candidates) <= len(best):
                return

    visit([], vertices.copy())
    return sorted(best), nodes


def generated_control(limit: int) -> dict[str, object]:
    cycles = {
        0: tuple([0] * limit + [1] * limit + [2] * limit),
        1: tuple(value for _ in range(limit) for value in (3, 4, 5)),
    }
    plaintexts = [
        [0, 1, 0, 0, 1, 1, 0, 1] * (limit + 2),
        [1, 0, 1, 0, 0, 1, 0, 1] * (limit + 2),
    ]
    phases = [{0: 0, 1: limit}, {0: 2 * limit, 1: 2 * limit}]
    ciphertexts: list[list[int]] = []
    for plaintext, initial in zip(plaintexts, phases):
        state = initial.copy()
        ciphertext: list[int] = []
        for symbol in plaintext:
            cycle = cycles[symbol]
            ciphertext.append(cycle[state[symbol] % len(cycle)])
            state[symbol] += 1
        ciphertexts.append(ciphertext)

    necklaces = binary_necklaces(limit)
    same_class_pairs_survive = all(
        pair_compatible(ciphertexts, a, b, necklaces)
        for cycle in cycles.values()
        for a, b in combinations(sorted(set(cycle)), 2)
    )
    broken = [[10] * (limit + 1) + [11] + [10] * (limit + 1) + [11]]
    over_limit_run_fails = not pair_compatible(broken, 10, 11, necklaces)
    return {
        "same_class_pairs_survive_with_message_specific_phases": same_class_pairs_survive,
        "over_limit_projected_run_fails": over_limit_run_fails,
    }


def main() -> None:
    source = DATA_PATH.read_bytes()
    raw = json.loads(source)
    message_names = list(raw)
    messages = [raw[name][1:] for name in message_names]
    labels = sorted({value for message in messages for value in message})
    assert labels == list(range(83))

    bounds: list[dict[str, object]] = []
    for limit in EXPECTED:
        necklaces = binary_necklaces(limit)
        adjacency = compatibility_graph(messages, labels, necklaces)
        edge_count = sum(map(len, adjacency)) // 2
        certificate, search_nodes = maximum_incompatible_set(adjacency)
        controls = generated_control(limit)
        assert all(controls.values())
        assert (len(necklaces), edge_count, len(certificate)) == EXPECTED[limit]
        assert all(b not in adjacency[a] for a, b in combinations(certificate, 2))
        bounds.append(
            {
                "maximum_label_multiplicity_per_class_cycle": limit,
                "binary_necklace_count": len(necklaces),
                "compatible_pair_count": edge_count,
                "incompatible_set_certificate": certificate,
                "plaintext_class_lower_bound": len(certificate),
                "exact_search_nodes": search_nodes,
                "controls": controls,
            }
        )

    result = {
        "status": "conditional exclusion; no plaintext or key recovered",
        "model": (
            "Each plaintext class owns one fixed periodic ciphertext-label cycle shared by all messages. "
            "Every observed label belongs to one class and occurs between one and r times per period; "
            "the class advances once per occurrence and each message may use its own starting phase."
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
        "label_count": len(labels),
        "pairs_tested_per_bound": len(labels) * (len(labels) - 1) // 2,
        "interpretation": (
            "Every listed certificate is pairwise incompatible under its bound, so its labels must "
            "belong to distinct plaintext classes. Optimality of certificate size is not needed for the claim."
        ),
        "bounds": bounds,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\r\n")
    print(
        json.dumps(
            [
                {
                    "multiplicity": row["maximum_label_multiplicity_per_class_cycle"],
                    "compatible_pairs": row["compatible_pair_count"],
                    "class_lower_bound": row["plaintext_class_lower_bound"],
                }
                for row in bounds
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
