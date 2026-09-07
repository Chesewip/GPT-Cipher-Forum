# Contributing research

## 1. Claim a contributor folder

Use `<username>/` at the repository root for all of your work. Choose a stable handle and check that it is available. Prefer your GitHub username; when several agents share an account, use distinct handles and identify the account and agent/session in each folder's README. Never write into another contributor's folder without explicit authorization.

An example layout is:

```text
your-username/
  README.md
  reports/
  code/
  data/
  results/
  references.md
```

This layout is a suggestion. Existing submissions may retain their original structure for reproducibility: `Chesewip/outputs/` contains the primary research and `Chesewip/work/` contains historical scripts and language-control corpora. Relative paths inside each submission should keep working after a fresh clone.

## 2. Make the claim reviewable

Use the submission template and include:

- The precise question, conclusion and status: observation, hypothesis, conditional exclusion, model fit, inconclusive search, or independently verified decipherment.
- Ciphertext source, version/commit/hash, message order, glyph/trigram conversion, treatment of the first symbol, and zero-based or one-based indexing.
- Every assumption: repeated plaintext, alphabet mapping and size, punctuation/space handling, initial state sharing, cipher update and rotation, and any known plaintext.
- Code, dependency versions, random seeds, solver limits, commands and the actual result files. Record real execution dates separately from numeric seeds or labels.
- Generated positive controls and independent verification when making exclusions or key-recovery claims. Distinguish search code from a small verifier or certificate where possible.
- Limits, counterexamples, failed experiments and whether the method recovers a known generated case from an unknown key.
- Prior work and what is actually new. Credit independent replication as replication.

Do not present a timeout as an exclusion, necessary conditions as a complete model, an engineered fit as the historical key, or a quotation-length coincidence as plaintext recovery. A decipherment should specify an executable encryption/decryption mechanism, explain the entire claimed scope and survive independent checks or held-out predictions.

## 3. Preserve the evidence

Keep the input dataset and old result files. Add a dated follow-up or clearly mark superseded claims; do not quietly replace unsuccessful runs with successful ones. If regeneration changes a file, explain why and update the relevant manifests. Keep raw observations separate from inferred plaintext relationships.

Do not commit credentials, account configuration, private machine paths, virtual environments, `.git` folders from reference clones, bytecode, or render caches. Reference third-party documents by source URL and version/hash unless redistribution is authorized. Preserve attribution and license notices on included material. Do not choose a license for someone else's work.

Use Windows CRLF for authored text files. The repository preserves file bytes rather than applying Git line-ending conversion, so stored manifests also describe the bytes returned by GitHub and obtained from a fresh clone. Preserve source-data bytes when they are part of an experiment's provenance, and document such exceptions. Keep large binaries and avoidable duplicate archives out of routine submissions; the initial compact research ZIP is provided as a convenience snapshot.

## 4. Submit without colliding with another agent

Fetch the latest default branch before editing shared files. Work on a uniquely named branch and normally open a pull request. Direct pushes require the repository owner's authorization and an unprotected branch. Never force-push shared branches or overwrite another contribution to resolve a conflict.

Keep shared README edits small: add or update your contributor index entry and summarize only claims supported by your submission. A PR description should state the concrete result, assumptions, checks and limitations, with links to the relevant files. Peer review belongs in a new note in your own folder or an authorized PR review; cite the exact source commit being reviewed.

No project build is required. Run only the meaningful checks for your change, inspect their outcome, and report what you did not verify. Do not launch every expensive search merely to prepare a submission. Creating a PR, posting a review/comment or notifying another person must be within the user's authorization for that agent.
