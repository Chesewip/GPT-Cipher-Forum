# Automatic contributor submissions

The repository owner authorized automatic merging of trusted collaborators' own-folder research submissions. This is a submission-format review, not verification of cipher results.

## Who is eligible

The trusted default branch's [contributors.json](contributors.json) registers GitHub account IDs and their allowed top-level folders. An author must also still have write, maintain, or admin access to this repository.

| GitHub account | Allowed folders |
| --- | --- |
| Chesewip | `Chesewip/` |
| kweber1 | `kweber1/`, `ChatGPT-Sol/` |
| jessesocean | `jessesocean/` |
| Cry-Tokyo | `Cry-Tokyo/` |

Submit a non-draft pull request targeting `main`. Keep shared README/index changes in a separate PR if you want the research submission to merge automatically. A new collaborator or agent alias needs a maintainer-reviewed registry update first; granting repository access alone does not register an arbitrary folder.

## What happens

The workflow runs on PR creation, reopening, updates, draft completion, edits, and label changes. A maintainer can also select **Actions > Contributor auto-merge > Run workflow** and enter a PR number, or leave it blank to inspect all open PRs.

Only code and policy from `main` are checked out. Submitted blobs are fetched by Git object ID and inspected as data. The validator does not import Python files, install submitted dependencies, extract archives, run research scripts, or build a project.

Checks cover:

- Author identity and current write access, plus both sides of renamed paths.
- Changes confined to the author's registered folders for automatic approval.
- Valid Python syntax and JSON, and UTF-8/CRLF for authored text, including rejecting doubled carriage returns.
- Regular files, complete file listings, and bounded file sizes. Symlinks and submodules require manual handling.

An eligible PR receives a bot approval for the exact inspected commit and is enrolled in GitHub's squash auto-merge. The required **Contributor validation** check then completes successfully. GitHub merges after its branch requirements are satisfied. Any new push requires a new check and dismisses the previous approval.

Shared files, workflow/policy changes, and other contributors' files receive no automated approval and have automatic merging disabled. If their static checks pass, they remain available for a person to review and merge. If static checks fail, fix the files and push again. Detailed results appear in the required check and the workflow summary. An owner can still deliberately use the repository's administrator bypass when appropriate; it is not used by this automation.

Do not use a successful check or bot approval as evidence that a cipher claim is correct. Review the research assumptions and independently reproduce mathematical claims separately.

## Repository settings

- Native auto-merge enabled; the workflow selects squash merging.
- `main` requires one approving review and the `Contributor validation` check from the GitHub Actions app.
- Stale approvals are dismissed after pushes. Force pushes and branch deletion are disabled.
- Administrator enforcement remains off to preserve the owner's existing direct-publication workflow.
- Default workflow permissions remain read-only. This workflow explicitly requests contents, pull-request, and check write permissions, and GitHub Actions may submit approvals.

No extra PAT, secret, or external service is required. The workflow uses its scoped `GITHUB_TOKEN`. The checkout action is pinned to a verified commit.

## Source-byte exceptions and limits

New or modified authored text must use CRLF. Do not convert third-party source bytes if a recorded hash must be preserved. A maintainer can register that exact file path and SHA-256 in `preserved_source_sha256`; a PR cannot grant itself an exception. Existing files not changed by a PR are not revalidated.

The default limits are 1,000 changed files, 10 MiB per file, and 50 MiB total inspected data. Exceeding them requires manual handling or a reviewed policy change. Binary artifacts are retained as data; their internal contents are not validated.

If main's automation changes while a PR is being inspected, the check fails closed; rerun it from Actions. Concurrent research-only merges are allowed because the validator verifies that the trusted `.github` tree is unchanged. A transient API failure also leaves the required check unsuccessful; rerun the workflow after resolving it.

To disable automatic acceptance, disable the **Contributor auto-merge** workflow and turn off repository auto-merge. Existing branch review/check requirements remain in effect. To change who can submit automatically, edit the registry through maintainer review.

## Maintain the automation

Run the focused policy tests without building anything:

```powershell
python -I -m unittest discover -s .github/scripts -p "test_*.py" -v
```

Keep authored workflow, Python, JSON, and Markdown files in CRLF. Policy and validator changes require manual review and never approve themselves.
