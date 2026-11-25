"""
FHIR R4 Medication search parameters
(https://www.hl7.org/fhir/R4/medication.html#search) plus the common `_id` /
`_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from medication_search() below.
Same arrangement as app.repository.service_request.search and
app.repository.specimen.search (references held as columns, shared token and reference
tables).

Each parameter's SQL reads only the search index (MedicationModel's columns and child
tables, see its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true

from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    period_match,
    reference_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.medication import (
    MANUFACTURER_TYPES,
    REFERENCE_TYPES,
    MedicationIdentifier,
    MedicationModel,
    MedicationReference,
    MedicationStatus,
    MedicationToken,
)
from app.repository._flag_revinclude import column_flag_revincludes
from app.repository._group_revinclude import (
    member_group_revincludes,
)
from app.repository._medication_administration_revinclude import (
    column_medication_administration_revincludes,
)
from app.repository._medication_dispense_revinclude import (
    column_medication_dispense_revincludes,
)
from app.repository._medication_request_revinclude import (
    column_medication_request_revincludes,
)
from app.repository._medication_statement_revinclude import (
    column_medication_statement_revincludes,
)
from app.repository._search_targets import MODELED

P = MedicationModel
_I = MedicationIdentifier
_Tk = MedicationToken
_R = MedicationReference
_STATUS_SYSTEM = "http://hl7.org/fhir/CodeSystem/medication-status"

# Every rebuilt resource type this server can chain through and `_include`: derived from
# RESOURCE_REGISTRY by app/repository/_search_targets.py, so there is no list to keep here.
#   type -> (model module, model class, public id column, search module, search factory)
_MODELED = MODELED


def _model(resource_type: str):
    module, cls, id_col, *_ = _MODELED[resource_type]
    model = getattr(importlib.import_module(module), cls)
    return model, getattr(model, id_col)


def _registry_of(resource_type: str):
    def get():
        _m, _c, _i, module, factory = _MODELED[resource_type]
        return getattr(importlib.import_module(module), factory)()

    return get


def _exists(model, *conditions):
    """Correlated EXISTS against one of the index child tables."""
    return exists(select(literal(1)).where(model.medication_pk == P.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.medication_pk == P.id, *conditions)
            .scalar_subquery()
        )

    return MultiValueSort(ascending=agg(func.min), descending=agg(func.max))


def last_updated():
    return func.coalesce(P.updated_at, P.created_at)


def _referenced(target: str, inner, ctx):
    """ids of `target` rows (same tenant) matching a chained condition. Does not correlate to
    the outer row - it ranges over the referenced resource."""
    model, id_col = _model(target)
    return select(id_col).where(model.tenant_id == ctx.tenant_id, inner).correlate(None)


def _id_match(value, modifier, ctx):
    token = parse_token(value)
    if (
        token.system or not (token.code or "").isdigit()
    ):  # ids are the numeric public id
        return false()
    return P.medication_id == int(token.code)


def _status_match(value, modifier, ctx):
    """`status` is a `code` bound to the medication-status system: `code` or `system|code`;
    another system or `|code` (no system) never matches; an unknown code matches nothing
    (rather than failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _STATUS_SYSTEM:
        return false()
    if token.code is None:
        return P.status.is_not(None)
    try:
        return P.status == MedicationStatus(token.code)
    except ValueError:
        return false()


def _expiration_match(value, modifier, ctx):
    # Medication.batch.expirationDate as a dateTime: matched as the range it covers.
    return period_match(P.expiration_start, P.expiration_end, value)


def _lot_number_match(value, modifier, ctx):
    """`lot-number` is a token search over a plain string: it matches the code only, so a
    `system|code` value (a string has no system) never matches."""
    token = parse_token(value)
    if token.system is not None or token.code is None:
        return false()
    return P.lot_number == token.code


# -- identifier / the three token parameters -----------------------------------------------


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
    """(match, present, sort) for one of the token parameters held in the shared token
    table, selected by its `param` value."""

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


# -- manufacturer: a reference held as columns ---------------------------------------------


def _column_ref(prefix: str, targets: tuple[str, ...]):
    """(match, present, chain, sort) for a 0..1 Reference held as `{prefix}_*` columns on the
    medication row."""
    ref, type_, id_ = (
        getattr(P, f"{prefix}_{part}") for part in ("reference", "type", "id")
    )
    ident_system, ident_value = (
        getattr(P, f"{prefix}_identifier_system"),
        getattr(P, f"{prefix}_identifier_value"),
    )

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return token_condition(ident_system, ident_value, parse_token(value))
        # `modifier` is a target type (manufacturer:Organization=190001) or None.
        return reference_match(type_, id_, ref, value, modifier, ctx, targets, str)

    def present(ctx):
        return or_(ref.is_not(None), ident_value.is_not(None))

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# -- ingredient: the reference table -------------------------------------------------------


def _ingredient_param(targets: tuple[str, ...]):
    """(match, present, chain, sort) for `ingredient`, held in the shared reference table."""
    param = "ingredient"

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return _exists(
                _R,
                _R.param == param,
                token_condition(
                    _R.reference_identifier_system,
                    _R.reference_identifier_value,
                    parse_token(value),
                ),
            )
        return _exists(
            _R,
            _R.param == param,
            reference_match(
                _R.reference_type,
                _R.reference_id,
                _R.reference_reference,
                value,
                modifier,
                ctx,
                targets,
                str,
            ),
        )

    def present(ctx):
        return _exists(
            _R,
            _R.param == param,
            or_(
                _R.reference_reference.is_not(None),
                _R.reference_identifier_value.is_not(None),
            ),
        )

    def chain(target, inner, ctx):
        return _exists(
            _R,
            _R.param == param,
            _R.reference_type == target,
            _R.reference_id.in_(_referenced(target, inner, ctx)),
        )

    def sort():
        return _child_sort(_R.reference_id, _R, _R.param == param)

    return match, present, chain, sort


# -- _include / _revinclude ----------------------------------------------------------------


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _load(session, ctx, resource_type: str, ids) -> list:
    if not ids:
        return []
    model, id_col = _model(resource_type)
    return await _fetch(
        session, select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids))
    )


def _include_column(prefix: str, resource_type: str):
    """_include of a reference held as columns (`manufacturer`): the rows of `resource_type`
    these medications point at."""

    async def fetch(session, ctx, medications):
        type_, id_ = f"{prefix}_type", f"{prefix}_id"
        ids = {
            getattr(m, id_)
            for m in medications
            if getattr(m, type_) == resource_type and getattr(m, id_)
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_child(model, resource_type: str, *conditions):
    """_include of a reference held in a child table (`ingredient`)."""

    async def fetch(session, ctx, medications):
        ids = select(model.reference_id).where(
            model.medication_pk.in_({m.id for m in medications}),
            model.reference_type == resource_type,
            model.reference_id.is_not(None),
            *conditions,
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def revinclude_medications_via_column(prefix: str, resource_type: str, key):
    """_revinclude=Medication:manufacturer - medications whose column reference points at
    one of these rows (matched on the public id `key(row)`). Declared on the registry of each
    target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        type_, id_ = getattr(P, f"{prefix}_type"), getattr(P, f"{prefix}_id")
        return await _fetch(
            session,
            select(P).where(
                P.tenant_id == ctx.tenant_id, type_ == resource_type, id_.in_(ids)
            ),
        )

    return fetch


def revinclude_medications_via_child(model, resource_type: str, key, *conditions):
    """_revinclude=Medication:ingredient - medications with a row in `model` pointing at one
    of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(model.medication_pk).where(
            model.reference_type == resource_type,
            model.reference_id.in_(ids),
            *conditions,
        )
        return await _fetch(
            session, select(P).where(P.tenant_id == ctx.tenant_id, P.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Medication rows."""
    from app.fhir.mappers.medication import to_fhir_medication
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(
        ResourceKind(
            "Medication", lambda m: m.medication_id, to_fhir_medication, "medications"
        )
    )


# -- registry ------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def medication_search() -> SearchRegistry:
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

    ingredient_targets = REFERENCE_TYPES["ingredient"]
    ing_match, ing_present, ing_chain, ing_sort = _ingredient_param(ingredient_targets)
    man_match, man_present, man_chain, man_sort = _column_ref(
        "manufacturer", MANUFACTURER_TYPES
    )

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public medication id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.medication_id,
            example="250001",
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
            "Returns medications for a specific code",
            "Medication.code",
            "http://www.nlm.nih.gov/research/umls/rxnorm|1049502",
        ),
        SearchParam(
            "expiration-date",
            "date",
            "Returns medications in a batch with this expiration date",
            "Medication.batch.expirationDate",
            _expiration_match,
            lambda ctx: P.expiration_start.is_not(None),
            sort=lambda: P.expiration_start,
            example="ge2026-01-01",
        ),
        token(
            "form",
            "Returns medications for a specific dose form",
            "Medication.form",
            "http://snomed.info/sct|385055001",
        ),
        SearchParam(
            "identifier",
            "token",
            "Returns medications with this external identifier",
            "Medication.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:medications|MED-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "ingredient",
            "reference",
            "Returns medications for this ingredient reference (a Substance or a Medication)",
            "(Medication.ingredient.item as Reference)",
            ing_match,
            ing_present,
            _REFERENCE,
            targets=ingredient_targets,
            chain=ing_chain,
            chain_targets={
                t: _registry_of(t) for t in ingredient_targets if t in _MODELED
            },
            sort=ing_sort,
            example="Medication/250001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        token(
            "ingredient-code",
            "Returns medications for this ingredient code",
            "(Medication.ingredient.item as CodeableConcept)",
            "http://snomed.info/sct|387458008",
        ),
        SearchParam(
            "lot-number",
            "token",
            "Returns medications in a batch with this lot number",
            "Medication.batch.lotNumber",
            _lot_number_match,
            lambda ctx: P.lot_number.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.lot_number,
            example="LOT-2026-1",
        ),
        SearchParam(
            "manufacturer",
            "reference",
            "Returns medications made or sold for this manufacturer",
            "Medication.manufacturer",
            man_match,
            man_present,
            _REFERENCE,
            targets=MANUFACTURER_TYPES,
            chain=man_chain,
            chain_targets={t: _registry_of(t) for t in MANUFACTURER_TYPES},
            sort=man_sort,
            example="Organization/190001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        SearchParam(
            "status",
            "token",
            f"active | inactive | entered-in-error (system {_STATUS_SYSTEM})",
            "Medication.status",
            _status_match,
            lambda ctx: P.status.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.status,
            example="active",
        ),
    ]

    return SearchRegistry(
        resource_type="Medication",
        params={p.name: p for p in params},
        # Σ elements in the R4 Medication definition (beyond id/meta/implicitRules).
        summary_elements=frozenset({"identifier", "code", "status", "manufacturer"}),
        # Medication has no element with minimum cardinality 1.
        mandatory_elements=frozenset(),
        includes=(
            IncludeTarget(
                "Medication",
                "manufacturer",
                "Organization",
                _include_column("manufacturer", "Organization"),
            ),
            IncludeTarget(
                "Medication",
                "ingredient",
                "Medication",
                _include_child(_R, "Medication", _R.param == "ingredient"),
            ),
        ),
        # A Medication that has another one as an ingredient points back at it.
        revincludes=(
            *column_flag_revincludes(
                ("subject",), "subject", "Medication", lambda x: x.medication_id
            ),
            *column_medication_dispense_revincludes(
                ("medication",), "medication", "Medication", lambda x: x.medication_id
            ),
            *column_medication_administration_revincludes(
                ("medication",), "medication", "Medication", lambda x: x.medication_id
            ),
            *column_medication_statement_revincludes(
                ("medication",), "medication", "Medication", lambda x: x.medication_id
            ),
            *member_group_revincludes("Medication", lambda m: m.medication_id),
            *column_medication_request_revincludes(
                ("medication",), "medication", "Medication", lambda m: m.medication_id
            ),
            IncludeTarget(
                "Medication",
                "ingredient",
                "Medication",
                revinclude_medications_via_child(
                    _R,
                    "Medication",
                    lambda m: m.medication_id,
                    _R.param == "ingredient",
                ),
                reverse=True,
            ),
        ),
        default_sort=lambda: [P.medication_id.desc()],
    )
