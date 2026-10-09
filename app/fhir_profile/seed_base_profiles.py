"""Seed base-layer FHIR profiles into fhir_profile.

Reads every real base resource StructureDefinition directly from HL7's own
published bundle (app/fhir/spec/profiles-resources.json — the same file
Organization's own base definition was originally extracted from) and
upserts each as a scope_level='base' row — the database-backed registry
app/fhir/profiling/README.md describes.

Filtered to kind == "resource" and derivation == "specialization" — the
exact two fields that distinguish "a real base resource type HL7 itself
defines" from everything else the bundle also carries (datatypes,
profiles, etc.); confirmed against the real file to yield exactly 147
entries, matching R4's known base resource count. See
docs/structure-definitions/02-structuredefinition-root-fields.md for what
both fields mean.

This supersedes seeding from individual app/fhir/profiling/<resource_type>/
base_fhir_r4.json files one resource at a time — that per-file copy is
still what app/fhir/validation/java_validator.py registers with the
validator sidecar directly (a different consumer, unaffected by this
script), but for database seeding, the bundle is the single, complete,
always-in-sync source of truth; nothing needs to be hand-copied per
resource here anymore.

Run:
  uv run python -m app.fhir_profile.seed_base_profiles

Idempotent — safe to re-run (ON CONFLICT upserts by canonical_url+version).
"""

import asyncio
import json
import time
from pathlib import Path

import asyncpg

_BUNDLE_PATH = (
    Path(__file__).resolve().parent.parent / "fhir" / "spec" / "profiles-resources.json"
)

_SEED_ACTOR = "system:seed_base_profiles"


def _discover_base_profiles() -> list[dict]:
    """Returns every StructureDefinition in the bundle that's a real base
    resource type — kind == "resource" and derivation == "specialization".
    Not filtered by resource_type at all: every one of the 147 real base
    resources comes back, regardless of whether this project has built
    that resource yet."""
    with _BUNDLE_PATH.open(encoding="utf-8") as f:
        bundle = json.load(f)
    return [
        entry["resource"]
        for entry in bundle["entry"]
        if entry["resource"].get("resourceType") == "StructureDefinition"
        and entry["resource"].get("kind") == "resource"
        and entry["resource"].get("derivation") == "specialization"
    ]


async def seed(db_url: str) -> None:
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    t0 = time.monotonic()

    try:
        upserted = 0
        for structure_definition in _discover_base_profiles():
            resource_type = structure_definition["type"]
            canonical_url = structure_definition["url"]
            # version falls back sensibly if a future HL7 publish ever
            # omits it (0..1 per spec, see
            # docs/structure-definitions/02-structuredefinition-root-fields.md).
            version = structure_definition.get("version", "1")
            #
            # status is NOT taken from the StructureDefinition's own
            # "status" field — that's HL7's own publication-maturity
            # declaration for the resource (e.g. Organization's real HL7
            # R4 entry genuinely says "draft", confirmed against the real
            # bundle; that's not an authoring mistake, just HL7's own
            # maturity model), a different concept from "is this the
            # profile layer this app currently enforces". Base rows have
            # no draft -> active -> retired lifecycle at all (there's
            # exactly one per resource_type, seeded here, never created or
            # activated through FhirProfileService's write path) — seeding
            # is this app's own ground truth, so every base row goes in as
            # 'active' unconditionally, same as every country row below.
            status = "active"

            await conn.execute(
                """
                INSERT INTO fhir_profile
                    (resource_type, scope_level, scope_id, parent_profile_id,
                     canonical_url, version, status, structure_definition,
                     created_by, updated_by)
                VALUES
                    ($1, 'base', NULL, NULL, $2, $3, $4, $5::jsonb, $6, $6)
                ON CONFLICT (canonical_url, version) DO UPDATE SET
                    resource_type         = EXCLUDED.resource_type,
                    status                = EXCLUDED.status,
                    structure_definition  = EXCLUDED.structure_definition,
                    updated_by            = EXCLUDED.updated_by,
                    updated_at            = now()
                """,
                resource_type,
                canonical_url,
                version,
                status,
                json.dumps(structure_definition),
                _SEED_ACTOR,
            )
            upserted += 1

        print(f"[SEED] Base profiles done - {upserted} upserted")
        print(f"[SEED] Elapsed: {time.monotonic() - t0:.1f}s")
    finally:
        await conn.close()


def main() -> None:
    from app.core.config import settings

    asyncio.run(seed(settings.FHIR_DATABASE_URL))


if __name__ == "__main__":
    main()
