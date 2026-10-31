from __future__ import annotations

import datetime as dt

from sqlalchemy import delete
from sqlalchemy.future import select

from app.models.activity_definition import (
    ActivityDefinitionBodySite,
    ActivityDefinitionBodySiteCoding,
    ActivityDefinitionCodeCoding,
    ActivityDefinitionContact,
    ActivityDefinitionContactRole,
    ActivityDefinitionContactTelecom,
    ActivityDefinitionDosage,
    ActivityDefinitionDosageAsNeededCoding,
    ActivityDefinitionDosageMethodCoding,
    ActivityDefinitionDosageRouteCoding,
    ActivityDefinitionDosageSiteCoding,
    ActivityDefinitionDynamicValue,
    ActivityDefinitionIdentifier,
    ActivityDefinitionIdentifierTypeCoding,
    ActivityDefinitionIntent,
    ActivityDefinitionJurisdiction,
    ActivityDefinitionJurisdictionCoding,
    ActivityDefinitionKind,
    ActivityDefinitionModel,
    ActivityDefinitionObservationRequirement,
    ActivityDefinitionObservationResultRequirement,
    ActivityDefinitionParticipant,
    ActivityDefinitionParticipantRoleCoding,
    ActivityDefinitionParticipantType,
    ActivityDefinitionPriority,
    ActivityDefinitionProductCoding,
    ActivityDefinitionQuantityComparator,
    ActivityDefinitionRelatedArtifact,
    ActivityDefinitionRelatedArtifactType,
    ActivityDefinitionSpecimenRequirement,
    ActivityDefinitionStatus,
    ActivityDefinitionSubjectCoding,
    ActivityDefinitionTopic,
    ActivityDefinitionTopicCoding,
    ActivityDefinitionUseContext,
    ActivityDefinitionUseContextValueCoding,
)
from app.models.enums import IdentifierUse
from app.schemas.activity_definition import (
    ActivityDefinitionCreateSchema,
    ActivityDefinitionPatchSchema,
)
from app.schemas.enums import ContactPointSystem, ContactPointUse

from ._shared import (
    _parse_assigner_ref,
    _parse_location_ref,
    _parse_observation_requirement_ref,
    _parse_observation_result_requirement_ref,
    _parse_product_ref,
    _parse_specimen_requirement_ref,
    _parse_subject_ref,
    _parse_use_context_value_ref,
    _validate_ref,
    _with_relationships,
)


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    if isinstance(coding, dict):
        return {
            "tenant_id": org_id,
            "created_by": created_by,
            "system": coding.get("system"),
            "version": coding.get("version"),
            "code": coding.get("code"),
            "display": coding.get("display"),
            "user_selected": coding.get("user_selected") or coding.get("userSelected"),
        }
    return {
        "tenant_id": org_id,
        "created_by": created_by,
        "system": getattr(coding, "system", None),
        "version": getattr(coding, "version", None),
        "code": getattr(coding, "code", None),
        "display": getattr(coding, "display", None),
        "user_selected": getattr(coding, "user_selected", None),
    }


async def _add_identifiers(
    session, activity_definition_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")
        ident = ActivityDefinitionIdentifier(
            activity_definition_pk=activity_definition_pk,
            tenant_id=org_id,
            use=(
                IdentifierUse(i.use.value)
                if (i.use and hasattr(i.use, "value"))
                else IdentifierUse(i.use)
                if i.use
                else None
            ),
            type_text=i.type_text,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner_reference=i.assigner,
            assigner_type=a_type,
            assigner_id=a_id,
            assigner_display=i.assigner_display,
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()

        if i.type_coding:
            for c in i.type_coding:
                session.add(
                    ActivityDefinitionIdentifierTypeCoding(
                        identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_contacts(
    session, activity_definition_pk: int, org_id: str, contacts, role: ActivityDefinitionContactRole, created_by: str
) -> None:
    for c in contacts or []:
        contact_row = ActivityDefinitionContact(
            activity_definition_pk=activity_definition_pk,
            tenant_id=org_id,
            role=role,
            name=c.name,
            created_by=created_by,
        )
        session.add(contact_row)
        await session.flush()

        if c.telecom:
            for t in c.telecom:
                t_sys = (
                    ContactPointSystem(t.system.value)
                    if (t.system and hasattr(t.system, "value"))
                    else ContactPointSystem(t.system)
                    if t.system
                    else None
                )
                t_use = (
                    ContactPointUse(t.use.value)
                    if (t.use and hasattr(t.use, "value"))
                    else ContactPointUse(t.use)
                    if t.use
                    else None
                )
                session.add(
                    ActivityDefinitionContactTelecom(
                        activity_definition_contact_id=contact_row.id,
                        tenant_id=org_id,
                        system=t_sys,
                        value=t.value,
                        use=t_use,
                        rank=t.rank,
                        period_start=t.period_start,
                        period_end=t.period_end,
                        created_by=created_by,
                    )
                )


async def _add_use_contexts(
    session, activity_definition_pk: int, org_id: str, use_contexts, created_by: str
) -> None:
    for uc in use_contexts or []:
        val_ref_type, val_ref_id = (
            _parse_use_context_value_ref(uc.value_reference)
            if uc.value_reference
            else (None, None)
        )
        if val_ref_type and val_ref_id:
            await _validate_ref(
                session, org_id, val_ref_type, val_ref_id, "use_context.value_reference"
            )

        q_comp = (
            ActivityDefinitionQuantityComparator(uc.value_quantity_comparator.value)
            if (uc.value_quantity_comparator and hasattr(uc.value_quantity_comparator, "value"))
            else ActivityDefinitionQuantityComparator(uc.value_quantity_comparator)
            if uc.value_quantity_comparator
            else None
        )

        vcc_text = uc.value_codeable_concept_text

        uc_row = ActivityDefinitionUseContext(
            activity_definition_pk=activity_definition_pk,
            tenant_id=org_id,
            system=uc.code_system,
            version=uc.code_version,
            code=uc.code_code,
            display=uc.code_display,
            user_selected=uc.code_user_selected,
            value_codeable_concept_text=vcc_text,
            value_quantity_value=uc.value_quantity_value,
            value_quantity_comparator=q_comp,
            value_quantity_unit=uc.value_quantity_unit,
            value_quantity_system=uc.value_quantity_system,
            value_quantity_code=uc.value_quantity_code,
            value_range_low_value=uc.value_range_low_value,
            value_range_low_unit=uc.value_range_low_unit,
            value_range_low_system=uc.value_range_low_system,
            value_range_low_code=uc.value_range_low_code,
            value_range_high_value=uc.value_range_high_value,
            value_range_high_unit=uc.value_range_high_unit,
            value_range_high_system=uc.value_range_high_system,
            value_range_high_code=uc.value_range_high_code,
            value_reference_reference=uc.value_reference,
            value_reference_type=val_ref_type,
            value_reference_id=val_ref_id,
            value_reference_display=uc.value_reference_display,
            created_by=created_by,
        )
        session.add(uc_row)
        await session.flush()

        if uc.value_codeable_concept_coding:
            for c in uc.value_codeable_concept_coding:
                session.add(
                    ActivityDefinitionUseContextValueCoding(
                        activity_definition_use_context_id=uc_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_jurisdictions(
    session, activity_definition_pk: int, org_id: str, jurisdictions, created_by: str
) -> None:
    for j in jurisdictions or []:
        j_row = ActivityDefinitionJurisdiction(
            activity_definition_pk=activity_definition_pk,
            tenant_id=org_id,
            text=j.text,
            created_by=created_by,
        )
        session.add(j_row)
        await session.flush()
        if j.coding:
            for c in j.coding:
                session.add(
                    ActivityDefinitionJurisdictionCoding(
                        activity_definition_jurisdiction_id=j_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_topics(
    session, activity_definition_pk: int, org_id: str, topics, created_by: str
) -> None:
    for t in topics or []:
        t_row = ActivityDefinitionTopic(
            activity_definition_pk=activity_definition_pk,
            tenant_id=org_id,
            text=t.text,
            created_by=created_by,
        )
        session.add(t_row)
        await session.flush()
        if t.coding:
            for c in t.coding:
                session.add(
                    ActivityDefinitionTopicCoding(
                        activity_definition_topic_id=t_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_body_sites(
    session, activity_definition_pk: int, org_id: str, body_sites, created_by: str
) -> None:
    for b in body_sites or []:
        b_row = ActivityDefinitionBodySite(
            activity_definition_pk=activity_definition_pk,
            tenant_id=org_id,
            text=b.text,
            created_by=created_by,
        )
        session.add(b_row)
        await session.flush()
        if b.coding:
            for c in b.coding:
                session.add(
                    ActivityDefinitionBodySiteCoding(
                        activity_definition_body_site_id=b_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


def _add_code_codings(
    session, activity_definition_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            ActivityDefinitionCodeCoding(
                activity_definition_pk=activity_definition_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


def _add_subject_codings(
    session, activity_definition_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            ActivityDefinitionSubjectCoding(
                activity_definition_pk=activity_definition_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


def _add_product_codings(
    session, activity_definition_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            ActivityDefinitionProductCoding(
                activity_definition_pk=activity_definition_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_related_artifacts(
    session, activity_definition_pk: int, org_id: str, artifacts, created_by: str
) -> None:
    for ra in artifacts or []:
        ra_type = (
            ActivityDefinitionRelatedArtifactType(ra.type.value)
            if (ra.type and hasattr(ra.type, "value"))
            else ActivityDefinitionRelatedArtifactType(ra.type)
            if ra.type
            else None
        )
        session.add(
            ActivityDefinitionRelatedArtifact(
                activity_definition_pk=activity_definition_pk,
                tenant_id=org_id,
                type=ra_type,
                label=ra.label,
                display=ra.display,
                citation=ra.citation,
                url=ra.url,
                document=ra.document,
                resource=ra.resource,
                created_by=created_by,
            )
        )


async def _add_participants(
    session, activity_definition_pk: int, org_id: str, participants, created_by: str
) -> None:
    for p in participants or []:
        p_type = (
            ActivityDefinitionParticipantType(p.type.value)
            if (p.type and hasattr(p.type, "value"))
            else ActivityDefinitionParticipantType(p.type)
            if p.type
            else None
        )
        p_row = ActivityDefinitionParticipant(
            activity_definition_pk=activity_definition_pk,
            tenant_id=org_id,
            type=p_type,
            role_text=p.role.text if p.role else None,
            created_by=created_by,
        )
        session.add(p_row)
        await session.flush()
        if p.role and p.role.coding:
            for c in p.role.coding:
                session.add(
                    ActivityDefinitionParticipantRoleCoding(
                        activity_definition_participant_id=p_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_dosages(
    session, activity_definition_pk: int, org_id: str, dosages, created_by: str
) -> None:
    for d in dosages or []:
        d_row = ActivityDefinitionDosage(
            activity_definition_pk=activity_definition_pk,
            tenant_id=org_id,
            sequence=d.sequence,
            text=d.text,
            patient_instruction=d.patient_instruction,
            timing=d.timing,
            as_needed_boolean=d.as_needed_boolean,
            as_needed_codeable_concept_text=(
                d.as_needed_codeable_concept.text
                if d.as_needed_codeable_concept
                else None
            ),
            site_text=d.site.text if d.site else None,
            route_text=d.route.text if d.route else None,
            method_text=d.method.text if d.method else None,
            dose_and_rate=d.dose_and_rate,
            max_dose_per_period=d.max_dose_per_period,
            max_dose_per_administration_value=d.max_dose_per_administration_value,
            max_dose_per_administration_unit=d.max_dose_per_administration_unit,
            max_dose_per_administration_system=d.max_dose_per_administration_system,
            max_dose_per_administration_code=d.max_dose_per_administration_code,
            max_dose_per_lifetime_value=d.max_dose_per_lifetime_value,
            max_dose_per_lifetime_unit=d.max_dose_per_lifetime_unit,
            max_dose_per_lifetime_system=d.max_dose_per_lifetime_system,
            max_dose_per_lifetime_code=d.max_dose_per_lifetime_code,
            created_by=created_by,
        )
        session.add(d_row)
        await session.flush()

        if d.site and d.site.coding:
            for c in d.site.coding:
                session.add(
                    ActivityDefinitionDosageSiteCoding(
                        activity_definition_dosage_id=d_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )
        if d.route and d.route.coding:
            for c in d.route.coding:
                session.add(
                    ActivityDefinitionDosageRouteCoding(
                        activity_definition_dosage_id=d_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )
        if d.method and d.method.coding:
            for c in d.method.coding:
                session.add(
                    ActivityDefinitionDosageMethodCoding(
                        activity_definition_dosage_id=d_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )
        if d.as_needed_codeable_concept and d.as_needed_codeable_concept.coding:
            for c in d.as_needed_codeable_concept.coding:
                session.add(
                    ActivityDefinitionDosageAsNeededCoding(
                        activity_definition_dosage_id=d_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_dynamic_values(
    session, activity_definition_pk: int, org_id: str, dynamic_values, created_by: str
) -> None:
    for dv in dynamic_values or []:
        session.add(
            ActivityDefinitionDynamicValue(
                activity_definition_pk=activity_definition_pk,
                tenant_id=org_id,
                path=dv.path,
                expression_description=dv.expression_description,
                expression_name=dv.expression_name,
                expression_language=dv.expression_language,
                expression_expression=dv.expression_expression,
                expression_reference=dv.expression_reference,
                created_by=created_by,
            )
        )


async def _add_specimen_requirements(
    session, activity_definition_pk: int, org_id: str, refs, created_by: str
) -> None:
    for r in refs or []:
        r_type, r_id = _parse_specimen_requirement_ref(r)
        if r_type and r_id:
            await _validate_ref(
                session, org_id, r_type, r_id, "specimen_requirement"
            )
        session.add(
            ActivityDefinitionSpecimenRequirement(
                activity_definition_pk=activity_definition_pk,
                tenant_id=org_id,
                reference_reference=r,
                reference_type=r_type,
                reference_id=r_id,
                created_by=created_by,
            )
        )


async def _add_observation_requirements(
    session, activity_definition_pk: int, org_id: str, refs, created_by: str
) -> None:
    for r in refs or []:
        r_type, r_id = _parse_observation_requirement_ref(r)
        if r_type and r_id:
            await _validate_ref(
                session, org_id, r_type, r_id, "observation_requirement"
            )
        session.add(
            ActivityDefinitionObservationRequirement(
                activity_definition_pk=activity_definition_pk,
                tenant_id=org_id,
                reference_reference=r,
                reference_type=r_type,
                reference_id=r_id,
                created_by=created_by,
            )
        )


async def _add_observation_result_requirements(
    session, activity_definition_pk: int, org_id: str, refs, created_by: str
) -> None:
    for r in refs or []:
        r_type, r_id = _parse_observation_result_requirement_ref(r)
        if r_type and r_id:
            await _validate_ref(
                session, org_id, r_type, r_id, "observation_result_requirement"
            )
        session.add(
            ActivityDefinitionObservationResultRequirement(
                activity_definition_pk=activity_definition_pk,
                tenant_id=org_id,
                reference_reference=r,
                reference_type=r_type,
                reference_id=r_id,
                created_by=created_by,
            )
        )


class _FullMixin:
    """Write operations for ActivityDefinition."""

    async def create_full(
        self,
        payload: ActivityDefinitionCreateSchema,
        org_id: str,
        created_by: str,
    ) -> ActivityDefinitionModel:
        async with self.session_factory() as session:
            # Parse references
            loc_type, loc_id = (
                _parse_location_ref(payload.location)
                if payload.location
                else (None, None)
            )
            if loc_type and loc_id:
                await _validate_ref(session, org_id, loc_type, loc_id, "location")

            prod_type, prod_id = (
                _parse_product_ref(payload.product_reference)
                if payload.product_reference
                else (None, None)
            )
            if prod_type and prod_id:
                await _validate_ref(
                    session, org_id, prod_type, prod_id, "product_reference"
                )

            subj_type, subj_id = (
                _parse_subject_ref(payload.subject_reference)
                if payload.subject_reference
                else (None, None)
            )
            if subj_type and subj_id:
                await _validate_ref(
                    session, org_id, subj_type, subj_id, "subject_reference"
                )

            status_val = (
                ActivityDefinitionStatus(payload.status.value)
                if hasattr(payload.status, "value")
                else ActivityDefinitionStatus(payload.status)
            )
            kind_val = (
                ActivityDefinitionKind(payload.kind.value)
                if (payload.kind and hasattr(payload.kind, "value"))
                else ActivityDefinitionKind(payload.kind)
                if payload.kind
                else None
            )
            intent_val = (
                ActivityDefinitionIntent(payload.intent.value)
                if (payload.intent and hasattr(payload.intent, "value"))
                else ActivityDefinitionIntent(payload.intent)
                if payload.intent
                else None
            )
            priority_val = (
                ActivityDefinitionPriority(payload.priority.value)
                if (payload.priority and hasattr(payload.priority, "value"))
                else ActivityDefinitionPriority(payload.priority)
                if payload.priority
                else None
            )
            qty_comp_val = (
                ActivityDefinitionQuantityComparator(payload.quantity_comparator.value)
                if (
                    payload.quantity_comparator
                    and hasattr(payload.quantity_comparator, "value")
                )
                else ActivityDefinitionQuantityComparator(payload.quantity_comparator)
                if payload.quantity_comparator
                else None
            )

            model = ActivityDefinitionModel(
                tenant_id=org_id,
                created_by=created_by,
                url=payload.url,
                version=payload.version,
                name=payload.name,
                title=payload.title,
                subtitle=payload.subtitle,
                status=status_val,
                experimental=payload.experimental,
                date=payload.date,
                publisher=payload.publisher,
                description=payload.description,
                purpose=payload.purpose,
                usage=payload.usage,
                copyright=payload.copyright,
                approval_date=payload.approval_date,
                last_review_date=payload.last_review_date,
                effective_period_start=payload.effective_period_start,
                effective_period_end=payload.effective_period_end,
                library=payload.library,
                kind=kind_val,
                profile=payload.profile,
                code_text=payload.code.text if payload.code else None,
                intent=intent_val,
                priority=priority_val,
                do_not_perform=payload.do_not_perform,
                timing_timing=payload.timing_timing,
                timing_date_time=payload.timing_date_time,
                timing_age_value=payload.timing_age_value,
                timing_age_unit=payload.timing_age_unit,
                timing_age_system=payload.timing_age_system,
                timing_age_code=payload.timing_age_code,
                timing_period_start=payload.timing_period_start,
                timing_period_end=payload.timing_period_end,
                timing_range_low_value=payload.timing_range_low_value,
                timing_range_low_unit=payload.timing_range_low_unit,
                timing_range_high_value=payload.timing_range_high_value,
                timing_range_high_unit=payload.timing_range_high_unit,
                timing_duration_value=payload.timing_duration_value,
                timing_duration_unit=payload.timing_duration_unit,
                timing_duration_system=payload.timing_duration_system,
                timing_duration_code=payload.timing_duration_code,
                location_reference=payload.location,
                location_type=loc_type,
                location_id=loc_id,
                location_display=payload.location_display,
                product_codeable_concept_text=(
                    payload.product_codeable_concept.text
                    if payload.product_codeable_concept
                    else None
                ),
                product_reference=payload.product_reference,
                product_type=prod_type,
                product_id=prod_id,
                product_display=payload.product_display,
                quantity_value=payload.quantity_value,
                quantity_comparator=qty_comp_val,
                quantity_unit=payload.quantity_unit,
                quantity_system=payload.quantity_system,
                quantity_code=payload.quantity_code,
                transform=payload.transform,
                subject_codeable_concept_text=(
                    payload.subject_codeable_concept.text
                    if payload.subject_codeable_concept
                    else None
                ),
                subject_reference=payload.subject_reference,
                subject_type=subj_type,
                subject_id=subj_id,
                subject_display=payload.subject_display,
                extension=payload.extension or [],
            )
            session.add(model)
            await session.flush()

            if payload.identifier:
                await _add_identifiers(
                    session, model.id, org_id, payload.identifier, created_by
                )

            if payload.contact:
                await _add_contacts(
                    session,
                    model.id,
                    org_id,
                    payload.contact,
                    ActivityDefinitionContactRole.contact,
                    created_by,
                )
            if payload.author:
                await _add_contacts(
                    session,
                    model.id,
                    org_id,
                    payload.author,
                    ActivityDefinitionContactRole.author,
                    created_by,
                )
            if payload.editor:
                await _add_contacts(
                    session,
                    model.id,
                    org_id,
                    payload.editor,
                    ActivityDefinitionContactRole.editor,
                    created_by,
                )
            if payload.reviewer:
                await _add_contacts(
                    session,
                    model.id,
                    org_id,
                    payload.reviewer,
                    ActivityDefinitionContactRole.reviewer,
                    created_by,
                )
            if payload.endorser:
                await _add_contacts(
                    session,
                    model.id,
                    org_id,
                    payload.endorser,
                    ActivityDefinitionContactRole.endorser,
                    created_by,
                )

            if payload.use_context:
                await _add_use_contexts(
                    session, model.id, org_id, payload.use_context, created_by
                )

            if payload.jurisdiction:
                await _add_jurisdictions(
                    session, model.id, org_id, payload.jurisdiction, created_by
                )

            if payload.topic:
                await _add_topics(session, model.id, org_id, payload.topic, created_by)

            if payload.body_site:
                await _add_body_sites(
                    session, model.id, org_id, payload.body_site, created_by
                )

            if payload.code and payload.code.coding:
                _add_code_codings(
                    session, model.id, org_id, payload.code.coding, created_by
                )

            if (
                payload.subject_codeable_concept
                and payload.subject_codeable_concept.coding
            ):
                _add_subject_codings(
                    session,
                    model.id,
                    org_id,
                    payload.subject_codeable_concept.coding,
                    created_by,
                )

            if (
                payload.product_codeable_concept
                and payload.product_codeable_concept.coding
            ):
                _add_product_codings(
                    session,
                    model.id,
                    org_id,
                    payload.product_codeable_concept.coding,
                    created_by,
                )

            if payload.related_artifact:
                await _add_related_artifacts(
                    session, model.id, org_id, payload.related_artifact, created_by
                )

            if payload.participant:
                await _add_participants(
                    session, model.id, org_id, payload.participant, created_by
                )

            if payload.dosage:
                await _add_dosages(
                    session, model.id, org_id, payload.dosage, created_by
                )

            if payload.dynamic_value:
                await _add_dynamic_values(
                    session, model.id, org_id, payload.dynamic_value, created_by
                )

            if payload.specimen_requirement:
                await _add_specimen_requirements(
                    session,
                    model.id,
                    org_id,
                    payload.specimen_requirement,
                    created_by,
                )

            if payload.observation_requirement:
                await _add_observation_requirements(
                    session,
                    model.id,
                    org_id,
                    payload.observation_requirement,
                    created_by,
                )

            if payload.observation_result_requirement:
                await _add_observation_result_requirements(
                    session,
                    model.id,
                    org_id,
                    payload.observation_result_requirement,
                    created_by,
                )

            await session.commit()

            stmt = select(ActivityDefinitionModel).where(
                ActivityDefinitionModel.id == model.id
            )
            stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalar_one()

    async def patch_full(
        self,
        activity_definition_id: int,
        payload: ActivityDefinitionPatchSchema,
        org_id: str,
        updated_by: str | None = None,
    ) -> ActivityDefinitionModel | None:
        async with self.session_factory() as session:
            stmt = select(ActivityDefinitionModel).where(
                ActivityDefinitionModel.activity_definition_id
                == activity_definition_id,
                ActivityDefinitionModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return None

            fields_set = payload.model_fields_set
            actor = updated_by or model.created_by

            if "url" in fields_set:
                model.url = payload.url
            if "version" in fields_set:
                model.version = payload.version
            if "name" in fields_set:
                model.name = payload.name
            if "title" in fields_set:
                model.title = payload.title
            if "subtitle" in fields_set:
                model.subtitle = payload.subtitle
            if "status" in fields_set:
                model.status = (
                    ActivityDefinitionStatus(payload.status.value)
                    if (payload.status and hasattr(payload.status, "value"))
                    else ActivityDefinitionStatus(payload.status)
                    if payload.status
                    else None
                )
            if "experimental" in fields_set:
                model.experimental = payload.experimental
            if "date" in fields_set:
                model.date = payload.date
            if "publisher" in fields_set:
                model.publisher = payload.publisher
            if "description" in fields_set:
                model.description = payload.description
            if "purpose" in fields_set:
                model.purpose = payload.purpose
            if "usage" in fields_set:
                model.usage = payload.usage
            if "copyright" in fields_set:
                model.copyright = payload.copyright
            if "approval_date" in fields_set:
                model.approval_date = payload.approval_date
            if "last_review_date" in fields_set:
                model.last_review_date = payload.last_review_date
            if "effective_period_start" in fields_set:
                model.effective_period_start = payload.effective_period_start
            if "effective_period_end" in fields_set:
                model.effective_period_end = payload.effective_period_end
            if "library" in fields_set:
                model.library = payload.library
            if "kind" in fields_set:
                model.kind = (
                    ActivityDefinitionKind(payload.kind.value)
                    if (payload.kind and hasattr(payload.kind, "value"))
                    else ActivityDefinitionKind(payload.kind)
                    if payload.kind
                    else None
                )
            if "profile" in fields_set:
                model.profile = payload.profile
            if "intent" in fields_set:
                model.intent = (
                    ActivityDefinitionIntent(payload.intent.value)
                    if (payload.intent and hasattr(payload.intent, "value"))
                    else ActivityDefinitionIntent(payload.intent)
                    if payload.intent
                    else None
                )
            if "priority" in fields_set:
                model.priority = (
                    ActivityDefinitionPriority(payload.priority.value)
                    if (payload.priority and hasattr(payload.priority, "value"))
                    else ActivityDefinitionPriority(payload.priority)
                    if payload.priority
                    else None
                )
            if "do_not_perform" in fields_set:
                model.do_not_perform = payload.do_not_perform

            # timing[x]
            if "timing_timing" in fields_set:
                model.timing_timing = payload.timing_timing
            if "timing_date_time" in fields_set:
                model.timing_date_time = payload.timing_date_time
            if "timing_age_value" in fields_set:
                model.timing_age_value = payload.timing_age_value
            if "timing_age_unit" in fields_set:
                model.timing_age_unit = payload.timing_age_unit
            if "timing_age_system" in fields_set:
                model.timing_age_system = payload.timing_age_system
            if "timing_age_code" in fields_set:
                model.timing_age_code = payload.timing_age_code
            if "timing_period_start" in fields_set:
                model.timing_period_start = payload.timing_period_start
            if "timing_period_end" in fields_set:
                model.timing_period_end = payload.timing_period_end
            if "timing_range_low_value" in fields_set:
                model.timing_range_low_value = payload.timing_range_low_value
            if "timing_range_low_unit" in fields_set:
                model.timing_range_low_unit = payload.timing_range_low_unit
            if "timing_range_high_value" in fields_set:
                model.timing_range_high_value = payload.timing_range_high_value
            if "timing_range_high_unit" in fields_set:
                model.timing_range_high_unit = payload.timing_range_high_unit
            if "timing_duration_value" in fields_set:
                model.timing_duration_value = payload.timing_duration_value
            if "timing_duration_unit" in fields_set:
                model.timing_duration_unit = payload.timing_duration_unit
            if "timing_duration_system" in fields_set:
                model.timing_duration_system = payload.timing_duration_system
            if "timing_duration_code" in fields_set:
                model.timing_duration_code = payload.timing_duration_code

            # location
            if "location" in fields_set or "location_display" in fields_set:
                loc_type, loc_id = (
                    _parse_location_ref(payload.location)
                    if payload.location
                    else (None, None)
                )
                if loc_type and loc_id:
                    await _validate_ref(session, org_id, loc_type, loc_id, "location")
                model.location_reference = payload.location
                model.location_type = loc_type
                model.location_id = loc_id
                model.location_display = payload.location_display

            # product[x]
            if "product_codeable_concept" in fields_set:
                model.product_codeable_concept_text = (
                    payload.product_codeable_concept.text
                    if payload.product_codeable_concept
                    else None
                )
                await session.execute(
                    delete(ActivityDefinitionProductCoding).where(
                        ActivityDefinitionProductCoding.activity_definition_pk
                        == model.id
                    )
                )
                if (
                    payload.product_codeable_concept
                    and payload.product_codeable_concept.coding
                ):
                    _add_product_codings(
                        session,
                        model.id,
                        org_id,
                        payload.product_codeable_concept.coding,
                        actor,
                    )

            if "product_reference" in fields_set or "product_display" in fields_set:
                prod_type, prod_id = (
                    _parse_product_ref(payload.product_reference)
                    if payload.product_reference
                    else (None, None)
                )
                if prod_type and prod_id:
                    await _validate_ref(
                        session, org_id, prod_type, prod_id, "product_reference"
                    )
                model.product_reference = payload.product_reference
                model.product_type = prod_type
                model.product_id = prod_id
                model.product_display = payload.product_display

            # quantity
            if "quantity_value" in fields_set:
                model.quantity_value = payload.quantity_value
            if "quantity_comparator" in fields_set:
                model.quantity_comparator = (
                    ActivityDefinitionQuantityComparator(
                        payload.quantity_comparator.value
                    )
                    if (
                        payload.quantity_comparator
                        and hasattr(payload.quantity_comparator, "value")
                    )
                    else ActivityDefinitionQuantityComparator(
                        payload.quantity_comparator
                    )
                    if payload.quantity_comparator
                    else None
                )
            if "quantity_unit" in fields_set:
                model.quantity_unit = payload.quantity_unit
            if "quantity_system" in fields_set:
                model.quantity_system = payload.quantity_system
            if "quantity_code" in fields_set:
                model.quantity_code = payload.quantity_code

            if "transform" in fields_set:
                model.transform = payload.transform

            # subject[x]
            if "subject_codeable_concept" in fields_set:
                model.subject_codeable_concept_text = (
                    payload.subject_codeable_concept.text
                    if payload.subject_codeable_concept
                    else None
                )
                await session.execute(
                    delete(ActivityDefinitionSubjectCoding).where(
                        ActivityDefinitionSubjectCoding.activity_definition_pk
                        == model.id
                    )
                )
                if (
                    payload.subject_codeable_concept
                    and payload.subject_codeable_concept.coding
                ):
                    _add_subject_codings(
                        session,
                        model.id,
                        org_id,
                        payload.subject_codeable_concept.coding,
                        actor,
                    )

            if "subject_reference" in fields_set or "subject_display" in fields_set:
                subj_type, subj_id = (
                    _parse_subject_ref(payload.subject_reference)
                    if payload.subject_reference
                    else (None, None)
                )
                if subj_type and subj_id:
                    await _validate_ref(
                        session, org_id, subj_type, subj_id, "subject_reference"
                    )
                model.subject_reference = payload.subject_reference
                model.subject_type = subj_type
                model.subject_id = subj_id
                model.subject_display = payload.subject_display

            if "extension" in fields_set:
                model.extension = payload.extension or []

            # code
            if "code" in fields_set:
                model.code_text = payload.code.text if payload.code else None
                await session.execute(
                    delete(ActivityDefinitionCodeCoding).where(
                        ActivityDefinitionCodeCoding.activity_definition_pk == model.id
                    )
                )
                if payload.code and payload.code.coding:
                    _add_code_codings(
                        session, model.id, org_id, payload.code.coding, actor
                    )

            # identifier
            if "identifier" in fields_set:
                ident_subq = select(ActivityDefinitionIdentifier.id).where(
                    ActivityDefinitionIdentifier.activity_definition_pk == model.id
                )
                await session.execute(
                    delete(ActivityDefinitionIdentifierTypeCoding).where(
                        ActivityDefinitionIdentifierTypeCoding.identifier_id.in_(
                            ident_subq
                        )
                    )
                )
                await session.execute(
                    delete(ActivityDefinitionIdentifier).where(
                        ActivityDefinitionIdentifier.activity_definition_pk == model.id
                    )
                )
                if payload.identifier:
                    await _add_identifiers(
                        session, model.id, org_id, payload.identifier, actor
                    )

            # contacts (contact, author, editor, reviewer, endorser)
            for role_name in ["contact", "author", "editor", "reviewer", "endorser"]:
                if role_name in fields_set:
                    role_enum = getattr(ActivityDefinitionContactRole, role_name)
                    c_subq = select(ActivityDefinitionContact.id).where(
                        ActivityDefinitionContact.activity_definition_pk == model.id,
                        ActivityDefinitionContact.role == role_enum,
                    )
                    await session.execute(
                        delete(ActivityDefinitionContactTelecom).where(
                            ActivityDefinitionContactTelecom.activity_definition_contact_id.in_(c_subq)
                        )
                    )
                    await session.execute(
                        delete(ActivityDefinitionContact).where(
                            ActivityDefinitionContact.activity_definition_pk == model.id,
                            ActivityDefinitionContact.role == role_enum,
                        )
                    )
                    items = getattr(payload, role_name)
                    if items:
                        await _add_contacts(
                            session, model.id, org_id, items, role_enum, actor
                        )

            # use_context
            if "use_context" in fields_set:
                uc_subq = select(ActivityDefinitionUseContext.id).where(
                    ActivityDefinitionUseContext.activity_definition_pk == model.id
                )
                await session.execute(
                    delete(ActivityDefinitionUseContextValueCoding).where(
                        ActivityDefinitionUseContextValueCoding.activity_definition_use_context_id.in_(
                            uc_subq
                        )
                    )
                )
                await session.execute(
                    delete(ActivityDefinitionUseContext).where(
                        ActivityDefinitionUseContext.activity_definition_pk == model.id
                    )
                )
                if payload.use_context:
                    await _add_use_contexts(
                        session, model.id, org_id, payload.use_context, actor
                    )

            # jurisdiction
            if "jurisdiction" in fields_set:
                j_subq = select(ActivityDefinitionJurisdiction.id).where(
                    ActivityDefinitionJurisdiction.activity_definition_pk == model.id
                )
                await session.execute(
                    delete(ActivityDefinitionJurisdictionCoding).where(
                        ActivityDefinitionJurisdictionCoding.activity_definition_jurisdiction_id.in_(j_subq)
                    )
                )
                await session.execute(
                    delete(ActivityDefinitionJurisdiction).where(
                        ActivityDefinitionJurisdiction.activity_definition_pk == model.id
                    )
                )
                if payload.jurisdiction:
                    await _add_jurisdictions(
                        session, model.id, org_id, payload.jurisdiction, actor
                    )

            # topic
            if "topic" in fields_set:
                t_subq = select(ActivityDefinitionTopic.id).where(
                    ActivityDefinitionTopic.activity_definition_pk == model.id
                )
                await session.execute(
                    delete(ActivityDefinitionTopicCoding).where(
                        ActivityDefinitionTopicCoding.activity_definition_topic_id.in_(t_subq)
                    )
                )
                await session.execute(
                    delete(ActivityDefinitionTopic).where(
                        ActivityDefinitionTopic.activity_definition_pk == model.id
                    )
                )
                if payload.topic:
                    await _add_topics(session, model.id, org_id, payload.topic, actor)

            # body_site
            if "body_site" in fields_set:
                b_subq = select(ActivityDefinitionBodySite.id).where(
                    ActivityDefinitionBodySite.activity_definition_pk == model.id
                )
                await session.execute(
                    delete(ActivityDefinitionBodySiteCoding).where(
                        ActivityDefinitionBodySiteCoding.activity_definition_body_site_id.in_(b_subq)
                    )
                )
                await session.execute(
                    delete(ActivityDefinitionBodySite).where(
                        ActivityDefinitionBodySite.activity_definition_pk == model.id
                    )
                )
                if payload.body_site:
                    await _add_body_sites(
                        session, model.id, org_id, payload.body_site, actor
                    )

            # related_artifact
            if "related_artifact" in fields_set:
                await session.execute(
                    delete(ActivityDefinitionRelatedArtifact).where(
                        ActivityDefinitionRelatedArtifact.activity_definition_pk
                        == model.id
                    )
                )
                if payload.related_artifact:
                    await _add_related_artifacts(
                        session, model.id, org_id, payload.related_artifact, actor
                    )

            # participant
            if "participant" in fields_set:
                p_subq = select(ActivityDefinitionParticipant.id).where(
                    ActivityDefinitionParticipant.activity_definition_pk == model.id
                )
                await session.execute(
                    delete(ActivityDefinitionParticipantRoleCoding).where(
                        ActivityDefinitionParticipantRoleCoding.activity_definition_participant_id.in_(
                            p_subq
                        )
                    )
                )
                await session.execute(
                    delete(ActivityDefinitionParticipant).where(
                        ActivityDefinitionParticipant.activity_definition_pk == model.id
                    )
                )
                if payload.participant:
                    await _add_participants(
                        session, model.id, org_id, payload.participant, actor
                    )

            # dosage
            if "dosage" in fields_set:
                d_subq = select(ActivityDefinitionDosage.id).where(
                    ActivityDefinitionDosage.activity_definition_pk == model.id
                )
                await session.execute(
                    delete(ActivityDefinitionDosageSiteCoding).where(
                        ActivityDefinitionDosageSiteCoding.activity_definition_dosage_id.in_(d_subq)
                    )
                )
                await session.execute(
                    delete(ActivityDefinitionDosageRouteCoding).where(
                        ActivityDefinitionDosageRouteCoding.activity_definition_dosage_id.in_(d_subq)
                    )
                )
                await session.execute(
                    delete(ActivityDefinitionDosageMethodCoding).where(
                        ActivityDefinitionDosageMethodCoding.activity_definition_dosage_id.in_(d_subq)
                    )
                )
                await session.execute(
                    delete(ActivityDefinitionDosageAsNeededCoding).where(
                        ActivityDefinitionDosageAsNeededCoding.activity_definition_dosage_id.in_(d_subq)
                    )
                )
                await session.execute(
                    delete(ActivityDefinitionDosage).where(
                        ActivityDefinitionDosage.activity_definition_pk == model.id
                    )
                )
                if payload.dosage:
                    await _add_dosages(session, model.id, org_id, payload.dosage, actor)

            # dynamic_value
            if "dynamic_value" in fields_set:
                await session.execute(
                    delete(ActivityDefinitionDynamicValue).where(
                        ActivityDefinitionDynamicValue.activity_definition_pk
                        == model.id
                    )
                )
                if payload.dynamic_value:
                    await _add_dynamic_values(
                        session, model.id, org_id, payload.dynamic_value, actor
                    )

            # specimen_requirement
            if "specimen_requirement" in fields_set:
                await session.execute(
                    delete(ActivityDefinitionSpecimenRequirement).where(
                        ActivityDefinitionSpecimenRequirement.activity_definition_pk
                        == model.id
                    )
                )
                if payload.specimen_requirement:
                    await _add_specimen_requirements(
                        session, model.id, org_id, payload.specimen_requirement, actor
                    )

            # observation_requirement
            if "observation_requirement" in fields_set:
                await session.execute(
                    delete(ActivityDefinitionObservationRequirement).where(
                        ActivityDefinitionObservationRequirement.activity_definition_pk
                        == model.id
                    )
                )
                if payload.observation_requirement:
                    await _add_observation_requirements(
                        session,
                        model.id,
                        org_id,
                        payload.observation_requirement,
                        actor,
                    )

            # observation_result_requirement
            if "observation_result_requirement" in fields_set:
                await session.execute(
                    delete(ActivityDefinitionObservationResultRequirement).where(
                        ActivityDefinitionObservationResultRequirement.activity_definition_pk
                        == model.id
                    )
                )
                if payload.observation_result_requirement:
                    await _add_observation_result_requirements(
                        session,
                        model.id,
                        org_id,
                        payload.observation_result_requirement,
                        actor,
                    )

            if updated_by:
                model.updated_by = updated_by

            await session.commit()

            stmt = select(ActivityDefinitionModel).where(
                ActivityDefinitionModel.id == model.id
            )
            stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalar_one()
