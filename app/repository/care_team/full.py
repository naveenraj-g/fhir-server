from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete
from sqlalchemy.future import select

from app.core.logging import get_logger
from app.models.care_team import (
    CareTeamCategory,
    CareTeamCategoryCoding,
    CareTeamIdentifier,
    CareTeamIdentifierTypeCoding,
    CareTeamManagingOrganization,
    CareTeamModel,
    CareTeamNote,
    CareTeamParticipant,
    CareTeamParticipantRole,
    CareTeamParticipantRoleCoding,
    CareTeamReasonCode,
    CareTeamReasonCodeCoding,
    CareTeamReasonReference,
    CareTeamTelecom,
)
from app.models.enums import IdentifierUse
from app.schemas.care_team import (
    CareTeamCreateSchema,
    CareTeamPatchSchema,
)
from app.schemas.enums import ContactPointSystem, ContactPointUse

from ._shared import (
    _parse_assigner_ref,
    _parse_encounter_ref,
    _parse_managing_org_ref,
    _parse_member_ref,
    _parse_note_author_ref,
    _parse_on_behalf_of_ref,
    _parse_reason_ref,
    _parse_subject_ref,
    _validate_ref,
)

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    if isinstance(coding, dict):
        return {
            "tenant_id": org_id,
            "created_by": created_by,
            "system": coding.get("system"),
            "version": coding.get("version"),
            "code": coding.get("code"),
            "display": coding.get("display"),
            "user_selected": coding.get("user_selected"),
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


async def _add_identifiers(session, care_team_pk: int, org_id: str, identifiers, created_by: str) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")
        ident = CareTeamIdentifier(
            care_team_pk=care_team_pk,
            tenant_id=org_id,
            use=IdentifierUse(i.use.value) if i.use else None,
            type_text=i.type.text if i.type else None,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner_reference=i.assigner,
            assigner_type=a_type,
            assigner_id=a_id,
            assigner_display=i.assigner_display,
            assigner_identifier_use=IdentifierUse(i.assigner_identifier_use.value) if i.assigner_identifier_use else None,
            assigner_identifier_system=i.assigner_identifier_system,
            assigner_identifier_value=i.assigner_identifier_value,
            assigner_identifier_type_text=i.assigner_identifier_type_text,
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()
        if i.type and i.type.coding:
            for c in i.type.coding:
                session.add(
                    CareTeamIdentifierTypeCoding(
                        identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_categories(session, care_team_pk: int, org_id: str, categories, created_by: str) -> None:
    for c in categories or []:
        cat = CareTeamCategory(
            care_team_pk=care_team_pk,
            tenant_id=org_id,
            text=c.text,
            created_by=created_by,
        )
        session.add(cat)
        await session.flush()
        if c.coding:
            for coding in c.coding:
                session.add(
                    CareTeamCategoryCoding(
                        category_id=cat.id,
                        **_coding_kwargs(coding, org_id, created_by),
                    )
                )


async def _add_participants(session, care_team_pk: int, org_id: str, participants, created_by: str) -> None:
    for p in participants or []:
        m_type, m_id = _parse_member_ref(p.member) if p.member else (None, None)
        if m_type and m_id:
            await _validate_ref(session, org_id, m_type, m_id, "participant.member")
        ob_type, ob_id = _parse_on_behalf_of_ref(p.on_behalf_of) if p.on_behalf_of else (None, None)
        if ob_type and ob_id:
            await _validate_ref(session, org_id, ob_type, ob_id, "participant.on_behalf_of")

        participant = CareTeamParticipant(
            care_team_pk=care_team_pk,
            tenant_id=org_id,
            member_reference=p.member,
            member_type=m_type,
            member_id=m_id,
            member_display=p.member_display,
            on_behalf_of_reference=p.on_behalf_of,
            on_behalf_of_type=ob_type,
            on_behalf_of_id=ob_id,
            on_behalf_of_display=p.on_behalf_of_display,
            period_start=p.period_start,
            period_end=p.period_end,
            created_by=created_by,
        )
        session.add(participant)
        await session.flush()

        if p.role:
            for r in p.role:
                p_role = CareTeamParticipantRole(
                    participant_id=participant.id,
                    tenant_id=org_id,
                    text=r.text,
                    created_by=created_by,
                )
                session.add(p_role)
                await session.flush()
                if r.coding:
                    for coding in r.coding:
                        session.add(
                            CareTeamParticipantRoleCoding(
                                role_id=p_role.id,
                                **_coding_kwargs(coding, org_id, created_by),
                            )
                        )


async def _add_reason_codes(session, care_team_pk: int, org_id: str, reason_codes, created_by: str) -> None:
    for r in reason_codes or []:
        rc = CareTeamReasonCode(
            care_team_pk=care_team_pk,
            tenant_id=org_id,
            text=r.text,
            created_by=created_by,
        )
        session.add(rc)
        await session.flush()
        if r.coding:
            for coding in r.coding:
                session.add(
                    CareTeamReasonCodeCoding(
                        reason_code_id=rc.id,
                        **_coding_kwargs(coding, org_id, created_by),
                    )
                )


async def _add_reason_references(session, care_team_pk: int, org_id: str, reason_references, created_by: str) -> None:
    for ref_str in reason_references or []:
        r_type, r_id = _parse_reason_ref(ref_str)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "reason_reference")
        session.add(
            CareTeamReasonReference(
                care_team_pk=care_team_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                created_by=created_by,
            )
        )


async def _add_managing_organizations(session, care_team_pk: int, org_id: str, managing_organizations, created_by: str) -> None:
    for ref_str in managing_organizations or []:
        m_type, m_id = _parse_managing_org_ref(ref_str)
        if m_type and m_id:
            await _validate_ref(session, org_id, m_type, m_id, "managing_organization")
        session.add(
            CareTeamManagingOrganization(
                care_team_pk=care_team_pk,
                tenant_id=org_id,
                reference_reference=ref_str,
                reference_type=m_type,
                reference_id=m_id,
                created_by=created_by,
            )
        )


async def _add_telecoms(session, care_team_pk: int, org_id: str, telecoms, created_by: str) -> None:
    for t in telecoms or []:
        session.add(
            CareTeamTelecom(
                care_team_pk=care_team_pk,
                tenant_id=org_id,
                system=(
                    ContactPointSystem(t.system)
                    if isinstance(t.system, str)
                    else t.system
                ),
                value=t.value,
                use=(
                    ContactPointUse(t.use)
                    if isinstance(t.use, str)
                    else t.use
                ),
                rank=t.rank,
                period_start=t.period_start,
                period_end=t.period_end,
                created_by=created_by,
            )
        )


async def _add_notes(session, care_team_pk: int, org_id: str, notes, created_by: str) -> None:
    for n in notes or []:
        auth_type, auth_id = (
            _parse_note_author_ref(n.author_reference)
            if n.author_reference
            else (None, None)
        )
        if auth_type and auth_id:
            await _validate_ref(session, org_id, auth_type, auth_id, "note.author")
        session.add(
            CareTeamNote(
                care_team_pk=care_team_pk,
                tenant_id=org_id,
                text=n.text,
                time=n.time,
                author_string=n.author_string,
                author_reference_reference=n.author_reference,
                author_reference_type=auth_type,
                author_reference_id=auth_id,
                author_reference_display=n.author_reference_display,
                created_by=created_by,
            )
        )


class _FullMixin:
    """Full-write operations for CareTeam (create_full, patch_full)."""

    async def create_full(
        self,
        payload: CareTeamCreateSchema,
        org_id: str,
        created_by: str,
    ) -> CareTeamModel:
        async with self.session_factory() as session:
            s_type, s_id = _parse_subject_ref(payload.subject) if payload.subject else (None, None)
            if s_type and s_id:
                await _validate_ref(session, org_id, s_type, s_id, "subject")

            e_type, e_id = _parse_encounter_ref(payload.encounter) if payload.encounter else (None, None)
            if e_type and e_id:
                await _validate_ref(session, org_id, e_type, e_id, "encounter")

            care_team = CareTeamModel(
                tenant_id=org_id,
                created_by=created_by,
                status=payload.status,
                name=payload.name,
                subject_reference=payload.subject,
                subject_type=s_type,
                subject_id=s_id,
                subject_display=payload.subject_display,
                encounter_reference=payload.encounter,
                encounter_type=e_type,
                encounter_id=e_id,
                encounter_display=payload.encounter_display,
                period_start=payload.period_start,
                period_end=payload.period_end,
            )
            session.add(care_team)
            await session.flush()

            # Add collections
            await _add_identifiers(session, care_team.id, org_id, payload.identifier, created_by)
            await _add_categories(session, care_team.id, org_id, payload.category, created_by)
            await _add_participants(session, care_team.id, org_id, payload.participant, created_by)
            await _add_reason_codes(session, care_team.id, org_id, payload.reason_code, created_by)
            await _add_reason_references(session, care_team.id, org_id, payload.reason_reference, created_by)
            await _add_managing_organizations(session, care_team.id, org_id, payload.managing_organization, created_by)
            await _add_telecoms(session, care_team.id, org_id, payload.telecom, created_by)
            await _add_notes(session, care_team.id, org_id, payload.note, created_by)

            await session.commit()

        return await self.get_by_care_team_id_in_org(care_team.care_team_id, org_id)

    async def patch_full(
        self,
        care_team_id: int,
        payload: CareTeamPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> CareTeamModel | None:
        async with self.session_factory() as session:
            stmt = select(CareTeamModel).where(
                CareTeamModel.care_team_id == care_team_id,
                CareTeamModel.tenant_id == org_id,
            )
            care_team = (await session.execute(stmt)).scalars().first()
            if not care_team:
                return None

            fields_set = payload.model_fields_set

            if "status" in fields_set:
                care_team.status = payload.status

            if "name" in fields_set:
                care_team.name = payload.name

            if "period_start" in fields_set:
                care_team.period_start = payload.period_start

            if "period_end" in fields_set:
                care_team.period_end = payload.period_end

            if "subject" in fields_set or "subject_display" in fields_set:
                if payload.subject:
                    s_type, s_id = _parse_subject_ref(payload.subject)
                    await _validate_ref(session, org_id, s_type, s_id, "subject")
                    care_team.subject_reference = payload.subject
                    care_team.subject_type = s_type
                    care_team.subject_id = s_id
                elif "subject" in fields_set and payload.subject is None:
                    care_team.subject_reference = None
                    care_team.subject_type = None
                    care_team.subject_id = None
                if "subject_display" in fields_set:
                    care_team.subject_display = payload.subject_display

            if "encounter" in fields_set or "encounter_display" in fields_set:
                if payload.encounter:
                    e_type, e_id = _parse_encounter_ref(payload.encounter)
                    await _validate_ref(session, org_id, e_type, e_id, "encounter")
                    care_team.encounter_reference = payload.encounter
                    care_team.encounter_type = e_type
                    care_team.encounter_id = e_id
                elif "encounter" in fields_set and payload.encounter is None:
                    care_team.encounter_reference = None
                    care_team.encounter_type = None
                    care_team.encounter_id = None
                if "encounter_display" in fields_set:
                    care_team.encounter_display = payload.encounter_display

            # Sub-resource replacements
            if "identifier" in fields_set:
                await session.execute(
                    delete(CareTeamIdentifier).where(CareTeamIdentifier.care_team_pk == care_team.id)
                )
                if payload.identifier:
                    await _add_identifiers(session, care_team.id, org_id, payload.identifier, updated_by)

            if "category" in fields_set:
                await session.execute(
                    delete(CareTeamCategory).where(CareTeamCategory.care_team_pk == care_team.id)
                )
                if payload.category:
                    await _add_categories(session, care_team.id, org_id, payload.category, updated_by)

            if "participant" in fields_set:
                await session.execute(
                    delete(CareTeamParticipant).where(CareTeamParticipant.care_team_pk == care_team.id)
                )
                if payload.participant:
                    await _add_participants(session, care_team.id, org_id, payload.participant, updated_by)

            if "reason_code" in fields_set:
                await session.execute(
                    delete(CareTeamReasonCode).where(CareTeamReasonCode.care_team_pk == care_team.id)
                )
                if payload.reason_code:
                    await _add_reason_codes(session, care_team.id, org_id, payload.reason_code, updated_by)

            if "reason_reference" in fields_set:
                await session.execute(
                    delete(CareTeamReasonReference).where(CareTeamReasonReference.care_team_pk == care_team.id)
                )
                if payload.reason_reference:
                    await _add_reason_references(session, care_team.id, org_id, payload.reason_reference, updated_by)

            if "managing_organization" in fields_set:
                await session.execute(
                    delete(CareTeamManagingOrganization).where(CareTeamManagingOrganization.care_team_pk == care_team.id)
                )
                if payload.managing_organization:
                    await _add_managing_organizations(session, care_team.id, org_id, payload.managing_organization, updated_by)

            if "telecom" in fields_set:
                await session.execute(
                    delete(CareTeamTelecom).where(CareTeamTelecom.care_team_pk == care_team.id)
                )
                if payload.telecom:
                    await _add_telecoms(session, care_team.id, org_id, payload.telecom, updated_by)

            if "note" in fields_set:
                await session.execute(
                    delete(CareTeamNote).where(CareTeamNote.care_team_pk == care_team.id)
                )
                if payload.note:
                    await _add_notes(session, care_team.id, org_id, payload.note, updated_by)

            care_team.updated_by = updated_by

            await session.commit()

        return await self.get_by_care_team_id_in_org(care_team_id, org_id)
