"""Utility for configuring the default DVC remote based on environment settings."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import Iterable


def _run(cmd: Iterable[str]) -> subprocess.CompletedProcess[str]:
    """Execute a DVC command and surface stderr on failure."""

    result = subprocess.run(
        list(cmd),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    return result


def _remote_exists(name: str) -> bool:
    """Return True when the remote already exists in the repo config."""

    result = _run(["dvc", "remote", "list"])
    for line in result.stdout.splitlines():
        parts = line.split()
        if parts and parts[0] == name:
            return True
    return False


def configure_remote(name: str, url: str, make_default: bool = True) -> None:
    """Create or update the configured remote."""

    if _remote_exists(name):
        _run(["dvc", "remote", "modify", name, "url", url])
    else:
        args = ["dvc", "remote", "add"]
        if make_default:
            args.append("-d")
        args.extend([name, url])
        _run(args)

    if make_default:
        _run(["dvc", "remote", "default", name])

    # Optional tuning for S3-compatible storage.
    endpoint = os.getenv("DVC_REMOTE_ENDPOINT")
    profile = os.getenv("DVC_REMOTE_PROFILE")
    credentialpath = os.getenv("DVC_REMOTE_CREDENTIALPATH")
    if endpoint:
        _run(["dvc", "remote", "modify", name, "endpointurl", endpoint])
    if profile:
        _run(["dvc", "remote", "modify", name, "profile", profile])
    if credentialpath:
        _run(["dvc", "remote", "modify", name, "credentialpath", credentialpath])



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure default DVC remote")
    parser.add_argument(
        "--name",
        default=os.getenv("DVC_REMOTE_NAME", "churn-remote"),
        help="Name of the remote (default: %(default)s or DVC_REMOTE_NAME)",
    )
    parser.add_argument(
        "--url",
        default=os.getenv("DVC_REMOTE_URL"),
        help="Remote URL (e.g. s3://bucket/path). Defaults to DVC_REMOTE_URL env.",
    )
    parser.add_argument(
        "--no-default",
        action="store_true",
        help="Do not mark the remote as default",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.url:
        raise SystemExit(
            "Remote URL not provided. Set --url or DVC_REMOTE_URL environment variable."
        )
    configure_remote(args.name, args.url, make_default=not args.no_default)
    print(f"Configured DVC remote '{args.name}' -> {args.url}")


if __name__ == "__main__":
    main()
