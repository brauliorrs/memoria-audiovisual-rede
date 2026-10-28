"""Verify GitHub's recorded independent deployment approval before Neon secrets.

Runs in the protected environment job *before* the secret-bearing integration
step. It never reads the Neon credential, only GitHub's approval history.
"""
from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPOSITORY = "brauliorrs/memoria-audiovisual-rede"
ENVIRONMENT = "mar-p0-neon-isolated"


def valid_independent_approval(
    records: Sequence[Mapping[str, object]], *, actor: str
) -> bool:
    """Require an explicit approved review for our environment by another human."""
    for record in records:
        if record.get("state") != "approved":
            continue
        user = record.get("user")
        if (
            not isinstance(user, dict)
            or user.get("type") != "User"
            or not isinstance(user.get("login"), str)
            or user["login"].casefold() == actor.casefold()
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
        or not run_id.isdecimal()
        or not actor
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
    if not isinstance(records, list) or not valid_independent_approval(
        records, actor=actor
    ):
        print("Gate P0 HOLD: independent_environment_approval_missing",
              file=sys.stderr)
        return 2
    print("Gate P0 human environment approval verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
