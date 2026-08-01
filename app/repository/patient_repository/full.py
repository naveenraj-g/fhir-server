from sqlalchemy import delete, select

from app.models.patient.patient import (
    PatientAddress,
    PatientCommunication,
    PatientContact,
    PatientContactRelationship,
    PatientContactTelecom,
    PatientGeneralPractitioner,
    PatientIdentifier,
    PatientLink,
    PatientModel,
    PatientName,
    PatientPhoto,
    PatientTelecom,
)
from app.schemas.patient import PatientFullCreateSchema, PatientFullPatchSchema

from ._shared import (
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch all 9 sub-resource types (plus core scalar fields) in one
    transaction."""

    async def create_full(
        self,
        payload: PatientFullCreateSchema,
        user_id: str | None,
        org_id: str,
        created_by: str | None = None,
    ) -> PatientModel:
        """Create a Patient plus any combination of its 9 sub-resource lists,
        atomically in one DB transaction (one commit at the end — if any
        insert fails, everything rolls back). Every list on the payload is
        optional; only the ones supplied get inserted."""
        mo_type, mo_id = (
            _parse_org_ref(payload.managing_organization)
            if payload.managing_organization
            else (None, None)
        )
        async with self.session_factory() as session:
            await _validate_reference(session, org_id, mo_type, mo_id, "managingOrganization")
            patient = PatientModel(
                user_id=user_id,
                org_id=org_id,
                active=payload.active,
                gender=payload.gender,
                birth_date=payload.birth_date,
                deceased_boolean=payload.deceased_boolean,
                deceased_datetime=payload.deceased_datetime,
                marital_status_system=payload.marital_status_system,
                marital_status_version=payload.marital_status_version,
                marital_status_code=payload.marital_status_code,
                marital_status_display=payload.marital_status_display,
                marital_status_text=payload.marital_status_text,
                marital_status_user_selected=payload.marital_status_user_selected,
                multiple_birth_boolean=payload.multiple_birth_boolean,
                multiple_birth_integer=payload.multiple_birth_integer,
                **_org_ref_kwargs(
                    "managing_organization",
                    payload.managing_organization,
                    payload.managing_organization_display,
                ),
                **_reference_kwargs("managing_organization", payload),
                created_by=created_by,
            )
            session.add(patient)
            await session.flush()

            if payload.names:
                for n in payload.names:
                    session.add(
                        PatientName(
                            patient_id=patient.id,
                            org_id=org_id,
                            use=n.use,
                            text=n.text,
                            family=n.family,
                            given=", ".join(n.given) if n.given else None,
                            prefix=", ".join(n.prefix) if n.prefix else None,
                            suffix=", ".join(n.suffix) if n.suffix else None,
                            period_start=n.period_start,
                            period_end=n.period_end,
                            created_by=created_by,
                        )
                    )

            if payload.identifiers:
                for i in payload.identifiers:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(session, org_id, a_type, a_id, "identifier.assigner")
                    session.add(
                        PatientIdentifier(
                            patient_id=patient.id,
                            org_id=org_id,
                            use=i.use,
                            type_system=i.type_system,
                            type_version=i.type_version,
                            type_code=i.type_code,
                            type_display=i.type_display,
                            type_text=i.type_text,
                            type_user_selected=i.type_user_selected,
                            system=i.system,
                            value=i.value,
                            period_start=i.period_start,
                            period_end=i.period_end,
                            **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                            **_reference_kwargs("assigner", i),
                            created_by=created_by,
                        )
                    )

            if payload.telecom:
                for t in payload.telecom:
                    session.add(
                        PatientTelecom(
                            patient_id=patient.id,
                            org_id=org_id,
                            system=t.system,
                            value=t.value,
                            use=t.use,
                            rank=t.rank,
                            period_start=t.period_start,
                            period_end=t.period_end,
                            created_by=created_by,
                        )
                    )

            if payload.addresses:
                for a in payload.addresses:
                    session.add(
                        PatientAddress(
                            patient_id=patient.id,
                            org_id=org_id,
                            use=a.use,
                            type=a.type,
                            text=a.text,
                            line=", ".join(a.line) if a.line else None,
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

            if payload.photos:
                for p in payload.photos:
                    session.add(
                        PatientPhoto(
                            patient_id=patient.id,
                            org_id=org_id,
                            content_type=p.content_type,
                            language=p.language,
                            data=p.data,
                            url=p.url,
                            size=p.size,
                            hash=p.hash,
                            title=p.title,
                            creation=p.creation,
                            created_by=created_by,
                        )
                    )

            if payload.contacts:
                for c in payload.contacts:
                    co_type, co_id = (
                        _parse_org_ref(c.organization) if c.organization else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, co_type, co_id, "contact.organization"
                    )
                    contact = PatientContact(
                        patient_id=patient.id,
                        org_id=org_id,
                        name_use=c.name_use,
                        name_text=c.name_text,
                        name_family=c.name_family,
                        name_given=", ".join(c.name_given) if c.name_given else None,
                        name_prefix=", ".join(c.name_prefix) if c.name_prefix else None,
                        name_suffix=", ".join(c.name_suffix) if c.name_suffix else None,
                        name_period_start=c.name_period_start,
                        name_period_end=c.name_period_end,
                        address_use=c.address_use,
                        address_type=c.address_type,
                        address_text=c.address_text,
                        address_line=", ".join(c.address_line)
                        if c.address_line
                        else None,
                        address_city=c.address_city,
                        address_district=c.address_district,
                        address_state=c.address_state,
                        address_postal_code=c.address_postal_code,
                        address_country=c.address_country,
                        address_period_start=c.address_period_start,
                        address_period_end=c.address_period_end,
                        gender=c.gender,
                        **_org_ref_kwargs(
                            "organization", c.organization, c.organization_display
                        ),
                        **_reference_kwargs("organization", c),
                        period_start=c.period_start,
                        period_end=c.period_end,
                        created_by=created_by,
                    )
                    session.add(contact)
                    await session.flush()

                    if c.relationship:
                        for r in c.relationship:
                            session.add(
                                PatientContactRelationship(
                                    contact_id=contact.id,
                                    org_id=org_id,
                                    coding_system=r.coding_system,
                                    coding_version=r.coding_version,
                                    coding_code=r.coding_code,
                                    coding_display=r.coding_display,
                                    text=r.text,
                                    coding_user_selected=r.coding_user_selected,
                                    created_by=created_by,
                                )
                            )

                    if c.telecom:
                        for t in c.telecom:
                            session.add(
                                PatientContactTelecom(
                                    contact_id=contact.id,
                                    org_id=org_id,
                                    system=t.system,
                                    value=t.value,
                                    use=t.use,
                                    rank=t.rank,
                                    period_start=t.period_start,
                                    period_end=t.period_end,
                                    created_by=created_by,
                                )
                            )

            if payload.communications:
                for cm in payload.communications:
                    session.add(
                        PatientCommunication(
                            patient_id=patient.id,
                            org_id=org_id,
                            language_system=cm.language_system,
                            language_version=cm.language_version,
                            language_code=cm.language_code,
                            language_display=cm.language_display,
                            language_text=cm.language_text,
                            language_user_selected=cm.language_user_selected,
                            preferred=cm.preferred,
                            created_by=created_by,
                        )
                    )

            if payload.general_practitioners:
                for gp in payload.general_practitioners:
                    await _validate_reference(
                        session, org_id, gp.reference_type, gp.reference_id, "generalPractitioner"
                    )
                    session.add(
                        PatientGeneralPractitioner(
                            patient_id=patient.id,
                            org_id=org_id,
                            reference_type=gp.reference_type,
                            reference_id=gp.reference_id,
                            reference_display=gp.reference_display,
                            **_reference_kwargs("reference", gp),
                            created_by=created_by,
                        )
                    )

            if payload.links:
                for lk in payload.links:
                    await _validate_reference(
                        session, org_id, lk.other_type, lk.other_id, "link.other"
                    )
                    session.add(
                        PatientLink(
                            patient_id=patient.id,
                            org_id=org_id,
                            other_type=lk.other_type,
                            other_id=lk.other_id,
                            other_display=lk.other_display,
                            **_reference_kwargs("other", lk),
                            type=lk.type,
                            created_by=created_by,
                        )
                    )

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
        payload: PatientFullPatchSchema,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Patches core scalar fields (same semantics as patch()) and, for
        each sub-resource list that is supplied — even `[]` — atomically
        deletes all existing rows and inserts the new ones. Lists omitted
        from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(PatientModel.patient_id == patient_id)
            patient = (await session.execute(stmt)).scalars().first()
            if not patient:
                return None

            _SUB = {
                "names",
                "identifiers",
                "telecom",
                "addresses",
                "photos",
                "contacts",
                "communications",
                "general_practitioners",
                "links",
            }
            for field, value in payload.model_dump(exclude_unset=True).items():
                if field in _SUB:
                    continue
                if field == "managing_organization":
                    if value is not None:
                        mo_type, mo_id = _parse_org_ref(value)
                        await _validate_reference(
                            session, patient.org_id, mo_type, mo_id, "managingOrganization"
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

            if payload.names is not None:
                await session.execute(
                    delete(PatientName).where(PatientName.patient_id == patient.id)
                )
                for n in payload.names:
                    session.add(
                        PatientName(
                            patient_id=patient.id,
                            org_id=patient.org_id,
                            use=n.use,
                            text=n.text,
                            family=n.family,
                            given=", ".join(n.given) if n.given else None,
                            prefix=", ".join(n.prefix) if n.prefix else None,
                            suffix=", ".join(n.suffix) if n.suffix else None,
                            period_start=n.period_start,
                            period_end=n.period_end,
                            created_by=updated_by,
                        )
                    )

            if payload.identifiers is not None:
                await session.execute(
                    delete(PatientIdentifier).where(
                        PatientIdentifier.patient_id == patient.id
                    )
                )
                for i in payload.identifiers:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, patient.org_id, a_type, a_id, "identifier.assigner"
                    )
                    session.add(
                        PatientIdentifier(
                            patient_id=patient.id,
                            org_id=patient.org_id,
                            use=i.use,
                            type_system=i.type_system,
                            type_version=i.type_version,
                            type_code=i.type_code,
                            type_display=i.type_display,
                            type_text=i.type_text,
                            type_user_selected=i.type_user_selected,
                            system=i.system,
                            value=i.value,
                            period_start=i.period_start,
                            period_end=i.period_end,
                            **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                            **_reference_kwargs("assigner", i),
                            created_by=updated_by,
                        )
                    )

            if payload.telecom is not None:
                await session.execute(
                    delete(PatientTelecom).where(
                        PatientTelecom.patient_id == patient.id
                    )
                )
                for t in payload.telecom:
                    session.add(
                        PatientTelecom(
                            patient_id=patient.id,
                            org_id=patient.org_id,
                            system=t.system,
                            value=t.value,
                            use=t.use,
                            rank=t.rank,
                            period_start=t.period_start,
                            period_end=t.period_end,
                            created_by=updated_by,
                        )
                    )

            if payload.addresses is not None:
                await session.execute(
                    delete(PatientAddress).where(
                        PatientAddress.patient_id == patient.id
                    )
                )
                for a in payload.addresses:
                    session.add(
                        PatientAddress(
                            patient_id=patient.id,
                            org_id=patient.org_id,
                            use=a.use,
                            type=a.type,
                            text=a.text,
                            line=", ".join(a.line) if a.line else None,
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

            if payload.photos is not None:
                await session.execute(
                    delete(PatientPhoto).where(PatientPhoto.patient_id == patient.id)
                )
                for p in payload.photos:
                    session.add(
                        PatientPhoto(
                            patient_id=patient.id,
                            org_id=patient.org_id,
                            content_type=p.content_type,
                            language=p.language,
                            data=p.data,
                            url=p.url,
                            size=p.size,
                            hash=p.hash,
                            title=p.title,
                            creation=p.creation,
                            created_by=updated_by,
                        )
                    )

            if payload.contacts is not None:
                contact_ids = list(
                    (
                        await session.execute(
                            select(PatientContact.id).where(
                                PatientContact.patient_id == patient.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if contact_ids:
                    await session.execute(
                        delete(PatientContactRelationship).where(
                            PatientContactRelationship.contact_id.in_(contact_ids)
                        )
                    )
                    await session.execute(
                        delete(PatientContactTelecom).where(
                            PatientContactTelecom.contact_id.in_(contact_ids)
                        )
                    )
                await session.execute(
                    delete(PatientContact).where(
                        PatientContact.patient_id == patient.id
                    )
                )
                for c in payload.contacts:
                    co_type, co_id = (
                        _parse_org_ref(c.organization) if c.organization else (None, None)
                    )
                    await _validate_reference(
                        session, patient.org_id, co_type, co_id, "contact.organization"
                    )
                    contact = PatientContact(
                        patient_id=patient.id,
                        org_id=patient.org_id,
                        name_use=c.name_use,
                        name_text=c.name_text,
                        name_family=c.name_family,
                        name_given=", ".join(c.name_given) if c.name_given else None,
                        name_prefix=", ".join(c.name_prefix) if c.name_prefix else None,
                        name_suffix=", ".join(c.name_suffix) if c.name_suffix else None,
                        address_use=c.address_use,
                        address_type=c.address_type,
                        address_text=c.address_text,
                        address_line=", ".join(c.address_line)
                        if c.address_line
                        else None,
                        address_city=c.address_city,
                        address_district=c.address_district,
                        address_state=c.address_state,
                        address_postal_code=c.address_postal_code,
                        address_country=c.address_country,
                        address_period_start=c.address_period_start,
                        address_period_end=c.address_period_end,
                        gender=c.gender,
                        **_org_ref_kwargs(
                            "organization", c.organization, c.organization_display
                        ),
                        **_reference_kwargs("organization", c),
                        period_start=c.period_start,
                        period_end=c.period_end,
                        created_by=updated_by,
                    )
                    session.add(contact)
                    await session.flush()
                    if c.relationship:
                        for r in c.relationship:
                            session.add(
                                PatientContactRelationship(
                                    contact_id=contact.id,
                                    org_id=patient.org_id,
                                    coding_system=r.coding_system,
                                    coding_version=r.coding_version,
                                    coding_code=r.coding_code,
                                    coding_display=r.coding_display,
                                    text=r.text,
                                    coding_user_selected=r.coding_user_selected,
                                    created_by=updated_by,
                                )
                            )
                    if c.telecom:
                        for t in c.telecom:
                            session.add(
                                PatientContactTelecom(
                                    contact_id=contact.id,
                                    org_id=patient.org_id,
                                    system=t.system,
                                    value=t.value,
                                    use=t.use,
                                    rank=t.rank,
                                    period_start=t.period_start,
                                    period_end=t.period_end,
                                    created_by=updated_by,
                                )
                            )

            if payload.communications is not None:
                await session.execute(
                    delete(PatientCommunication).where(
                        PatientCommunication.patient_id == patient.id
                    )
                )
                for cm in payload.communications:
                    session.add(
                        PatientCommunication(
                            patient_id=patient.id,
                            org_id=patient.org_id,
                            language_system=cm.language_system,
                            language_version=cm.language_version,
                            language_code=cm.language_code,
                            language_display=cm.language_display,
                            language_text=cm.language_text,
                            language_user_selected=cm.language_user_selected,
                            preferred=cm.preferred,
                            created_by=updated_by,
                        )
                    )

            if payload.general_practitioners is not None:
                await session.execute(
                    delete(PatientGeneralPractitioner).where(
                        PatientGeneralPractitioner.patient_id == patient.id
                    )
                )
                for gp in payload.general_practitioners:
                    await _validate_reference(
                        session,
                        patient.org_id,
                        gp.reference_type,
                        gp.reference_id,
                        "generalPractitioner",
                    )
                    session.add(
                        PatientGeneralPractitioner(
                            patient_id=patient.id,
                            org_id=patient.org_id,
                            reference_type=gp.reference_type,
                            reference_id=gp.reference_id,
                            reference_display=gp.reference_display,
                            **_reference_kwargs("reference", gp),
                            created_by=updated_by,
                        )
                    )

            if payload.links is not None:
                await session.execute(
                    delete(PatientLink).where(PatientLink.patient_id == patient.id)
                )
                for lk in payload.links:
                    await _validate_reference(
                        session, patient.org_id, lk.other_type, lk.other_id, "link.other"
                    )
                    session.add(
                        PatientLink(
                            patient_id=patient.id,
                            org_id=patient.org_id,
                            other_type=lk.other_type,
                            other_id=lk.other_id,
                            other_display=lk.other_display,
                            **_reference_kwargs("other", lk),
                            type=lk.type,
                            created_by=updated_by,
                        )
                    )

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)
