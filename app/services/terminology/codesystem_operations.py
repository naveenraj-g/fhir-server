from app.errors.base import ApplicationError
from app.errors.fhir_codes import IssueType
from app.fhir.parameters import (
    build_parameters,
    param_boolean,
    param_code,
    param_coding,
    param_part,
    param_string,
)

# Equivalence vocabulary for $subsumes is a SEPARATE mapping from $closure's
# (see app/repository/terminology/hierarchy.py's subsumption_relationship()
# docstring) — this is $subsumes's own mapping only.
_SUBSUMES_OUTCOME = {
    "equal": "equivalent",
    "a_subsumes_b": "subsumes",
    "b_subsumes_a": "subsumed-by",
    "disjoint": "not-subsumed",
}

# http://terminology.hl7.org/CodeSystem/designation-usage#display — the
# standard "this designation is the system's own display text" use code,
# applied to translations ($lookup's designation[] output below). Synonyms
# get no `use` Coding at all (none of the standard use codes — display,
# definition, etc. — fit "informal alternate name" precisely; omitting
# `use` is spec-legal, `use` is 0..1).
_DESIGNATION_USE_DISPLAY = {
    "system": "http://terminology.hl7.org/CodeSystem/designation-usage",
    "code": "display",
}


class _CodeSystemOperationsMixin:
    """CodeSystem's `$lookup`, `$validate-code`, `$subsumes`, `$find-matches`
    — see docs/terminology-service/09-fhir-r4-terminology-standard-reference.md
    §2.6. Every method returns a plain dict already shaped as the
    operation's `Parameters` response body (built via app/fhir/parameters.py)
    — see that module's own docstring for why these aren't Pydantic models."""

    async def lookup_operation(
        self,
        *,
        system: str | None,
        code: str | None,
        coding: dict | None,
        properties: list[str] | None,
    ) -> dict:
        effective_system = system or (coding.get("system") if coding else None)
        effective_code = code or (coding.get("code") if coding else None)
        if not effective_system or not effective_code:
            raise ApplicationError(
                name="InvalidParameterError",
                message="$lookup requires system+code or a coding",
                status_code=400,
                code="INVALID_PARAMETER",
                issue_type=IssueType.REQUIRED,
            )

        cs, concept = await self.repository.lookup_concept(
            effective_system, effective_code
        )
        if concept is None:
            raise ApplicationError(
                name="CodeNotFoundError",
                message=f"Code '{effective_code}' not found in system '{effective_system}'",
                status_code=400,
                code="CODE_NOT_FOUND",
                issue_type=IssueType.NOT_FOUND,
            )

        # `properties` (the IN `property` list) is advisory only — if given,
        # it names which OUT fields the client is most interested in, but
        # this server always returns every designation it actually has
        # rather than suppressing known-good data the client didn't happen
        # to ask for by name (spec: "server decides" when omitted; treating
        # a non-empty list as a strict allow-list would mean a client that
        # forgot to list "designation" gets silently less than a client
        # that omitted `property` entirely, which is a worse default).
        del properties

        synonyms = await self.repository.get_concept_synonyms(concept.id)
        translations = await self.repository.get_concept_translations(concept.id)

        designations = [
            param_part("designation", param_string("value", s.synonym))
            for s in synonyms
        ] + [
            param_part(
                "designation",
                param_code("language", t.language_code),
                param_coding("use", _DESIGNATION_USE_DISPLAY),
                param_string("value", t.display),
            )
            for t in translations
        ]

        return build_parameters(
            param_string("name", cs.name),
            param_string("version", cs.version),
            param_string("display", concept.display),
            *designations,
        )

    async def validate_code_on_codesystem_operation(
        self,
        *,
        url: str | None,
        code: str | None,
        version: str | None,
        display: str | None,
        coding: dict | None,
        codeable_concept: dict | None,
    ) -> dict:
        del version, display  # not enforceable — see get_value_set_by_url()'s
        # own docstring (app/repository/terminology/value_sets.py) for the
        # identical single-version-per-URL limitation this schema has for
        # CodeSystem too; `display` is informational-only to compare
        # against, not validated here.

        if coding:
            effective_url = coding.get("system")
            effective_code = coding.get("code")
        elif codeable_concept and codeable_concept.get("coding"):
            first = codeable_concept["coding"][0]
            effective_url = first.get("system")
            effective_code = first.get("code")
        else:
            effective_url = url
            effective_code = code

        if not effective_url:
            raise ApplicationError(
                name="MissingSystemError",
                message="$validate-code requires a CodeSystem url (directly, or via coding.system)",
                status_code=400,
                code="MISSING_SYSTEM",
                issue_type=IssueType.NOT_FOUND,
            )

        cs = await self.repository.get_code_system_by_url(effective_url)
        if cs is None:
            raise ApplicationError(
                name="CodeSystemNotFoundError",
                message=f"CodeSystem '{effective_url}' not found",
                status_code=400,
                code="CODE_SYSTEM_NOT_FOUND",
                issue_type=IssueType.NOT_FOUND,
            )

        _, concept = (
            await self.repository.lookup_concept(effective_url, effective_code)
            if effective_code
            else (None, None)
        )
        result = concept is not None
        message = (
            f"Code '{effective_code}' is valid in CodeSystem '{effective_url}'."
            if result
            else f"Code '{effective_code}' was not found in CodeSystem '{effective_url}'."
        )
        return build_parameters(
            param_boolean("result", result),
            param_string("message", message),
            param_string("display", concept.display if concept else None),
        )

    async def subsumes_operation(
        self,
        *,
        code_a: str | None,
        code_b: str | None,
        system: str | None,
        coding_a: dict | None,
        coding_b: dict | None,
    ) -> dict:
        if coding_a and coding_b and coding_a.get("system") != coding_b.get("system"):
            raise ApplicationError(
                name="CrossSystemSubsumptionNotSupportedError",
                message=(
                    "$subsumes across two different code systems is not "
                    "supported — no cross-system subsumption relationship "
                    "is defined in this repository"
                ),
                status_code=400,
                code="NOT_SUPPORTED",
                issue_type=IssueType.NOT_SUPPORTED,
            )

        effective_system_a = (coding_a or {}).get("system") or system
        effective_code_a = (coding_a or {}).get("code") or code_a
        effective_system_b = (coding_b or {}).get("system") or system
        effective_code_b = (coding_b or {}).get("code") or code_b

        if not all(
            [effective_system_a, effective_code_a, effective_system_b, effective_code_b]
        ):
            raise ApplicationError(
                name="InvalidParameterError",
                message="$subsumes requires both codeA and codeB (as codes+system, or Codings)",
                status_code=400,
                code="INVALID_PARAMETER",
                issue_type=IssueType.REQUIRED,
            )

        _, concept_a = await self.repository.lookup_concept(
            effective_system_a, effective_code_a
        )
        _, concept_b = await self.repository.lookup_concept(
            effective_system_b, effective_code_b
        )
        if concept_a is None or concept_b is None:
            raise ApplicationError(
                name="CodeNotFoundError",
                message="One or both codes passed to $subsumes were not found",
                status_code=400,
                code="CODE_NOT_FOUND",
                issue_type=IssueType.NOT_FOUND,
            )

        raw = await self.repository.subsumption_relationship(
            concept_a.id, concept_b.id
        )
        return build_parameters(param_code("outcome", _SUBSUMES_OUTCOME[raw]))

    async def find_matches_operation(
        self,
        *,
        system: str | None,
        version: str | None,
        properties: list[dict],
        exact: bool | None,
        compositional: bool | None,
    ) -> dict:
        del system, version, properties, compositional  # see note below — no
        # property-based matching exists to apply these to.
        if exact is None:
            raise ApplicationError(
                name="InvalidParameterError",
                message="$find-matches requires 'exact'",
                status_code=400,
                code="INVALID_PARAMETER",
                issue_type=IssueType.REQUIRED,
            )
        # This repository has no generic CodeSystem.property key/value data
        # on TerminologyConcept to match against (confirmed: no such table
        # exists) — returning a real, spec-shaped, empty-match response is
        # honest; faking a match here would not be.
        return build_parameters(
            param_string(
                "comment",
                "No property-based concept matching is implemented — this "
                "repository has no CodeSystem.property data to match against.",
            )
        )
