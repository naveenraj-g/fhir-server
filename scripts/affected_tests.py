"""Print the pytest command for the tests a change can affect.

    uv run python scripts/affected_tests.py            # uncommitted + untracked changes
    uv run python scripts/affected_tests.py HEAD~1     # changes since a revision

The rule (see CLAUDE.md, "Which tests to run"):

* a change confined to one resource's own files -> that resource's integration
  folder and its conformance file;
* a change that edits other resources' files (wiring, revinclude helpers) -> the
  folders of every resource it touches;
* a change to shared engine code (app/fhir/search, app/repository/_content_index,
  _reference_shared, app/core, app/models/shared, tests/conftest) -> everything,
  because every resource depends on it. The full run is slow (about an hour), so
  do it deliberately — e.g. once every resource is built.

Always included: tests/unit, tests/conformance and tests/integration/capability.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Paths whose change can affect every resource.
SHARED = (
    "app/fhir/search/",
    "app/fhir/validation/",
    "app/fhir/mappers/content.py",
    "app/fhir/input_payload.py",
    "app/repository/_content_index.py",
    "app/repository/_reference_shared.py",
    "app/repository/base.py",
    "app/routers/_fhir_search.py",
    "app/core/",
    "app/models/shared/",
    "app/main.py",
    "tests/conftest.py",
    "tests/helpers/",
)

# app/<layer>/<resource>/... and app/fhir/mappers/<resource>/...
RESOURCE_PATH = re.compile(
    r"^app/(?:models|repository|services|routers|schemas|fhir/mappers|di/modules|di/dependencies)/([a-z_]+?)(?:/|\.py$)"
)
TEST_PATH = re.compile(
    r"^tests/(?:integration|conformance)/(?:test_)?([a-z_]+?)(?:_fhir\.py$|/)"
)
MIGRATION = re.compile(r"^migrations/versions/[0-9a-z]+_([a-z_]+?)_content_jsonb")


def changed_files(rev: str | None) -> list[str]:
    def git(*args: str) -> list[str]:
        out = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
        return [line for line in out.splitlines() if line]

    if rev:
        return git("diff", "--name-only", rev)
    return sorted(
        set(git("diff", "--name-only", "HEAD"))
        | set(git("ls-files", "--others", "--exclude-standard"))
    )


def main() -> int:
    files = changed_files(sys.argv[1] if len(sys.argv) > 1 else None)
    if not files:
        print("No changes.")
        return 0

    if any(f.startswith(SHARED) for f in files):
        shared = [f for f in files if f.startswith(SHARED)]
        print(
            "Shared engine code changed:",
            ", ".join(shared[:5]) + (" ..." if len(shared) > 5 else ""),
        )
        print(
            "If the engine change only ADDS something (a new matcher no existing resource calls), the "
            "resource-level run below is enough; if it changes existing behavior, run everything."
        )
        print(
            "Run everything (slow):\n  uv run pytest tests/unit tests/conformance tests/integration -q -p no:cacheprovider"
        )
        print(
            "(`pytest tests` as a whole fails at collection — always pass the directories.)"
        )
        print()

    resources: set[str] = set()
    for f in files:
        for pattern in (RESOURCE_PATH, TEST_PATH, MIGRATION):
            match = pattern.match(f)
            if match:
                resources.add(match.group(1))
    # Shared revinclude helpers (app/repository/_<resource>_revinclude.py) name their resource.
    for f in files:
        match = re.match(r"^app/repository/_([a-z_]+?)_revinclude\.py$", f)
        if match:
            resources.add(
                match.group(1)
            )  # dropped below: only a resource's own folder is run

    # A shared revinclude helper (`_x_revinclude`) names a resource but is not one itself; the registries
    # that import it show up as changed files of their own. `capability` is always run.
    resources = {r for r in resources if not r.startswith("_")}
    folders = sorted(
        r
        for r in resources
        if (ROOT / "tests" / "integration" / r).is_dir() and r != "capability"
    )
    unmatched = sorted(r for r in resources if r not in folders and r != "capability")
    command = [
        "uv run pytest tests/unit tests/conformance tests/integration/capability"
    ]
    command += [f"tests/integration/{r}" for r in folders]
    print("Changed resources:", ", ".join(sorted(resources)) or "(none)")
    if unmatched:
        print("No integration folder for:", ", ".join(unmatched))
    print("Run:\n  " + " ".join(command) + " -q -p no:cacheprovider")
    print(
        "Slow runs (a resource's test_search.py takes ~3 minutes): use run_in_background and wait for the "
        "completion notification."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
