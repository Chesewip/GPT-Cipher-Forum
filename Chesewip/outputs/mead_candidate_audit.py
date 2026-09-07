"""Independent checks of the friend's E3/E4 plaintext PDF.

The source text discrepancy and cipher exclusions are separate issues.
Fixed per-letter positional permutations with a fixed output position are a
conditional cipher family, not every possible stateful encryption scheme.
"""
from pathlib import Path
import collections, hashlib, itertools, json
from permutation_action_fold import Fold, solve
ROOT = Path(__file__).resolve().parent
NAMES = ['E1', 'W1', 'E2', 'W2', 'E3', 'W3', 'E4', 'W4', 'E5']
E3_TEXT = ('There is no difference with one another; there is no partiality with Him. '
           'But they are one in Thought. One is the Prescience of all. '
           'They have one Mind-their Father.')
E4_TEXT = ('There is no Good that can be got from objects in the world. '
           'For all the things that fall beneath the eye are image-things and pictures as it were;')


def normalize(text):
    return text.upper().replace('\u2014', '-').replace(' ', '')


def common_prefix(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))


def canonical(row):
    seen = {}
    return [seen.setdefault(c, len(seen)) for c in row]


def selected_fold(pt, ct, indices):
    alphabet = {c: i + 1 for i, c in enumerate(dict.fromkeys(pt))}
    f = Fold()
    top = f.node()
    endpoints = {}
    for t in sorted(indices):
        node = top
        for c in reversed(pt[:t + 1]):
            label = alphabet[c]
            if label not in f.adj[node]:
                nxt = f.node()
                f.edge(node, label, nxt)
            node = f.adj[node][label]
        c = ct[t]
        if f.colour[node] is not None and f.colour[node] != c:
            return True
        f.colour[node] = c
        if c in endpoints:
            f.merge(node, endpoints[c])
        else:
            endpoints[c] = node
    f.drain()
    return f.failure is not None


def minimize_observations(pt, ct):
    active = list(range(len(pt)))
    assert selected_fold(pt, ct, active)
    for i in list(active):
        trial = [j for j in active if j != i]
        if selected_fold(pt, ct, trial):
            active = trial
    return active


def periodic_checks(pt, ct):
    p = [ord(c) for c in pt]
    key = [(c - x) % 83 for c, x in zip(ct, p)]
    additive = []
    affine = []
    for period in range(1, 33):
        first_errors = sum(k != key[i % period] for i, k in enumerate(key))
        optimal_errors = 0
        affine_possible = True
        for residue in range(period):
            group = key[residue::period]
            optimal_errors += len(group) - max(collections.Counter(group).values())
            points = list(zip(p[residue::period], ct[residue::period]))
            if not any(all((a * x + ((points[0][1] - a * points[0][0]) % 83)) % 83 == c for x, c in points) for a in range(1, 83)):
                affine_possible = False
        additive.append(dict(period=period, first_block_key_errors=first_errors, best_periodic_key_errors=optimal_errors))
        affine.append(dict(period=period, exact_fit=affine_possible))
    return dict(plaintext_numeric_encoding='ASCII ord(character), modulo 83; other non-affine encodings require separate tests',
                additive=additive, affine=affine)


def run():
    raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
    body = [row[1:] for row in raw]
    p3, p4 = normalize(E3_TEXT), normalize(E4_TEXT)
    assert [len(p3), len(p4)] == [136, 118]
    expected = [[0,24,24,2,2,2,2,2,2],[24,0,24,2,2,2,2,2,2],[24,24,0,2,2,2,2,2,2],
                [2,2,2,0,5,5,5,5,5],[2,2,2,5,0,5,9,9,9],[2,2,2,5,5,0,5,5,5],
                [2,2,2,5,9,5,0,20,20],[2,2,2,5,9,5,20,0,20],[2,2,2,5,9,5,20,20,0]]
    observed = [[0 if i == j else common_prefix(x, y) for j, y in enumerate(body)] for i, x in enumerate(body)]
    assert observed == expected
    pattern = [0,1,2,3,4,1,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,17,21,22,11,23,24]
    windows = [(4,63),(6,72),(7,75),(8,73)]
    assert all(canonical(raw[i][s:s + 28]) == pattern for i, s in windows)
    extension = {}
    for length in [28,29,30,31]:
        groups = collections.defaultdict(list)
        for i, s in windows:
            groups[tuple(canonical(raw[i][s:s + length]))].append(NAMES[i])
        extension[length] = list(groups.values())
    repetition_pairs = [(a,b,b-a,b-a-1) for a in range(28) for b in range(a + 1,28) if pattern[a] == pattern[b]]
    e3_fold = solve([p3], [body[4]])
    e4_fold = solve([p4], [body[6]])
    core = minimize_observations(p3, body[4])
    # Earliest failing prefix helps make the result easy to independently inspect.
    first_bad = next(length for length in range(1,len(p3)+1) if solve([p3[:length]],[body[4][:length]])['status'] == 'contradiction')
    early_core = minimize_observations(p3[:first_bad], body[4][:first_bad])
    source_opening = 'With Him, therefore, is there no difference with one another;'
    candidate_opening = E3_TEXT.split(';')[0] + ';'
    exact_source = E3_TEXT.replace(candidate_opening, source_opening, 1)
    results = dict(status='PDF observations partly verified; proposed E3 rejected within fixed-per-letter permutation family',
                   candidate_texts={'E3':p3,'E4':p4}, candidate_lengths={'E3':len(p3),'E4':len(p4)},
                   ciphertext_lengths={name:len(row) for name,row in zip(NAMES,raw)},
                   headers={name:row[0] for name,row in zip(NAMES,raw)}, prefix_matrix_matches=True, prefix_matrix=observed,
                   candidate_common_prefix=common_prefix(p3,p4),
                   source_comparison=dict(url='https://sacred-texts.com/gno/th2/th235.htm',
                                          source_opening=source_opening, candidate_opening=candidate_opening,
                                          normalized_source_passage_length=len(normalize(exact_source)),
                                          normalized_candidate_length=len(p3),
                                          discrepancy='Opening rewritten, not solely case/space/dash normalization.'),
                   block28=dict(verified=True, raw_indices_are_zero_based=True, canonical_pattern=pattern,
                                repetition_pairs_zero_based_with_distance_and_intervening_count=repetition_pairs,
                                extension_partitions=extension,
                                aligned_candidate_E3=p3[62:90], aligned_candidate_E4=p4[71:99],
                                candidate_passages_equal=p3[62:90]==p4[71:99]),
                   E3_E_distinct_ciphertext_values=len(set(c for p,c in zip(p3,body[4]) if p=='E')),
                   periodic_checks=periodic_checks(p3,body[4]), E3_permutation_action=e3_fold,E4_permutation_action=e4_fold,
                   E3_core_body_indices_zero_based=core,
                   earliest_E3_permutation_contradiction_prefix_length=first_bad,
                   earliest_core=[dict(body_index_zero_based=i, raw_index_zero_based=i+1,
                                       body_position_one_based=i+1, plaintext_letter=p3[i],ciphertext=body[4][i]) for i in early_core],
                   exclusion_scope='Each plaintext character chooses one fixed permutation of positions, followed by reading a fixed output position; arbitrary initial deck and arbitrary per-character permutations. Covers the fixed-update positional deck/GAK model, not all stateful or time-dependent ciphers.',
                   warning='Survival is not a key or a plaintext verification. Exact lengths and ciphertext isomorphism do not establish a decipherment.')
    (ROOT / 'mead_candidate_audit.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    return results


if __name__ == '__main__':
    r = run()
    print(json.dumps({k:v for k,v in r.items() if k not in ['prefix_matrix','periodic_checks','candidate_texts']},indent=2))
