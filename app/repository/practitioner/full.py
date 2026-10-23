from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.practitioner import (
    PractitionerAddress,
    PractitionerCommunication,
    PractitionerCommunicationCoding,
    PractitionerIdentifier,
    PractitionerIdentifierTypeCoding,
    PractitionerModel,
    PractitionerName,
    PractitionerPhoto,
    PractitionerQualification,
    PractitionerQualificationCodeCoding,
    PractitionerQualificationIdentifier,
    PractitionerQualificationIdentifierTypeCoding,
    PractitionerTelecom,
)
from app.schemas.practitioner import PractitionerCreateSchema, PractitionerPatchSchema

from ._shared import (
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

logger = get_logger(__name__)


def _coding_kwargs(coding, created_by: str | None) -> dict:
    """Build constructor kwargs for one app.schemas.datatypes.CodingInput entry,
    targeting any of Practitioner's dedicated coding[] child tables
    (PractitionerIdentifierTypeCoding/PractitionerQualificationCodeCoding/
    PractitionerQualificationIdentifierTypeCoding/
    PractitionerCommunicationCoding) — all share the same shape via
    FhirCodingMixin, so one helper covers all of them."""
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


async def _add_identifier(session, practitioner_pk, org_id, i, created_by) -> None:
    """Insert one PractitionerIdentifier (+ its type_codings) — shared by
    create_full and patch_full."""
    a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
    await _validate_reference(session, org_id, a_type, a_id, "identifier.assigner")
    identifier = PractitionerIdentifier(
        practitioner_pk=practitioner_pk,
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
                PractitionerIdentifierTypeCoding(
                    practitioner_identifier_id=identifier.id,
                    tenant_id=org_id,
                    **_coding_kwargs(coding, created_by),
                )
            )


async def _add_qualification(session, practitioner_pk, org_id, q, created_by) -> None:
    """Insert one PractitionerQualification (+ its identifiers and
    code_codings) — shared by create_full and patch_full."""
    is_type, is_id = _parse_org_ref(q.issuer) if q.issuer else (None, None)
    await _validate_reference(session, org_id, is_type, is_id, "qualification.issuer")
    qualification = PractitionerQualification(
        practitioner_pk=practitioner_pk,
        tenant_id=org_id,
        code_text=q.code_text,
        period_start=q.period_start,
        period_end=q.period_end,
        issuer_reference=q.issuer,
        **_org_ref_kwargs("issuer", q.issuer, q.issuer_display),
        **_reference_kwargs("issuer", q),
        created_by=created_by,
    )
    session.add(qualification)
    await session.flush()

    if q.code_coding:
        for coding in q.code_coding:
            session.add(
                PractitionerQualificationCodeCoding(
                    practitioner_qualification_id=qualification.id,
                    tenant_id=org_id,
                    **_coding_kwargs(coding, created_by),
                )
            )

    for qi in q.identifier or []:
        qa_type, qa_id = (
            _parse_org_ref(qi.assigner) if qi.assigner else (None, None)
        )
        await _validate_reference(
            session, org_id, qa_type, qa_id, "qualification.identifier.assigner"
        )
        q_identifier = PractitionerQualificationIdentifier(
            practitioner_qualification_id=qualification.id,
            tenant_id=org_id,
            use=qi.use,
            type_text=qi.type_text,
            system=qi.system,
            value=qi.value,
            period_start=qi.period_start,
            period_end=qi.period_end,
            assigner_reference=qi.assigner,
            **_org_ref_kwargs("assigner", qi.assigner, qi.assigner_display),
            **_reference_kwargs("assigner", qi),
            created_by=created_by,
        )
        session.add(q_identifier)
        if qi.type_coding:
            await session.flush()
            for coding in qi.type_coding:
                session.add(
                    PractitionerQualificationIdentifierTypeCoding(
                        practitioner_qualification_identifier_id=q_identifier.id,
                        tenant_id=org_id,
                        **_coding_kwargs(coding, created_by),
                    )
                )


async def _add_communication(session, practitioner_pk, org_id, c, created_by) -> None:
    """Insert one PractitionerCommunication (+ its codings) — shared by
    create_full and patch_full."""
    communication = PractitionerCommunication(
        practitioner_pk=practitioner_pk,
        tenant_id=org_id,
        text=c.text,
        created_by=created_by,
    )
    session.add(communication)
    if c.coding:
        await session.flush()
        for coding in c.coding:
            session.add(
                PractitionerCommunicationCoding(
                    practitioner_communication_id=communication.id,
                    tenant_id=org_id,
                    **_coding_kwargs(coding, created_by),
                )
            )


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch all 7 sub-resource types (plus core scalar fields) in one
    transaction."""

    async def create_full(
        self,
        payload: PractitionerCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> PractitionerModel:
        """Create a Practitioner plus any combination of its 7 sub-resource
        lists, atomically in one DB transaction. Every list on the payload
        is optional; only the ones supplied get inserted."""
        async with self.session_factory() as session:
            practitioner = PractitionerModel(
                tenant_id=org_id,
                created_by=created_by,
                user_id=payload.user_id,
                active=payload.active,
                gender=payload.gender,
                birth_date=payload.birth_date,
                extension=payload.extension or [],
            )
            session.add(practitioner)
            await session.flush()

            for i in payload.identifier or []:
                await _add_identifier(session, practitioner.id, org_id, i, created_by)

            for n in payload.name or []:
                session.add(
                    PractitionerName(
                        practitioner_pk=practitioner.id,
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
                    PractitionerTelecom(
                        practitioner_pk=practitioner.id,
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
                    PractitionerAddress(
                        practitioner_pk=practitioner.id,
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
                    PractitionerPhoto(
                        practitioner_pk=practitioner.id,
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

            for q in payload.qualification or []:
                await _add_qualification(
                    session, practitioner.id, org_id, q, created_by
                )

            for c in payload.communication or []:
                await _add_communication(session, practitioner.id, org_id, c, created_by)

            try:
                await session.commit()
                await session.refresh(practitioner)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_practitioner_id(practitioner.practitioner_id)

    async def patch_full(
        self,
        practitioner_id: int,
        payload: PractitionerPatchSchema,
        updated_by: str | None = None,
    ) -> PractitionerModel | None:
        """Patches core scalar fields (same semantics as patch()) and, for
        each sub-resource list that is supplied — even `[]` — atomically
        deletes all existing rows and inserts the new ones. Lists omitted
        from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(
                PractitionerModel.practitioner_id == practitioner_id
            )
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None

            _SUB = {
                "identifier",
                "name",
                "telecom",
                "address",
                "photo",
                "qualification",
                "communication",
            }
            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                if field in _SUB:
                    continue
                setattr(practitioner, field, value)
            if updated_by is not None:
                practitioner.updated_by = updated_by

            if payload.identifier is not None:
                await session.execute(
                    delete(PractitionerIdentifier).where(
                        PractitionerIdentifier.practitioner_pk == practitioner.id
                    )
                )
                for i in payload.identifier:
                    await _add_identifier(
                        session, practitioner.id, practitioner.tenant_id, i, updated_by
                    )

            if payload.name is not None:
                await session.execute(
                    delete(PractitionerName).where(
                        PractitionerName.practitioner_pk == practitioner.id
                    )
                )
                for n in payload.name:
                    session.add(
                        PractitionerName(
                            practitioner_pk=practitioner.id,
                            tenant_id=practitioner.tenant_id,
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
                    delete(PractitionerTelecom).where(
                        PractitionerTelecom.practitioner_pk == practitioner.id
                    )
                )
                for t in payload.telecom:
                    session.add(
                        PractitionerTelecom(
                            practitioner_pk=practitioner.id,
                            tenant_id=practitioner.tenant_id,
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
                    delete(PractitionerAddress).where(
                        PractitionerAddress.practitioner_pk == practitioner.id
                    )
                )
                for a in payload.address:
                    session.add(
                        PractitionerAddress(
                            practitioner_pk=practitioner.id,
                            tenant_id=practitioner.tenant_id,
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
                    delete(PractitionerPhoto).where(
                        PractitionerPhoto.practitioner_pk == practitioner.id
                    )
                )
                for ph in payload.photo:
                    session.add(
                        PractitionerPhoto(
                            practitioner_pk=practitioner.id,
                            tenant_id=practitioner.tenant_id,
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

            if payload.qualification is not None:
                qualification_ids = list(
                    (
                        await session.execute(
                            select(PractitionerQualification.id).where(
                                PractitionerQualification.practitioner_pk
                                == practitioner.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if qualification_ids:
                    identifier_ids = list(
                        (
                            await session.execute(
                                select(PractitionerQualificationIdentifier.id).where(
                                    PractitionerQualificationIdentifier.practitioner_qualification_id.in_(
                                        qualification_ids
                                    )
                                )
                            )
                        )
                        .scalars()
                        .all()
                    )
                    if identifier_ids:
                        await session.execute(
                            delete(PractitionerQualificationIdentifierTypeCoding).where(
                                PractitionerQualificationIdentifierTypeCoding.practitioner_qualification_identifier_id.in_(
                                    identifier_ids
                                )
                            )
                        )
                    await session.execute(
                        delete(PractitionerQualificationIdentifier).where(
                            PractitionerQualificationIdentifier.practitioner_qualification_id.in_(
                                qualification_ids
                            )
                        )
                    )
                    await session.execute(
                        delete(PractitionerQualificationCodeCoding).where(
                            PractitionerQualificationCodeCoding.practitioner_qualification_id.in_(
                                qualification_ids
                            )
                        )
                    )
                await session.execute(
                    delete(PractitionerQualification).where(
                        PractitionerQualification.practitioner_pk == practitioner.id
                    )
                )
                for q in payload.qualification:
                    await _add_qualification(
                        session, practitioner.id, practitioner.tenant_id, q, updated_by
                    )

            if payload.communication is not None:
                communication_ids = list(
                    (
                        await session.execute(
                            select(PractitionerCommunication.id).where(
                                PractitionerCommunication.practitioner_pk
                                == practitioner.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if communication_ids:
                    await session.execute(
                        delete(PractitionerCommunicationCoding).where(
                            PractitionerCommunicationCoding.practitioner_communication_id.in_(
                                communication_ids
                            )
                        )
                    )
                await session.execute(
                    delete(PractitionerCommunication).where(
                        PractitionerCommunication.practitioner_pk == practitioner.id
                    )
                )
                for c in payload.communication:
                    await _add_communication(
                        session, practitioner.id, practitioner.tenant_id, c, updated_by
                    )

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            replaced = sorted(_SUB & set(data.keys()))
            if replaced:
                logger.debug(
                    "Practitioner sub-resource lists replaced",
                    extra={
                        "event": "practitioner.sublists_replaced",
                        "practitioner_id": practitioner_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_practitioner_id(practitioner_id)
