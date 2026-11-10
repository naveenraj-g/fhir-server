"""The `TerminologyCapabilities` resource — see
docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §6.
Describes what THIS running deployment actually supports (which code
systems/versions it hosts, which operations and parameters work), as
distinct from a generic `CapabilityStatement` (the REST-API-shape document
every resource would need, not built here — see
docs/terminology-service/08-fhir-r4-standard-compliance-gap-analysis.md §7
for why that's a separate, broader, still-deferred gap) and from a plain
`CodeSystem` (describes one vocabulary's own content, not this server's
behavior)."""

from datetime import UTC, datetime


class _CapabilitiesMixin:
    async def get_terminology_capabilities(self) -> dict:
        """`kind: "instance"` — per 09 §6.1's resource-level rule, this is
        the shape a real running deployment publishes (`implementation`
        required, `software` optional), not `kind: "capability"` (a
        product's generic capabilities with no specific install, which
        requires `software` and forbids `implementation` instead)."""
        code_systems = await self.repository.list_code_systems()
        hierarchy_ids = await self.repository.code_systems_with_hierarchy_data()

        code_system_entries = [
            {
                "uri": cs.canonical_url,
                "version": (
                    [{"code": cs.version, "isDefault": True}] if cs.version else []
                ),
                "subsumption": cs.id in hierarchy_ids,
            }
            for cs in code_systems
        ]

        return {
            "resourceType": "TerminologyCapabilities",
            "status": "active",
            "date": datetime.now(UTC).isoformat(),
            "kind": "instance",
            "implementation": {
                "description": "Embedded FHIR R4 terminology service — CodeSystem/ValueSet/ConceptMap operations over this repository's own loaded terminologies.",
            },
            "codeSystem": code_system_entries,
            "expansion": {
                "hierarchical": False,
                "paging": True,
                "incomplete": False,
                "parameter": [
                    {"name": "url", "documentation": "Canonical ValueSet URL"},
                    {"name": "valueSetVersion", "documentation": "Checked against the one stored version, not selected among several"},
                    {"name": "filter", "documentation": "Free-text ILIKE filter on concept display"},
                    {"name": "offset", "documentation": "Paging start"},
                    {"name": "count", "documentation": "Page size"},
                ],
            },
            "codeSearch": "explicit",
            "validateCode": {"translations": False},
            "translation": {"needsMap": True},
            "closure": {"translation": False},
        }
