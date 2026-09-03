from app.core.logging import get_logger
from sqlalchemy import delete
from sqlalchemy.future import select

from app.models.practitioner import (
    PractitionerAddress,
    PractitionerCommunication,
    PractitionerIdentifier,
    PractitionerModel,
    PractitionerName,
    PractitionerPhoto,
    PractitionerQualification,
    PractitionerQualificationIdentifier,
    PractitionerTelecom,
)
from app.schemas.practitioner import (
    PractitionerFullCreateSchema,
    PractitionerFullPatchSchema,
)

from ._shared import (
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)


logger = get_logger(__name__)


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch all 7 sub-resource types (plus core scalar fields) in one
    transaction."""

    async def create_full(
        self,
        payload: PractitionerFullCreateSchema,
        user_id: str | None = None,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PractitionerModel:
        async with self.session_factory() as session:
            practitioner = PractitionerModel(
                user_id=user_id,
                org_id=org_id,
                active=payload.active,
                gender=payload.gender,
                birth_date=payload.birth_date,
                created_by=created_by,
            )
            session.add(practitioner)
            await session.flush()

            if payload.names:
                for n in payload.names:
                    session.add(
                        PractitionerName(
                            practitioner_id=practitioner.id,
                            org_id=org_id,
                            use=n.use,
                            text=n.text,
                            family=n.family,
                            given=",".join(n.given) if n.given else None,
                            prefix=",".join(n.prefix) if n.prefix else None,
                            suffix=",".join(n.suffix) if n.suffix else None,
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
                    await _validate_reference(
                        session, org_id, a_type, a_id, "identifier.assigner"
                    )
                    session.add(
                        PractitionerIdentifier(
                            practitioner_id=practitioner.id,
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
                            **_org_ref_kwargs(
                                "assigner", i.assigner, i.assigner_display
                            ),
                            **_reference_kwargs("assigner", i),
                            created_by=created_by,
                        )
                    )

            if payload.telecom:
                for t in payload.telecom:
                    session.add(
                        PractitionerTelecom(
                            practitioner_id=practitioner.id,
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
                        PractitionerAddress(
                            practitioner_id=practitioner.id,
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
                        PractitionerPhoto(
                            practitioner_id=practitioner.id,
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

            if payload.qualifications:
                for q in payload.qualifications:
                    i_type, i_id = (
                        _parse_org_ref(q.issuer) if q.issuer else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, i_type, i_id, "qualification.issuer"
                    )
                    qualification = PractitionerQualification(
                        practitioner_id=practitioner.id,
                        org_id=org_id,
                        code_system=q.code_system,
                        code_code=q.code_code,
                        code_display=q.code_display,
                        code_text=q.code_text,
                        period_start=q.period_start,
                        period_end=q.period_end,
                        **_org_ref_kwargs("issuer", q.issuer, q.issuer_display),
                        **_reference_kwargs("issuer", q),
                        created_by=created_by,
                    )
                    session.add(qualification)
                    await session.flush()

                    if q.identifier:
                        for qi in q.identifier:
                            qa_type, qa_id = (
                                _parse_org_ref(qi.assigner)
                                if qi.assigner
                                else (None, None)
                            )
                            await _validate_reference(
                                session,
                                org_id,
                                qa_type,
                                qa_id,
                                "qualification.identifier.assigner",
                            )
                            session.add(
                                PractitionerQualificationIdentifier(
                                    qualification_id=qualification.id,
                                    org_id=org_id,
                                    use=qi.use,
                                    type_system=qi.type_system,
                                    type_version=qi.type_version,
                                    type_code=qi.type_code,
                                    type_display=qi.type_display,
                                    type_text=qi.type_text,
                                    type_user_selected=qi.type_user_selected,
                                    system=qi.system,
                                    value=qi.value,
                                    period_start=qi.period_start,
                                    period_end=qi.period_end,
                                    **_org_ref_kwargs(
                                        "assigner", qi.assigner, qi.assigner_display
                                    ),
                                    **_reference_kwargs("assigner", qi),
                                    created_by=created_by,
                                )
                            )

            if payload.communications:
                for cm in payload.communications:
                    session.add(
                        PractitionerCommunication(
                            practitioner_id=practitioner.id,
                            org_id=org_id,
                            language_system=cm.language_system,
                            language_version=cm.language_version,
                            language_code=cm.language_code,
                            language_display=cm.language_display,
                            language_text=cm.language_text,
                            language_user_selected=cm.language_user_selected,
                            created_by=created_by,
                        )
                    )

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
        payload: PractitionerFullPatchSchema,
        updated_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(
                PractitionerModel.practitioner_id == practitioner_id
            )
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None

            _SUB = {
                "names",
                "identifiers",
                "telecom",
                "addresses",
                "photos",
                "qualifications",
                "communications",
            }
            for field, value in payload.model_dump(exclude_unset=True).items():
                if field in _SUB:
                    continue
                setattr(practitioner, field, value)
            if updated_by is not None:
                practitioner.updated_by = updated_by

            if payload.names is not None:
                await session.execute(
                    delete(PractitionerName).where(
                        PractitionerName.practitioner_id == practitioner.id
                    )
                )
                for n in payload.names:
                    session.add(
                        PractitionerName(
                            practitioner_id=practitioner.id,
                            org_id=practitioner.org_id,
                            use=n.use,
                            text=n.text,
                            family=n.family,
                            given=",".join(n.given) if n.given else None,
                            prefix=",".join(n.prefix) if n.prefix else None,
                            suffix=",".join(n.suffix) if n.suffix else None,
                            period_start=n.period_start,
                            period_end=n.period_end,
                            created_by=updated_by,
                        )
                    )

            if payload.identifiers is not None:
                await session.execute(
                    delete(PractitionerIdentifier).where(
                        PractitionerIdentifier.practitioner_id == practitioner.id
                    )
                )
                for i in payload.identifiers:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session,
                        practitioner.org_id,
                        a_type,
                        a_id,
                        "identifier.assigner",
                    )
                    session.add(
                        PractitionerIdentifier(
                            practitioner_id=practitioner.id,
                            org_id=practitioner.org_id,
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
                            **_org_ref_kwargs(
                                "assigner", i.assigner, i.assigner_display
                            ),
                            **_reference_kwargs("assigner", i),
                            created_by=updated_by,
                        )
                    )

            if payload.telecom is not None:
                await session.execute(
                    delete(PractitionerTelecom).where(
                        PractitionerTelecom.practitioner_id == practitioner.id
                    )
                )
                for t in payload.telecom:
                    session.add(
                        PractitionerTelecom(
                            practitioner_id=practitioner.id,
                            org_id=practitioner.org_id,
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
                    delete(PractitionerAddress).where(
                        PractitionerAddress.practitioner_id == practitioner.id
                    )
                )
                for a in payload.addresses:
                    session.add(
                        PractitionerAddress(
                            practitioner_id=practitioner.id,
                            org_id=practitioner.org_id,
                            use=a.use,
                            type=a.type,
                            text=a.text,
                            line=",".join(a.line) if a.line else None,
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
                    delete(PractitionerPhoto).where(
                        PractitionerPhoto.practitioner_id == practitioner.id
                    )
                )
                for p in payload.photos:
                    session.add(
                        PractitionerPhoto(
                            practitioner_id=practitioner.id,
                            org_id=practitioner.org_id,
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

            if payload.qualifications is not None:
                qual_ids = list(
                    (
                        await session.execute(
                            select(PractitionerQualification.id).where(
                                PractitionerQualification.practitioner_id
                                == practitioner.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if qual_ids:
                    await session.execute(
                        delete(PractitionerQualificationIdentifier).where(
                            PractitionerQualificationIdentifier.qualification_id.in_(
                                qual_ids
                            )
                        )
                    )
                await session.execute(
                    delete(PractitionerQualification).where(
                        PractitionerQualification.practitioner_id == practitioner.id
                    )
                )
                for q in payload.qualifications:
                    i_type, i_id = (
                        _parse_org_ref(q.issuer) if q.issuer else (None, None)
                    )
                    await _validate_reference(
                        session,
                        practitioner.org_id,
                        i_type,
                        i_id,
                        "qualification.issuer",
                    )
                    qualification = PractitionerQualification(
                        practitioner_id=practitioner.id,
                        org_id=practitioner.org_id,
                        code_system=q.code_system,
                        code_code=q.code_code,
                        code_display=q.code_display,
                        code_text=q.code_text,
                        period_start=q.period_start,
                        period_end=q.period_end,
                        **_org_ref_kwargs("issuer", q.issuer, q.issuer_display),
                        **_reference_kwargs("issuer", q),
                        created_by=updated_by,
                    )
                    session.add(qualification)
                    await session.flush()
                    if q.identifier:
                        for qi in q.identifier:
                            qa_type, qa_id = (
                                _parse_org_ref(qi.assigner)
                                if qi.assigner
                                else (None, None)
                            )
                            await _validate_reference(
                                session,
                                practitioner.org_id,
                                qa_type,
                                qa_id,
                                "qualification.identifier.assigner",
                            )
                            session.add(
                                PractitionerQualificationIdentifier(
                                    qualification_id=qualification.id,
                                    org_id=practitioner.org_id,
                                    use=qi.use,
                                    type_system=qi.type_system,
                                    type_version=qi.type_version,
                                    type_code=qi.type_code,
                                    type_display=qi.type_display,
                                    type_text=qi.type_text,
                                    type_user_selected=qi.type_user_selected,
                                    system=qi.system,
                                    value=qi.value,
                                    period_start=qi.period_start,
                                    period_end=qi.period_end,
                                    **_org_ref_kwargs(
                                        "assigner", qi.assigner, qi.assigner_display
                                    ),
                                    **_reference_kwargs("assigner", qi),
                                    created_by=updated_by,
                                )
                            )

            if payload.communications is not None:
                await session.execute(
                    delete(PractitionerCommunication).where(
                        PractitionerCommunication.practitioner_id == practitioner.id
                    )
                )
                for cm in payload.communications:
                    session.add(
                        PractitionerCommunication(
                            practitioner_id=practitioner.id,
                            org_id=practitioner.org_id,
                            language_system=cm.language_system,
                            language_version=cm.language_version,
                            language_code=cm.language_code,
                            language_display=cm.language_display,
                            language_text=cm.language_text,
                            language_user_selected=cm.language_user_selected,
                            created_by=updated_by,
                        )
                    )

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            # Which sub-resource lists were wholesale replaced. Only the
            # repository knows this — the service sees "a patch happened", and
            # "replaced telecom with 0 rows" vs. "left telecom untouched" is
            # exactly the distinction that turns into a support ticket.
            # model_fields_set is the explicitly-supplied field names, same as
            # model_dump(exclude_unset=True).keys() but without the dump.
            replaced = sorted(_SUB & payload.model_fields_set)
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
