from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.patient import (
    PatientAddress,
    PatientCommunication,
    PatientCommunicationLanguageCoding,
    PatientContact,
    PatientContactRelationship,
    PatientContactRelationshipCoding,
    PatientContactTelecom,
    PatientGeneralPractitioner,
    PatientIdentifier,
    PatientIdentifierTypeCoding,
    PatientLink,
    PatientMaritalStatusCoding,
    PatientModel,
    PatientName,
    PatientPhoto,
    PatientTelecom,
)
from app.schemas.patient import PatientCreateSchema, PatientPatchSchema

from ._shared import (
    _org_ref_kwargs,
    _parse_gp_ref,
    _parse_link_ref,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

logger = get_logger(__name__)


def _coding_kwargs(coding, created_by: str | None) -> dict:
    """Build constructor kwargs for one CodingInput entry."""
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


async def _add_identifier(session, patient_pk, org_id, i, created_by) -> None:
    """Insert one PatientIdentifier (+ its type_codings)."""
    a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
    await _validate_reference(session, org_id, a_type, a_id, "identifier.assigner")
    identifier = PatientIdentifier(
        patient_pk=patient_pk,
        tenant_id=org_id,
        use=i.use,
        type_text=i.type_text,
        system=i.system,
        value=i.value,
        period_start=i.period_start,
        period_end=i.period_end,
        assigner_reference=i.assigner,
        **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
        **_reference_kwargs("assigner", i),
        created_by=created_by,
    )
    session.add(identifier)
    if i.type_coding:
        await session.flush()
        for coding in i.type_coding:
            session.add(
                PatientIdentifierTypeCoding(
                    patient_identifier_id=identifier.id,
                    tenant_id=org_id,
                    **_coding_kwargs(coding, created_by),
                )
            )


async def _add_contact(session, patient_pk, org_id, c, created_by) -> None:
    """Insert one PatientContact (+ relationships, codings, telecoms)."""
    co_type, co_id = (
        _parse_org_ref(c.organization) if c.organization else (None, None)
    )
    await _validate_reference(session, org_id, co_type, co_id, "contact.organization")
    contact = PatientContact(
        patient_pk=patient_pk,
        tenant_id=org_id,
        gender=c.gender,
        name_use=c.name_use,
        name_text=c.name_text,
        name_family=c.name_family,
        name_given=c.name_given,
        name_prefix=c.name_prefix,
        name_suffix=c.name_suffix,
        name_period_start=c.name_period_start,
        name_period_end=c.name_period_end,
        use=c.address_use,
        type=c.address_type,
        text=c.address_text,
        line=c.address_line,
        city=c.address_city,
        district=c.address_district,
        state=c.address_state,
        postal_code=c.address_postal_code,
        country=c.address_country,
        period_start=c.period_start,
        period_end=c.period_end,
        organization_reference=c.organization,
        **_org_ref_kwargs("organization", c.organization, c.organization_display),
        **_reference_kwargs("organization", c),
        created_by=created_by,
    )
    session.add(contact)
    await session.flush()

    for rel in c.relationship or []:
        contact_rel = PatientContactRelationship(
            contact_id=contact.id,
            tenant_id=org_id,
            text=rel.text,
            created_by=created_by,
        )
        session.add(contact_rel)
        if rel.coding:
            await session.flush()
            for coding in rel.coding:
                session.add(
                    PatientContactRelationshipCoding(
                        relationship_id=contact_rel.id,
                        tenant_id=org_id,
                        **_coding_kwargs(coding, created_by),
                    )
                )

    for tel in c.telecom or []:
        session.add(
            PatientContactTelecom(
                contact_id=contact.id,
                tenant_id=org_id,
                system=tel.system,
                value=tel.value,
                use=tel.use,
                rank=tel.rank,
                period_start=tel.period_start,
                period_end=tel.period_end,
                created_by=created_by,
            )
        )


async def _add_communication(session, patient_pk, org_id, c, created_by) -> None:
    """Insert one PatientCommunication (+ language_codings)."""
    communication = PatientCommunication(
        patient_pk=patient_pk,
        tenant_id=org_id,
        language_text=c.language_text,
        preferred=c.preferred,
        created_by=created_by,
    )
    session.add(communication)
    if c.language_coding:
        await session.flush()
        for coding in c.language_coding:
            session.add(
                PatientCommunicationLanguageCoding(
                    patient_communication_id=communication.id,
                    tenant_id=org_id,
                    **_coding_kwargs(coding, created_by),
                )
            )


async def _add_general_practitioner(
    session, patient_pk, org_id, gp, created_by
) -> None:
    """Insert one PatientGeneralPractitioner."""
    ref_type = gp.reference_type
    ref_id = gp.reference_id
    if (not ref_type or not ref_id) and gp.reference:
        ref_type, ref_id = _parse_gp_ref(gp.reference)
    await _validate_reference(
        session, org_id, ref_type, ref_id, "general_practitioner.reference"
    )
    session.add(
        PatientGeneralPractitioner(
            patient_pk=patient_pk,
            tenant_id=org_id,
            reference_reference=gp.reference,
            reference_type=ref_type,
            reference_id=ref_id,
            reference_display=gp.display,
            reference_identifier_system=gp.reference_identifier_system,
            reference_identifier_value=gp.reference_identifier_value,
            reference_identifier_use=gp.reference_identifier_use,
            reference_identifier_type_text=gp.reference_identifier_type_text,
            created_by=created_by,
        )
    )


async def _add_link(session, patient_pk, org_id, lk, created_by) -> None:
    """Insert one PatientLink."""
    other_type = lk.other_type
    other_id = lk.other_id
    if (not other_type or not other_id) and lk.other:
        other_type, other_id = _parse_link_ref(lk.other)
    await _validate_reference(session, org_id, other_type, other_id, "link.other")
    session.add(
        PatientLink(
            patient_pk=patient_pk,
            tenant_id=org_id,
            other_reference=lk.other,
            other_type=other_type,
            other_id=other_id,
            other_display=lk.other_display,
            other_identifier_system=lk.other_identifier_system,
            other_identifier_value=lk.other_identifier_value,
            other_identifier_use=lk.other_identifier_use,
            other_identifier_type_text=lk.other_identifier_type_text,
            type=lk.type,
            created_by=created_by,
        )
    )


class _FullMixin:
    """Atomic nested-write orchestrators for Patient."""

    async def create_full(
        self,
        payload: PatientCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> PatientModel:
        """Create a Patient plus any combination of its sub-resource lists
        atomically in one DB transaction."""
        async with self.session_factory() as session:
            mo_type, mo_id = (
                _parse_org_ref(payload.managing_organization)
                if payload.managing_organization
                else (None, None)
            )
            await _validate_reference(
                session, org_id, mo_type, mo_id, "managing_organization"
            )
            patient = PatientModel(
                tenant_id=org_id,
                created_by=created_by,
                user_id=payload.user_id,
                active=payload.active,
                gender=payload.gender,
                birth_date=payload.birth_date,
                deceased_boolean=payload.deceased_boolean,
                deceased_date_time=payload.deceased_date_time,
                marital_status_text=payload.marital_status_text,
                multiple_birth_boolean=payload.multiple_birth_boolean,
                multiple_birth_integer=payload.multiple_birth_integer,
                managing_organization_reference=payload.managing_organization,
                **_org_ref_kwargs(
                    "managing_organization",
                    payload.managing_organization,
                    payload.managing_organization_display,
                ),
                **_reference_kwargs("managing_organization", payload),
                extension=payload.extension or [],
            )
            session.add(patient)
            await session.flush()

            for mc in payload.marital_status_coding or []:
                session.add(
                    PatientMaritalStatusCoding(
                        patient_pk=patient.id,
                        tenant_id=org_id,
                        **_coding_kwargs(mc, created_by),
                    )
                )

            for i in payload.identifier or []:
                await _add_identifier(session, patient.id, org_id, i, created_by)

            for n in payload.name or []:
                session.add(
                    PatientName(
                        patient_pk=patient.id,
                        tenant_id=org_id,
                        use=n.use,
                        text=n.text,
                        family=n.family,
                        given=n.given,
                        prefix=n.prefix,
                        suffix=n.suffix,
                        period_start=n.period_start,
                        period_end=n.period_end,
                        created_by=created_by,
                    )
                )

            for t in payload.telecom or []:
                session.add(
                    PatientTelecom(
                        patient_pk=patient.id,
                        tenant_id=org_id,
                        system=t.system,
                        value=t.value,
                        use=t.use,
                        rank=t.rank,
                        period_start=t.period_start,
                        period_end=t.period_end,
                        created_by=created_by,
                    )
                )

            for a in payload.address or []:
                session.add(
                    PatientAddress(
                        patient_pk=patient.id,
                        tenant_id=org_id,
                        use=a.use,
                        type=a.type,
                        text=a.text,
                        line=a.line,
                        city=a.city,
                        district=a.district,
                        state=a.state,
                        postal_code=a.postal_code,
                        country=a.country,
                        period_start=a.period_start,
                        period_end=a.period_end,
                        created_by=created_by,
                    )
                )

            for ph in payload.photo or []:
                session.add(
                    PatientPhoto(
                        patient_pk=patient.id,
                        tenant_id=org_id,
                        content_type=ph.content_type,
                        language=ph.language,
                        data=ph.data,
                        url=ph.url,
                        size=ph.size,
                        hash=ph.hash,
                        title=ph.title,
                        creation=ph.creation,
                        created_by=created_by,
                    )
                )

            for c in payload.contact or []:
                await _add_contact(session, patient.id, org_id, c, created_by)

            for comm in payload.communication or []:
                await _add_communication(
                    session, patient.id, org_id, comm, created_by
                )

            for gp in payload.general_practitioner or []:
                await _add_general_practitioner(
                    session, patient.id, org_id, gp, created_by
                )

            for lk in payload.link or []:
                await _add_link(session, patient.id, org_id, lk, created_by)

            try:
                await session.commit()
                await session.refresh(patient)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient.patient_id)

    async def patch_full(
        self,
        patient_id: int,
        payload: PatientPatchSchema,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Patches core scalar fields and replaces any supplied sub-resource
        lists wholesale. Lists omitted from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(
                PatientModel.patient_id == patient_id
            )
            patient = (await session.execute(stmt)).scalars().first()
            if not patient:
                return None

            _SUB = {
                "identifier",
                "name",
                "telecom",
                "address",
                "photo",
                "contact",
                "communication",
                "general_practitioner",
                "link",
                "marital_status_coding",
            }
            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                if field in _SUB:
                    continue

                if field == "managing_organization":
                    patient.managing_organization_reference = value
                    if value is not None:
                        mo_type, mo_id = _parse_org_ref(value)
                        await _validate_reference(
                            session,
                            patient.tenant_id,
                            mo_type,
                            mo_id,
                            "managingOrganization",
                        )
                        patient.managing_organization_type = mo_type
                        patient.managing_organization_id = mo_id
                    else:
                        patient.managing_organization_type = None
                        patient.managing_organization_id = None
                else:
                    setattr(patient, field, value)

            if updated_by is not None:
                patient.updated_by = updated_by

            if payload.marital_status_coding is not None:
                await session.execute(
                    delete(PatientMaritalStatusCoding).where(
                        PatientMaritalStatusCoding.patient_pk == patient.id
                    )
                )
                for mc in payload.marital_status_coding:
                    session.add(
                        PatientMaritalStatusCoding(
                            patient_pk=patient.id,
                            tenant_id=patient.tenant_id,
                            **_coding_kwargs(mc, updated_by),
                        )
                    )

            if payload.identifier is not None:
                ident_ids = list(
                    (
                        await session.execute(
                            select(PatientIdentifier.id).where(
                                PatientIdentifier.patient_pk == patient.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if ident_ids:
                    await session.execute(
                        delete(PatientIdentifierTypeCoding).where(
                            PatientIdentifierTypeCoding.patient_identifier_id.in_(
                                ident_ids
                            )
                        )
                    )
                    await session.execute(
                        delete(PatientIdentifier).where(
                            PatientIdentifier.id.in_(ident_ids)
                        )
                    )
                for i in payload.identifier:
                    await _add_identifier(
                        session, patient.id, patient.tenant_id, i, updated_by
                    )

            if payload.name is not None:
                await session.execute(
                    delete(PatientName).where(
                        PatientName.patient_pk == patient.id
                    )
                )
                for n in payload.name:
                    session.add(
                        PatientName(
                            patient_pk=patient.id,
                            tenant_id=patient.tenant_id,
                            use=n.use,
                            text=n.text,
                            family=n.family,
                            given=n.given,
                            prefix=n.prefix,
                            suffix=n.suffix,
                            period_start=n.period_start,
                            period_end=n.period_end,
                            created_by=updated_by,
                        )
                    )

            if payload.telecom is not None:
                await session.execute(
                    delete(PatientTelecom).where(
                        PatientTelecom.patient_pk == patient.id
                    )
                )
                for t in payload.telecom:
                    session.add(
                        PatientTelecom(
                            patient_pk=patient.id,
                            tenant_id=patient.tenant_id,
                            system=t.system,
                            value=t.value,
                            use=t.use,
                            rank=t.rank,
                            period_start=t.period_start,
                            period_end=t.period_end,
                            created_by=updated_by,
                        )
                    )

            if payload.address is not None:
                await session.execute(
                    delete(PatientAddress).where(
                        PatientAddress.patient_pk == patient.id
                    )
                )
                for a in payload.address:
                    session.add(
                        PatientAddress(
                            patient_pk=patient.id,
                            tenant_id=patient.tenant_id,
                            use=a.use,
                            type=a.type,
                            text=a.text,
                            line=a.line,
                            city=a.city,
                            district=a.district,
                            state=a.state,
                            postal_code=a.postal_code,
                            country=a.country,
                            period_start=a.period_start,
                            period_end=a.period_end,
                            created_by=updated_by,
                        )
                    )

            if payload.photo is not None:
                await session.execute(
                    delete(PatientPhoto).where(
                        PatientPhoto.patient_pk == patient.id
                    )
                )
                for ph in payload.photo:
                    session.add(
                        PatientPhoto(
                            patient_pk=patient.id,
                            tenant_id=patient.tenant_id,
                            content_type=ph.content_type,
                            language=ph.language,
                            data=ph.data,
                            url=ph.url,
                            size=ph.size,
                            hash=ph.hash,
                            title=ph.title,
                            creation=ph.creation,
                            created_by=updated_by,
                        )
                    )

            if payload.contact is not None:
                contact_ids = list(
                    (
                        await session.execute(
                            select(PatientContact.id).where(
                                PatientContact.patient_pk == patient.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if contact_ids:
                    await session.execute(
                        delete(PatientContactTelecom).where(
                            PatientContactTelecom.contact_id.in_(contact_ids)
                        )
                    )
                    rel_ids = list(
                        (
                            await session.execute(
                                select(PatientContactRelationship.id).where(
                                    PatientContactRelationship.contact_id.in_(
                                        contact_ids
                                    )
                                )
                            )
                        )
                        .scalars()
                        .all()
                    )
                    if rel_ids:
                        await session.execute(
                            delete(PatientContactRelationshipCoding).where(
                                PatientContactRelationshipCoding.relationship_id.in_(
                                    rel_ids
                                )
                            )
                        )
                        await session.execute(
                            delete(PatientContactRelationship).where(
                                PatientContactRelationship.id.in_(rel_ids)
                            )
                        )
                    await session.execute(
                        delete(PatientContact).where(
                            PatientContact.id.in_(contact_ids)
                        )
                    )
                for c in payload.contact:
                    await _add_contact(
                        session, patient.id, patient.tenant_id, c, updated_by
                    )

            if payload.communication is not None:
                comm_ids = list(
                    (
                        await session.execute(
                            select(PatientCommunication.id).where(
                                PatientCommunication.patient_pk == patient.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if comm_ids:
                    await session.execute(
                        delete(PatientCommunicationLanguageCoding).where(
                            PatientCommunicationLanguageCoding.patient_communication_id.in_(
                                comm_ids
                            )
                        )
                    )
                    await session.execute(
                        delete(PatientCommunication).where(
                            PatientCommunication.id.in_(comm_ids)
                        )
                    )
                for comm in payload.communication:
                    await _add_communication(
                        session, patient.id, patient.tenant_id, comm, updated_by
                    )

            if payload.general_practitioner is not None:
                await session.execute(
                    delete(PatientGeneralPractitioner).where(
                        PatientGeneralPractitioner.patient_pk == patient.id
                    )
                )
                for gp in payload.general_practitioner:
                    await _add_general_practitioner(
                        session, patient.id, patient.tenant_id, gp, updated_by
                    )

            if payload.link is not None:
                await session.execute(
                    delete(PatientLink).where(
                        PatientLink.patient_pk == patient.id
                    )
                )
                for lk in payload.link:
                    await _add_link(
                        session, patient.id, patient.tenant_id, lk, updated_by
                    )

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient.patient_id)
