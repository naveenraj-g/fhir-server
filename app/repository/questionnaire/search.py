"""
FHIR R4 Questionnaire search parameters
(https://www.hl7.org/fhir/R4/questionnaire.html#search) plus the common `_id` / `_lastUpdated`,
declared once for app.fhir.search: parsing, SQL, `_sort`, and the OpenAPI docs all come from
questionnaire_search() below. Questionnaire is a definitional resource, so there is no reference
parameter (and nothing to chain or `_include`): the parameters are strings, uris, dates, tokens
held in one shared table, a quantity over an Age/Range-like value (`context-quantity`) and two
composites that pair a useContext's code with its value (same `slot`, as in Observation).

Each parameter's SQL reads only the search index (QuestionnaireModel's columns and child tables,
see its docstring) - never `content`.
"""

from __future__ import annotations

from functools import cache

from sqlalchemy import exists, false, func, literal, or_, select, true
from sqlalchemy.orm import aliased

from app.repository._plan_definition_revinclude import (
    definition_plan_definition_revincludes,
)
from app.core.filters import array_contains
from app.fhir.search import (
    IncludeTarget,
    MultiValueSort,
    SearchParam,
    SearchRegistry,
)
from app.fhir.search.composite import split_composite
from app.fhir.search.quantity import quantity_range_match
from app.fhir.search.sql import (
    ArrayAggregate,
    coded_token_match,
    date_match,
    period_match,
    string_match,
    token_match,
    token_text_match,
    uri_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.questionnaire import (
    TOKEN_PARAMS,
    QuestionnaireContextQuantity,
    QuestionnaireDefinition,
    QuestionnaireIdentifier,
    QuestionnaireModel,
    QuestionnaireStatus,
    QuestionnaireSubjectType,
    QuestionnaireToken,
)

M = QuestionnaireModel
_I = QuestionnaireIdentifier
_Tk = QuestionnaireToken
_D = QuestionnaireDefinition
_Q = QuestionnaireContextQuantity

# Questionnaire.status is a `code` from the R4 publication-status system.
_STATUS_SYSTEM = "http://hl7.org/fhir/publication-status"
_RESOURCE_TYPES_SYSTEM = "http://hl7.org/fhir/resource-types"


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(select(literal(1)).where(model.questionnaire_pk == M.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.questionnaire_pk == M.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(M.updated_at, M.created_at)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return M.questionnaire_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the publication-status system: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing (rather
    than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return M.status.is_not(None)
    try:
        return M.status == QuestionnaireStatus(token.code)
    except ValueError:
        return false()


def _subject_type_match(value, modifier, ctx):
    """`subject-type` is a 0..* `code` bound to the resource-types system: any entry is the code;
    another system or an unknown code matches nothing."""
    token = parse_token(value)
    if token.system is not None and token.system != _RESOURCE_TYPES_SYSTEM:
        return false()
    if token.code is None:
        return M.subject_type.is_not(None)
    if token.code not in {m.value for m in QuestionnaireSubjectType}:
        return false()
    return array_contains(M.subject_type, token.code)


def _subject_type_sort():
    """Smallest subject type ascending, largest descending."""
    return MultiValueSort(
        ascending=ArrayAggregate(M.subject_type, "min"),
        descending=ArrayAggregate(M.subject_type, "max"),
    )


def _version_match(value, modifier, ctx):
    """`version` is a token search over a plain string: it matches the code only, so a
    `system|code` value (a string has no system) never matches."""
    token = parse_token(value)
    if token.system is not None or token.code is None:
        return false()
    return M.version == token.code


def _date_match(value, modifier, ctx):
    # Questionnaire.date is a dateTime, possibly partial (`2026`, `2026-02`): matched as the range
    # it covers.
    return period_match(M.date_start, M.date_end, value)


def _effective_match(value, modifier, ctx):
    return period_match(M.effective_start, M.effective_end, value)


def _identifier_match(value, modifier, ctx):
    if modifier == "text":
        return _exists(
            _I, token_text_match((_I.type_text_norm, _I.type_display_norm), value)
        )
    if modifier == "of-type":
        type_system, type_code, ident = parse_of_type(value)
        return _exists(
            _I,
            _I.type_system == type_system,
            _I.type_code == type_code,
            _I.value == ident,
        )
    return _exists(_I, token_match(_I.system, _I.value, value))


def _token_param(param: str):
    """(match, present, sort) for one of the token parameters held in the shared token table,
    selected by its `param` value."""

    def match(value, modifier, ctx):
        return _exists(
            _Tk,
            _Tk.param == param,
            coded_token_match(
                _Tk.system, _Tk.code, value, modifier, (_Tk.text_norm, _Tk.display_norm)
            ),
        )

    def present(ctx):
        return _exists(_Tk, _Tk.param == param)

    def sort():
        return _child_sort(_Tk.code, _Tk, _Tk.param == param)

    return match, present, sort


def _string_param(raw, norm):
    """(match, present, sort) for a 0..1 string held as a raw + normalized column pair."""

    def match(value, modifier, ctx):
        return string_match(raw, norm, value, modifier)

    return match, lambda ctx: raw.is_not(None), lambda: norm


def _context_quantity_match(value, modifier, ctx):
    # useContext.value as Quantity | Range: R4 range semantics over [low, high].
    return _exists(
        _Q,
        quantity_range_match(
            _Q.quantity_low,
            _Q.quantity_high,
            _Q.quantity_system,
            _Q.quantity_code,
            _Q.quantity_unit,
            value,
        ),
    )


def _composite(value_kind: str):
    """`context-type$<value>`: some useContext (slot) has a code matching the first part *and* a
    value of `value_kind` (`concept` -> the `context` token, `quantity` -> the quantity row)
    matching the second part. Both rows must carry the same `slot`, which is what stops the code
    of one useContext pairing with the value of another. (`,` ORs several composites - the parser
    splits it; `$` splits the parts here.)"""

    def match(value, modifier, ctx):
        code_part, value_part = split_composite(value, 2)
        code = aliased(_Tk)
        if value_kind == "concept":
            other = aliased(_Tk)
            paired = exists(
                select(literal(1))
                .where(
                    other.questionnaire_pk == M.id,
                    other.slot == code.slot,
                    other.param == "context",
                    token_match(other.system, other.code, value_part),
                )
                .correlate(M, code)
            )
        else:
            other = aliased(_Q)
            paired = exists(
                select(literal(1))
                .where(
                    other.questionnaire_pk == M.id,
                    other.slot == code.slot,
                    quantity_range_match(
                        other.quantity_low,
                        other.quantity_high,
                        other.quantity_system,
                        other.quantity_code,
                        other.quantity_unit,
                        value_part,
                    ),
                )
                .correlate(M, code)
            )
        return exists(
            select(literal(1))
            .where(
                code.questionnaire_pk == M.id,
                code.param == "context-type",
                token_match(code.system, code.code, code_part),
                paired,
            )
            .correlate(M)
        )

    return match


def _revinclude_responses():
    """_revinclude=QuestionnaireResponse:questionnaire - the responses whose canonical (or relative
    `Questionnaire/<id>`) resolves to the matched questionnaires. Imported lazily so the two
    registries never import each other at load."""
    from app.repository.questionnaire_response.search import (
        revinclude_responses_via_questionnaire,
    )

    return revinclude_responses_via_questionnaire(
        lambda r: r.url, lambda r: r.questionnaire_id
    )


def _register_kind() -> None:
    """How the search engine identifies and renders Questionnaire rows."""
    from app.fhir.mappers.questionnaire import to_fhir_questionnaire
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Questionnaire",
            lambda r: r.questionnaire_id,
            to_fhir_questionnaire,
            "questionnaires",
        )
    )


# -- registry ------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_STRING = frozenset({"exact", "contains", "missing"})
_IDENTIFIER = frozenset({"text", "not", "of-type", "missing"})
_TEXT_DOC = {
    "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
}
_COMPOSITE_DOC = (
    " Composite: `<context-type>$<value>`, the two parts separated by `$` (a literal `$` is"
    " written `\\$`), both taken from the same useContext. Takes no modifiers and cannot be"
    " sorted."
)


@cache
def questionnaire_search() -> SearchRegistry:
    _register_kind()

    def token(name, description, expression, example):
        match, present, sort = _token_param(name)
        return SearchParam(
            name,
            "token",
            description,
            expression,
            match,
            present,
            _TOKEN,
            sort=sort,
            example=example,
        )

    def string(name, description, expression, raw, norm, example):
        match, present, sort = _string_param(raw, norm)
        return SearchParam(
            name,
            "string",
            description,
            expression,
            match,
            present,
            _STRING,
            sort=sort,
            example=example,
        )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public questionnaire id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: M.questionnaire_id,
            example="380001",
        ),
        SearchParam(
            "_lastUpdated",
            "date",
            "When the resource last changed (meta.lastUpdated)",
            "Resource.meta.lastUpdated",
            lambda v, m, ctx: date_match(last_updated(), v),
            lambda ctx: true(),
            sort=last_updated,
            example="ge2024-01-01",
        ),
        token(
            "code",
            "A code that corresponds to one of its items in the questionnaire",
            "Questionnaire.item.code",
            "http://loinc.org|44250-9",
        ),
        token(
            "context",
            "A use context assigned to the questionnaire",
            "(Questionnaire.useContext.value as CodeableConcept)",
            "http://snomed.info/sct|35489007",
        ),
        SearchParam(
            "context-quantity",
            "quantity",
            "A quantity- or range-valued use context assigned to the questionnaire",
            "(Questionnaire.useContext.value as Quantity) | (Questionnaire.useContext.value as Range)",
            _context_quantity_match,
            lambda ctx: _exists(_Q),
            frozenset({"missing"}),
            sort=lambda: _child_sort(_Q.quantity_low, _Q),
            example="ge5|http://unitsofmeasure.org|mg",
        ),
        token(
            "context-type",
            "A type of use context assigned to the questionnaire",
            "Questionnaire.useContext.code",
            "http://terminology.hl7.org/CodeSystem/usage-context-type|focus",
        ),
        SearchParam(
            "context-type-quantity",
            "composite",
            "A use context type and quantity- or range-based value assigned to the questionnaire"
            + _COMPOSITE_DOC,
            "Questionnaire.useContext",
            _composite("quantity"),
            lambda ctx: true(),
            frozenset(),
            example="age$ge18|http://unitsofmeasure.org|a",
        ),
        SearchParam(
            "context-type-value",
            "composite",
            "A use context type and value assigned to the questionnaire"
            + _COMPOSITE_DOC,
            "Questionnaire.useContext",
            _composite("concept"),
            lambda ctx: true(),
            frozenset(),
            example="focus$http://snomed.info/sct|35489007",
        ),
        SearchParam(
            "date",
            "date",
            "The questionnaire publication date",
            "Questionnaire.date",
            _date_match,
            lambda ctx: M.date_start.is_not(None),
            sort=lambda: M.date_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "definition",
            "uri",
            "ElementDefinition - details for the item",
            "Questionnaire.item.definition",
            lambda v, m, ctx: _exists(_D, uri_match(_D.uri, v, m)),
            lambda ctx: _exists(_D),
            frozenset({"above", "below", "missing"}),
            sort=lambda: _child_sort(_D.uri, _D),
            example="http://example.org/definitions/interest",
            modifier_docs={
                "below": "`:below` — stored URIs that start with the value.",
                "above": "`:above` — stored URIs that are a prefix of the value.",
            },
        ),
        string(
            "description",
            "The description of the questionnaire",
            "Questionnaire.description",
            M.description,
            M.description_norm,
            "depression",
        ),
        SearchParam(
            "effective",
            "date",
            "The time during which the questionnaire is intended to be in use",
            "Questionnaire.effectivePeriod",
            _effective_match,
            lambda ctx: or_(
                M.effective_start.is_not(None), M.effective_end.is_not(None)
            ),
            sort=lambda: M.effective_start,
            example="ge2026-01-01",
        ),
        SearchParam(
            "identifier",
            "token",
            "External identifier for the questionnaire",
            "Questionnaire.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            _IDENTIFIER,
            sort=lambda: _child_sort(_I.value, _I),
            example="https://fhir-server.dev/fhir/identifier-system/questionnaire-id|PHQ-9",
            modifier_docs=_TEXT_DOC,
        ),
        token(
            "jurisdiction",
            "Intended jurisdiction for the questionnaire",
            "Questionnaire.jurisdiction",
            "urn:iso:std:iso:3166|US",
        ),
        string(
            "name",
            "Computationally friendly name of the questionnaire",
            "Questionnaire.name",
            M.name,
            M.name_norm,
            "PHQ",
        ),
        string(
            "publisher",
            "Name of the publisher of the questionnaire",
            "Questionnaire.publisher",
            M.publisher,
            M.publisher_norm,
            "Example",
        ),
        SearchParam(
            "status",
            "token",
            "The current status of the questionnaire",
            "Questionnaire.status",
            _status_match,
            lambda ctx: M.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.status,
            example="active",
        ),
        SearchParam(
            "subject-type",
            "token",
            "Resource that can be subject of QuestionnaireResponse",
            "Questionnaire.subjectType",
            _subject_type_match,
            lambda ctx: M.subject_type.is_not(
                None
            ),  # stored NULL, never an empty array
            frozenset({"not", "missing"}),
            sort=_subject_type_sort,
            example="Patient",
        ),
        string(
            "title",
            "The human-friendly name of the questionnaire",
            "Questionnaire.title",
            M.title,
            M.title_norm,
            "Patient Health",
        ),
        SearchParam(
            "url",
            "uri",
            "The uri that identifies the questionnaire",
            "Questionnaire.url",
            lambda v, m, ctx: uri_match(M.url, v, m),
            lambda ctx: M.url.is_not(None),
            frozenset({"above", "below", "missing"}),
            sort=lambda: M.url,
            example="https://fhir-server.dev/fhir/Questionnaire/phq-9",
            modifier_docs={
                "below": "`:below` — stored URLs that start with the value.",
                "above": "`:above` — stored URLs that are a prefix of the value.",
            },
        ),
        SearchParam(
            "version",
            "token",
            "The business version of the questionnaire",
            "Questionnaire.version",
            _version_match,
            lambda ctx: M.version.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: M.version,
            example="1.0",
        ),
    ]

    # Keep the declared token parameters and the model's TOKEN_PARAMS in step.
    assert {"code", "context", "context-type", "jurisdiction"} == set(TOKEN_PARAMS)

    return SearchRegistry(
        resource_type="Questionnaire",
        params={p.name: p for p in params},
        # Σ elements in the R4 Questionnaire definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "url",
                "identifier",
                "version",
                "name",
                "title",
                "status",
                "experimental",
                "subjectType",
                "date",
                "publisher",
                "contact",
                "useContext",
                "jurisdiction",
                "effectivePeriod",
                "code",
            }
        ),
        # Elements with min cardinality 1 in R4 - kept by _summary=text / _elements.
        mandatory_elements=frozenset({"status"}),
        # Nothing rebuilt points at a Questionnaire through a Reference-typed search parameter
        # (QuestionnaireResponse.questionnaire is a canonical URL).
        includes=(),
        revincludes=(
            IncludeTarget(
                "QuestionnaireResponse",
                "questionnaire",
                "Questionnaire",
                _revinclude_responses(),
                reverse=True,
            ),
            # A PlanDefinition's action can ask a questionnaire.
            *definition_plan_definition_revincludes(
                "Questionnaire", lambda r: r.questionnaire_id
            ),
        ),
        default_sort=lambda: [M.questionnaire_id.desc()],
    )
