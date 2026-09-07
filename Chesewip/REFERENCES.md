# References and third-party material

## Ciphertext and research provenance

The included [ciphertext.json](outputs/ciphertext.json) has 1,036 symbols in nine messages, using the published alternating triangular/base-five reading and labels 0-82. Its two published representations were crosschecked. We did not independently extract it from the game executable or original glyph images. The original [provenance.json](outputs/provenance.json) records the corpus hash and source commits.

- [ngraham20/NoitaCryptographyResearch](https://github.com/ngraham20/NoitaCryptographyResearch), commit `901123781c8af9a164bd71bda082391933611162`. The comparison CSV is `eye/reference/noita_eye_data_trigrams.csv`.
- [Lymm37 eye-messages wiki](https://github.com/Lymm37/eye-messages/wiki), commit `546aa0466db896b6e71925eb64149b34f33107da` in the wiki Git repository.
- [User-supplied research document](https://docs.google.com/document/d/1XMNXktCoSabnFWZf9rJFoaKMzsA1bbv7x1Xh9tXkKYk/edit).
- [Overview document](https://docs.google.com/document/d/1QeagH8TklJsd8iribMtT5LIRL91laOUU_tFcVl7OOqA/edit).
- [Pattern/gap document](https://docs.google.com/document/d/12sCi3OrTuy4PPcu3zUykue7suHvAPyK-uFKcm8Rp4Go/edit). Its retraction of an earlier triple-plaintext/no-space inference is relevant to the assumption audits.
- [mvelzel/eye-vibe](https://github.com/mvelzel/eye-vibe), including `scripts/prove_c82_combined_contexts.py`, `scripts/prove_c41_last_contexts.py`, `scripts/test_affine_isomorph_embedding.py`, and `src/eye_mystery/affine_embedding.py`. The affine exclusion work here credits the existing public results and does not claim first discovery.
- [GarethLowe/Noita-Eyes notebook](https://github.com/GarethLowe/Noita-Eyes/blob/claude/bootstrap-files-extract-myxfgl/NOTEBOOK.md), discussed in the reconvergence/model-assumption reviews.

The research documents and third-party repositories are referenced rather than republished wholesale. To restore the optional source clones, run from `Chesewip/`:

```powershell
git clone https://github.com/ngraham20/NoitaCryptographyResearch.git work/reference
git -C work/reference checkout 901123781c8af9a164bd71bda082391933611162
git clone https://github.com/Lymm37/eye-messages.wiki.git work/wiki
git -C work/wiki checkout 546aa0466db896b6e71925eb64149b34f33107da
```

These folders are ignored by this repository. Some verifiers record whether the optional reference CSV was present. Other verifiers use the included corpus directly. External documents can change; consult pinned commits and the original audit reports.

## Language-control corpora

`work/pg1342.txt` is Jane Austen's *Pride and Prejudice*, obtained from [Project Gutenberg eBook 1342](https://www.gutenberg.org/ebooks/1342). `work/pg1661.txt` is Arthur Conan Doyle's *The Adventures of Sherlock Holmes*, from [eBook 1661](https://www.gutenberg.org/ebooks/1661). Their complete original headers, attribution and Gutenberg licenses are included, and their bytes have not been altered for publication. The saved English-control results record the source hashes. Public-domain status and the Gutenberg distribution terms are documented in those files; no new license is imposed on them.

## Hermetic quotation review

- [Mead, Corpus Hermeticum XVIII, section 14](https://sacred-texts.com/gno/th2/th235.htm).
- [Corpus Hermeticum VI transcription](https://sacred-texts.com/chr/herm/hermes6.htm).
- User-supplied `Noita_Eye_Messages_E3_E4_Step_by_Step (1).pdf`, eight pages, identified by SHA-256 in [mead_candidate_audit.json](outputs/mead_candidate_audit.json). The PDF itself is not redistributed. Our review and independently checkable contradiction are included.

## Licensing and attribution

No repository-wide license has been chosen for the original research in this initial publication. Publication is not a representation that third-party material has been relicensed. Retain source attribution, respect the licenses attached to included corpora and external code, and obtain the relevant owner's authorization before adding or changing a license.

## Phase-switch continuation

The E4/W4/E5 bridge and adjacent late-phase observations come from [mvelzel/eye-vibe, synchronizing-bridge analysis](https://github.com/mvelzel/eye-vibe/blob/main/docs/thirty-second-synchronizing-bridge-results-2026-07-26.md). Our `outputs/phase-switch-findings.md` independently reconstructs the relevant maps and derives a conditional small-update obstruction. It does not replicate that source's statistical controls or adopt its broader interpretation.

## Arbitrary-feedback continuation

The [GarethLowe/Noita-Eyes research overview](https://github.com/GarethLowe/Noita-Eyes/blob/claude/bootstrap-files-extract-myxfgl/CLAUDE.md), accessed 2026-09-07, identifies nonlinear ciphertext-autokey feedback as open beyond affine tests. Our [five-context certificate](outputs/lookup-feedback-findings.md) addresses the stated shared-table additive family with a small encoded alphabet. The source is prior-work context; its other cipher exclusions are not adopted as independently verified.
