"""Seed country-layer FHIR profiles into fhir_profile.

Walks app/fhir/profiling/<resource_type>/country_<code>.json for every
resource_type that has one (today: Organization's country_in.json) and
upserts each as a scope_level='country' row, with scope_id set to the
country code extracted from the filename (e.g. "country_in.json" -> "IN",
matching settings.fhir_validation.country's own casing — see
app/fhir/validation/dispatch.py's module docstring for why country
selection is a single global config value, not per-row/per-tenant).

Depends on the base layer already being seeded: parent_profile_id is
resolved by looking up the row whose canonical_url matches this profile's
own "baseDefinition" field — run seed_base_profiles first (the justfile's
fhir-profile-seed-country recipe already depends on fhir-profile-seed-base
for exactly this reason). A country profile whose base isn't seeded yet is
skipped with a warning, not silently inserted with a dangling/null parent.

Run:
  uv run python -m app.fhir_profile.seed_country_profiles

Idempotent — safe to re-run (ON CONFLICT upserts by canonical_url+version).
"""

import asyncio
import json
import time
from pathlib import Path

import asyncpg

_PROFILING_ROOT = Path(__file__).resolve().parent.parent / "fhir" / "profiling"

_SEED_ACTOR = "system:seed_country_profiles"


def _discover_country_profiles() -> list[tuple[str, str, Path]]:
    """Returns (resource_type, country_code, file_path) for every
    country_<code>.json found under app/fhir/profiling/ — resource_type is
    the folder name capitalized (e.g. "organization" -> "Organization"),
    country_code is the uppercased <code> portion of the filename (e.g.
    "country_in.json" -> "IN"). Not hardcoded to Organization or India —
    picks up any resource/country pair that follows the naming convention
    documented in app/fhir/profiling/README.md."""
    found = []
    if not _PROFILING_ROOT.is_dir():
        return found
    for resource_dir in sorted(_PROFILING_ROOT.iterdir()):
        if not resource_dir.is_dir():
            continue
        resource_type = resource_dir.name.capitalize()
        for country_file in sorted(resource_dir.glob("country_*.json")):
            # "country_in.json" -> "in" -> "IN"
            code = country_file.stem.removeprefix("country_").upper()
            found.append((resource_type, code, country_file))
    return found


async def seed(db_url: str) -> None:
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    t0 = time.monotonic()

    try:
        upserted = 0
        skipped_no_base = 0

        for resource_type, country_code, path in _discover_country_profiles():
            structure_definition = json.loads(path.read_text(encoding="utf-8"))
            canonical_url = structure_definition["url"]
            base_definition_url = structure_definition.get("baseDefinition")
            version = structure_definition.get("version", "1")
            status = structure_definition.get("status", "draft")

            parent_profile_id = None
            if base_definition_url:
                parent_profile_id = await conn.fetchval(
                    """
                    SELECT id FROM fhir_profile
                    WHERE canonical_url = $1 AND scope_level = 'base'
                    ORDER BY id DESC LIMIT 1
                    """,
                    base_definition_url,
                )

            if parent_profile_id is None:
                skipped_no_base += 1
                print(
                    f"[SEED] SKIPPED {resource_type}/{country_code} — "
                    f"no base row found for baseDefinition={base_definition_url!r}. "
                    f"Run fhir-profile-seed-base first."
                )
                continue

            await conn.execute(
                """
                INSERT INTO fhir_profile
                    (resource_type, scope_level, scope_id, parent_profile_id,
                     canonical_url, version, status, structure_definition,
                     created_by, updated_by)
                VALUES
                    ($1, 'country', $2, $3, $4, $5, $6, $7::jsonb, $8, $8)
                ON CONFLICT (canonical_url, version) DO UPDATE SET
                    resource_type         = EXCLUDED.resource_type,
                    scope_id              = EXCLUDED.scope_id,
                    parent_profile_id     = EXCLUDED.parent_profile_id,
                    status                = EXCLUDED.status,
                    structure_definition  = EXCLUDED.structure_definition,
                    updated_by            = EXCLUDED.updated_by,
                    updated_at            = now()
                """,
                resource_type,
                country_code,
                parent_profile_id,
                canonical_url,
                version,
                status,
                json.dumps(structure_definition),
                _SEED_ACTOR,
            )
            upserted += 1
            print(
                f"[SEED] {resource_type} country={country_code} profile -> "
                f"{canonical_url}@{version} (parent id={parent_profile_id})"
            )

        print(
            f"[SEED] Country profiles done — {upserted} upserted, "
            f"{skipped_no_base} skipped (no matching base row)"
        )
        print(f"[SEED] Elapsed: {time.monotonic() - t0:.1f}s")
    finally:
        await conn.close()


def main() -> None:
    from app.core.config import settings

    asyncio.run(seed(settings.FHIR_DATABASE_URL))


if __name__ == "__main__":
    main()
