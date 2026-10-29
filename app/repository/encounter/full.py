from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.encounter import (
    EncounterAccount,
    EncounterAppointment,
    EncounterBasedOn,
    EncounterClassHistory,
    EncounterDiagnosis,
    EncounterDiagnosisUseCoding,
    EncounterEpisodeOfCare,
    EncounterHospitalization,
    EncounterHospitalizationAdmitSourceCoding,
    EncounterHospitalizationDietPreference,
    EncounterHospitalizationDietPreferenceCoding,
    EncounterHospitalizationDischargeDispositionCoding,
    EncounterHospitalizationPreAdmissionIdentifierTypeCoding,
    EncounterHospitalizationReAdmissionCoding,
    EncounterHospitalizationSpecialArrangement,
    EncounterHospitalizationSpecialArrangementCoding,
    EncounterHospitalizationSpecialCourtesy,
    EncounterHospitalizationSpecialCourtesyCoding,
    EncounterIdentifier,
    EncounterIdentifierTypeCoding,
    EncounterLocationPhysicalTypeCoding,
    EncounterLocationRow,
    EncounterModel,
    EncounterParticipant,
    EncounterParticipantType,
    EncounterParticipantTypeCoding,
    EncounterReasonCode,
    EncounterReasonCodeCoding,
    EncounterReasonReference,
    EncounterStatus as EncounterStatusModel,
    EncounterStatusHistory,
    EncounterType,
    EncounterTypeCoding,
)
from app.models.encounter.enums import EncounterHospitalizationReferenceType
from app.models.enums import (
    AppointmentReferenceType,
    EncounterReferenceType,
    OrganizationReferenceType,
    SubjectReferenceType,
)
from app.schemas.encounter import EncounterCreateSchema, EncounterPatchSchema

from ._shared import (
    _org_ref_kwargs,
    _parse_org_ref,
    _parse_ref,
    _ref_kwargs,
    _reference_kwargs,
    _validate_individual_reference,
    _validate_reference,
)

logger = get_logger(__name__)

# Sub-resource LIST fields on the create/patch payloads (hospitalization is
# 0..1, handled separately below, not through this set). A supplied list
# (even `[]`) replaces the corresponding rows wholesale; an omitted one is
# untouched.
_SUB = {
    "identifier", "status_history", "class_history", "type", "episode_of_care",
    "based_on", "appointment", "reason_code", "reason_reference", "account",
    "participant", "diagnosis", "location",
}

# Handled by hand in create_full/patch_full rather than the generic setattr
# loop, since they need conversion/promotion, not a plain column assignment.
_SPECIAL = {
    "class_coding", "service_type_coding", "service_type_text",
    "priority_coding", "priority_text",
    "subject", "subject_display", "subject_identifier_use", "subject_identifier_type_system",
    "subject_identifier_type_version", "subject_identifier_type_code", "subject_identifier_type_display",
    "subject_identifier_type_text", "subject_identifier_type_user_selected", "subject_identifier_system",
    "subject_identifier_value", "subject_identifier_period_start", "subject_identifier_period_end",
    "length_value", "length_comparator", "length_unit", "length_system", "length_code",
    "service_provider", "service_provider_display", "service_provider_identifier_use",
    "service_provider_identifier_type_system", "service_provider_identifier_type_version",
    "service_provider_identifier_type_code", "service_provider_identifier_type_display",
    "service_provider_identifier_type_text", "service_provider_identifier_type_user_selected",
    "service_provider_identifier_system", "service_provider_identifier_value",
    "service_provider_identifier_period_start", "service_provider_identifier_period_end",
    "part_of", "part_of_display", "part_of_identifier_use", "part_of_identifier_type_system",
    "part_of_identifier_type_version", "part_of_identifier_type_code", "part_of_identifier_type_display",
    "part_of_identifier_type_text", "part_of_identifier_type_user_selected", "part_of_identifier_system",
    "part_of_identifier_value", "part_of_identifier_period_start", "part_of_identifier_period_end",
    "hospitalization",
}


def _coding_kwargs(coding, created_by: str | None) -> dict:
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


def _single_coding_kwargs(coding) -> dict:
    """Build `system`/`version`/`code`/`display`/`user_selected` ORM
    constructor kwargs from a single app.schemas.datatypes.CodingInput
    object (not a list) — used for Encounter.class /
    Encounter.classHistory.class, both built from FhirCodingMixin.

    Deliberately bare attribute names, never `{prefix}`-prefixed:
    FhirCodingMixin's `_coding_prefix` only renames the underlying DB
    *column* (`Column(f"{cls._coding_prefix}system", ...)`) — the Python
    *attribute* (and therefore the ORM constructor kwarg) is always the
    bare declared_attr method name (`system`, not `class_system`), a
    distinction that cost a `TypeError: 'class_system' is an invalid
    keyword argument` the first time this was gotten wrong."""
    if coding is None:
        return {"system": None, "version": None, "code": None, "display": None, "user_selected": None}
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
    }


def _model_status(status) -> EncounterStatusModel:
    """Convert the Pydantic input schema's app.schemas.enums.EncounterStatus
    (hyphenated .value) to the model-layer
    app.models.encounter.enums.EncounterStatus (underscore-only .value) by
    member NAME — never by value."""
    return EncounterStatusModel[status.name]


def _model_length_comparator(comparator):
    """Convert the Pydantic input schema's app.schemas.enums.EncounterLengthComparator
    (symbolic `.value`, e.g. "<") to the model-layer
    app.models.encounter.enums.EncounterLengthComparator (readable
    lt/le/ge/gt `.value`) by member NAME — never by value. Passing the
    Pydantic enum straight through was a real bug: Postgres rejected the
    literal "<" against the `encounter_length_comparator` type, which
    only accepts the member names."""
    if comparator is None:
        return None
    from app.models.encounter.enums import EncounterLengthComparator as EncounterLengthComparatorModel

    return EncounterLengthComparatorModel[comparator.name]


async def _cascade_delete_cc_list(session, child_model, coding_model, child_fk_col, coding_fk_col, parent_id) -> None:
    """Delete every `coding_model` row belonging to a `child_model` row
    under `parent_id`, then every `child_model` row itself — grandchildren
    first, since there's no DB-level ON DELETE CASCADE on this FK pattern
    (see CLAUDE.md's "A bulk Core delete() of a parent CodeableConcept-list
    row does not cascade" invariant, discovered building
    AppointmentResponse)."""
    await session.execute(
        delete(coding_model).where(
            coding_fk_col.in_(select(child_model.id).where(child_fk_col == parent_id))
        )
    )
    await session.execute(delete(child_model).where(child_fk_col == parent_id))


async def _delete_hospitalization(session, hospitalization_id: int) -> None:
    """Delete an EncounterHospitalization row and every one of its
    grandchildren/children first — see `_cascade_delete_cc_list`'s
    docstring for why this can't just be a single bulk delete of the
    parent row."""
    await _cascade_delete_cc_list(
        session, EncounterHospitalizationDietPreference, EncounterHospitalizationDietPreferenceCoding,
        EncounterHospitalizationDietPreference.encounter_hospitalization_id,
        EncounterHospitalizationDietPreferenceCoding.encounter_hospitalization_diet_preference_id,
        hospitalization_id,
    )
    await _cascade_delete_cc_list(
        session, EncounterHospitalizationSpecialCourtesy, EncounterHospitalizationSpecialCourtesyCoding,
        EncounterHospitalizationSpecialCourtesy.encounter_hospitalization_id,
        EncounterHospitalizationSpecialCourtesyCoding.encounter_hospitalization_special_courtesy_id,
        hospitalization_id,
    )
    await _cascade_delete_cc_list(
        session, EncounterHospitalizationSpecialArrangement, EncounterHospitalizationSpecialArrangementCoding,
        EncounterHospitalizationSpecialArrangement.encounter_hospitalization_id,
        EncounterHospitalizationSpecialArrangementCoding.encounter_hospitalization_special_arrangement_id,
        hospitalization_id,
    )
    await session.execute(
        delete(EncounterHospitalizationAdmitSourceCoding).where(
            EncounterHospitalizationAdmitSourceCoding.encounter_hospitalization_id == hospitalization_id
        )
    )
    await session.execute(
        delete(EncounterHospitalizationReAdmissionCoding).where(
            EncounterHospitalizationReAdmissionCoding.encounter_hospitalization_id == hospitalization_id
        )
    )
    await session.execute(
        delete(EncounterHospitalizationDischargeDispositionCoding).where(
            EncounterHospitalizationDischargeDispositionCoding.encounter_hospitalization_id == hospitalization_id
        )
    )
    await session.execute(
        delete(EncounterHospitalizationPreAdmissionIdentifierTypeCoding).where(
            EncounterHospitalizationPreAdmissionIdentifierTypeCoding.encounter_hospitalization_id == hospitalization_id
        )
    )
    await session.execute(
        delete(EncounterHospitalization).where(EncounterHospitalization.id == hospitalization_id)
    )


async def _add_hospitalization(session, encounter_id: int, org_id: str, h, created_by: str | None) -> None:
    """Insert a new EncounterHospitalization row (plus every one of its
    children/grandchildren) for `h` (an EncounterHospitalizationInput)."""
    origin_type, origin_id = _parse_ref(h.origin, EncounterHospitalizationReferenceType) if h.origin else (None, None)
    if origin_type and origin_id:
        await _validate_reference(session, org_id, origin_type, origin_id, "hospitalization.origin")
    destination_type, destination_id = (
        _parse_ref(h.destination, EncounterHospitalizationReferenceType) if h.destination else (None, None)
    )
    if destination_type and destination_id:
        await _validate_reference(session, org_id, destination_type, destination_id, "hospitalization.destination")

    assigner_type, assigner_id = (
        _parse_org_ref(h.pre_admission_identifier_assigner)
        if h.pre_admission_identifier_assigner else (None, None)
    )
    await _validate_reference(session, org_id, assigner_type, assigner_id, "hospitalization.preAdmissionIdentifier.assigner")

    hospitalization = EncounterHospitalization(
        encounter_pk=encounter_id,
        tenant_id=org_id,
        pre_admission_identifier_use=h.pre_admission_identifier_use,
        pre_admission_identifier_type_text=h.pre_admission_identifier_type_text,
        pre_admission_identifier_system=h.pre_admission_identifier_system,
        pre_admission_identifier_value=h.pre_admission_identifier_value,
        pre_admission_identifier_period_start=h.pre_admission_identifier_period_start,
        pre_admission_identifier_period_end=h.pre_admission_identifier_period_end,
        pre_admission_identifier_assigner_reference=h.pre_admission_identifier_assigner,
        **_org_ref_kwargs(
            "pre_admission_identifier_assigner",
            h.pre_admission_identifier_assigner,
            h.pre_admission_identifier_assigner_display,
        ),
        **_reference_kwargs("pre_admission_identifier_assigner", h),
        origin_reference=h.origin,
        **_ref_kwargs("origin", h.origin, h.origin_display, EncounterHospitalizationReferenceType),
        **_reference_kwargs("origin", h),
        admit_source_text=h.admit_source_text,
        re_admission_text=h.re_admission_text,
        destination_reference=h.destination,
        **_ref_kwargs("destination", h.destination, h.destination_display, EncounterHospitalizationReferenceType),
        **_reference_kwargs("destination", h),
        discharge_disposition_text=h.discharge_disposition_text,
        created_by=created_by,
    )
    session.add(hospitalization)
    await session.flush()

    for coding in h.pre_admission_identifier_type_coding or []:
        session.add(
            EncounterHospitalizationPreAdmissionIdentifierTypeCoding(
                encounter_hospitalization_id=hospitalization.id, tenant_id=org_id,
                **_coding_kwargs(coding, created_by),
            )
        )
    for coding in h.admit_source_coding or []:
        session.add(
            EncounterHospitalizationAdmitSourceCoding(
                encounter_hospitalization_id=hospitalization.id, tenant_id=org_id,
                **_coding_kwargs(coding, created_by),
            )
        )
    for coding in h.re_admission_coding or []:
        session.add(
            EncounterHospitalizationReAdmissionCoding(
                encounter_hospitalization_id=hospitalization.id, tenant_id=org_id,
                **_coding_kwargs(coding, created_by),
            )
        )
    for coding in h.discharge_disposition_coding or []:
        session.add(
            EncounterHospitalizationDischargeDispositionCoding(
                encounter_hospitalization_id=hospitalization.id, tenant_id=org_id,
                **_coding_kwargs(coding, created_by),
            )
        )
    for dp in h.diet_preference or []:
        diet_preference = EncounterHospitalizationDietPreference(
            encounter_hospitalization_id=hospitalization.id, tenant_id=org_id, text=dp.text, created_by=created_by,
        )
        session.add(diet_preference)
        if dp.coding:
            await session.flush()
            for coding in dp.coding:
                session.add(
                    EncounterHospitalizationDietPreferenceCoding(
                        encounter_hospitalization_diet_preference_id=diet_preference.id, tenant_id=org_id,
                        **_coding_kwargs(coding, created_by),
                    )
                )
    for sc in h.special_courtesy or []:
        special_courtesy = EncounterHospitalizationSpecialCourtesy(
            encounter_hospitalization_id=hospitalization.id, tenant_id=org_id, text=sc.text, created_by=created_by,
        )
        session.add(special_courtesy)
        if sc.coding:
            await session.flush()
            for coding in sc.coding:
                session.add(
                    EncounterHospitalizationSpecialCourtesyCoding(
                        encounter_hospitalization_special_courtesy_id=special_courtesy.id, tenant_id=org_id,
                        **_coding_kwargs(coding, created_by),
                    )
                )
    for sa in h.special_arrangement or []:
        special_arrangement = EncounterHospitalizationSpecialArrangement(
            encounter_hospitalization_id=hospitalization.id, tenant_id=org_id, text=sa.text, created_by=created_by,
        )
        session.add(special_arrangement)
        if sa.coding:
            await session.flush()
            for coding in sa.coding:
                session.add(
                    EncounterHospitalizationSpecialArrangementCoding(
                        encounter_hospitalization_special_arrangement_id=special_arrangement.id, tenant_id=org_id,
                        **_coding_kwargs(coding, created_by),
                    )
                )


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch every sub-resource type (plus core scalar fields,
    including the required status/class) in one transaction."""

    async def create_full(
        self,
        payload: EncounterCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> EncounterModel:
        async with self.session_factory() as session:
            subject_type, subject_id = (
                _parse_ref(payload.subject, SubjectReferenceType) if payload.subject else (None, None)
            )
            service_provider_type, service_provider_id = (
                _parse_ref(payload.service_provider, OrganizationReferenceType)
                if payload.service_provider else (None, None)
            )
            if service_provider_type and service_provider_id:
                await _validate_reference(session, org_id, service_provider_type, service_provider_id, "serviceProvider")
            part_of_type, part_of_id = (
                _parse_ref(payload.part_of, EncounterReferenceType) if payload.part_of else (None, None)
            )
            if part_of_type and part_of_id:
                await _validate_reference(session, org_id, part_of_type, part_of_id, "partOf")

            encounter = EncounterModel(
                tenant_id=org_id,
                created_by=created_by,
                extension=payload.extension or [],
                status=_model_status(payload.status),
                **_single_coding_kwargs(payload.class_coding),
                service_type_text=payload.service_type_text,
                priority_text=payload.priority_text,
                subject_reference=payload.subject,
                **_ref_kwargs("subject", payload.subject, payload.subject_display, SubjectReferenceType),
                **_reference_kwargs("subject", payload),
                period_start=payload.period_start,
                period_end=payload.period_end,
                length_value=payload.length_value,
                length_comparator=_model_length_comparator(payload.length_comparator),
                length_unit=payload.length_unit,
                length_system=payload.length_system,
                length_code=payload.length_code,
                service_provider_reference=payload.service_provider,
                **_ref_kwargs("service_provider", payload.service_provider, payload.service_provider_display, OrganizationReferenceType),
                **_reference_kwargs("service_provider", payload),
                part_of_reference=payload.part_of,
                **_ref_kwargs("part_of", payload.part_of, payload.part_of_display, EncounterReferenceType),
                **_reference_kwargs("part_of", payload),
            )
            session.add(encounter)
            await session.flush()

            for coding in payload.service_type_coding or []:
                from app.models.encounter import EncounterServiceTypeCoding

                session.add(EncounterServiceTypeCoding(encounter_pk=encounter.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)))
            for coding in payload.priority_coding or []:
                from app.models.encounter import EncounterPriorityCoding

                session.add(EncounterPriorityCoding(encounter_pk=encounter.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)))

            for i in payload.identifier or []:
                a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
                await _validate_reference(session, org_id, a_type, a_id, "identifier.assigner")
                identifier = EncounterIdentifier(
                    encounter_pk=encounter.id, tenant_id=org_id, use=i.use, type_text=i.type_text,
                    system=i.system, value=i.value, period_start=i.period_start, period_end=i.period_end,
                    assigner_reference=i.assigner,
                    **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                    **_reference_kwargs("assigner", i),
                    created_by=created_by,
                )
                session.add(identifier)
                if i.type_coding:
                    await session.flush()
                    for coding in i.type_coding:
                        session.add(EncounterIdentifierTypeCoding(encounter_identifier_id=identifier.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)))

            for sh in payload.status_history or []:
                session.add(EncounterStatusHistory(encounter_pk=encounter.id, tenant_id=org_id, status=_model_status(sh.status), period_start=sh.period_start, period_end=sh.period_end, created_by=created_by))

            for ch in payload.class_history or []:
                session.add(EncounterClassHistory(encounter_pk=encounter.id, tenant_id=org_id, period_start=ch.period_start, period_end=ch.period_end, created_by=created_by, **_single_coding_kwargs(ch.class_coding)))

            for t in payload.type or []:
                type_row = EncounterType(encounter_pk=encounter.id, tenant_id=org_id, text=t.text, created_by=created_by)
                session.add(type_row)
                if t.coding:
                    await session.flush()
                    for coding in t.coding:
                        session.add(EncounterTypeCoding(encounter_type_id=type_row.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)))

            for eoc in payload.episode_of_care or []:
                from app.models.encounter.enums import EncounterEpisodeOfCareReferenceType

                session.add(EncounterEpisodeOfCare(encounter_pk=encounter.id, tenant_id=org_id, reference_reference=eoc.reference, **_ref_kwargs("reference", eoc.reference, eoc.reference_display, EncounterEpisodeOfCareReferenceType), **_reference_kwargs("reference", eoc), created_by=created_by))

            for bo in payload.based_on or []:
                from app.models.encounter.enums import EncounterBasedOnReferenceType

                session.add(EncounterBasedOn(encounter_pk=encounter.id, tenant_id=org_id, reference_reference=bo.reference, **_ref_kwargs("reference", bo.reference, bo.reference_display, EncounterBasedOnReferenceType), **_reference_kwargs("reference", bo), created_by=created_by))

            for ap in payload.appointment or []:
                ap_type, ap_id = _parse_ref(ap.reference, AppointmentReferenceType) if ap.reference else (None, None)
                if ap_type and ap_id:
                    await _validate_reference(session, org_id, ap_type, ap_id, "appointment")
                session.add(EncounterAppointment(encounter_pk=encounter.id, tenant_id=org_id, reference_reference=ap.reference, **_ref_kwargs("reference", ap.reference, ap.reference_display, AppointmentReferenceType), **_reference_kwargs("reference", ap), created_by=created_by))

            for rc in payload.reason_code or []:
                reason_code = EncounterReasonCode(encounter_pk=encounter.id, tenant_id=org_id, text=rc.text, created_by=created_by)
                session.add(reason_code)
                if rc.coding:
                    await session.flush()
                    for coding in rc.coding:
                        session.add(EncounterReasonCodeCoding(encounter_reason_code_id=reason_code.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)))

            for rr in payload.reason_reference or []:
                from app.models.encounter.enums import EncounterReasonReferenceType

                session.add(EncounterReasonReference(encounter_pk=encounter.id, tenant_id=org_id, reference_reference=rr.reference, **_ref_kwargs("reference", rr.reference, rr.reference_display, EncounterReasonReferenceType), **_reference_kwargs("reference", rr), created_by=created_by))

            for ac in payload.account or []:
                from app.models.encounter.enums import EncounterAccountReferenceType

                session.add(EncounterAccount(encounter_pk=encounter.id, tenant_id=org_id, reference_reference=ac.reference, **_ref_kwargs("reference", ac.reference, ac.reference_display, EncounterAccountReferenceType), **_reference_kwargs("reference", ac), created_by=created_by))

            for p in payload.participant or []:
                from app.models.encounter.enums import EncounterParticipantIndividualReferenceType

                ind_type, ind_id = _parse_ref(p.individual, EncounterParticipantIndividualReferenceType) if p.individual else (None, None)
                await _validate_individual_reference(session, org_id, ind_type, ind_id)
                participant = EncounterParticipant(
                    encounter_pk=encounter.id, tenant_id=org_id, period_start=p.period_start, period_end=p.period_end,
                    individual_reference=p.individual,
                    **_ref_kwargs("individual", p.individual, p.individual_display, EncounterParticipantIndividualReferenceType),
                    **_reference_kwargs("individual", p),
                    created_by=created_by,
                )
                session.add(participant)
                if p.type:
                    await session.flush()
                    for t in p.type:
                        participant_type = EncounterParticipantType(encounter_participant_id=participant.id, tenant_id=org_id, text=t.text, created_by=created_by)
                        session.add(participant_type)
                        if t.coding:
                            await session.flush()
                            for coding in t.coding:
                                session.add(EncounterParticipantTypeCoding(encounter_participant_type_id=participant_type.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)))

            for d in payload.diagnosis or []:
                from app.models.encounter.enums import EncounterConditionOrProcedureReferenceType

                diagnosis = EncounterDiagnosis(
                    encounter_pk=encounter.id, tenant_id=org_id,
                    condition_reference=d.condition,
                    **_ref_kwargs("condition", d.condition, d.condition_display, EncounterConditionOrProcedureReferenceType),
                    **_reference_kwargs("condition", d),
                    use_text=d.use_text, rank=d.rank, created_by=created_by,
                )
                session.add(diagnosis)
                if d.use_coding:
                    await session.flush()
                    for coding in d.use_coding:
                        session.add(EncounterDiagnosisUseCoding(encounter_diagnosis_id=diagnosis.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)))

            if payload.hospitalization:
                await _add_hospitalization(session, encounter.id, org_id, payload.hospitalization, created_by)

            for loc in payload.location or []:
                from app.models.encounter.enums import EncounterLocationReferenceType, EncounterLocationStatus as EncounterLocationStatusModel

                loc_type, loc_id = _parse_ref(loc.location, EncounterLocationReferenceType) if loc.location else (None, None)
                if loc_type and loc_id:
                    await _validate_reference(session, org_id, loc_type, loc_id, "location.location")
                location_row = EncounterLocationRow(
                    encounter_pk=encounter.id, tenant_id=org_id,
                    location_reference=loc.location,
                    **_ref_kwargs("location", loc.location, loc.location_display, EncounterLocationReferenceType),
                    **_reference_kwargs("location", loc),
                    status=EncounterLocationStatusModel[loc.status.name] if loc.status else None,
                    physical_type_text=loc.physical_type_text,
                    period_start=loc.period_start, period_end=loc.period_end,
                    created_by=created_by,
                )
                session.add(location_row)
                if loc.physical_type_coding:
                    await session.flush()
                    for coding in loc.physical_type_coding:
                        session.add(EncounterLocationPhysicalTypeCoding(encounter_location_id=location_row.id, tenant_id=org_id, **_coding_kwargs(coding, created_by)))

            try:
                await session.commit()
                await session.refresh(encounter)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_encounter_id(encounter.encounter_id)

    async def patch_full(
        self,
        encounter_id: int,
        payload: EncounterPatchSchema,
        updated_by: str | None = None,
    ) -> EncounterModel | None:
        async with self.session_factory() as session:
            stmt = select(EncounterModel).where(EncounterModel.encounter_id == encounter_id)
            row = (await session.execute(stmt)).scalars().first()
            if not row:
                return None

            data = payload.model_dump(exclude_unset=True)
            provided = payload.model_fields_set

            for field, value in data.items():
                if field in _SUB or field in _SPECIAL:
                    continue
                setattr(row, field, value)

            if "status" in provided and payload.status is not None:
                row.status = _model_status(payload.status)
            if "class_coding" in provided:
                for k, v in _single_coding_kwargs(payload.class_coding).items():
                    setattr(row, k, v)
            if "service_type_text" in provided:
                row.service_type_text = payload.service_type_text
            if "priority_text" in provided:
                row.priority_text = payload.priority_text

            if provided & {"subject", "subject_display"}:
                if payload.subject is not None:
                    s_type, s_id = _parse_ref(payload.subject, SubjectReferenceType)
                    row.subject_type = s_type
                    row.subject_id = s_id
                if "subject_display" in provided:
                    row.subject_display = payload.subject_display
            for suffix in ("use", "type_system", "type_version", "type_code", "type_display", "type_text", "type_user_selected", "system", "value", "period_start", "period_end"):
                field = f"subject_identifier_{suffix}"
                if field in provided:
                    setattr(row, field, getattr(payload, field))

            if "length_value" in provided:
                row.length_value = payload.length_value
            if "length_comparator" in provided:
                row.length_comparator = _model_length_comparator(payload.length_comparator)
            if "length_unit" in provided:
                row.length_unit = payload.length_unit
            if "length_system" in provided:
                row.length_system = payload.length_system
            if "length_code" in provided:
                row.length_code = payload.length_code

            if provided & {"service_provider", "service_provider_display"}:
                if payload.service_provider is not None:
                    sp_type, sp_id = _parse_ref(payload.service_provider, OrganizationReferenceType)
                    await _validate_reference(session, row.tenant_id, sp_type, sp_id, "serviceProvider")
                    row.service_provider_type = sp_type
                    row.service_provider_id = sp_id
                if "service_provider_display" in provided:
                    row.service_provider_display = payload.service_provider_display
            for suffix in ("use", "type_system", "type_version", "type_code", "type_display", "type_text", "type_user_selected", "system", "value", "period_start", "period_end"):
                field = f"service_provider_identifier_{suffix}"
                if field in provided:
                    setattr(row, field, getattr(payload, field))

            if provided & {"part_of", "part_of_display"}:
                if payload.part_of is not None:
                    po_type, po_id = _parse_ref(payload.part_of, EncounterReferenceType)
                    await _validate_reference(session, row.tenant_id, po_type, po_id, "partOf")
                    row.part_of_type = po_type
                    row.part_of_id = po_id
                if "part_of_display" in provided:
                    row.part_of_display = payload.part_of_display
            for suffix in ("use", "type_system", "type_version", "type_code", "type_display", "type_text", "type_user_selected", "system", "value", "period_start", "period_end"):
                field = f"part_of_identifier_{suffix}"
                if field in provided:
                    setattr(row, field, getattr(payload, field))

            if updated_by is not None:
                row.updated_by = updated_by

            if "service_type_coding" in provided:
                from app.models.encounter import EncounterServiceTypeCoding

                await session.execute(delete(EncounterServiceTypeCoding).where(EncounterServiceTypeCoding.encounter_pk == row.id))
                for coding in payload.service_type_coding or []:
                    session.add(EncounterServiceTypeCoding(encounter_pk=row.id, tenant_id=row.tenant_id, **_coding_kwargs(coding, updated_by)))

            if "priority_coding" in provided:
                from app.models.encounter import EncounterPriorityCoding

                await session.execute(delete(EncounterPriorityCoding).where(EncounterPriorityCoding.encounter_pk == row.id))
                for coding in payload.priority_coding or []:
                    session.add(EncounterPriorityCoding(encounter_pk=row.id, tenant_id=row.tenant_id, **_coding_kwargs(coding, updated_by)))

            if payload.identifier is not None:
                await _cascade_delete_cc_list(session, EncounterIdentifier, EncounterIdentifierTypeCoding, EncounterIdentifier.encounter_pk, EncounterIdentifierTypeCoding.encounter_identifier_id, row.id)
                for i in payload.identifier:
                    a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    await _validate_reference(session, row.tenant_id, a_type, a_id, "identifier.assigner")
                    identifier = EncounterIdentifier(encounter_pk=row.id, tenant_id=row.tenant_id, use=i.use, type_text=i.type_text, system=i.system, value=i.value, period_start=i.period_start, period_end=i.period_end, assigner_reference=i.assigner, **_org_ref_kwargs("assigner", i.assigner, i.assigner_display), **_reference_kwargs("assigner", i), created_by=updated_by)
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(EncounterIdentifierTypeCoding(encounter_identifier_id=identifier.id, tenant_id=row.tenant_id, **_coding_kwargs(coding, updated_by)))

            if payload.status_history is not None:
                await session.execute(delete(EncounterStatusHistory).where(EncounterStatusHistory.encounter_pk == row.id))
                for sh in payload.status_history:
                    session.add(EncounterStatusHistory(encounter_pk=row.id, tenant_id=row.tenant_id, status=_model_status(sh.status), period_start=sh.period_start, period_end=sh.period_end, created_by=updated_by))

            if payload.class_history is not None:
                await session.execute(delete(EncounterClassHistory).where(EncounterClassHistory.encounter_pk == row.id))
                for ch in payload.class_history:
                    session.add(EncounterClassHistory(encounter_pk=row.id, tenant_id=row.tenant_id, period_start=ch.period_start, period_end=ch.period_end, created_by=updated_by, **_single_coding_kwargs(ch.class_coding)))

            if payload.type is not None:
                await _cascade_delete_cc_list(session, EncounterType, EncounterTypeCoding, EncounterType.encounter_pk, EncounterTypeCoding.encounter_type_id, row.id)
                for t in payload.type:
                    type_row = EncounterType(encounter_pk=row.id, tenant_id=row.tenant_id, text=t.text, created_by=updated_by)
                    session.add(type_row)
                    if t.coding:
                        await session.flush()
                        for coding in t.coding:
                            session.add(EncounterTypeCoding(encounter_type_id=type_row.id, tenant_id=row.tenant_id, **_coding_kwargs(coding, updated_by)))

            if payload.episode_of_care is not None:
                from app.models.encounter.enums import EncounterEpisodeOfCareReferenceType

                await session.execute(delete(EncounterEpisodeOfCare).where(EncounterEpisodeOfCare.encounter_pk == row.id))
                for eoc in payload.episode_of_care:
                    session.add(EncounterEpisodeOfCare(encounter_pk=row.id, tenant_id=row.tenant_id, reference_reference=eoc.reference, **_ref_kwargs("reference", eoc.reference, eoc.reference_display, EncounterEpisodeOfCareReferenceType), **_reference_kwargs("reference", eoc), created_by=updated_by))

            if payload.based_on is not None:
                from app.models.encounter.enums import EncounterBasedOnReferenceType

                await session.execute(delete(EncounterBasedOn).where(EncounterBasedOn.encounter_pk == row.id))
                for bo in payload.based_on:
                    session.add(EncounterBasedOn(encounter_pk=row.id, tenant_id=row.tenant_id, reference_reference=bo.reference, **_ref_kwargs("reference", bo.reference, bo.reference_display, EncounterBasedOnReferenceType), **_reference_kwargs("reference", bo), created_by=updated_by))

            if payload.appointment is not None:
                await session.execute(delete(EncounterAppointment).where(EncounterAppointment.encounter_pk == row.id))
                for ap in payload.appointment:
                    ap_type, ap_id = _parse_ref(ap.reference, AppointmentReferenceType) if ap.reference else (None, None)
                    if ap_type and ap_id:
                        await _validate_reference(session, row.tenant_id, ap_type, ap_id, "appointment")
                    session.add(EncounterAppointment(encounter_pk=row.id, tenant_id=row.tenant_id, reference_reference=ap.reference, **_ref_kwargs("reference", ap.reference, ap.reference_display, AppointmentReferenceType), **_reference_kwargs("reference", ap), created_by=updated_by))

            if payload.reason_code is not None:
                await _cascade_delete_cc_list(session, EncounterReasonCode, EncounterReasonCodeCoding, EncounterReasonCode.encounter_pk, EncounterReasonCodeCoding.encounter_reason_code_id, row.id)
                for rc in payload.reason_code:
                    reason_code = EncounterReasonCode(encounter_pk=row.id, tenant_id=row.tenant_id, text=rc.text, created_by=updated_by)
                    session.add(reason_code)
                    if rc.coding:
                        await session.flush()
                        for coding in rc.coding:
                            session.add(EncounterReasonCodeCoding(encounter_reason_code_id=reason_code.id, tenant_id=row.tenant_id, **_coding_kwargs(coding, updated_by)))

            if payload.reason_reference is not None:
                from app.models.encounter.enums import EncounterReasonReferenceType

                await session.execute(delete(EncounterReasonReference).where(EncounterReasonReference.encounter_pk == row.id))
                for rr in payload.reason_reference:
                    session.add(EncounterReasonReference(encounter_pk=row.id, tenant_id=row.tenant_id, reference_reference=rr.reference, **_ref_kwargs("reference", rr.reference, rr.reference_display, EncounterReasonReferenceType), **_reference_kwargs("reference", rr), created_by=updated_by))

            if payload.account is not None:
                from app.models.encounter.enums import EncounterAccountReferenceType

                await session.execute(delete(EncounterAccount).where(EncounterAccount.encounter_pk == row.id))
                for ac in payload.account:
                    session.add(EncounterAccount(encounter_pk=row.id, tenant_id=row.tenant_id, reference_reference=ac.reference, **_ref_kwargs("reference", ac.reference, ac.reference_display, EncounterAccountReferenceType), **_reference_kwargs("reference", ac), created_by=updated_by))

            if payload.participant is not None:
                from app.models.encounter.enums import EncounterParticipantIndividualReferenceType

                await session.execute(
                    delete(EncounterParticipantTypeCoding).where(
                        EncounterParticipantTypeCoding.encounter_participant_type_id.in_(
                            select(EncounterParticipantType.id).where(
                                EncounterParticipantType.encounter_participant_id.in_(
                                    select(EncounterParticipant.id).where(EncounterParticipant.encounter_pk == row.id)
                                )
                            )
                        )
                    )
                )
                await session.execute(
                    delete(EncounterParticipantType).where(
                        EncounterParticipantType.encounter_participant_id.in_(
                            select(EncounterParticipant.id).where(EncounterParticipant.encounter_pk == row.id)
                        )
                    )
                )
                await session.execute(delete(EncounterParticipant).where(EncounterParticipant.encounter_pk == row.id))
                for p in payload.participant:
                    ind_type, ind_id = _parse_ref(p.individual, EncounterParticipantIndividualReferenceType) if p.individual else (None, None)
                    await _validate_individual_reference(session, row.tenant_id, ind_type, ind_id)
                    participant = EncounterParticipant(encounter_pk=row.id, tenant_id=row.tenant_id, period_start=p.period_start, period_end=p.period_end, individual_reference=p.individual, **_ref_kwargs("individual", p.individual, p.individual_display, EncounterParticipantIndividualReferenceType), **_reference_kwargs("individual", p), created_by=updated_by)
                    session.add(participant)
                    if p.type:
                        await session.flush()
                        for t in p.type:
                            participant_type = EncounterParticipantType(encounter_participant_id=participant.id, tenant_id=row.tenant_id, text=t.text, created_by=updated_by)
                            session.add(participant_type)
                            if t.coding:
                                await session.flush()
                                for coding in t.coding:
                                    session.add(EncounterParticipantTypeCoding(encounter_participant_type_id=participant_type.id, tenant_id=row.tenant_id, **_coding_kwargs(coding, updated_by)))

            if payload.diagnosis is not None:
                await _cascade_delete_cc_list(session, EncounterDiagnosis, EncounterDiagnosisUseCoding, EncounterDiagnosis.encounter_pk, EncounterDiagnosisUseCoding.encounter_diagnosis_id, row.id)
                from app.models.encounter.enums import EncounterConditionOrProcedureReferenceType

                for d in payload.diagnosis:
                    diagnosis = EncounterDiagnosis(encounter_pk=row.id, tenant_id=row.tenant_id, condition_reference=d.condition, **_ref_kwargs("condition", d.condition, d.condition_display, EncounterConditionOrProcedureReferenceType), **_reference_kwargs("condition", d), use_text=d.use_text, rank=d.rank, created_by=updated_by)
                    session.add(diagnosis)
                    if d.use_coding:
                        await session.flush()
                        for coding in d.use_coding:
                            session.add(EncounterDiagnosisUseCoding(encounter_diagnosis_id=diagnosis.id, tenant_id=row.tenant_id, **_coding_kwargs(coding, updated_by)))

            if "hospitalization" in provided:
                existing_hosp_stmt = select(EncounterHospitalization.id).where(EncounterHospitalization.encounter_pk == row.id)
                existing_hosp_id = (await session.execute(existing_hosp_stmt)).scalar_one_or_none()
                if existing_hosp_id is not None:
                    await _delete_hospitalization(session, existing_hosp_id)
                if payload.hospitalization:
                    await _add_hospitalization(session, row.id, row.tenant_id, payload.hospitalization, updated_by)

            if payload.location is not None:
                await _cascade_delete_cc_list(session, EncounterLocationRow, EncounterLocationPhysicalTypeCoding, EncounterLocationRow.encounter_pk, EncounterLocationPhysicalTypeCoding.encounter_location_id, row.id)
                from app.models.encounter.enums import EncounterLocationReferenceType, EncounterLocationStatus as EncounterLocationStatusModel

                for loc in payload.location:
                    loc_type, loc_id = _parse_ref(loc.location, EncounterLocationReferenceType) if loc.location else (None, None)
                    if loc_type and loc_id:
                        await _validate_reference(session, row.tenant_id, loc_type, loc_id, "location.location")
                    location_row = EncounterLocationRow(encounter_pk=row.id, tenant_id=row.tenant_id, location_reference=loc.location, **_ref_kwargs("location", loc.location, loc.location_display, EncounterLocationReferenceType), **_reference_kwargs("location", loc), status=EncounterLocationStatusModel[loc.status.name] if loc.status else None, physical_type_text=loc.physical_type_text, period_start=loc.period_start, period_end=loc.period_end, created_by=updated_by)
                    session.add(location_row)
                    if loc.physical_type_coding:
                        await session.flush()
                        for coding in loc.physical_type_coding:
                            session.add(EncounterLocationPhysicalTypeCoding(encounter_location_id=location_row.id, tenant_id=row.tenant_id, **_coding_kwargs(coding, updated_by)))

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            replaced = sorted(_SUB & set(data.keys()))
            if replaced:
                logger.debug(
                    "Encounter sub-resource lists replaced",
                    extra={"event": "encounter.sublists_replaced", "encounter_id": encounter_id, "replaced": replaced},
                )

        return await self.get_by_encounter_id(encounter_id)
