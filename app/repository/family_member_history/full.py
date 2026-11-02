from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import IdentifierUse as IdentifierUseModel
from app.models.family_member_history import (
    FamilyMemberHistoryCondition,
    FamilyMemberHistoryConditionCodeCoding,
    FamilyMemberHistoryConditionNote,
    FamilyMemberHistoryConditionOutcomeCoding,
    FamilyMemberHistoryDataAbsentReasonCoding,
    FamilyMemberHistoryIdentifier,
    FamilyMemberHistoryIdentifierTypeCoding,
    FamilyMemberHistoryModel,
    FamilyMemberHistoryNote,
    FamilyMemberHistoryReasonCode,
    FamilyMemberHistoryReasonCodeCoding,
    FamilyMemberHistoryReasonReference,
    FamilyMemberHistoryRelationshipCoding,
    FamilyMemberHistorySexCoding,
)
from app.schemas.family_member_history import (
    FamilyMemberHistoryCreateSchema,
    FamilyMemberHistoryPatchSchema,
)

from ._shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _parse_assigner_ref,
    _parse_author_ref,
    _parse_patient_ref,
    _parse_reason_ref,
    _reference_kwargs,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    return {
        "tenant_id": org_id,
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


async def _add_identifiers(
    session, family_member_history_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")

        ident = FamilyMemberHistoryIdentifier(
            family_member_history_pk=family_member_history_pk,
            tenant_id=org_id,
            use=IdentifierUseModel[i.use.name] if i.use else None,
            type_text=i.type.text if i.type else None,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner_reference=i.assigner,
            assigner_type=a_type,
            assigner_id=a_id,
            assigner_display=i.assigner_display,
            assigner_identifier_use=(
                IdentifierUseModel[i.assigner_identifier_use.name]
                if getattr(i, "assigner_identifier_use", None)
                else None
            ),
            **{
                f"assigner_{s}": getattr(i, f"assigner_{s}", None)
                for s in _IDENTIFIER_FALLBACK_SUFFIXES
                if s != "identifier_use"
            },
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()

        if i.type and i.type.coding:
            for c in i.type.coding:
                session.add(
                    FamilyMemberHistoryIdentifierTypeCoding(
                        family_member_history_identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


def _add_data_absent_reason_codings(
    session, family_member_history_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            FamilyMemberHistoryDataAbsentReasonCoding(
                family_member_history_pk=family_member_history_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


def _add_relationship_codings(
    session, family_member_history_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            FamilyMemberHistoryRelationshipCoding(
                family_member_history_pk=family_member_history_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


def _add_sex_codings(
    session, family_member_history_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            FamilyMemberHistorySexCoding(
                family_member_history_pk=family_member_history_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_reason_codes(
    session, family_member_history_pk: int, org_id: str, reason_codes, created_by: str
) -> None:
    for rc in reason_codes or []:
        code_row = FamilyMemberHistoryReasonCode(
            family_member_history_pk=family_member_history_pk,
            tenant_id=org_id,
            text=rc.text,
            created_by=created_by,
        )
        session.add(code_row)
        await session.flush()

        for c in rc.coding or []:
            session.add(
                FamilyMemberHistoryReasonCodeCoding(
                    family_member_history_reason_code_id=code_row.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_reason_references(
    session, family_member_history_pk: int, org_id: str, reason_refs, created_by: str
) -> None:
    for rr in reason_refs or []:
        ref_type, ref_id = (
            _parse_reason_ref(rr.reference) if rr.reference else (None, None)
        )
        if ref_type and ref_id:
            await _validate_ref(
                session, org_id, ref_type, ref_id, "reason_reference.reference"
            )

        session.add(
            FamilyMemberHistoryReasonReference(
                family_member_history_pk=family_member_history_pk,
                tenant_id=org_id,
                reference_reference=rr.reference,
                reference_type=ref_type,
                reference_id=ref_id,
                reference_display=rr.display,
                reference_identifier_use=(
                    IdentifierUseModel[rr.identifier_use.name]
                    if getattr(rr, "identifier_use", None)
                    else None
                ),
                **{
                    f"reference_{s}": getattr(rr, s, None)
                    for s in _IDENTIFIER_FALLBACK_SUFFIXES
                    if s != "identifier_use"
                },
                created_by=created_by,
            )
        )


async def _add_notes(
    session, family_member_history_pk: int, org_id: str, notes, created_by: str
) -> None:
    for n in notes or []:
        author_type, author_id = (
            _parse_author_ref(n.author_reference)
            if n.author_reference
            else (None, None)
        )
        if author_type and author_id:
            await _validate_ref(
                session, org_id, author_type, author_id, "note.author_reference"
            )
        session.add(
            FamilyMemberHistoryNote(
                family_member_history_pk=family_member_history_pk,
                tenant_id=org_id,
                text=n.text,
                time=n.time,
                author_string=n.author_string,
                author_reference=n.author_reference,
                author_type=author_type,
                author_id=author_id,
                author_display=n.author_reference_display,
                author_identifier_use=(
                    IdentifierUseModel[n.author_identifier_use.name]
                    if getattr(n, "author_identifier_use", None)
                    else None
                ),
                **{
                    f"author_{s}": getattr(n, f"author_{s}", None)
                    for s in _IDENTIFIER_FALLBACK_SUFFIXES
                    if s != "identifier_use"
                },
                created_by=created_by,
            )
        )


async def _add_conditions(
    session, family_member_history_pk: int, org_id: str, conditions, created_by: str
) -> None:
    for cond_input in conditions or []:
        cond_row = FamilyMemberHistoryCondition(
            family_member_history_pk=family_member_history_pk,
            tenant_id=org_id,
            code_text=cond_input.code.text if cond_input.code else None,
            outcome_text=cond_input.outcome.text if cond_input.outcome else None,
            contributed_to_death=cond_input.contributed_to_death,
            onset_age_value=cond_input.onset_age_value,
            onset_age_comparator=cond_input.onset_age_comparator,
            onset_age_unit=cond_input.onset_age_unit,
            onset_age_system=cond_input.onset_age_system,
            onset_age_code=cond_input.onset_age_code,
            onset_range_low_value=cond_input.onset_range_low_value,
            onset_range_low_unit=cond_input.onset_range_low_unit,
            onset_range_low_system=cond_input.onset_range_low_system,
            onset_range_low_code=cond_input.onset_range_low_code,
            onset_range_high_value=cond_input.onset_range_high_value,
            onset_range_high_unit=cond_input.onset_range_high_unit,
            onset_range_high_system=cond_input.onset_range_high_system,
            onset_range_high_code=cond_input.onset_range_high_code,
            onset_period_start=cond_input.onset_period_start,
            onset_period_end=cond_input.onset_period_end,
            onset_string=cond_input.onset_string,
            created_by=created_by,
        )
        session.add(cond_row)
        await session.flush()

        if cond_input.code and cond_input.code.coding:
            for c in cond_input.code.coding:
                session.add(
                    FamilyMemberHistoryConditionCodeCoding(
                        family_member_history_condition_id=cond_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )

        if cond_input.outcome and cond_input.outcome.coding:
            for c in cond_input.outcome.coding:
                session.add(
                    FamilyMemberHistoryConditionOutcomeCoding(
                        family_member_history_condition_id=cond_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )

        if cond_input.note:
            for cn in cond_input.note:
                c_author_type, c_author_id = (
                    _parse_author_ref(cn.author_reference)
                    if cn.author_reference
                    else (None, None)
                )
                if c_author_type and c_author_id:
                    await _validate_ref(
                        session,
                        org_id,
                        c_author_type,
                        c_author_id,
                        "condition.note.author_reference",
                    )
                session.add(
                    FamilyMemberHistoryConditionNote(
                        family_member_history_condition_id=cond_row.id,
                        tenant_id=org_id,
                        text=cn.text,
                        time=cn.time,
                        author_string=cn.author_string,
                        author_reference=cn.author_reference,
                        author_type=c_author_type,
                        author_id=c_author_id,
                        author_display=cn.author_reference_display,
                        author_identifier_use=(
                            IdentifierUseModel[cn.author_identifier_use.name]
                            if getattr(cn, "author_identifier_use", None)
                            else None
                        ),
                        **{
                            f"author_{s}": getattr(cn, f"author_{s}", None)
                            for s in _IDENTIFIER_FALLBACK_SUFFIXES
                            if s != "identifier_use"
                        },
                        created_by=created_by,
                    )
                )


class _FullMixin:
    """Mixin for atomic create_full and patch_full operations on FamilyMemberHistory."""

    async def create_full(
        self,
        payload: FamilyMemberHistoryCreateSchema,
        org_id: str,
        created_by: str,
    ) -> FamilyMemberHistoryModel:
        """Create a complete FamilyMemberHistory and all child records in a single transaction."""
        async with self.session_factory() as session:
            # 1. Parse & validate patient reference
            p_type, p_id = _parse_patient_ref(payload.patient)
            await _validate_ref(session, org_id, p_type, p_id, "patient")

            model = FamilyMemberHistoryModel(
                tenant_id=org_id,
                created_by=created_by,
                instantiates_canonical=payload.instantiates_canonical,
                instantiates_uri=payload.instantiates_uri,
                status=payload.status,
                data_absent_reason_text=(
                    payload.data_absent_reason.text
                    if payload.data_absent_reason
                    else None
                ),
                patient_reference=payload.patient,
                patient_type=p_type,
                patient_id=p_id,
                patient_display=payload.patient_display,
                **_reference_kwargs("patient", payload),
                date=payload.date,
                name=payload.name,
                relationship_text=(
                    payload.relationship.text if payload.relationship else None
                ),
                sex_text=payload.sex.text if payload.sex else None,
                born_period_start=payload.born_period_start,
                born_period_end=payload.born_period_end,
                born_date=payload.born_date,
                born_string=payload.born_string,
                age_age_value=payload.age_age_value,
                age_age_comparator=payload.age_age_comparator,
                age_age_unit=payload.age_age_unit,
                age_age_system=payload.age_age_system,
                age_age_code=payload.age_age_code,
                age_range_low_value=payload.age_range_low_value,
                age_range_low_unit=payload.age_range_low_unit,
                age_range_low_system=payload.age_range_low_system,
                age_range_low_code=payload.age_range_low_code,
                age_range_high_value=payload.age_range_high_value,
                age_range_high_unit=payload.age_range_high_unit,
                age_range_high_system=payload.age_range_high_system,
                age_range_high_code=payload.age_range_high_code,
                age_string=payload.age_string,
                estimated_age=payload.estimated_age,
                deceased_boolean=payload.deceased_boolean,
                deceased_age_value=payload.deceased_age_value,
                deceased_age_comparator=payload.deceased_age_comparator,
                deceased_age_unit=payload.deceased_age_unit,
                deceased_age_system=payload.deceased_age_system,
                deceased_age_code=payload.deceased_age_code,
                deceased_range_low_value=payload.deceased_range_low_value,
                deceased_range_low_unit=payload.deceased_range_low_unit,
                deceased_range_low_system=payload.deceased_range_low_system,
                deceased_range_low_code=payload.deceased_range_low_code,
                deceased_range_high_value=payload.deceased_range_high_value,
                deceased_range_high_unit=payload.deceased_range_high_unit,
                deceased_range_high_system=payload.deceased_range_high_system,
                deceased_range_high_code=payload.deceased_range_high_code,
                deceased_date=payload.deceased_date,
                deceased_string=payload.deceased_string,
                extension=payload.extension or [],
            )
            session.add(model)
            await session.flush()

            # 2. Add sub-resources
            if payload.data_absent_reason and payload.data_absent_reason.coding:
                _add_data_absent_reason_codings(
                    session,
                    model.id,
                    org_id,
                    payload.data_absent_reason.coding,
                    created_by,
                )

            if payload.relationship and payload.relationship.coding:
                _add_relationship_codings(
                    session,
                    model.id,
                    org_id,
                    payload.relationship.coding,
                    created_by,
                )

            if payload.sex and payload.sex.coding:
                _add_sex_codings(
                    session,
                    model.id,
                    org_id,
                    payload.sex.coding,
                    created_by,
                )

            if payload.reason_code:
                await _add_reason_codes(
                    session, model.id, org_id, payload.reason_code, created_by
                )

            if payload.reason_reference:
                await _add_reason_references(
                    session, model.id, org_id, payload.reason_reference, created_by
                )

            if payload.note:
                await _add_notes(session, model.id, org_id, payload.note, created_by)

            if payload.condition:
                await _add_conditions(
                    session, model.id, org_id, payload.condition, created_by
                )

            if payload.identifier:
                await _add_identifiers(
                    session, model.id, org_id, payload.identifier, created_by
                )

            await session.commit()

        return await self.get_by_family_member_history_id_in_org(
            model.family_member_history_id, org_id
        )

    async def patch_full(
        self,
        family_member_history_id: int,
        payload: FamilyMemberHistoryPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> FamilyMemberHistoryModel | None:
        """Partially update a FamilyMemberHistory and replace any supplied sub-resource lists atomically."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(FamilyMemberHistoryModel).where(
                    FamilyMemberHistoryModel.family_member_history_id
                    == family_member_history_id,
                    FamilyMemberHistoryModel.tenant_id == org_id,
                )
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            data = payload.model_dump(exclude_unset=True)

            # References
            if "patient" in data and payload.patient is not None:
                p_type, p_id = _parse_patient_ref(payload.patient)
                await _validate_ref(session, org_id, p_type, p_id, "patient")
                model.patient_reference = payload.patient
                model.patient_type = p_type
                model.patient_id = p_id

            if "patient_display" in data:
                model.patient_display = payload.patient_display

            for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
                field_name = f"patient_{suffix}"
                if field_name in data:
                    val = getattr(payload, field_name, None)
                    if suffix == "identifier_use" and val is not None:
                        setattr(model, field_name, IdentifierUseModel[val.name] if hasattr(val, "name") else val)
                    else:
                        setattr(model, field_name, val)

            # Scalar fields
            scalar_fields = (
                "instantiates_canonical",
                "instantiates_uri",
                "status",
                "date",
                "name",
                "born_period_start",
                "born_period_end",
                "born_date",
                "born_string",
                "age_age_value",
                "age_age_comparator",
                "age_age_unit",
                "age_age_system",
                "age_age_code",
                "age_range_low_value",
                "age_range_low_unit",
                "age_range_low_system",
                "age_range_low_code",
                "age_range_high_value",
                "age_range_high_unit",
                "age_range_high_system",
                "age_range_high_code",
                "age_string",
                "estimated_age",
                "deceased_boolean",
                "deceased_age_value",
                "deceased_age_comparator",
                "deceased_age_unit",
                "deceased_age_system",
                "deceased_age_code",
                "deceased_range_low_value",
                "deceased_range_low_unit",
                "deceased_range_low_system",
                "deceased_range_low_code",
                "deceased_range_high_value",
                "deceased_range_high_unit",
                "deceased_range_high_system",
                "deceased_range_high_code",
                "deceased_date",
                "deceased_string",
                "extension",
            )
            for f in scalar_fields:
                if f in data:
                    setattr(model, f, getattr(payload, f))

            # data_absent_reason
            if "data_absent_reason" in data:
                await session.execute(
                    delete(FamilyMemberHistoryDataAbsentReasonCoding).where(
                        FamilyMemberHistoryDataAbsentReasonCoding.family_member_history_pk
                        == model.id
                    )
                )
                if payload.data_absent_reason:
                    model.data_absent_reason_text = payload.data_absent_reason.text
                    if payload.data_absent_reason.coding:
                        _add_data_absent_reason_codings(
                            session,
                            model.id,
                            org_id,
                            payload.data_absent_reason.coding,
                            updated_by,
                        )
                else:
                    model.data_absent_reason_text = None

            # relationship
            if "relationship" in data:
                await session.execute(
                    delete(FamilyMemberHistoryRelationshipCoding).where(
                        FamilyMemberHistoryRelationshipCoding.family_member_history_pk
                        == model.id
                    )
                )
                if payload.relationship:
                    model.relationship_text = payload.relationship.text
                    if payload.relationship.coding:
                        _add_relationship_codings(
                            session,
                            model.id,
                            org_id,
                            payload.relationship.coding,
                            updated_by,
                        )
                else:
                    model.relationship_text = None

            # sex
            if "sex" in data:
                await session.execute(
                    delete(FamilyMemberHistorySexCoding).where(
                        FamilyMemberHistorySexCoding.family_member_history_pk
                        == model.id
                    )
                )
                if payload.sex:
                    model.sex_text = payload.sex.text
                    if payload.sex.coding:
                        _add_sex_codings(
                            session,
                            model.id,
                            org_id,
                            payload.sex.coding,
                            updated_by,
                        )
                else:
                    model.sex_text = None

            # reason_code (with grandchild reason_code_coding)
            if "reason_code" in data:
                rc_ids_sub = select(FamilyMemberHistoryReasonCode.id).where(
                    FamilyMemberHistoryReasonCode.family_member_history_pk == model.id
                )
                await session.execute(
                    delete(FamilyMemberHistoryReasonCodeCoding).where(
                        FamilyMemberHistoryReasonCodeCoding.family_member_history_reason_code_id.in_(
                            rc_ids_sub
                        )
                    )
                )
                await session.execute(
                    delete(FamilyMemberHistoryReasonCode).where(
                        FamilyMemberHistoryReasonCode.family_member_history_pk
                        == model.id
                    )
                )
                if payload.reason_code:
                    await _add_reason_codes(
                        session, model.id, org_id, payload.reason_code, updated_by
                    )

            # reason_reference
            if "reason_reference" in data:
                await session.execute(
                    delete(FamilyMemberHistoryReasonReference).where(
                        FamilyMemberHistoryReasonReference.family_member_history_pk
                        == model.id
                    )
                )
                if payload.reason_reference:
                    await _add_reason_references(
                        session,
                        model.id,
                        org_id,
                        payload.reason_reference,
                        updated_by,
                    )

            # note
            if "note" in data:
                await session.execute(
                    delete(FamilyMemberHistoryNote).where(
                        FamilyMemberHistoryNote.family_member_history_pk == model.id
                    )
                )
                if payload.note:
                    await _add_notes(
                        session, model.id, org_id, payload.note, updated_by
                    )

            # condition (with grandchildren condition_code_coding, outcome_coding, notes)
            if "condition" in data:
                cond_ids_sub = select(FamilyMemberHistoryCondition.id).where(
                    FamilyMemberHistoryCondition.family_member_history_pk == model.id
                )
                await session.execute(
                    delete(FamilyMemberHistoryConditionCodeCoding).where(
                        FamilyMemberHistoryConditionCodeCoding.family_member_history_condition_id.in_(
                            cond_ids_sub
                        )
                    )
                )
                await session.execute(
                    delete(FamilyMemberHistoryConditionOutcomeCoding).where(
                        FamilyMemberHistoryConditionOutcomeCoding.family_member_history_condition_id.in_(
                            cond_ids_sub
                        )
                    )
                )
                await session.execute(
                    delete(FamilyMemberHistoryConditionNote).where(
                        FamilyMemberHistoryConditionNote.family_member_history_condition_id.in_(
                            cond_ids_sub
                        )
                    )
                )
                await session.execute(
                    delete(FamilyMemberHistoryCondition).where(
                        FamilyMemberHistoryCondition.family_member_history_pk == model.id
                    )
                )
                if payload.condition:
                    await _add_conditions(
                        session, model.id, org_id, payload.condition, updated_by
                    )

            # identifier (with grandchild identifier_type_coding)
            if "identifier" in data:
                ident_ids_sub = select(FamilyMemberHistoryIdentifier.id).where(
                    FamilyMemberHistoryIdentifier.family_member_history_pk == model.id
                )
                await session.execute(
                    delete(FamilyMemberHistoryIdentifierTypeCoding).where(
                        FamilyMemberHistoryIdentifierTypeCoding.family_member_history_identifier_id.in_(
                            ident_ids_sub
                        )
                    )
                )
                await session.execute(
                    delete(FamilyMemberHistoryIdentifier).where(
                        FamilyMemberHistoryIdentifier.family_member_history_pk
                        == model.id
                    )
                )
                if payload.identifier:
                    await _add_identifiers(
                        session, model.id, org_id, payload.identifier, updated_by
                    )

            # Always set updated_by explicitly
            model.updated_by = updated_by

            await session.commit()

        return await self.get_by_family_member_history_id_in_org(
            model.family_member_history_id, org_id
        )
