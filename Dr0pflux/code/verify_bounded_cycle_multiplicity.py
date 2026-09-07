"""Independent certificate checker for bounded cyclic-label multiplicity."""

from __future__ import annotations

from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
DATA_PATH = REPOSITORY / "Chesewip" / "outputs" / "ciphertext.json"
RESULT_PATH = Path(__file__).resolve().parents[1] / "results" / "bounded_cycle_multiplicity.json"


def all_bounded_words(limit: int) -> list[tuple[int, ...]]:
    """Enumerate linear representatives directly, without necklace reduction."""
    words: list[tuple[int, ...]] = []
    for zero_count in range(1, limit + 1):
        for one_count in range(1, limit + 1):
            length = zero_count + one_count
            for zero_positions in combinations(range(length), zero_count):
                zero_set = set(zero_positions)
                words.append(tuple(0 if index in zero_set else 1 for index in range(length)))
    return words


def fits_from_some_phase(sequence: list[int], word: tuple[int, ...]) -> bool:
    return not sequence or any(
        sequence == [word[(phase + index) % len(word)] for index in range(len(sequence))]
        for phase in range(len(word))
    )


def independently_compatible(
    messages: list[list[int]], a: int, b: int, limit: int
) -> bool:
    projections = [[0 if value == a else 1 for value in row if value in (a, b)] for row in messages]
    return any(
        all(fits_from_some_phase(projection, word) for projection in projections)
        for word in all_bounded_words(limit)
    )


def control(limit: int) -> bool:
    word = tuple([0] * limit + [1] * limit)
    sequences = [
        [word[(index + phase) % len(word)] for index in range(8 * len(word) + 3)]
        for phase in (0, limit, len(word) - 1)
    ]
    positive = any(all(fits_from_some_phase(sequence, candidate) for sequence in sequences)
                   for candidate in all_bounded_words(limit))
    negative_sequence = [0] * (limit + 1) + [1] + [0] * (limit + 1) + [1]
    negative = not any(
        fits_from_some_phase(negative_sequence, candidate) for candidate in all_bounded_words(limit)
    )
    return positive and negative


def main() -> None:
    source = DATA_PATH.read_bytes()
    raw = json.loads(source)
    messages = [row[1:] for row in raw.values()]
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    assert result["source"]["sha256"] == sha256(source).hexdigest()
    assert result["source"]["message_order"] == list(raw)
    assert result["source"]["body_lengths"] == list(map(len, messages))

    checked_pairs = 0
    for row in result["bounds"]:
        limit = row["maximum_label_multiplicity_per_class_cycle"]
        certificate = row["incompatible_set_certificate"]
        assert len(certificate) == row["plaintext_class_lower_bound"]
        assert control(limit)
        for a, b in combinations(certificate, 2):
            assert not independently_compatible(messages, a, b, limit), (limit, a, b)
            checked_pairs += 1

    assert [row["plaintext_class_lower_bound"] for row in result["bounds"]] == [79, 60, 40, 28, 20]
    print(
        json.dumps(
            {
                "status": "verified",
                "independently_checked_incompatible_pairs": checked_pairs,
                "class_lower_bounds": [
                    row["plaintext_class_lower_bound"] for row in result["bounds"]
                ],
                "controls": "passed for multiplicity bounds 1 through 5",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
