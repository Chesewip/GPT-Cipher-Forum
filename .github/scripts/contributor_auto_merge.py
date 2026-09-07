"""Validate PR blobs as data, then approve/auto-merge authorized own-folder PRs.

Only the trusted main-branch checkout supplies code and policy. Submitted
Python is parsed, never imported or executed. No PR checkout or build occurs.
"""
import ast
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import urllib.error
import urllib.request

TEXT_SUFFIXES = {
    '.py', '.json', '.jsonl', '.ndjson', '.md', '.txt', '.csv', '.tsv',
    '.toml', '.yaml', '.yml', '.sha256', '.rst', '.ps1', '.sh', '.bat',
    '.cfg', '.ini', '.tex', '.bib', '.log', '.html', '.css', '.js', '.ts',
    '.xml', '.svg', '.r', '.sql', '.c', '.cpp', '.h',
}
TEXT_NAMES = {'LICENSE', 'NOTICE', 'Makefile', '.gitignore', '.gitattributes'}


class GitHub:
    def __init__(self, repository, token):
        self.repository = repository
        self.token = token

    def request(self, path, method='GET', data=None):
        request = urllib.request.Request(
            'https://api.github.com/' + path.lstrip('/'), method=method,
            data=None if data is None else json.dumps(data).encode('utf-8'),
            headers={'Authorization': 'Bearer ' + self.token,
                     'Accept': 'application/vnd.github+json',
                     'Content-Type': 'application/json',
                     'X-GitHub-Api-Version': '2022-11-28',
                     'User-Agent': 'Cipher-Forum-contributor-validation'})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as error:
            # Do not print response bodies, request headers, or credentials.
            raise RuntimeError(f'GitHub API {method} returned HTTP {error.code}') from None

    def repo(self, path, method='GET', data=None):
        return self.request('repos/' + self.repository + '/' + path, method, data)

    def pages(self, path, limit=1000):
        result = []
        for page in range(1, limit // 100 + 2):
            rows = self.repo(f'{path}{"&" if "?" in path else "?"}per_page=100&page={page}')
            result.extend(rows)
            if len(result) > limit:
                raise ValueError('Pagination exceeds the configured limit; manual review required')
            if len(rows) < 100:
                return result
        raise ValueError('Incomplete API pagination')

    def graphql(self, query, variables):
        result = self.request('graphql', 'POST', {'query': query, 'variables': variables})
        if result.get('errors'):
            raise RuntimeError('GitHub GraphQL rejected the auto-merge change')
        return result['data']


def safe_path(name):
    path = PurePosixPath(name)
    return (bool(name) and not path.is_absolute() and '\\' not in name
            and str(path) == name and all(p not in {'.', '..', ''} for p in path.parts)
            and not any(ord(c) < 32 or ord(c) == 127 for c in name))


def eligibility(pr, files, policy, permission):
    reasons = []
    user = pr['user']
    entry = policy['contributors'].get(user['login'])
    if not entry or entry['github_id'] != user['id']:
        reasons.append('Author is not registered by GitHub account ID')
    if permission not in {'write', 'maintain', 'admin'}:
        reasons.append('Author does not currently have repository write access')
    if pr['base']['ref'] != policy['base_branch'] or pr.get('draft'):
        reasons.append('Only ready-for-review PRs targeting main can auto-merge')
    folders = set(entry['folders']) if entry else set()
    for file in files:
        for name in [file['filename']] + ([file['previous_filename']] if 'previous_filename' in file else []):
            if not safe_path(name):
                reasons.append('An unsafe or ambiguous path needs manual review')
            elif len(PurePosixPath(name).parts) < 2 or PurePosixPath(name).parts[0] not in folders:
                reasons.append('Changes include shared files or another contributor folder')
    return sorted(set(reasons))


def validate_blob(name, data, mode, policy):
    if not safe_path(name):
        raise ValueError('Unsafe or ambiguous filename')
    if mode not in {'100644', '100755'}:
        raise ValueError('Symlinks and submodules require manual handling')
    if len(data) > policy['max_file_bytes']:
        raise ValueError('File exceeds automatic validation size limit')
    expected = policy.get('preserved_source_sha256', {}).get(name)
    if expected and hashlib.sha256(data).hexdigest() == expected:
        return
    suffix = PurePosixPath(name).suffix.lower()
    known_text = suffix in TEXT_SUFFIXES or PurePosixPath(name).name in TEXT_NAMES
    if not known_text:
        # Also enforce line endings on extensionless/unknown UTF-8 text.
        if b'\x00' in data:
            return
        try:
            text = data.decode('utf-8-sig')
        except UnicodeDecodeError:
            return  # Binary artifacts are stored, never opened or executed.
    else:
        text = data.decode('utf-8-sig')
    if '\x00' in text:
        raise ValueError('NUL byte in a text file')
    remaining = data.replace(b'\r\n', b'')
    if b'\n' in remaining or b'\r' in remaining:
        raise ValueError('Authored text must use CRLF, without bare CR or LF')
    if suffix == '.json':
        json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-standard JSON constant')))
    elif suffix in {'.jsonl', '.ndjson'}:
        for line in text.splitlines():
            if line.strip():
                json.loads(line)
    elif suffix == '.py':
        ast.parse(text, filename=name)


def inspect_files(api, pr, files, policy):
    tree = api.repo('git/trees/' + pr['head']['sha'] + '?recursive=1')
    if tree.get('truncated'):
        raise ValueError('Truncated file tree; manual review required')
    entries = {entry['path']: entry for entry in tree['tree']}
    total = 0
    errors = []
    for file in files:
        name = file['filename']
        try:
            if not safe_path(name):
                raise ValueError('Unsafe or ambiguous filename')
            if file['status'] == 'removed':
                continue
            entry = entries[name]
            if entry['type'] != 'blob' or entry['mode'] not in {'100644', '100755'}:
                raise ValueError('Symlinks and submodules require manual handling')
            if entry.get('size', policy['max_file_bytes'] + 1) > policy['max_file_bytes']:
                raise ValueError('File exceeds automatic validation size limit')
            blob = api.repo('git/blobs/' + entry['sha'])
            if blob['encoding'] != 'base64':
                raise ValueError('Unsupported blob encoding')
            data = base64.b64decode(blob['content'], validate=False)
            # Authenticate the returned data against the pinned head's Git tree.
            actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if actual != entry['sha']:
                raise ValueError('Blob does not match the pinned Git object')
            total += len(data)
            if total > policy['max_total_bytes']:
                raise ValueError('PR exceeds automatic validation total size limit')
            validate_blob(name, data, entry['mode'], policy)
        except (ValueError, SyntaxError, UnicodeError, KeyError, RecursionError) as error:
            # Log bounded filenames/reasons; never render submitted source text.
            reason = str(error) if isinstance(error, ValueError) and not isinstance(error, UnicodeError) else type(error).__name__
            if isinstance(error, SyntaxError):
                reason = f'Python syntax error at line {error.lineno}: {error.msg}'
            errors.append(f'{name!r}: {reason[:160]}')
    return errors


def trusted_policy_unchanged(api, trusted_sha, current_sha):
    if trusted_sha == current_sha:
        return True
    # Concurrent research merges may move main without changing automation.
    # Compare the whole trusted .github tree before issuing an approval.
    def automation_tree(commit):
        tree = api.repo('git/trees/' + commit)
        return next((e['sha'] for e in tree['tree']
                     if e['path'] == '.github' and e['type'] == 'tree'), None)
    trusted = automation_tree(trusted_sha)
    return bool(trusted) and trusted == automation_tree(current_sha)


def process(api, number, policy, trusted_sha):
    pr = api.repo(f'pulls/{number}')
    if pr['state'] != 'open':
        return {'pr': number, 'status': 'already closed'}
    sha = pr['head']['sha']
    check = api.repo('check-runs', 'POST', {'name': policy['check_name'], 'head_sha': sha,
        'status': 'in_progress', 'output': {'title': 'Inspecting submitted files',
        'summary': 'Checks use trusted main-branch code. Submitted code is never executed.'}})
    conclusion = 'failure'
    summary = 'Validation did not complete; no automated approval is authorized.'
    try:
        files = api.pages(f'pulls/{number}/files', policy['max_files'])
        if not files or len(files) != pr['changed_files']:
            raise ValueError('Incomplete or empty changed-file list')
        login = pr['user']['login']
        permission = api.repo(f'collaborators/{login}/permission')['permission']
        reasons = eligibility(pr, files, policy, permission)
        errors = inspect_files(api, pr, files, policy)
        # Refuse an approval if either the candidate or trusted policy changed.
        fresh = api.repo(f'pulls/{number}')
        current_base = api.repo('git/ref/heads/' + policy['base_branch'])['object']['sha']
        if (fresh['head']['sha'] != sha or fresh['state'] != 'open'
                or fresh['base']['ref'] != pr['base']['ref']
                or fresh.get('draft') != pr.get('draft')
                or not trusted_policy_unchanged(api, trusted_sha, current_base)):
            raise ValueError('Head or trusted main changed during validation; rerun against current commits')
        if errors or reasons:
            if fresh.get('auto_merge'):
                api.graphql('mutation($id:ID!){disablePullRequestAutoMerge(input:{pullRequestId:$id}){pullRequest{id}}}', {'id': pr['node_id']})
            for review in api.pages(f'pulls/{number}/reviews'):
                if (review['user']['login'] == 'github-actions[bot]' and review['state'] == 'APPROVED'
                        and review.get('body', '').startswith('Automated submission-policy approval:')):
                    api.repo(f'pulls/{number}/reviews/{review["id"]}/dismissals', 'PUT',
                             {'message': 'This submission requires manual review under the current policy.'})
            summary = '\n'.join(['Manual review required.'] + reasons + errors[:30])
            conclusion = 'failure' if errors else 'success'
            result = {'pr': number, 'status': 'manual review', 'reasons': reasons, 'errors': errors}
        else:
            reviews = api.pages(f'pulls/{number}/reviews')
            already_approved = any(r['user']['login'] == 'github-actions[bot]' and r['state'] == 'APPROVED'
                                   and r.get('commit_id') == sha for r in reviews)
            if not already_approved:
                api.repo(f'pulls/{number}/reviews', 'POST', {'commit_id': sha, 'event': 'APPROVE',
                    'body': 'Automated submission-policy approval: registered collaborator, own folders only, and static file checks passed. This does not verify the cipher research.'})
            # The required check is still pending, so auto-merge waits for its
            # success. Protection dismisses this approval on subsequent pushes.
            if not fresh.get('auto_merge'):
                api.graphql('mutation($id:ID!){enablePullRequestAutoMerge(input:{pullRequestId:$id,mergeMethod:SQUASH}){pullRequest{id}}}', {'id': pr['node_id']})
            conclusion = 'success'
            summary = 'Registered collaborator and own-folder policy passed. Python/JSON syntax and text CRLF checked. Auto-merge enabled; research claims were not executed or authenticated.'
            result = {'pr': number, 'status': 'auto-merge enabled', 'head_sha': sha, 'files': len(files)}
    except Exception:
        # Keep the required check failed even for API failures or races.
        raise
    finally:
        api.repo('check-runs/' + str(check['id']), 'PATCH', {'status': 'completed',
            'conclusion': conclusion, 'output': {'title': 'Submission validation ' + conclusion,
            'summary': summary[:60000]}})
    return result


def main():
    policy = json.loads((Path(__file__).resolve().parents[1] / 'contributors.json').read_text(encoding='utf-8'))
    repository = os.environ['GITHUB_REPOSITORY']
    api = GitHub(repository, os.environ['GH_TOKEN'])
    # Checkout's actual commit, supplied by the workflow after the trusted checkout.
    trusted_sha = os.environ['TRUSTED_BASE_SHA']
    number = os.environ.get('PR_NUMBER', '').strip()
    numbers = [int(number)] if number else [p['number'] for p in api.pages('pulls?state=open')]
    results = [process(api, n, policy, trusted_sha) for n in numbers]
    print(json.dumps(results, indent=2))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        Path(os.environ['GITHUB_STEP_SUMMARY']).write_text('```json\n' + json.dumps(results, indent=2) + '\n```\n', encoding='utf-8')


if __name__ == '__main__':
    main()
