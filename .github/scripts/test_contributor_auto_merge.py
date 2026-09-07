"""Focused policy and API-flow tests; no research code or project build."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import unittest
from contributor_auto_merge import discard_root_readme, eligibility, process, safe_path, trusted_policy_unchanged, validate_blob

POLICY = json.loads((Path(__file__).resolve().parents[1] / 'contributors.json').read_text(encoding='utf-8'))
PR = {'number': 2, 'node_id': 'test-pr', 'state': 'open', 'draft': False,
      'user': {'login': 'kweber1', 'id': 38956382}, 'head': {'sha': 'head'},
      'base': {'ref': 'main'}, 'changed_files': 1, 'auto_merge': None}


class FakeGitHub:
    repository = 'Chesewip/GPT-Cipher-Forum'
    def __init__(self, name='ChatGPT-Sol/example.py', data=b'answer = 42\r\n', fresh=None):
        self.name = name
        self.data = data
        self.fresh = fresh or copy.deepcopy(PR)
        self.pr_reads = 0
        self.base = 'trusted-main'
        self.calls = []
        self.sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

    def repo(self, path, method='GET', data=None):
        self.calls.append((path, method, data))
        if method != 'GET':
            return {'id': 100}
        if path == 'pulls/2':
            self.pr_reads += 1
            return copy.deepcopy(PR if self.pr_reads == 1 else self.fresh)
        if path.startswith('collaborators/'):
            return {'permission': 'write'}
        if path.startswith('git/trees/'):
            return {'truncated': False, 'tree': [{'path': self.name, 'type': 'blob',
                    'mode': '100644', 'size': len(self.data), 'sha': self.sha}]}
        if path.startswith('git/blobs/'):
            return {'encoding': 'base64', 'content': base64.b64encode(self.data).decode()}
        if path.startswith('git/ref/'):
            return {'object': {'sha': self.base}}
        raise AssertionError(path)

    def pages(self, path, limit=1000):
        if path.endswith('/files'):
            return [{'filename': self.name, 'status': 'added'}]
        if path.endswith('/reviews'):
            return []
        raise AssertionError(path)

    def graphql(self, query, variables):
        self.calls.append(('graphql', query, variables))
        return {}


class PolicyTests(unittest.TestCase):
    def test_author_scope_and_identity(self):
        files = [{'filename': 'ChatGPT-Sol/results/value.json'}]
        self.assertEqual(eligibility(PR, files, POLICY, 'write'), [])
        for change in [{'filename': 'README.md'}, {'filename': 'Chesewip/file.py'},
                       {'filename': 'ChatGPT-Sol/new.md', 'previous_filename': 'README.md'}]:
            self.assertTrue(eligibility(PR, [change], POLICY, 'write'))
        other = copy.deepcopy(PR)
        other['user']['id'] = 1
        self.assertTrue(eligibility(other, files, POLICY, 'write'))
        self.assertTrue(eligibility(PR, files, POLICY, 'read'))
        other = copy.deepcopy(PR)
        other['draft'] = True
        self.assertTrue(eligibility(other, files, POLICY, 'write'))

    def test_paths(self):
        for name in ['../README.md', '/README.md', 'a/../README.md', 'a//b', 'a\\b', 'a/b\n']:
            self.assertFalse(safe_path(name), name)
        self.assertTrue(safe_path('ChatGPT-Sol/reports/result.md'))

    def test_static_parsing_and_crlf(self):
        # This parses successfully; running/importing it would fail the test.
        validate_blob('x.py', b'raise RuntimeError("MUST NOT EXECUTE")\r\n', '100644', POLICY)
        validate_blob('x.json', b'{"ok": true}\r\n', '100644', POLICY)
        for name, data in [('x.py', b'def broken(:\r\n'), ('x.json', b'{bad}\r\n'),
                           ('x.md', b'LF only\n'), ('x.md', b'bad\r\r\n'),
                           ('x.json', b'{"n": NaN}\r\n')]:
            with self.assertRaises((ValueError, SyntaxError)):
                validate_blob(name, data, '100644', POLICY)
        with self.assertRaises(ValueError):
            validate_blob('x.py', b'pass\r\n', '120000', POLICY)

    def test_success_approves_exact_head_before_completing_required_check(self):
        api = FakeGitHub()
        self.assertEqual(process(api, 2, POLICY, 'trusted-main')['status'], 'auto-merge enabled')
        review = next(c for c in api.calls if c[0] == 'pulls/2/reviews')
        self.assertEqual(review[2]['commit_id'], 'head')
        self.assertEqual(review[2]['event'], 'APPROVE')
        self.assertEqual(api.calls[-1][2]['conclusion'], 'success')
        self.assertIn('enablePullRequestAutoMerge', api.calls[-2][1])

    def test_shared_file_requires_review_without_bot_approval(self):
        api = FakeGitHub('CONTRIBUTING.md', b'Shared documentation\r\n')
        self.assertEqual(process(api, 2, POLICY, 'trusted-main')['status'], 'manual review')
        self.assertFalse(any(c[0] == 'pulls/2/reviews' for c in api.calls))
        self.assertEqual(api.calls[-1][2]['conclusion'], 'success')

    def test_invalid_blob_never_approved(self):
        api = FakeGitHub(data=b'invalid python (\r\n')
        self.assertEqual(process(api, 2, POLICY, 'trusted-main')['status'], 'manual review')
        self.assertFalse(any(c[0] == 'pulls/2/reviews' for c in api.calls))
        self.assertEqual(api.calls[-1][2]['conclusion'], 'failure')

    def test_changed_head_base_or_draft_fails_closed(self):
        for field in ['head', 'base', 'draft', 'trusted']:
            fresh = copy.deepcopy(PR)
            if field == 'head': fresh['head']['sha'] = 'new-head'
            if field == 'base': fresh['base']['ref'] = 'different-branch'
            if field == 'draft': fresh['draft'] = True
            api = FakeGitHub(fresh=fresh)
            if field == 'trusted': api.base = 'new-main'
            with self.assertRaises(ValueError):
                process(api, 2, POLICY, 'trusted-main')
            self.assertFalse(any(c[0] == 'pulls/2/reviews' for c in api.calls))
            self.assertEqual(api.calls[-1][2]['conclusion'], 'failure')

    def test_ineligible_change_disables_existing_auto_merge(self):
        fresh = copy.deepcopy(PR)
        fresh['auto_merge'] = {'enabled': True}
        api = FakeGitHub('README.md', b'Shared docs\r\n', fresh)
        process(api, 2, POLICY, 'trusted-main')
        self.assertTrue(any('disablePullRequestAutoMerge' in c[1] for c in api.calls if c[0] == 'graphql'))

    def test_concurrent_research_merge_keeps_same_trusted_policy(self):
        class Trees:
            def repo(self, path):
                return {'tree': [{'path': '.github', 'type': 'tree', 'sha': 'same-policy'}]}
        self.assertTrue(trusted_policy_unchanged(Trees(), 'old-main', 'new-main'))

    def test_obsolete_policy_approval_is_dismissed(self):
        class PreviousApproval(FakeGitHub):
            def pages(self, path, limit=1000):
                if path.endswith('/reviews'):
                    return [{'id': 77, 'user': {'login': 'github-actions[bot]'}, 'state': 'APPROVED',
                             'body': 'Automated submission-policy approval: earlier run'}]
                return super().pages(path, limit)
        api = PreviousApproval('README.md', b'Shared docs\r\n')
        process(api, 2, POLICY, 'trusted-main')
        self.assertTrue(any(c[0] == 'pulls/2/reviews/77/dismissals' for c in api.calls))

    def test_chesewip_may_update_root_and_contributor_readmes(self):
        owner = copy.deepcopy(PR)
        owner['user'] = {'login': 'Chesewip', 'id': 67127680}
        files = [{'filename': 'README.md'}, {'filename': 'Chesewip/README.md'}]
        self.assertEqual(eligibility(owner, files, POLICY, 'admin'), [])
        self.assertEqual(eligibility(PR, [{'filename': 'ChatGPT-Sol/README.md'}], POLICY, 'write'), [])
        self.assertTrue(eligibility(PR, [{'filename': 'README.md'}], POLICY, 'write'))

    def test_unrestorable_nonowner_root_change_fails_the_required_check(self):
        api = FakeGitHub('README.md', b'Unauthorized root text\r\n')
        result = process(api, 2, POLICY, 'trusted-main')
        self.assertEqual(result['status'], 'manual review')
        self.assertEqual(api.calls[-1][2]['conclusion'], 'failure')
        self.assertFalse(any(c[0] == 'pulls/2/reviews' for c in api.calls))


class RestoreAPI:
    repository = 'Chesewip/GPT-Cipher-Forum'

    def __init__(self, race=False):
        self.calls = []
        self.pr = copy.deepcopy(PR)
        self.pr['head'].update(ref='contributor/topic', repo={'full_name': self.repository})
        self.race = race

    def repo(self, path, method='GET', data=None):
        self.calls.append((path, method, data))
        if path == 'git/ref/heads/main': return {'object': {'sha': 'trusted-main'}}
        if path == 'compare/trusted-main...head': return {'merge_base_commit': {'sha': 'common-ancestor'}}
        if path == 'git/trees/common-ancestor':
            return {'tree': [{'path': 'README.md', 'sha': 'original-readme-blob', 'mode': '100644', 'type': 'blob'}]}
        if path == 'git/commits/head': return {'tree': {'sha': 'all-contributor-files'}}
        if path == 'pulls/2':
            p = copy.deepcopy(self.pr)
            if self.race: p['head']['sha'] = 'new-contributor-commit'
            return p
        if path == 'git/trees' and method == 'POST': return {'sha': 'restored-tree'}
        if path == 'git/commits' and method == 'POST': return {'sha': 'restoration-commit'}
        if path == 'git/refs/heads/contributor%2Ftopic' and method == 'PATCH': return {}
        raise AssertionError((path, method))


class ReadmeRestorationTests(unittest.TestCase):
    def test_only_root_blob_is_restored_and_history_is_preserved(self):
        api = RestoreAPI()
        files = [{'filename': 'README.md', 'status': 'modified'},
                 {'filename': 'ChatGPT-Sol/README.md', 'status': 'added'}]
        result = discard_root_readme(api, api.pr, files, POLICY, 'write', 'trusted-main')
        self.assertEqual(result, 'restoration-commit')
        tree = next(c[2] for c in api.calls if c[:2] == ('git/trees', 'POST'))
        self.assertEqual(tree['base_tree'], 'all-contributor-files')
        self.assertEqual(tree['tree'], [{'path': 'README.md', 'mode': '100644',
                                        'type': 'blob', 'sha': 'original-readme-blob'}])
        commit = next(c[2] for c in api.calls if c[:2] == ('git/commits', 'POST'))
        self.assertEqual(commit['parents'], ['head'])
        self.assertEqual(api.calls[-1][2], {'sha': 'restoration-commit', 'force': False})

    def test_concurrent_update_is_not_overwritten(self):
        api = RestoreAPI(race=True)
        with self.assertRaises(ValueError):
            discard_root_readme(api, api.pr, [{'filename': 'README.md'}], POLICY, 'write', 'trusted-main')
        self.assertFalse(any(c[1] != 'GET' for c in api.calls))

    def test_owner_or_fork_or_root_rename_is_not_rewritten(self):
        for kind in ['owner', 'fork', 'rename']:
            api = RestoreAPI()
            files = [{'filename': 'README.md'}]
            if kind == 'owner': api.pr['user'] = {'login': 'Chesewip', 'id': 67127680}
            if kind == 'fork': api.pr['head']['repo']['full_name'] = 'someone/fork'
            if kind == 'rename': files[0]['previous_filename'] = 'ChatGPT-Sol/README.md'
            self.assertIsNone(discard_root_readme(api, api.pr, files, POLICY, 'write', 'trusted-main'))
            self.assertEqual(api.calls, [])


if __name__ == '__main__':
    unittest.main()
