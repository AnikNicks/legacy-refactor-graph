#!/usr/bin/env python3
"""Guardrail CLI for the legacy-refactor-agent pipeline.

Usage:
    python scripts/validate_state.py preflight --target <path>
    python scripts/validate_state.py validate --schema <Name> --file <path>
    python scripts/validate_state.py stage-diff-check --stage <n> --target <path>

Prints GUARDRAIL_PASS or GUARDRAIL_FAIL (with reasons) and exits 0/1 accordingly.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import schemas  # noqa: E402

SCHEMA_MAP = {
    "ArchaeologyReport": schemas.ArchaeologyReport,
    "RiskAssessment": schemas.RiskAssessment,
    "RefactorPlan": schemas.RefactorPlan,
    "StageResult": schemas.StageResult,
}


def _fail(*lines):
    print("GUARDRAIL_FAIL")
    for line in lines:
        print(f"  - {line}")
    return 1


def cmd_preflight(args):
    errors = []

    target = REPO_ROOT / args.target
    if not target.exists():
        errors.append(f"target path does not exist: {args.target}")

    git_dir = REPO_ROOT / ".git"
    if not git_dir.exists():
        errors.append("no git repository found at repo root")
    else:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        branch = result.stdout.strip()
        if branch == "main":
            errors.append("current branch is 'main' - pipeline phases must run on a dedicated branch")
        elif not branch:
            errors.append("could not determine current branch (detached HEAD or no commits yet)")

    output_dir = REPO_ROOT / "output"
    if not output_dir.is_dir():
        errors.append("output/ directory is missing")

    if errors:
        return _fail(*errors)

    print("GUARDRAIL_PASS: preflight ok")
    return 0


def cmd_validate(args):
    schema_cls = SCHEMA_MAP.get(args.schema)
    if schema_cls is None:
        return _fail(f"unknown schema: {args.schema} (known: {', '.join(SCHEMA_MAP)})")

    file_path = Path(args.file)
    if not file_path.exists():
        return _fail(f"file does not exist: {args.file}")

    try:
        data = json.loads(file_path.read_text())
    except json.JSONDecodeError as e:
        return _fail(f"invalid JSON: {e}")

    try:
        schema_cls.model_validate(data)
    except Exception as e:
        return _fail(str(e))

    print(f"GUARDRAIL_PASS: {args.file} matches {args.schema}")
    return 0


def cmd_stage_diff_check(args):
    target_prefix = args.target.rstrip("/") + "/"
    allowed_prefixes = (target_prefix, "tests/")

    # Checks the most recent commit's changed files — this runs *after* the
    # stage's commit, per the Phase 5 loop in GRAPH.md.
    diff = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        return _fail(f"git diff failed: {diff.stderr.strip()}")

    changed = [line for line in diff.stdout.splitlines() if line.strip()]
    if not changed:
        return _fail(f"no changes found in the latest commit for stage {args.stage} - nothing to check")

    offenders = [f for f in changed if not f.startswith(allowed_prefixes)]
    if offenders:
        return _fail(
            f"stage {args.stage} touched files outside {allowed_prefixes}:",
            *offenders,
        )

    print(f"GUARDRAIL_PASS: stage {args.stage} diff stays within {allowed_prefixes}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_pre = sub.add_parser("preflight")
    p_pre.add_argument("--target", required=True)
    p_pre.set_defaults(func=cmd_preflight)

    p_val = sub.add_parser("validate")
    p_val.add_argument("--schema", required=True)
    p_val.add_argument("--file", required=True)
    p_val.set_defaults(func=cmd_validate)

    p_diff = sub.add_parser("stage-diff-check")
    p_diff.add_argument("--stage", required=True, type=int)
    p_diff.add_argument("--target", required=True)
    p_diff.set_defaults(func=cmd_stage_diff_check)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
