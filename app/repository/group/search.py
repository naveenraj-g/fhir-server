"""
FHIR R4 Group search parameters (https://www.hl7.org/fhir/R4/group.html#search) plus the
common `_id` / `_lastUpdated`, declared once for app.fhir.search: parsing, SQL, `_sort`,
`_include` / `_revinclude`, and the OpenAPI docs all come from group_search() below. Same
arrangement as app.repository.medication.search (a column reference, a shared token table);
`characteristic-value` is a composite like Observation's (a characteristic code and a value of
the *same* characteristic, paired by `slot`).

Each parameter's SQL reads only the search index (GroupModel's columns and child tables, see
its docstring) - never `content`.
"""

from __future__ import annotations

import importlib
from functools import cache

from sqlalchemy import and_, exists, false, func, literal, or_, select, true
from sqlalchemy.orm import aliased

from app.repository._search_targets import MODELED
from app.repository._medication_dispense_revinclude import (
    column_medication_dispense_revincludes,
)
from app.repository._medication_administration_revinclude import (
    column_medication_administration_revincludes,
)
from app.repository._medication_statement_revinclude import (
    column_medication_statement_revincludes,
)
from app.repository._document_reference_revinclude import (
    column_document_reference_revincludes,
)
from app.repository._care_plan_revinclude import column_care_plan_revincludes
from app.repository._care_team_revinclude import column_care_team_revincludes
from app.fhir.search import IncludeTarget, MultiValueSort, SearchParam, SearchRegistry
from app.fhir.search.composite import split_composite
from app.fhir.search.sql import (
    coded_token_match,
    date_match,
    reference_match,
    token_condition,
    token_match,
    token_text_match,
)
from app.fhir.search.values import parse_of_type, parse_token
from app.models.group import (
    MANAGING_ENTITY_TYPES,
    MEMBER_TYPES,
    GroupIdentifier,
    GroupMember,
    GroupModel,
    GroupToken,
    GroupType,
)

P = GroupModel
_I = GroupIdentifier
_Tk = GroupToken
_Mb = GroupMember
_TYPE_SYSTEM = "http://hl7.org/fhir/group-type"


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
    return exists(select(literal(1)).where(model.group_pk == P.id, *conditions))


def _child_sort(column, model, *conditions):
    """_sort key for a parameter held in a child table (several values per resource): its
    smallest value ascending, its largest descending."""

    def agg(fn):
        return (
            select(fn(column))
            .where(model.group_pk == P.id, *conditions)
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
    return P.group_id == int(token.code)


def _type_match(value, modifier, ctx):
    """`type` is a `code` bound to the group-type system: `code` or `system|code`; another
    system or `|code` (no system) never matches; an unknown code matches nothing (rather than
    failing the Postgres enum cast)."""
    token = parse_token(value)
    if token.system is not None and token.system != _TYPE_SYSTEM:
        return false()
    if token.code is None:
        return P.type.is_not(None)
    try:
        return P.type == GroupType(token.code)
    except ValueError:
        return false()


def _actual_match(value, modifier, ctx):
    """`actual` is a boolean token: `true` or `false` (a boolean has no system)."""
    token = parse_token(value)
    if token.system is not None or token.code not in ("true", "false"):
        return false()
    return P.actual.is_(token.code == "true")


# -- identifier / the token parameters ---------------------------------------------------------


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
    selected by its `param` value. A boolean is a row with code `true` / `false`."""

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


def _characteristic_value_match(value, modifier, ctx):
    """`characteristic-value` composite: some characteristic (slot) has a code matching the
    first part *and* a value matching the second. Both rows carry the same `slot`, which stops
    the code of one characteristic pairing with the value of another."""
    code_part, value_part = split_composite(value, 2)
    code = aliased(_Tk)
    other = aliased(_Tk)
    paired = exists(
        select(literal(1))
        .where(
            other.group_pk == P.id,
            other.slot == code.slot,
            other.param == "value",
            token_match(other.system, other.code, value_part),
        )
        .correlate(P, code)
    )
    return exists(
        select(literal(1))
        .where(
            code.group_pk == P.id,
            code.param == "characteristic",
            token_match(code.system, code.code, code_part),
            paired,
        )
        .correlate(P)
    )


# -- managing-entity: a reference held as columns ---------------------------------------------


def _managing_entity():
    """(match, present, chain, sort) for the 0..1 managingEntity Reference held as
    `managing_entity_*` columns on the group row."""
    ref, type_, id_ = (
        P.managing_entity_reference,
        P.managing_entity_type,
        P.managing_entity_id,
    )
    ident_system, ident_value = (
        P.managing_entity_identifier_system,
        P.managing_entity_identifier_value,
    )

    def match(value, modifier, ctx):
        if modifier == "identifier":
            return token_condition(ident_system, ident_value, parse_token(value))
        # `modifier` is a target type (managing-entity:Organization=190001) or None; a bare id
        # with several targets is ambiguous and is rejected by reference_target().
        return reference_match(
            type_, id_, ref, value, modifier, ctx, MANAGING_ENTITY_TYPES, str
        )

    def present(ctx):
        return or_(ref.is_not(None), ident_value.is_not(None))

    def chain(target, inner, ctx):
        return and_(type_ == target, id_.in_(_referenced(target, inner, ctx)))

    return match, present, chain, lambda: id_


# -- member: the member table ------------------------------------------------------------------


def _member_match(value, modifier, ctx):
    if modifier == "identifier":
        return _exists(
            _Mb,
            token_condition(
                _Mb.reference_identifier_system,
                _Mb.reference_identifier_value,
                parse_token(value),
            ),
        )
    return _exists(
        _Mb,
        reference_match(
            _Mb.reference_type,
            _Mb.reference_id,
            _Mb.reference_reference,
            value,
            modifier,
            ctx,
            MEMBER_TYPES,
            str,
        ),
    )


def _member_present(ctx):
    return _exists(
        _Mb,
        or_(
            _Mb.reference_reference.is_not(None),
            _Mb.reference_identifier_value.is_not(None),
        ),
    )


def _member_chain(target, inner, ctx):
    return _exists(
        _Mb,
        _Mb.reference_type == target,
        _Mb.reference_id.in_(_referenced(target, inner, ctx)),
    )


# -- _include / _revinclude --------------------------------------------------------------------


async def _fetch(session, stmt) -> list:
    return list((await session.execute(stmt)).scalars().all())


async def _load(session, ctx, resource_type: str, ids) -> list:
    if not ids:
        return []
    model, id_col = _model(resource_type)
    return await _fetch(
        session, select(model).where(model.tenant_id == ctx.tenant_id, id_col.in_(ids))
    )


def _include_managing_entity(resource_type: str):
    async def fetch(session, ctx, groups):
        ids = {
            g.managing_entity_id
            for g in groups
            if g.managing_entity_type == resource_type and g.managing_entity_id
        }
        return await _load(session, ctx, resource_type, ids)

    return fetch


def _include_member(resource_type: str):
    async def fetch(session, ctx, groups):
        ids = select(_Mb.reference_id).where(
            _Mb.group_pk.in_({g.id for g in groups}),
            _Mb.reference_type == resource_type,
            _Mb.reference_id.is_not(None),
        )
        return await _load(
            session,
            ctx,
            resource_type,
            set((await session.execute(ids)).scalars().all()),
        )

    return fetch


def revinclude_groups_via_managing_entity(resource_type: str, key):
    """_revinclude=Group:managing-entity - groups whose managingEntity points at one of these
    rows (matched on the public id `key(row)`). Declared on the registry of each target type."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        return await _fetch(
            session,
            select(P).where(
                P.tenant_id == ctx.tenant_id,
                P.managing_entity_type == resource_type,
                P.managing_entity_id.in_(ids),
            ),
        )

    return fetch


def revinclude_groups_via_member(resource_type: str, key):
    """_revinclude=Group:member - groups with a member pointing at one of these rows."""

    async def fetch(session, ctx, rows):
        ids = {key(r) for r in rows}
        pks = select(_Mb.group_pk).where(
            _Mb.reference_type == resource_type, _Mb.reference_id.in_(ids)
        )
        return await _fetch(
            session, select(P).where(P.tenant_id == ctx.tenant_id, P.id.in_(pks))
        )

    return fetch


def _register_kind() -> None:
    """How the search engine identifies and renders Group rows."""
    from app.fhir.mappers.group import to_fhir_group
    from app.fhir.search.execute import ResourceKind, register_kind

    register_kind(ResourceKind("Group", lambda g: g.group_id, to_fhir_group, "groups"))


# -- registry ----------------------------------------------------------------------------------

_TOKEN = frozenset({"text", "not", "in", "not-in", "above", "below", "missing"})
_REFERENCE = frozenset({"identifier", "missing"})
_IDENTIFIER_DOC = {
    "identifier": "`:identifier` — match the logical identifier of a target that has no resource here."
}


@cache
def group_search() -> SearchRegistry:
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

    me_match, me_present, me_chain, me_sort = _managing_entity()
    modeled_members = [t for t in MEMBER_TYPES if t in _MODELED]

    params = [
        SearchParam(
            "_id",
            "token",
            "Logical id of the resource (the public group id)",
            "Resource.id",
            _id_match,
            lambda ctx: true(),
            frozenset({"not", "missing"}),
            sort=lambda: P.group_id,
            example="430001",
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
        SearchParam(
            "actual",
            "token",
            "Descriptive or actual (true | false)",
            "Group.actual",
            _actual_match,
            lambda ctx: P.actual.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.actual,
            example="true",
        ),
        token(
            "characteristic",
            "Kind of characteristic",
            "Group.characteristic.code",
            "http://loinc.org|8302-2",
        ),
        SearchParam(
            "characteristic-value",
            "composite",
            "A composite of both characteristic and value, on the same characteristic "
            "(`characteristic$value`, e.g. `8302-2$180`)",
            "Group.characteristic: characteristic: code, value: value",
            _characteristic_value_match,
            lambda ctx: _exists(_Tk, _Tk.param == "characteristic"),
            frozenset(),
            example="http://loinc.org|8302-2$http://snomed.info/sct|248153007",
        ),
        token(
            "code",
            "The kind of resources contained",
            "Group.code",
            "http://snomed.info/sct|385093006",
        ),
        token(
            "exclude",
            "Group includes or excludes (true | false)",
            "Group.characteristic.exclude",
            "false",
        ),
        SearchParam(
            "identifier",
            "token",
            "Unique id",
            "Group.identifier",
            _identifier_match,
            lambda ctx: _exists(_I),
            frozenset({"text", "not", "of-type", "missing"}),
            sort=lambda: _child_sort(_I.value, _I),
            example="urn:groups|GRP-1",
            modifier_docs={
                "text": "`:text` — string search (starts-with) on Identifier.type.text / type.coding.display."
            },
        ),
        SearchParam(
            "managing-entity",
            "reference",
            "Entity that is the custodian of the Group's definition",
            "Group.managingEntity",
            me_match,
            me_present,
            _REFERENCE,
            targets=MANAGING_ENTITY_TYPES,
            chain=me_chain,
            chain_targets={t: _registry_of(t) for t in MANAGING_ENTITY_TYPES},
            sort=me_sort,
            example="Organization/190001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        SearchParam(
            "member",
            "reference",
            "Reference to the group member",
            "Group.member.entity",
            _member_match,
            _member_present,
            _REFERENCE,
            targets=MEMBER_TYPES,
            chain=_member_chain,
            chain_targets={t: _registry_of(t) for t in modeled_members},
            sort=lambda: _child_sort(_Mb.reference_id, _Mb),
            example="Patient/10001",
            modifier_docs=_IDENTIFIER_DOC,
        ),
        SearchParam(
            "type",
            "token",
            "person | animal | practitioner | device | medication | substance "
            f"(system {_TYPE_SYSTEM})",
            "Group.type",
            _type_match,
            lambda ctx: P.type.is_not(None),
            frozenset({"not", "missing"}),
            sort=lambda: P.type,
            example="person",
        ),
        token(
            "value",
            "Value held by characteristic (a CodeableConcept or a boolean)",
            "(Group.characteristic.value as CodeableConcept) | (Group.characteristic.value as boolean)",
            "http://snomed.info/sct|248153007",
        ),
    ]

    return SearchRegistry(
        resource_type="Group",
        params={p.name: p for p in params},
        # Σ elements in the R4 Group definition (beyond id/meta/implicitRules).
        summary_elements=frozenset(
            {
                "identifier",
                "active",
                "type",
                "actual",
                "code",
                "name",
                "quantity",
                "managingEntity",
            }
        ),
        # Elements with min cardinality 1 in R4 — kept by _summary=text / _elements.
        mandatory_elements=frozenset({"type", "actual"}),
        includes=(
            *(
                IncludeTarget(
                    "Group", "managing-entity", t, _include_managing_entity(t)
                )
                for t in MANAGING_ENTITY_TYPES
            ),
            *(
                IncludeTarget("Group", "member", t, _include_member(t))
                for t in modeled_members
            ),
        ),
        # A Group that has another one as a member points back at it.
        revincludes=(
            *column_medication_dispense_revincludes(
                ("subject",), "subject", "Group", lambda x: x.group_id
            ),
            *column_medication_administration_revincludes(
                ("subject",), "subject", "Group", lambda x: x.group_id
            ),
            *column_medication_statement_revincludes(
                ("subject",), "subject", "Group", lambda x: x.group_id
            ),
            *column_document_reference_revincludes(
                ("subject",), "subject", "Group", lambda x: x.group_id
            ),
            *column_care_plan_revincludes(
                ("subject",), "subject", "Group", lambda x: x.group_id
            ),
            *column_care_team_revincludes(
                ("subject",), "subject", "Group", lambda g: g.group_id
            ),
            IncludeTarget(
                "Group",
                "member",
                "Group",
                revinclude_groups_via_member("Group", lambda g: g.group_id),
                reverse=True,
            ),
        ),
        default_sort=lambda: [P.group_id.desc()],
    )
