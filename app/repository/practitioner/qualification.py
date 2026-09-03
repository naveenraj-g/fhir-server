from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.practitioner import PractitionerModel, PractitionerQualification, PractitionerQualificationIdentifier
from app.schemas.practitioner import PractitionerQualificationCreate, PractitionerQualificationPatch

from ._shared import _delete_child, _org_ref_kwargs, _parse_org_ref, _reference_kwargs, _validate_reference


class _QualificationMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.qualification
    rows, including the nested qualification.identifier[] grandchildren."""

    async def add_qualification(
        self, practitioner_id: int, payload: PractitionerQualificationCreate, created_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            i_type, i_id = (
                _parse_org_ref(payload.issuer) if payload.issuer else (None, None)
            )
            await _validate_reference(session, practitioner.org_id, i_type, i_id, "qualification.issuer")
            qualification = PractitionerQualification(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                code_system=payload.code_system,
                code_code=payload.code_code,
                code_display=payload.code_display,
                code_text=payload.code_text,
                period_start=payload.period_start,
                period_end=payload.period_end,
                **_org_ref_kwargs("issuer", payload.issuer, payload.issuer_display),
                **_reference_kwargs("issuer", payload),
                created_by=created_by,
            )
            session.add(qualification)
            await session.flush()  # get qualification.id before adding grandchildren

            if payload.identifier:
                for qi in payload.identifier:
                    qa_type, qa_id = (
                        _parse_org_ref(qi.assigner) if qi.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, practitioner.org_id, qa_type, qa_id, "qualification.identifier.assigner"
                    )
                    session.add(PractitionerQualificationIdentifier(
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
                        **_org_ref_kwargs("assigner", qi.assigner, qi.assigner_display),
                        **_reference_kwargs("assigner", qi),
                        created_by=created_by,
                    ))

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

    async def get_qualifications(self, practitioner_id: int) -> list:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return []
            stmt = (
                select(PractitionerQualification)
                .where(PractitionerQualification.practitioner_id == practitioner.id)
                .options(selectinload(PractitionerQualification.identifiers))
            )
            return list((await session.execute(stmt)).scalars().all())

    async def delete_qualification(self, practitioner_id: int, qualification_id: int) -> bool:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return False
            return await _delete_child(session, PractitionerQualification, qualification_id, practitioner.id)

    async def patch_qualification(
        self, practitioner_id: int, qualification_id: int, payload: PractitionerQualificationPatch,
        updated_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return None
            stmt = (
                select(PractitionerQualification)
                .where(
                    PractitionerQualification.id == qualification_id,
                    PractitionerQualification.practitioner_id == practitioner.id,
                )
                .options(selectinload(PractitionerQualification.identifiers))
            )
            qualification = (await session.execute(stmt)).scalars().first()
            if not qualification:
                return None

            data = payload.model_dump(exclude_unset=True, exclude={"identifier", "issuer"})

            if payload.identifier is not None:
                for qi_row in list(qualification.identifiers):
                    await session.delete(qi_row)
                for qi in payload.identifier:
                    qa_type, qa_id = (
                        _parse_org_ref(qi.assigner) if qi.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, practitioner.org_id, qa_type, qa_id, "qualification.identifier.assigner"
                    )
                    session.add(PractitionerQualificationIdentifier(
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
                        **_org_ref_kwargs("assigner", qi.assigner, qi.assigner_display),
                        **_reference_kwargs("assigner", qi),
                        created_by=updated_by,
                    ))

            if "issuer" in payload.model_fields_set:
                if payload.issuer:
                    i_type, i_id = _parse_org_ref(payload.issuer)
                    await _validate_reference(
                        session, practitioner.org_id, i_type, i_id, "qualification.issuer"
                    )
                    qualification.issuer_type = i_type
                    qualification.issuer_id = i_id
                else:
                    qualification.issuer_type = None
                    qualification.issuer_id = None

            for field, value in data.items():
                setattr(qualification, field, value)
            if updated_by is not None:
                qualification.updated_by = updated_by

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)
