"""Fail closed unless GitHub records an explicit manual P0 environment approval.

Solo-maintainer mode: only the repository owner may both trigger and approve
this narrowly scoped, SHA-pinned, synthetic-only workflow. GitHub must hold the
job until manual review; a bypass or missing review is never sufficient.
No Neon credential is loaded by this script.
"""
from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPOSITORY = "brauliorrs/memoria-audiovisual-rede"
OWNER = "brauliorrs"
ENVIRONMENT = "mar-p0-neon-isolated"
HEAD_REF = "feature/mar-p0-neon-storage-20261021"


def valid_owner_approval(
    records: Sequence[Mapping[str, object]], *, actor: str
) -> bool:
    """Require an approved deployment record, by owner, for this environment."""
    if actor.casefold() != OWNER:
        return False
    for record in records:
        if not isinstance(record, dict) or record.get("state") != "approved":
            continue
        user = record.get("user")
        if (
            not isinstance(user, dict)
            or user.get("type") != "User"
            or not isinstance(user.get("login"), str)
            or user["login"].casefold() != OWNER
        ):
            continue
        environments = record.get("environments")
        if not isinstance(environments, list):
            continue
        if any(
            isinstance(environment, dict)
            and environment.get("name") == ENVIRONMENT
            for environment in environments
        ):
            return True
    return False


def main() -> int:
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    actor = os.environ.get("GITHUB_ACTOR", "")
    token = os.environ.get("GH_TOKEN", "")
    if (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
        or os.environ.get("GITHUB_RUN_ATTEMPT") != "1"
        or os.environ.get("GITHUB_EVENT_NAME") != "pull_request"
        or os.environ.get("GITHUB_REF") != "refs/pull/90/merge"
        or os.environ.get("GITHUB_HEAD_REF") != HEAD_REF
        or actor.casefold() != OWNER
        or not run_id.isdecimal()
        or not token
    ):
        print("Gate P0 HOLD: approval_check_context_invalid", file=sys.stderr)
        return 2
    request = Request(
        f"https://api.github.com/repos/{REPOSITORY}/actions/runs/"
        f"{run_id}/approvals",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            records = json.load(response)
    except (HTTPError, URLError, ValueError, TimeoutError, OSError):
        print("Gate P0 HOLD: approval_history_unavailable", file=sys.stderr)
        return 2
    if not isinstance(records, list) or not valid_owner_approval(
        records, actor=actor
    ):
        print("Gate P0 HOLD: explicit_owner_environment_approval_missing",
              file=sys.stderr)
        return 2
    print("Gate P0 explicit solo-owner environment approval verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
