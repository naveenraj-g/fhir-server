from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.allergy_intolerance import (
    AllergyIntoleranceClinicalStatusCoding,
    AllergyIntoleranceCodeCoding,
    AllergyIntoleranceIdentifier,
    AllergyIntoleranceIdentifierTypeCoding,
    AllergyIntoleranceModel,
    AllergyIntoleranceNote,
    AllergyIntoleranceReaction,
    AllergyIntoleranceReactionExposureRouteCoding,
    AllergyIntoleranceReactionManifestation,
    AllergyIntoleranceReactionManifestationCoding,
    AllergyIntoleranceReactionNote,
    AllergyIntoleranceReactionSubstanceCoding,
    AllergyIntoleranceVerificationStatusCoding,
)
from app.schemas.allergy_intolerance import (
    AllergyIntoleranceCreateSchema,
    AllergyIntolerancePatchSchema,
)

from ._shared import (
    _parse_asserter_ref,
    _parse_assigner_ref,
    _parse_author_ref,
    _parse_encounter_ref,
    _parse_patient_ref,
    _parse_reaction_author_ref,
    _parse_recorder_ref,
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
    session, allergy_intolerance_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")

        ident = AllergyIntoleranceIdentifier(
            allergy_intolerance_pk=allergy_intolerance_pk,
            tenant_id=org_id,
            use=i.use,
            type_text=i.type.text if i.type else None,
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

        if i.type and i.type.coding:
            for c in i.type.coding:
                session.add(
                    AllergyIntoleranceIdentifierTypeCoding(
                        identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_notes(
    session, allergy_intolerance_pk: int, org_id: str, notes, created_by: str
) -> None:
    for n in notes or []:
        author_type, author_id = (
            _parse_author_ref(n.author_reference) if n.author_reference else (None, None)
        )
        if author_type and author_id:
            await _validate_ref(
                session, org_id, author_type, author_id, "note.author_reference"
            )
        session.add(
            AllergyIntoleranceNote(
                allergy_intolerance_pk=allergy_intolerance_pk,
                tenant_id=org_id,
                text=n.text,
                time=n.time,
                author_string=n.author_string,
                author_reference_type=author_type,
                author_reference_id=author_id,
                author_reference_display=n.author_reference_display,
                created_by=created_by,
            )
        )


async def _add_reactions(
    session, allergy_intolerance_pk: int, org_id: str, reactions, created_by: str
) -> None:
    for r in reactions or []:
        reaction = AllergyIntoleranceReaction(
            allergy_intolerance_pk=allergy_intolerance_pk,
            tenant_id=org_id,
            description=r.description,
            onset=r.onset,
            severity=r.severity,
            substance_text=r.substance.text if r.substance else None,
            exposure_route_text=r.exposure_route.text if r.exposure_route else None,
            created_by=created_by,
        )
        session.add(reaction)
        await session.flush()

        if r.substance and r.substance.coding:
            for c in r.substance.coding:
                session.add(
                    AllergyIntoleranceReactionSubstanceCoding(
                        reaction_id=reaction.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )

        if r.exposure_route and r.exposure_route.coding:
            for c in r.exposure_route.coding:
                session.add(
                    AllergyIntoleranceReactionExposureRouteCoding(
                        reaction_id=reaction.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )

        for m in r.manifestation or []:
            manif = AllergyIntoleranceReactionManifestation(
                reaction_id=reaction.id,
                tenant_id=org_id,
                text=m.text,
                created_by=created_by,
            )
            session.add(manif)
            await session.flush()

            if m.coding:
                for c in m.coding:
                    session.add(
                        AllergyIntoleranceReactionManifestationCoding(
                            manifestation_id=manif.id,
                            **_coding_kwargs(c, org_id, created_by),
                        )
                    )

        if r.note:
            for rn in r.note:
                author_type, author_id = (
                    _parse_reaction_author_ref(rn.author_reference)
                    if rn.author_reference
                    else (None, None)
                )
                if author_type and author_id:
                    await _validate_ref(
                        session,
                        org_id,
                        author_type,
                        author_id,
                        "reaction.note.author_reference",
                    )
                session.add(
                    AllergyIntoleranceReactionNote(
                        reaction_id=reaction.id,
                        tenant_id=org_id,
                        text=rn.text,
                        time=rn.time,
                        author_string=rn.author_string,
                        author_reference_type=author_type,
                        author_reference_id=author_id,
                        author_reference_display=rn.author_reference_display,
                        created_by=created_by,
                    )
                )


class _FullMixin:
    """Mixin for atomic create_full and patch_full operations on AllergyIntolerance."""

    async def create_full(
        self,
        payload: AllergyIntoleranceCreateSchema,
        org_id: str,
        created_by: str,
    ) -> AllergyIntoleranceModel:
        """Create a complete AllergyIntolerance and all child records in a single transaction."""
        async with self.session_factory() as session:
            # 1. Parse & validate references
            p_type, p_id = _parse_patient_ref(payload.patient)
            await _validate_ref(session, org_id, p_type, p_id, "patient")

            enc_type, enc_id = (
                _parse_encounter_ref(payload.encounter)
                if payload.encounter
                else (None, None)
            )
            if enc_type and enc_id:
                await _validate_ref(session, org_id, enc_type, enc_id, "encounter")

            rec_type, rec_id = (
                _parse_recorder_ref(payload.recorder)
                if payload.recorder
                else (None, None)
            )
            if rec_type and rec_id:
                await _validate_ref(session, org_id, rec_type, rec_id, "recorder")

            ass_type, ass_id = (
                _parse_asserter_ref(payload.asserter)
                if payload.asserter
                else (None, None)
            )
            if ass_type and ass_id:
                await _validate_ref(session, org_id, ass_type, ass_id, "asserter")

            # 2. Construct main model
            model = AllergyIntoleranceModel(
                tenant_id=org_id,
                created_by=created_by,
                clinical_status_text=(
                    payload.clinical_status.text if payload.clinical_status else None
                ),
                verification_status_text=(
                    payload.verification_status.text
                    if payload.verification_status
                    else None
                ),
                type=payload.type,
                category=payload.category,
                criticality=payload.criticality,
                code_text=payload.code.text if payload.code else None,
                patient_reference=payload.patient,
                patient_type=p_type,
                patient_id=p_id,
                patient_display=payload.patient_display,
                encounter_reference=payload.encounter,
                encounter_type=enc_type,
                encounter_id=enc_id,
                encounter_display=payload.encounter_display,
                onset_date_time=payload.onset_date_time,
                onset_age=payload.onset_age,
                onset_period_start=payload.onset_period_start,
                onset_period_end=payload.onset_period_end,
                onset_range=payload.onset_range,
                onset_string=payload.onset_string,
                recorded_date=payload.recorded_date,
                recorder_reference=payload.recorder,
                recorder_type=rec_type,
                recorder_id=rec_id,
                recorder_display=payload.recorder_display,
                asserter_reference=payload.asserter,
                asserter_type=ass_type,
                asserter_id=ass_id,
                asserter_display=payload.asserter_display,
                last_occurrence=payload.last_occurrence,
                extension=payload.extension or [],
            )
            session.add(model)
            await session.flush()

            # 3. Add clinical_status codings
            if payload.clinical_status and payload.clinical_status.coding:
                for c in payload.clinical_status.coding:
                    session.add(
                        AllergyIntoleranceClinicalStatusCoding(
                            allergy_intolerance_pk=model.id,
                            **_coding_kwargs(c, org_id, created_by),
                        )
                    )

            # 4. Add verification_status codings
            if payload.verification_status and payload.verification_status.coding:
                for c in payload.verification_status.coding:
                    session.add(
                        AllergyIntoleranceVerificationStatusCoding(
                            allergy_intolerance_pk=model.id,
                            **_coding_kwargs(c, org_id, created_by),
                        )
                    )

            # 5. Add code codings
            if payload.code and payload.code.coding:
                for c in payload.code.coding:
                    session.add(
                        AllergyIntoleranceCodeCoding(
                            allergy_intolerance_pk=model.id,
                            **_coding_kwargs(c, org_id, created_by),
                        )
                    )

            # 6. Add identifiers
            if payload.identifier:
                await _add_identifiers(
                    session, model.id, org_id, payload.identifier, created_by
                )

            # 7. Add notes
            if payload.note:
                await _add_notes(session, model.id, org_id, payload.note, created_by)

            # 8. Add reactions
            if payload.reaction:
                await _add_reactions(
                    session, model.id, org_id, payload.reaction, created_by
                )

            await session.commit()
            return await self.get_by_allergy_intolerance_id_in_org(
                model.allergy_intolerance_id, org_id
            )

    async def patch_full(
        self,
        allergy_intolerance_id: int,
        payload: AllergyIntolerancePatchSchema,
        org_id: str,
        updated_by: str,
    ) -> AllergyIntoleranceModel | None:
        """Patch an existing AllergyIntolerance and all touched child records atomically."""
        async with self.session_factory() as session:
            stmt = select(AllergyIntoleranceModel).where(
                AllergyIntoleranceModel.allergy_intolerance_id == allergy_intolerance_id,
                AllergyIntoleranceModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return None

            fields_set = payload.model_fields_set

            # Scalars
            if "type" in fields_set:
                model.type = payload.type
            if "category" in fields_set:
                model.category = payload.category
            if "criticality" in fields_set:
                model.criticality = payload.criticality
            if "onset_date_time" in fields_set:
                model.onset_date_time = payload.onset_date_time
            if "onset_age" in fields_set:
                model.onset_age = payload.onset_age
            if "onset_period_start" in fields_set:
                model.onset_period_start = payload.onset_period_start
            if "onset_period_end" in fields_set:
                model.onset_period_end = payload.onset_period_end
            if "onset_range" in fields_set:
                model.onset_range = payload.onset_range
            if "onset_string" in fields_set:
                model.onset_string = payload.onset_string
            if "recorded_date" in fields_set:
                model.recorded_date = payload.recorded_date
            if "last_occurrence" in fields_set:
                model.last_occurrence = payload.last_occurrence
            if "extension" in fields_set:
                model.extension = payload.extension or []

            # Patient reference
            if "patient" in fields_set:
                if payload.patient is not None:
                    p_type, p_id = _parse_patient_ref(payload.patient)
                    await _validate_ref(session, org_id, p_type, p_id, "patient")
                    model.patient_reference = payload.patient
                    model.patient_type = p_type
                    model.patient_id = p_id
            if "patient_display" in fields_set:
                model.patient_display = payload.patient_display

            # Encounter reference
            if "encounter" in fields_set:
                if payload.encounter is not None:
                    enc_type, enc_id = _parse_encounter_ref(payload.encounter)
                    await _validate_ref(session, org_id, enc_type, enc_id, "encounter")
                    model.encounter_reference = payload.encounter
                    model.encounter_type = enc_type
                    model.encounter_id = enc_id
                else:
                    model.encounter_reference = None
                    model.encounter_type = None
                    model.encounter_id = None
            if "encounter_display" in fields_set:
                model.encounter_display = payload.encounter_display

            # Recorder reference
            if "recorder" in fields_set:
                if payload.recorder is not None:
                    rec_type, rec_id = _parse_recorder_ref(payload.recorder)
                    await _validate_ref(session, org_id, rec_type, rec_id, "recorder")
                    model.recorder_reference = payload.recorder
                    model.recorder_type = rec_type
                    model.recorder_id = rec_id
                else:
                    model.recorder_reference = None
                    model.recorder_type = None
                    model.recorder_id = None
            if "recorder_display" in fields_set:
                model.recorder_display = payload.recorder_display

            # Asserter reference
            if "asserter" in fields_set:
                if payload.asserter is not None:
                    ass_type, ass_id = _parse_asserter_ref(payload.asserter)
                    await _validate_ref(session, org_id, ass_type, ass_id, "asserter")
                    model.asserter_reference = payload.asserter
                    model.asserter_type = ass_type
                    model.asserter_id = ass_id
                else:
                    model.asserter_reference = None
                    model.asserter_type = None
                    model.asserter_id = None
            if "asserter_display" in fields_set:
                model.asserter_display = payload.asserter_display

            # Clinical status
            if "clinical_status" in fields_set:
                await session.execute(
                    delete(AllergyIntoleranceClinicalStatusCoding).where(
                        AllergyIntoleranceClinicalStatusCoding.allergy_intolerance_pk
                        == model.id
                    )
                )
                model.clinical_status_text = (
                    payload.clinical_status.text if payload.clinical_status else None
                )
                if payload.clinical_status and payload.clinical_status.coding:
                    for c in payload.clinical_status.coding:
                        session.add(
                            AllergyIntoleranceClinicalStatusCoding(
                                allergy_intolerance_pk=model.id,
                                **_coding_kwargs(c, org_id, updated_by),
                            )
                        )

            # Verification status
            if "verification_status" in fields_set:
                await session.execute(
                    delete(AllergyIntoleranceVerificationStatusCoding).where(
                        AllergyIntoleranceVerificationStatusCoding.allergy_intolerance_pk
                        == model.id
                    )
                )
                model.verification_status_text = (
                    payload.verification_status.text
                    if payload.verification_status
                    else None
                )
                if (
                    payload.verification_status
                    and payload.verification_status.coding
                ):
                    for c in payload.verification_status.coding:
                        session.add(
                            AllergyIntoleranceVerificationStatusCoding(
                                allergy_intolerance_pk=model.id,
                                **_coding_kwargs(c, org_id, updated_by),
                            )
                        )

            # Code
            if "code" in fields_set:
                await session.execute(
                    delete(AllergyIntoleranceCodeCoding).where(
                        AllergyIntoleranceCodeCoding.allergy_intolerance_pk
                        == model.id
                    )
                )
                model.code_text = payload.code.text if payload.code else None
                if payload.code and payload.code.coding:
                    for c in payload.code.coding:
                        session.add(
                            AllergyIntoleranceCodeCoding(
                                allergy_intolerance_pk=model.id,
                                **_coding_kwargs(c, org_id, updated_by),
                            )
                        )

            # Identifiers
            if "identifier" in fields_set:
                await session.execute(
                    delete(AllergyIntoleranceIdentifier).where(
                        AllergyIntoleranceIdentifier.allergy_intolerance_pk
                        == model.id
                    )
                )
                if payload.identifier:
                    await _add_identifiers(
                        session, model.id, org_id, payload.identifier, updated_by
                    )

            # Notes
            if "note" in fields_set:
                await session.execute(
                    delete(AllergyIntoleranceNote).where(
                        AllergyIntoleranceNote.allergy_intolerance_pk == model.id
                    )
                )
                if payload.note:
                    await _add_notes(
                        session, model.id, org_id, payload.note, updated_by
                    )

            # Reactions
            if "reaction" in fields_set:
                await session.execute(
                    delete(AllergyIntoleranceReaction).where(
                        AllergyIntoleranceReaction.allergy_intolerance_pk == model.id
                    )
                )
                if payload.reaction:
                    await _add_reactions(
                        session, model.id, org_id, payload.reaction, updated_by
                    )

            model.updated_by = updated_by
            await session.commit()

        return await self.get_by_allergy_intolerance_id_in_org(
            allergy_intolerance_id, org_id
        )
