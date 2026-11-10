"""FHIR R4 ValueSet operations — `$expand` and `$validate-code` — see
docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §3.2
and the "`$validate-code` on ValueSet" subsection of §2.6. Distinct from
this package's existing `value_sets.py` (the older, non-standard
`/value-sets`/`/value-sets/{id}/expand` endpoints, left untouched) and from
`validation.py`'s `validate()` (this app's own resource+field-binding
concept, not the real ValueSet-canonical-URL operation)."""

from datetime import UTC, datetime

from app.errors.base import ApplicationError
from app.errors.fhir_codes import IssueType


class _ValueSetOperationsMixin:
    async def expand_operation(
        self,
        *,
        value_set_id: int | None,
        url: str | None,
        value_set_version: str | None,
        filter_text: str | None,
        offset: int,
        count: int,
    ) -> dict:
        """Resolves a ValueSet by internal id (instance-level invocation)
        or canonical url+version (type-level), then returns a real `ValueSet`
        resource dict with a materialized `expansion` — NOT wrapped in
        `Parameters` (the spec returns the expanded ValueSet directly as
        `return`). Raises ApplicationError(404) if nothing resolves."""
        if value_set_id is not None:
            vs = await self.repository.get_value_set(value_set_id)
        else:
            vs = await self.repository.get_value_set_by_url(
                url, version=value_set_version
            )
        if vs is None:
            raise ApplicationError(
                name="ValueSetNotFound",
                message="No ValueSet matches the given id/url(+version).",
                status_code=404,
                code="VALUE_SET_NOT_FOUND",
                issue_type=IssueType.NOT_FOUND,
            )

        total, rows = await self.repository.expand_value_set(
            vs.id, filter_text, count, offset
        )

        expansion: dict = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total": total,
            "contains": [
                {
                    "system": cs.canonical_url,
                    "code": concept.code,
                    "display": concept.display,
                }
                for concept, cs in rows
            ],
        }
        if offset:
            expansion["offset"] = offset

        result = {
            "resourceType": "ValueSet",
            "url": vs.canonical_url,
            "version": vs.version,
            "name": vs.name,
            "title": vs.title,
            "status": "active" if vs.active else "retired",
            "expansion": expansion,
        }
        return {k: v for k, v in result.items() if v is not None}

    async def validate_code_on_valueset_operation(
        self,
        *,
        value_set_id: int | None,
        url: str | None,
        value_set_version: str | None,
        code: str | None,
        system: str | None,
        display: str | None,
    ) -> dict:
        """Resolves a ValueSet the same way expand_operation() does, then
        answers "is system+code a member of it" via the existing
        lookup_concept_in_value_set() repository method. Always 200 once
        the ValueSet itself resolves — an unresolvable ValueSet is the one
        case this raises for (400: "server genuinely can't determine
        validity" per the spec's own OUT description), not a non-member
        code, which is a normal result=false response."""
        if value_set_id is not None:
            vs = await self.repository.get_value_set(value_set_id)
        else:
            vs = await self.repository.get_value_set_by_url(
                url, version=value_set_version
            )
        if vs is None:
            raise ApplicationError(
                name="ValueSetNotFound",
                message="No ValueSet matches the given id/url(+version) — cannot validate against it.",
                status_code=400,
                code="VALUE_SET_NOT_FOUND",
                issue_type=IssueType.NOT_FOUND,
            )

        _cs, concept, in_value_set = await self.repository.lookup_concept_in_value_set(
            vs.id, system, code
        )

        if concept is None:
            return {
                "result": False,
                "message": f"Unknown code '{code}' in system '{system}'.",
            }

        result: dict = {
            "result": in_value_set,
            "message": (
                f"Code '{code}' is a member of ValueSet '{vs.canonical_url}'."
                if in_value_set
                else f"Code '{code}' is NOT a member of ValueSet '{vs.canonical_url}'."
            ),
            "display": display or concept.display,
        }
        return result
