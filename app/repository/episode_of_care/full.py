from __future__ import annotations

import datetime as dt

from sqlalchemy import delete
from sqlalchemy.future import select

from app.models.enums import IdentifierUse
from app.models.episode_of_care import (
    EpisodeOfCareAccount,
    EpisodeOfCareDiagnosis,
    EpisodeOfCareDiagnosisRoleCoding,
    EpisodeOfCareIdentifier,
    EpisodeOfCareIdentifierTypeCoding,
    EpisodeOfCareModel,
    EpisodeOfCareReferralRequest,
    EpisodeOfCareStatus,
    EpisodeOfCareStatusHistory,
    EpisodeOfCareTeam,
    EpisodeOfCareType,
    EpisodeOfCareTypeCoding,
)
from app.schemas.episode_of_care import (
    EpisodeOfCareCreateSchema,
    EpisodeOfCarePatchSchema,
)

from ._shared import (
    _parse_account_ref,
    _parse_assigner_ref,
    _parse_care_manager_ref,
    _parse_condition_ref,
    _parse_managing_org_ref,
    _parse_patient_ref,
    _parse_referral_request_ref,
    _parse_team_ref,
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


async def _add_identifiers(
    session, episode_of_care_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")
        ident = EpisodeOfCareIdentifier(
            episode_of_care_pk=episode_of_care_pk,
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
            assigner_identifier_use=(
                IdentifierUse(i.assigner_identifier_use.value)
                if (i.assigner_identifier_use and hasattr(i.assigner_identifier_use, "value"))
                else IdentifierUse(i.assigner_identifier_use)
                if i.assigner_identifier_use
                else None
            ),
            assigner_identifier_system=i.assigner_identifier_system,
            assigner_identifier_value=i.assigner_identifier_value,
            assigner_identifier_type_text=i.assigner_identifier_type_text,
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()
        if i.type_codings:
            for c in i.type_codings:
                session.add(
                    EpisodeOfCareIdentifierTypeCoding(
                        identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_status_history(
    session, episode_of_care_pk: int, org_id: str, history, created_by: str
) -> None:
    for h in history or []:
        sh = EpisodeOfCareStatusHistory(
            episode_of_care_pk=episode_of_care_pk,
            tenant_id=org_id,
            status=(
                EpisodeOfCareStatus(h.status.value)
                if hasattr(h.status, "value")
                else EpisodeOfCareStatus(h.status)
            ),
            period_start=h.period_start,
            period_end=h.period_end,
            created_by=created_by,
        )
        session.add(sh)


async def _add_types(
    session, episode_of_care_pk: int, org_id: str, types, created_by: str
) -> None:
    for t in types or []:
        eoc_type = EpisodeOfCareType(
            episode_of_care_pk=episode_of_care_pk,
            tenant_id=org_id,
            text=t.text,
            created_by=created_by,
        )
        session.add(eoc_type)
        await session.flush()
        if t.coding:
            for c in t.coding:
                session.add(
                    EpisodeOfCareTypeCoding(
                        type_id=eoc_type.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_diagnoses(
    session, episode_of_care_pk: int, org_id: str, diagnoses, created_by: str
) -> None:
    for d in diagnoses or []:
        c_type, c_id = _parse_condition_ref(d.condition) if d.condition else (None, None)
        if c_type and c_id:
            await _validate_ref(session, org_id, c_type, c_id, "diagnosis.condition")
        diag = EpisodeOfCareDiagnosis(
            episode_of_care_pk=episode_of_care_pk,
            tenant_id=org_id,
            condition_reference=d.condition,
            condition_type=c_type,
            condition_id=c_id,
            condition_display=d.condition_display,
            role_text=d.role.text if d.role else None,
            rank=d.rank,
            created_by=created_by,
        )
        session.add(diag)
        await session.flush()
        if d.role and d.role.coding:
            for c in d.role.coding:
                session.add(
                    EpisodeOfCareDiagnosisRoleCoding(
                        diagnosis_id=diag.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_referral_requests(
    session, episode_of_care_pk: int, org_id: str, referrals, created_by: str
) -> None:
    for r in referrals or []:
        ref_type, ref_id = _parse_referral_request_ref(r) if r else (None, None)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "referralRequest")
        session.add(
            EpisodeOfCareReferralRequest(
                episode_of_care_pk=episode_of_care_pk,
                tenant_id=org_id,
                reference_reference=r,
                reference_type=ref_type,
                reference_id=ref_id,
                created_by=created_by,
            )
        )


async def _add_teams(
    session, episode_of_care_pk: int, org_id: str, teams, created_by: str
) -> None:
    for t in teams or []:
        ref_type, ref_id = _parse_team_ref(t) if t else (None, None)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "team")
        session.add(
            EpisodeOfCareTeam(
                episode_of_care_pk=episode_of_care_pk,
                tenant_id=org_id,
                reference_reference=t,
                reference_type=ref_type,
                reference_id=ref_id,
                created_by=created_by,
            )
        )


async def _add_accounts(
    session, episode_of_care_pk: int, org_id: str, accounts, created_by: str
) -> None:
    for a in accounts or []:
        ref_type, ref_id = _parse_account_ref(a) if a else (None, None)
        if ref_type and ref_id:
            await _validate_ref(session, org_id, ref_type, ref_id, "account")
        session.add(
            EpisodeOfCareAccount(
                episode_of_care_pk=episode_of_care_pk,
                tenant_id=org_id,
                reference_reference=a,
                reference_type=ref_type,
                reference_id=ref_id,
                created_by=created_by,
            )
        )


class _FullMixin:
    """Full nested create and patch operations for EpisodeOfCare."""

    async def create_full(
        self,
        payload: EpisodeOfCareCreateSchema,
        org_id: str,
        created_by: str,
    ) -> EpisodeOfCareModel:
        async with self.session_factory() as session:
            # 1. References validation
            p_type, p_id = _parse_patient_ref(payload.patient) if payload.patient else (None, None)
            if p_type and p_id:
                await _validate_ref(session, org_id, p_type, p_id, "patient")

            mo_type, mo_id = (
                _parse_managing_org_ref(payload.managing_organization)
                if payload.managing_organization
                else (None, None)
            )
            if mo_type and mo_id:
                await _validate_ref(session, org_id, mo_type, mo_id, "managingOrganization")

            cm_type, cm_id = (
                _parse_care_manager_ref(payload.care_manager)
                if payload.care_manager
                else (None, None)
            )
            if cm_type and cm_id:
                await _validate_ref(session, org_id, cm_type, cm_id, "careManager")

            # 2. Main resource creation
            eoc = EpisodeOfCareModel(
                tenant_id=org_id,
                status=(
                    EpisodeOfCareStatus(payload.status.value)
                    if hasattr(payload.status, "value")
                    else EpisodeOfCareStatus(payload.status)
                ),
                patient_reference=payload.patient,
                patient_type=p_type,
                patient_id=p_id,
                patient_display=payload.patient_display,
                managing_organization_reference=payload.managing_organization,
                managing_organization_type=mo_type,
                managing_organization_id=mo_id,
                managing_organization_display=payload.managing_organization_display,
                period_start=payload.period_start,
                period_end=payload.period_end,
                care_manager_reference=payload.care_manager,
                care_manager_type=cm_type,
                care_manager_id=cm_id,
                care_manager_display=payload.care_manager_display,
                created_by=created_by,
            )
            session.add(eoc)
            await session.flush()

            # 3. Add child collections
            if payload.identifiers if hasattr(payload, "identifiers") else payload.identifier:
                await _add_identifiers(
                    session,
                    eoc.id,
                    org_id,
                    payload.identifier,
                    created_by,
                )

            if payload.status_history:
                await _add_status_history(
                    session,
                    eoc.id,
                    org_id,
                    payload.status_history,
                    created_by,
                )

            if payload.type:
                await _add_types(
                    session,
                    eoc.id,
                    org_id,
                    payload.type,
                    created_by,
                )

            if payload.diagnosis:
                await _add_diagnoses(
                    session,
                    eoc.id,
                    org_id,
                    payload.diagnosis,
                    created_by,
                )

            if payload.referral_request:
                await _add_referral_requests(
                    session,
                    eoc.id,
                    org_id,
                    payload.referral_request,
                    created_by,
                )

            if payload.team:
                await _add_teams(
                    session,
                    eoc.id,
                    org_id,
                    payload.team,
                    created_by,
                )

            if payload.account:
                await _add_accounts(
                    session,
                    eoc.id,
                    org_id,
                    payload.account,
                    created_by,
                )

            await session.commit()
            eoc_id = eoc.episode_of_care_id

        return await self.get_by_episode_of_care_id_in_org(eoc_id, org_id)

    async def patch_full(
        self,
        episode_of_care_id: int,
        payload: EpisodeOfCarePatchSchema,
        org_id: str,
        updated_by: str | None = None,
    ) -> EpisodeOfCareModel | None:
        async with self.session_factory() as session:
            stmt = select(EpisodeOfCareModel).where(
                EpisodeOfCareModel.episode_of_care_id == episode_of_care_id,
                EpisodeOfCareModel.tenant_id == org_id,
            )
            eoc = (await session.execute(stmt)).scalars().first()
            if not eoc:
                return None

            fields_set = payload.model_fields_set

            if "status" in fields_set and payload.status is not None:
                eoc.status = (
                    EpisodeOfCareStatus(payload.status.value)
                    if hasattr(payload.status, "value")
                    else EpisodeOfCareStatus(payload.status)
                )

            if "patient" in fields_set:
                if payload.patient:
                    p_type, p_id = _parse_patient_ref(payload.patient)
                    if p_type and p_id:
                        await _validate_ref(session, org_id, p_type, p_id, "patient")
                    eoc.patient_reference = payload.patient
                    eoc.patient_type = p_type
                    eoc.patient_id = p_id
                else:
                    eoc.patient_reference = None
                    eoc.patient_type = None
                    eoc.patient_id = None

            if "patient_display" in fields_set:
                eoc.patient_display = payload.patient_display

            if "managing_organization" in fields_set:
                if payload.managing_organization:
                    mo_type, mo_id = _parse_managing_org_ref(payload.managing_organization)
                    if mo_type and mo_id:
                        await _validate_ref(session, org_id, mo_type, mo_id, "managingOrganization")
                    eoc.managing_organization_reference = payload.managing_organization
                    eoc.managing_organization_type = mo_type
                    eoc.managing_organization_id = mo_id
                else:
                    eoc.managing_organization_reference = None
                    eoc.managing_organization_type = None
                    eoc.managing_organization_id = None

            if "managing_organization_display" in fields_set:
                eoc.managing_organization_display = payload.managing_organization_display

            if "period_start" in fields_set:
                eoc.period_start = payload.period_start

            if "period_end" in fields_set:
                eoc.period_end = payload.period_end

            if "care_manager" in fields_set:
                if payload.care_manager:
                    cm_type, cm_id = _parse_care_manager_ref(payload.care_manager)
                    if cm_type and cm_id:
                        await _validate_ref(session, org_id, cm_type, cm_id, "careManager")
                    eoc.care_manager_reference = payload.care_manager
                    eoc.care_manager_type = cm_type
                    eoc.care_manager_id = cm_id
                else:
                    eoc.care_manager_reference = None
                    eoc.care_manager_type = None
                    eoc.care_manager_id = None

            if "care_manager_display" in fields_set:
                eoc.care_manager_display = payload.care_manager_display

            # Sub-resources atomic replacement
            if "identifier" in fields_set:
                await session.execute(
                    delete(EpisodeOfCareIdentifier).where(
                        EpisodeOfCareIdentifier.episode_of_care_pk == eoc.id
                    )
                )
                if payload.identifier:
                    await _add_identifiers(
                        session, eoc.id, org_id, payload.identifier, updated_by or eoc.created_by
                    )

            if "status_history" in fields_set:
                await session.execute(
                    delete(EpisodeOfCareStatusHistory).where(
                        EpisodeOfCareStatusHistory.episode_of_care_pk == eoc.id
                    )
                )
                if payload.status_history:
                    await _add_status_history(
                        session, eoc.id, org_id, payload.status_history, updated_by or eoc.created_by
                    )

            if "type" in fields_set:
                await session.execute(
                    delete(EpisodeOfCareType).where(
                        EpisodeOfCareType.episode_of_care_pk == eoc.id
                    )
                )
                if payload.type:
                    await _add_types(
                        session, eoc.id, org_id, payload.type, updated_by or eoc.created_by
                    )

            if "diagnosis" in fields_set:
                await session.execute(
                    delete(EpisodeOfCareDiagnosis).where(
                        EpisodeOfCareDiagnosis.episode_of_care_pk == eoc.id
                    )
                )
                if payload.diagnosis:
                    await _add_diagnoses(
                        session, eoc.id, org_id, payload.diagnosis, updated_by or eoc.created_by
                    )

            if "referral_request" in fields_set:
                await session.execute(
                    delete(EpisodeOfCareReferralRequest).where(
                        EpisodeOfCareReferralRequest.episode_of_care_pk == eoc.id
                    )
                )
                if payload.referral_request:
                    await _add_referral_requests(
                        session, eoc.id, org_id, payload.referral_request, updated_by or eoc.created_by
                    )

            if "team" in fields_set:
                await session.execute(
                    delete(EpisodeOfCareTeam).where(
                        EpisodeOfCareTeam.episode_of_care_pk == eoc.id
                    )
                )
                if payload.team:
                    await _add_teams(
                        session, eoc.id, org_id, payload.team, updated_by or eoc.created_by
                    )

            if "account" in fields_set:
                await session.execute(
                    delete(EpisodeOfCareAccount).where(
                        EpisodeOfCareAccount.episode_of_care_pk == eoc.id
                    )
                )
                if payload.account:
                    await _add_accounts(
                        session, eoc.id, org_id, payload.account, updated_by or eoc.created_by
                    )

            eoc.updated_by = updated_by
            eoc.updated_at = dt.datetime.now(dt.timezone.utc)
            await session.commit()

        return await self.get_by_episode_of_care_id_in_org(episode_of_care_id, org_id)
