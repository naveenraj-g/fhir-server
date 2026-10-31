from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.consent import (
    ConsentCategory,
    ConsentCategoryCoding,
    ConsentIdentifier,
    ConsentIdentifierTypeCoding,
    ConsentModel,
    ConsentOrganization,
    ConsentPerformer,
    ConsentPolicy,
    ConsentPolicyRuleCoding,
    ConsentProvision,
    ConsentProvisionAction,
    ConsentProvisionActionCoding,
    ConsentProvisionActor,
    ConsentProvisionActorRoleCoding,
    ConsentProvisionClass,
    ConsentProvisionCode,
    ConsentProvisionCodeCoding,
    ConsentProvisionData,
    ConsentProvisionPurpose,
    ConsentProvisionSecurityLabel,
    ConsentScopeCoding,
    ConsentVerification,
)
from app.schemas.consent import (
    ConsentCreateSchema,
    ConsentPatchSchema,
    ConsentProvisionInput,
)

from ._shared import (
    _parse_actor_ref,
    _parse_assigner_ref,
    _parse_generic_ref,
    _parse_organization_ref,
    _parse_patient_ref,
    _parse_performer_ref,
    _parse_source_ref,
    _parse_verified_with_ref,
    _validate_ref,
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
    session, consent_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")

        ident = ConsentIdentifier(
            consent_pk=consent_pk,
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
                    ConsentIdentifierTypeCoding(
                        identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_scope_codings(
    session, consent_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            ConsentScopeCoding(
                consent_pk=consent_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_categories(
    session, consent_pk: int, org_id: str, categories, created_by: str
) -> None:
    for cat in categories or []:
        cat_row = ConsentCategory(
            consent_pk=consent_pk,
            tenant_id=org_id,
            text=cat.text,
            created_by=created_by,
        )
        session.add(cat_row)
        await session.flush()

        if cat.coding:
            for c in cat.coding:
                session.add(
                    ConsentCategoryCoding(
                        category_id=cat_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_performers(
    session, consent_pk: int, org_id: str, performers, created_by: str
) -> None:
    for p in performers or []:
        p_type, p_id = _parse_performer_ref(p.reference)
        if p_type and p_id:
            await _validate_ref(session, org_id, p_type, p_id, "performer")
        session.add(
            ConsentPerformer(
                consent_pk=consent_pk,
                tenant_id=org_id,
                reference_reference=p.reference,
                reference_type=p_type,
                reference_id=p_id,
                reference_display=p.display,
                created_by=created_by,
            )
        )


async def _add_organizations(
    session, consent_pk: int, org_id: str, organizations, created_by: str
) -> None:
    for o in organizations or []:
        o_type, o_id = _parse_organization_ref(o.reference)
        if o_type and o_id:
            await _validate_ref(session, org_id, o_type, o_id, "organization")
        session.add(
            ConsentOrganization(
                consent_pk=consent_pk,
                tenant_id=org_id,
                reference_reference=o.reference,
                reference_type=o_type,
                reference_id=o_id,
                reference_display=o.display,
                created_by=created_by,
            )
        )


async def _add_policies(
    session, consent_pk: int, org_id: str, policies, created_by: str
) -> None:
    for pol in policies or []:
        session.add(
            ConsentPolicy(
                consent_pk=consent_pk,
                tenant_id=org_id,
                authority=pol.authority,
                uri=pol.uri,
                created_by=created_by,
            )
        )


async def _add_policy_rule_codings(
    session, consent_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            ConsentPolicyRuleCoding(
                consent_pk=consent_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_verifications(
    session, consent_pk: int, org_id: str, verifications, created_by: str
) -> None:
    for v in verifications or []:
        vw_type, vw_id = (
            _parse_verified_with_ref(v.verified_with)
            if v.verified_with
            else (None, None)
        )
        if vw_type and vw_id:
            await _validate_ref(
                session, org_id, vw_type, vw_id, "verification.verified_with"
            )

        session.add(
            ConsentVerification(
                consent_pk=consent_pk,
                tenant_id=org_id,
                verified=v.verified,
                verified_with_reference=v.verified_with,
                verified_with_type=vw_type,
                verified_with_id=vw_id,
                verified_with_display=v.verified_with_display,
                verification_date=v.verification_date,
                created_by=created_by,
            )
        )


async def _add_provision_tree(
    session,
    consent_pk: int,
    org_id: str,
    prov_input: ConsentProvisionInput,
    parent_provision_id: int | None,
    created_by: str,
) -> None:
    p = ConsentProvision(
        consent_pk=consent_pk,
        parent_provision_id=parent_provision_id,
        tenant_id=org_id,
        type=prov_input.type,
        period_start=prov_input.period_start,
        period_end=prov_input.period_end,
        data_period_start=prov_input.data_period_start,
        data_period_end=prov_input.data_period_end,
        created_by=created_by,
    )
    session.add(p)
    await session.flush()

    if prov_input.actor:
        for a in prov_input.actor:
            a_type, a_id = _parse_actor_ref(a.reference)
            if a_type and a_id:
                await _validate_ref(
                    session, org_id, a_type, a_id, "provision.actor.reference"
                )
            actor_row = ConsentProvisionActor(
                provision_id=p.id,
                tenant_id=org_id,
                role_text=a.role.text if a.role else None,
                reference_reference=a.reference,
                reference_type=a_type,
                reference_id=a_id,
                reference_display=a.reference_display,
                created_by=created_by,
            )
            session.add(actor_row)
            await session.flush()

            if a.role and a.role.coding:
                for c in a.role.coding:
                    session.add(
                        ConsentProvisionActorRoleCoding(
                            provision_actor_id=actor_row.id,
                            **_coding_kwargs(c, org_id, created_by),
                        )
                    )

    if prov_input.action:
        for act in prov_input.action:
            action_row = ConsentProvisionAction(
                provision_id=p.id,
                tenant_id=org_id,
                text=act.text,
                created_by=created_by,
            )
            session.add(action_row)
            await session.flush()

            if act.coding:
                for c in act.coding:
                    session.add(
                        ConsentProvisionActionCoding(
                            action_id=action_row.id,
                            **_coding_kwargs(c, org_id, created_by),
                        )
                    )

    if prov_input.security_label:
        for s in prov_input.security_label:
            session.add(
                ConsentProvisionSecurityLabel(
                    provision_id=p.id,
                    **_coding_kwargs(s, org_id, created_by),
                )
            )

    if prov_input.purpose:
        for pr in prov_input.purpose:
            session.add(
                ConsentProvisionPurpose(
                    provision_id=p.id,
                    **_coding_kwargs(pr, org_id, created_by),
                )
            )

    classes = getattr(prov_input, "class_", None)
    if classes:
        for cl in classes:
            session.add(
                ConsentProvisionClass(
                    provision_id=p.id,
                    **_coding_kwargs(cl, org_id, created_by),
                )
            )

    if prov_input.code:
        for cd in prov_input.code:
            code_row = ConsentProvisionCode(
                provision_id=p.id,
                tenant_id=org_id,
                text=cd.text,
                created_by=created_by,
            )
            session.add(code_row)
            await session.flush()

            if cd.coding:
                for c in cd.coding:
                    session.add(
                        ConsentProvisionCodeCoding(
                            code_id=code_row.id,
                            **_coding_kwargs(c, org_id, created_by),
                        )
                    )

    if prov_input.data:
        for dt in prov_input.data:
            dt_type, dt_id = _parse_generic_ref(dt.reference)
            if dt_type and dt_id:
                await _validate_ref(
                    session, org_id, dt_type, dt_id, "provision.data.reference"
                )
            data_row = ConsentProvisionData(
                provision_id=p.id,
                tenant_id=org_id,
                meaning=dt.meaning,
                reference_reference=dt.reference,
                reference_type=dt_type,
                reference_id=dt_id,
                reference_display=dt.reference_display,
                created_by=created_by,
            )
            session.add(data_row)

    if prov_input.provision:
        for sub in prov_input.provision:
            await _add_provision_tree(
                session, consent_pk, org_id, sub, p.id, created_by
            )


class _FullMixin:
    """Composite create and patch operations for Consent."""

    async def create_full(
        self, payload: ConsentCreateSchema, org_id: str, created_by: str
    ) -> ConsentModel:
        async with self.session_factory() as session:
            # Resolve patient
            pat_type, pat_id = (
                _parse_patient_ref(payload.patient)
                if payload.patient
                else (None, None)
            )
            if pat_type and pat_id:
                await _validate_ref(session, org_id, pat_type, pat_id, "patient")

            # Resolve sourceReference
            src_type, src_id = (
                _parse_source_ref(payload.source_reference)
                if payload.source_reference
                else (None, None)
            )
            if src_type and src_id:
                await _validate_ref(
                    session, org_id, src_type, src_id, "source_reference"
                )

            consent = ConsentModel(
                tenant_id=org_id,
                status=payload.status,
                scope_text=payload.scope.text if payload.scope else None,
                patient_reference=payload.patient,
                patient_type=pat_type,
                patient_id=pat_id,
                patient_display=payload.patient_display,
                date_time=payload.date_time,
                source_reference_reference=payload.source_reference,
                source_reference_type=src_type,
                source_reference_id=src_id,
                source_reference_display=payload.source_reference_display,
                source_attachment=payload.source_attachment,
                policy_rule_text=payload.policy_rule.text
                if payload.policy_rule
                else None,
                extension=payload.extension or [],
                created_by=created_by,
            )
            session.add(consent)
            await session.flush()

            await _add_identifiers(
                session, consent.id, org_id, payload.identifier, created_by
            )

            if payload.scope and payload.scope.coding:
                await _add_scope_codings(
                    session, consent.id, org_id, payload.scope.coding, created_by
                )

            await _add_categories(
                session, consent.id, org_id, payload.category, created_by
            )
            await _add_performers(
                session, consent.id, org_id, payload.performer, created_by
            )
            await _add_organizations(
                session, consent.id, org_id, payload.organization, created_by
            )
            await _add_policies(
                session, consent.id, org_id, payload.policy, created_by
            )

            if payload.policy_rule and payload.policy_rule.coding:
                await _add_policy_rule_codings(
                    session,
                    consent.id,
                    org_id,
                    payload.policy_rule.coding,
                    created_by,
                )

            await _add_verifications(
                session, consent.id, org_id, payload.verification, created_by
            )

            if payload.provision:
                await _add_provision_tree(
                    session,
                    consent.id,
                    org_id,
                    payload.provision,
                    None,
                    created_by,
                )

            await session.commit()

        return await self.get_by_consent_id_in_org(consent.consent_id, org_id)

    async def patch_full(
        self,
        consent_id: int,
        payload: ConsentPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> ConsentModel | None:
        async with self.session_factory() as session:
            stmt = select(ConsentModel).where(
                ConsentModel.consent_id == consent_id,
                ConsentModel.tenant_id == org_id,
            )
            consent = (await session.execute(stmt)).scalars().first()
            if not consent:
                return None

            fields_set = payload.model_fields_set

            if "status" in fields_set:
                consent.status = payload.status
            if "date_time" in fields_set:
                consent.date_time = payload.date_time
            if "source_attachment" in fields_set:
                consent.source_attachment = payload.source_attachment
            if "extension" in fields_set:
                consent.extension = payload.extension or []

            if "patient" in fields_set or "patient_display" in fields_set:
                if payload.patient:
                    pat_type, pat_id = _parse_patient_ref(payload.patient)
                    await _validate_ref(
                        session, org_id, pat_type, pat_id, "patient"
                    )
                    consent.patient_reference = payload.patient
                    consent.patient_type = pat_type
                    consent.patient_id = pat_id
                elif "patient" in fields_set and payload.patient is None:
                    consent.patient_reference = None
                    consent.patient_type = None
                    consent.patient_id = None
                if "patient_display" in fields_set:
                    consent.patient_display = payload.patient_display

            if (
                "source_reference" in fields_set
                or "source_reference_display" in fields_set
            ):
                if payload.source_reference:
                    src_type, src_id = _parse_source_ref(
                        payload.source_reference
                    )
                    await _validate_ref(
                        session, org_id, src_type, src_id, "source_reference"
                    )
                    consent.source_reference_reference = (
                        payload.source_reference
                    )
                    consent.source_reference_type = src_type
                    consent.source_reference_id = src_id
                elif (
                    "source_reference" in fields_set
                    and payload.source_reference is None
                ):
                    consent.source_reference_reference = None
                    consent.source_reference_type = None
                    consent.source_reference_id = None
                if "source_reference_display" in fields_set:
                    consent.source_reference_display = (
                        payload.source_reference_display
                    )

            if "scope" in fields_set:
                await session.execute(
                    delete(ConsentScopeCoding).where(
                        ConsentScopeCoding.consent_pk == consent.id
                    )
                )
                consent.scope_text = (
                    payload.scope.text if payload.scope else None
                )
                if payload.scope and payload.scope.coding:
                    await _add_scope_codings(
                        session,
                        consent.id,
                        org_id,
                        payload.scope.coding,
                        updated_by,
                    )

            if "category" in fields_set:
                await session.execute(
                    delete(ConsentCategory).where(
                        ConsentCategory.consent_pk == consent.id
                    )
                )
                if payload.category:
                    await _add_categories(
                        session,
                        consent.id,
                        org_id,
                        payload.category,
                        updated_by,
                    )

            if "performer" in fields_set:
                await session.execute(
                    delete(ConsentPerformer).where(
                        ConsentPerformer.consent_pk == consent.id
                    )
                )
                if payload.performer:
                    await _add_performers(
                        session,
                        consent.id,
                        org_id,
                        payload.performer,
                        updated_by,
                    )

            if "organization" in fields_set:
                await session.execute(
                    delete(ConsentOrganization).where(
                        ConsentOrganization.consent_pk == consent.id
                    )
                )
                if payload.organization:
                    await _add_organizations(
                        session,
                        consent.id,
                        org_id,
                        payload.organization,
                        updated_by,
                    )

            if "policy" in fields_set:
                await session.execute(
                    delete(ConsentPolicy).where(
                        ConsentPolicy.consent_pk == consent.id
                    )
                )
                if payload.policy:
                    await _add_policies(
                        session, consent.id, org_id, payload.policy, updated_by
                    )

            if "policy_rule" in fields_set:
                await session.execute(
                    delete(ConsentPolicyRuleCoding).where(
                        ConsentPolicyRuleCoding.consent_pk == consent.id
                    )
                )
                consent.policy_rule_text = (
                    payload.policy_rule.text if payload.policy_rule else None
                )
                if payload.policy_rule and payload.policy_rule.coding:
                    await _add_policy_rule_codings(
                        session,
                        consent.id,
                        org_id,
                        payload.policy_rule.coding,
                        updated_by,
                    )

            if "verification" in fields_set:
                await session.execute(
                    delete(ConsentVerification).where(
                        ConsentVerification.consent_pk == consent.id
                    )
                )
                if payload.verification:
                    await _add_verifications(
                        session,
                        consent.id,
                        org_id,
                        payload.verification,
                        updated_by,
                    )

            if "provision" in fields_set:
                await session.execute(
                    delete(ConsentProvision).where(
                        ConsentProvision.consent_pk == consent.id
                    )
                )
                if payload.provision:
                    await _add_provision_tree(
                        session,
                        consent.id,
                        org_id,
                        payload.provision,
                        None,
                        updated_by,
                    )

            if "identifier" in fields_set:
                await session.execute(
                    delete(ConsentIdentifier).where(
                        ConsentIdentifier.consent_pk == consent.id
                    )
                )
                if payload.identifier:
                    await _add_identifiers(
                        session,
                        consent.id,
                        org_id,
                        payload.identifier,
                        updated_by,
                    )

            consent.updated_by = updated_by
            await session.commit()

        return await self.get_by_consent_id_in_org(consent_id, org_id)
