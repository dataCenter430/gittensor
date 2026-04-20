# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Regression tests for `issues list --json` and related view command error handling."""

import json
import sys
import types
from unittest.mock import patch

class _FakeSubstrate:
    def __init__(self, url=None):
        pass


_SUBSTRATE_EXCEPTIONS_STUB = types.SimpleNamespace(ExtrinsicNotFound=Exception)
_SUBSTRATE_STUB = types.SimpleNamespace(
    SubstrateInterface=_FakeSubstrate,
    Keypair=object,
    exceptions=_SUBSTRATE_EXCEPTIONS_STUB,
)


def _patch_substrate():
    return patch.dict(
        sys.modules,
        {
            'substrateinterface': _SUBSTRATE_STUB,
            'substrateinterface.exceptions': _SUBSTRATE_EXCEPTIONS_STUB,
        },
    )

FAKE_ISSUES = [
    {
        'id': 1,
        'repository_full_name': 'owner/repo',
        'issue_number': 10,
        'bounty_amount': 50_000_000_000,
        'target_bounty': 100_000_000_000,
        'status': 'Active',
    },
]


def test_issues_list_json_missing_issue_returns_structured_error(cli_root, runner):
    """Requesting a nonexistent issue ID must return a structured JSON error with non-zero exit."""
    with (
        patch(
            'gittensor.cli.issue_commands.view._resolve_contract_and_network',
            return_value=('5Fakeaddr', 'ws://x', 'test'),
        ),
        patch('gittensor.cli.issue_commands.view.read_issues_from_contract', return_value=FAKE_ISSUES),
    ):
        result = runner.invoke(cli_root, ['issues', 'list', '--json', '--id', '999'], catch_exceptions=False)

    assert result.exit_code != 0

    payload = json.loads(result.output)
    assert payload['success'] is False
    assert payload['error']['type'] == 'not_found'
    assert '999' in payload['error']['message']


def test_issues_bounty_pool_json_error_returns_structured_json(cli_root, runner):
    """Network failure in bounty-pool --json must return structured JSON, not plain text."""
    with (
        _patch_substrate(),
        patch(
            'gittensor.cli.issue_commands.view._resolve_contract_and_network',
            return_value=('5Fakeaddr', 'ws://x', 'test'),
        ),
        patch(
            'gittensor.cli.issue_commands.view._read_issues_from_child_storage',
            side_effect=RuntimeError('connection refused'),
        ),
    ):
        result = runner.invoke(cli_root, ['issues', 'bounty-pool', '--json'], catch_exceptions=False)

    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload['success'] is False
    assert 'connection refused' in payload['error']['message']


def test_issues_pending_harvest_json_error_returns_structured_json(cli_root, runner):
    """Network failure in pending-harvest --json must return structured JSON, not plain text."""
    with (
        _patch_substrate(),
        patch(
            'gittensor.cli.issue_commands.view._resolve_contract_and_network',
            return_value=('5Fakeaddr', 'ws://x', 'test'),
        ),
        patch('gittensor.cli.issue_commands.view._read_issues_from_child_storage', side_effect=RuntimeError('timeout')),
    ):
        result = runner.invoke(cli_root, ['issues', 'pending-harvest', '--json'], catch_exceptions=False)

    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload['success'] is False
    assert 'timeout' in payload['error']['message']


def test_admin_info_json_error_returns_structured_json(cli_root, runner):
    """Contract read failure in admin info --json must return structured JSON, not plain text."""
    with (
        _patch_substrate(),
        patch(
            'gittensor.cli.issue_commands.view._resolve_contract_and_network',
            return_value=('5Fakeaddr', 'ws://x', 'test'),
        ),
        patch(
            'gittensor.cli.issue_commands.view._read_contract_packed_storage',
            side_effect=RuntimeError('decode error'),
        ),
    ):
        result = runner.invoke(cli_root, ['admin', 'info', '--json'], catch_exceptions=False)

    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload['success'] is False
    assert 'decode error' in payload['error']['message']
