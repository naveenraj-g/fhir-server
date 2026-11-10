"""SNOMED CT -> ICD-10-CM concept map loader.

Requires a UMLS/NLM account (same as SNOMED's own RF2 download):
  https://www.nlm.nih.gov/healthit/snomedct/us_edition.html
  -> "SNOMED CT to ICD-10-CM Resources" package
  Extract: tls_Icd10cmHumanReadableMap_<module>_<date>.tsv

Requires BOTH the SNOMED CT and ICD-10-CM code systems to already be
loaded (`terminology-snomed` and `terminology-icd10cm`) — every row here
resolves a SNOMED concept_id and an ICD-10-CM code against concepts that
must already exist; a row that doesn't resolve is skipped and counted,
not a hard failure for the whole run.

This is SNOMED's own "Human-Readable Map" / Extended Map release, which
is RULE-BASED, not a plain 1:1 table — a single SNOMED concept can have
several candidate ICD-10-CM targets gated by patient-context rules
(mapRule), e.g. an age- or sex-dependent choice ("IFA 445518008 | Age at
onset ... | < 29.0 days"). This loader only keeps the UNCONDITIONAL rows
(mapRule = "TRUE" or "OTHERWISE TRUE" — the default/fallback rule within
a mapGroup that applies when no patient-context condition is needed),
since a static seed script has no patient to evaluate a condition
against. Conditional rows are skipped and counted at the end of the run —
see docs/terminology-service/05-seeding-and-external-loaders.md for the
measured split (roughly 52% of rows are unconditional, on the 2026-03-01
release this was built against).

ICD-10-CM codes in this map file are DOTTED ("A41.9"); this project's own
seeded ICD-10-CM concepts (app/terminology/import_/loaders/icd10cm.py,
from CMS's own code list) are DOTLESS ("A419") — both represent the same
code, confirmed against the actual files. Dots are stripped before
resolving against the ICD-10-CM concept map.

mapCategoryName (the file's own classification of mapping quality) maps
to the real FHIR ConceptMap.equivalence:
  MAP SOURCE CONCEPT IS PROPERLY CLASSIFIED  -> equivalent
  MAP OF SOURCE CONCEPT IS CONTEXT DEPENDENT -> inexact
  MAP SOURCE CONCEPT CANNOT BE CLASSIFIED... -> never carries a mapTarget
    at all (confirmed empirically against the actual file) — already
    excluded by requiring a non-empty target, no explicit handling needed.

Run:
  just terminology-snomed-icd10cm-map
  # or
  uv run python -m app.terminology.import_.cli --source snomed-icd10cm-map \\
    --file terminology_data/SNOMED_CT_to_ICD-10-CM_Resources_20260301/tls_Icd10cmHumanReadableMap_US1000124_20260301.tsv
"""
import csv
import time

from app.terminology.import_.base import BaseLoader

SNOMED_URL = "http://snomed.info/sct"
ICD10CM_URL = "http://hl7.org/fhir/sid/icd-10-cm"

_UNCONDITIONAL_RULES = {"TRUE", "OTHERWISE TRUE"}

_CATEGORY_TO_EQUIVALENCE = {
    "MAP SOURCE CONCEPT IS PROPERLY CLASSIFIED": "equivalent",
    "MAP OF SOURCE CONCEPT IS CONTEXT DEPENDENT": "inexact",
}


class SnomedIcd10cmMapLoader(BaseLoader):
    source_name = "snomed-icd10cm-map"

    async def load(self, file_path: str) -> None:
        t0 = time.monotonic()
        self._log(f"Reading {file_path}")

        snomed_cs_id = await self._require_code_system(
            SNOMED_URL, "run `just terminology-snomed` first"
        )
        icd10cm_cs_id = await self._require_code_system(
            ICD10CM_URL, "run `just terminology-icd10cm` first"
        )

        self._log("Loading concept id maps for both code systems...")
        snomed_ids = await self.fetch_concept_id_map(snomed_cs_id)
        icd10cm_ids = await self.fetch_concept_id_map(icd10cm_cs_id)
        self._log(
            f"  {len(snomed_ids):,} SNOMED concepts, "
            f"{len(icd10cm_ids):,} ICD-10-CM concepts already in DB"
        )

        total_rows = 0
        skipped_inactive = 0
        skipped_conditional = 0
        skipped_no_target = 0
        skipped_unresolved_source = 0
        skipped_unresolved_target = 0
        skipped_unknown_category = 0
        seen: set[tuple[int, int, str]] = set()
        records: list[tuple] = []

        with open(file_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                total_rows += 1

                if row.get("active") != "1":
                    skipped_inactive += 1
                    continue

                if (row.get("mapRule") or "").strip() not in _UNCONDITIONAL_RULES:
                    skipped_conditional += 1
                    continue

                target_code = (row.get("mapTarget") or "").strip()
                if not target_code:
                    skipped_no_target += 1
                    continue

                source_db_id = snomed_ids.get((row.get("referencedComponentId") or "").strip())
                if source_db_id is None:
                    skipped_unresolved_source += 1
                    continue

                target_db_id = icd10cm_ids.get(target_code.replace(".", ""))
                if target_db_id is None:
                    skipped_unresolved_target += 1
                    continue

                equivalence = _CATEGORY_TO_EQUIVALENCE.get(
                    (row.get("mapCategoryName") or "").strip()
                )
                if equivalence is None:
                    skipped_unknown_category += 1
                    continue

                key = (source_db_id, target_db_id, equivalence)
                if key in seen:
                    continue
                seen.add(key)
                records.append((source_db_id, target_db_id, equivalence, None))

        self._log(
            f"{total_rows:,} rows read — {len(records):,} unique mappings to insert. "
            f"Skipped: {skipped_inactive:,} inactive, {skipped_conditional:,} "
            f"patient-context-conditional, {skipped_no_target:,} no mapTarget, "
            f"{skipped_unresolved_source:,} unresolved SNOMED source, "
            f"{skipped_unresolved_target:,} unresolved ICD-10-CM target, "
            f"{skipped_unknown_category:,} unrecognized mapCategoryName."
        )

        inserted = await self.bulk_insert_concept_maps(records)
        self._log(f"Done — {inserted:,} mapping rows processed in {time.monotonic() - t0:.1f}s")

    async def _require_code_system(self, canonical_url: str, hint: str) -> int:
        row = await self.conn.fetchrow(
            "SELECT id FROM terminology_code_system WHERE canonical_url = $1",
            canonical_url,
        )
        if row is None:
            raise RuntimeError(f"CodeSystem '{canonical_url}' is not loaded yet — {hint}.")
        return row["id"]
