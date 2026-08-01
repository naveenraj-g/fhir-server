from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.patient.patient import (
    PatientContact,
    PatientContactRelationship,
    PatientContactTelecom,
    PatientModel,
)
from app.schemas.patient import ContactCreate, ContactPatch

from ._shared import _delete_child, _org_ref_kwargs, _parse_org_ref, _reference_kwargs, _validate_reference


class _ContactMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.contact rows
    (plus their relationship[]/telecom[] grandchildren)."""

    async def add_contact(
        self, patient_id: int, payload: ContactCreate, created_by: str | None = None
    ) -> PatientModel | None:
        """Append one contact row (plus its relationship[]/telecom[] grandchildren) to this patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            co_type, co_id = (
                _parse_org_ref(payload.organization) if payload.organization else (None, None)
            )
            await _validate_reference(
                session, patient.org_id, co_type, co_id, "contact.organization"
            )
            contact = PatientContact(
                patient_id=patient.id,
                org_id=patient.org_id,
                name_use=payload.name_use,
                name_text=payload.name_text,
                name_family=payload.name_family,
                name_given=", ".join(payload.name_given)
                if payload.name_given
                else None,
                name_prefix=", ".join(payload.name_prefix)
                if payload.name_prefix
                else None,
                name_suffix=", ".join(payload.name_suffix)
                if payload.name_suffix
                else None,
                name_period_start=payload.name_period_start,
                name_period_end=payload.name_period_end,
                address_use=payload.address_use,
                address_type=payload.address_type,
                address_text=payload.address_text,
                address_line=", ".join(payload.address_line)
                if payload.address_line
                else None,
                address_city=payload.address_city,
                address_district=payload.address_district,
                address_state=payload.address_state,
                address_postal_code=payload.address_postal_code,
                address_country=payload.address_country,
                address_period_start=payload.address_period_start,
                address_period_end=payload.address_period_end,
                gender=payload.gender,
                **_org_ref_kwargs(
                    "organization", payload.organization, payload.organization_display
                ),
                **_reference_kwargs("organization", payload),
                period_start=payload.period_start,
                period_end=payload.period_end,
                created_by=created_by,
            )
            session.add(contact)
            await session.flush()  # get contact.id before adding grandchildren

            if payload.relationship:
                for r in payload.relationship:
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
                            created_by=created_by,
                        )
                    )

            if payload.telecom:
                for t in payload.telecom:
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
                            created_by=created_by,
                        )
                    )

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def get_contacts(self, patient_id: int) -> list:
        """All contact rows (with relationship[]/telecom[] grandchildren eager-loaded)
        for this patient. Backs GET /{patient_id}/contacts."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return []
            stmt = (
                select(PatientContact)
                .where(PatientContact.patient_id == patient.id)
                .options(
                    selectinload(PatientContact.relationships),
                    selectinload(PatientContact.telecoms),
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def delete_contact(self, patient_id: int, contact_id: int) -> bool:
        """Delete one contact row (cascades to its relationship[]/telecom[]
        grandchildren) — False if it doesn't exist or belongs to a different patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return False
            return await _delete_child(
                session, PatientContact, contact_id, patient.id
            )

    async def patch_contact(
        self,
        patient_id: int,
        contact_id: int,
        payload: ContactPatch,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of one contact row. If `relationship` or `telecom`
        is supplied, the corresponding grandchild rows are entirely replaced;
        other supplied fields flow through a generic setattr."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None
            stmt = (
                select(PatientContact)
                .where(
                    PatientContact.id == contact_id,
                    PatientContact.patient_id == patient.id,
                )
                .options(
                    selectinload(PatientContact.relationships),
                    selectinload(PatientContact.telecoms),
                )
            )
            contact = (await session.execute(stmt)).scalars().first()
            if not contact:
                return None

            data = payload.model_dump(exclude_unset=True)

            if "relationship" in data:
                for r in contact.relationships:
                    await session.delete(r)
                for r in data.pop("relationship") or []:
                    session.add(
                        PatientContactRelationship(
                            contact_id=contact.id,
                            org_id=patient.org_id,
                            created_by=updated_by,
                            **r,
                        )
                    )
            else:
                data.pop("relationship", None)

            if "telecom" in data:
                for t in contact.telecoms:
                    await session.delete(t)
                for t in data.pop("telecom") or []:
                    session.add(
                        PatientContactTelecom(
                            contact_id=contact.id,
                            org_id=patient.org_id,
                            created_by=updated_by,
                            **t,
                        )
                    )
            else:
                data.pop("telecom", None)

            if "organization" in data:
                org = data.pop("organization")
                if org:
                    co_type, co_id = _parse_org_ref(org)
                    await _validate_reference(
                        session, patient.org_id, co_type, co_id, "contact.organization"
                    )
                    contact.organization_type = co_type
                    contact.organization_id = co_id
                else:
                    contact.organization_type = None
                    contact.organization_id = None

            for field in ("name_given", "name_prefix", "name_suffix"):
                if field in data:
                    data[field] = ", ".join(data[field]) if data[field] else None
            if "address_line" in data:
                data["address_line"] = (
                    ", ".join(data["address_line"]) if data["address_line"] else None
                )

            for field, value in data.items():
                setattr(contact, field, value)
            if updated_by is not None:
                contact.updated_by = updated_by

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_patient_id(patient_id)
