from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.related_person import (
    RelatedPersonAddress,
    RelatedPersonCommunication,
    RelatedPersonCommunicationLanguageCoding,
    RelatedPersonIdentifier,
    RelatedPersonIdentifierTypeCoding,
    RelatedPersonModel,
    RelatedPersonName,
    RelatedPersonPhoto,
    RelatedPersonRelationship,
    RelatedPersonRelationshipCoding,
    RelatedPersonTelecom,
)
from app.schemas.related_person import (
    RelatedPersonCreateSchema,
    RelatedPersonPatchSchema,
)

from ._shared import (
    _parse_assigner_ref,
    _parse_patient_ref,
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
    session, related_person_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")

        ident = RelatedPersonIdentifier(
            related_person_pk=related_person_pk,
            tenant_id=org_id,
            use=i.use,
            type_text=i.type_text,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner_reference=i.assigner,
            assigner_type=a_type,
            assigner_id=a_id,
            assigner_display=i.assigner_display,
            assigner_identifier_use=i.assigner_identifier_use,
            assigner_identifier_type_system=i.assigner_identifier_type_system,
            assigner_identifier_type_version=i.assigner_identifier_type_version,
            assigner_identifier_type_code=i.assigner_identifier_type_code,
            assigner_identifier_type_display=i.assigner_identifier_type_display,
            assigner_identifier_type_text=i.assigner_identifier_type_text,
            assigner_identifier_type_user_selected=i.assigner_identifier_type_user_selected,
            assigner_identifier_system=i.assigner_identifier_system,
            assigner_identifier_value=i.assigner_identifier_value,
            assigner_identifier_period_start=i.assigner_identifier_period_start,
            assigner_identifier_period_end=i.assigner_identifier_period_end,
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()

        if i.type_coding:
            for c in i.type_coding:
                session.add(
                    RelatedPersonIdentifierTypeCoding(
                        related_person_identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_relationships(
    session, related_person_pk: int, org_id: str, relationships, created_by: str
) -> None:
    for r in relationships or []:
        rel = RelatedPersonRelationship(
            related_person_pk=related_person_pk,
            tenant_id=org_id,
            text=r.text,
            created_by=created_by,
        )
        session.add(rel)
        await session.flush()

        if r.coding:
            for c in r.coding:
                session.add(
                    RelatedPersonRelationshipCoding(
                        related_person_relationship_id=rel.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_names(
    session, related_person_pk: int, org_id: str, names, created_by: str
) -> None:
    for n in names or []:
        session.add(
            RelatedPersonName(
                related_person_pk=related_person_pk,
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


async def _add_telecoms(
    session, related_person_pk: int, org_id: str, telecoms, created_by: str
) -> None:
    for t in telecoms or []:
        session.add(
            RelatedPersonTelecom(
                related_person_pk=related_person_pk,
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


async def _add_addresses(
    session, related_person_pk: int, org_id: str, addresses, created_by: str
) -> None:
    for a in addresses or []:
        session.add(
            RelatedPersonAddress(
                related_person_pk=related_person_pk,
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


async def _add_photos(
    session, related_person_pk: int, org_id: str, photos, created_by: str
) -> None:
    for p in photos or []:
        session.add(
            RelatedPersonPhoto(
                related_person_pk=related_person_pk,
                tenant_id=org_id,
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


async def _add_communications(
    session, related_person_pk: int, org_id: str, communications, created_by: str
) -> None:
    for c in communications or []:
        comm = RelatedPersonCommunication(
            related_person_pk=related_person_pk,
            tenant_id=org_id,
            language_text=c.language_text,
            preferred=c.preferred,
            created_by=created_by,
        )
        session.add(comm)
        await session.flush()

        if c.language_coding:
            for cd in c.language_coding:
                session.add(
                    RelatedPersonCommunicationLanguageCoding(
                        related_person_communication_id=comm.id,
                        **_coding_kwargs(cd, org_id, created_by),
                    )
                )


class _FullMixin:
    """Full nested create/patch implementation for RelatedPerson."""

    async def create_full(
        self,
        payload: RelatedPersonCreateSchema,
        org_id: str,
        created_by: str,
    ) -> RelatedPersonModel:
        async with self.session_factory() as session:
            p_type, p_id = _parse_patient_ref(payload.patient)
            await _validate_ref(session, org_id, p_type, p_id, "patient")

            model = RelatedPersonModel(
                tenant_id=org_id,
                created_by=created_by,
                active=payload.active,
                patient_reference=payload.patient,
                patient_type=p_type,
                patient_id=p_id,
                patient_display=payload.patient_display,
                gender=payload.gender,
                birth_date=payload.birth_date,
                period_start=payload.period_start,
                period_end=payload.period_end,
                extension=payload.extension or [],
            )
            session.add(model)
            await session.flush()

            await _add_identifiers(
                session, model.id, org_id, payload.identifier, created_by
            )
            await _add_relationships(
                session, model.id, org_id, payload.relationship, created_by
            )
            await _add_names(session, model.id, org_id, payload.name, created_by)
            await _add_telecoms(
                session, model.id, org_id, payload.telecom, created_by
            )
            await _add_addresses(
                session, model.id, org_id, payload.address, created_by
            )
            await _add_photos(session, model.id, org_id, payload.photo, created_by)
            await _add_communications(
                session, model.id, org_id, payload.communication, created_by
            )

            await session.commit()

            stmt = _with_relationships(
                select(RelatedPersonModel).where(RelatedPersonModel.id == model.id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def patch_full(
        self,
        related_person_id: int,
        payload: RelatedPersonPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> RelatedPersonModel | None:
        async with self.session_factory() as session:
            query = select(RelatedPersonModel).where(
                RelatedPersonModel.related_person_id == related_person_id
            )
            if org_id is not None:
                query = query.where(RelatedPersonModel.tenant_id == org_id)

            model = (await session.execute(query)).scalars().first()
            if not model:
                return None

            provided = payload.model_fields_set

            if "active" in provided:
                model.active = payload.active

            if "patient" in provided and payload.patient:
                p_type, p_id = _parse_patient_ref(payload.patient)
                await _validate_ref(
                    session, model.tenant_id, p_type, p_id, "patient"
                )
                model.patient_reference = payload.patient
                model.patient_type = p_type
                model.patient_id = p_id

            if "patient_display" in provided:
                model.patient_display = payload.patient_display

            if "gender" in provided:
                model.gender = payload.gender

            if "birth_date" in provided:
                model.birth_date = payload.birth_date

            if "period_start" in provided:
                model.period_start = payload.period_start

            if "period_end" in provided:
                model.period_end = payload.period_end

            if "extension" in provided:
                model.extension = payload.extension or []

            model.updated_by = updated_by

            # Wholesale sub-resource replacement
            effective_org_id = model.tenant_id

            if "identifier" in provided:
                # Delete grandchildren first
                await session.execute(
                    delete(RelatedPersonIdentifierTypeCoding).where(
                        RelatedPersonIdentifierTypeCoding.related_person_identifier_id.in_(
                            select(RelatedPersonIdentifier.id).where(
                                RelatedPersonIdentifier.related_person_pk == model.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(RelatedPersonIdentifier).where(
                        RelatedPersonIdentifier.related_person_pk == model.id
                    )
                )
                await _add_identifiers(
                    session, model.id, effective_org_id, payload.identifier, updated_by
                )

            if "relationship" in provided:
                # Delete grandchildren first
                await session.execute(
                    delete(RelatedPersonRelationshipCoding).where(
                        RelatedPersonRelationshipCoding.related_person_relationship_id.in_(
                            select(RelatedPersonRelationship.id).where(
                                RelatedPersonRelationship.related_person_pk == model.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(RelatedPersonRelationship).where(
                        RelatedPersonRelationship.related_person_pk == model.id
                    )
                )
                await _add_relationships(
                    session, model.id, effective_org_id, payload.relationship, updated_by
                )

            if "name" in provided:
                await session.execute(
                    delete(RelatedPersonName).where(
                        RelatedPersonName.related_person_pk == model.id
                    )
                )
                await _add_names(
                    session, model.id, effective_org_id, payload.name, updated_by
                )

            if "telecom" in provided:
                await session.execute(
                    delete(RelatedPersonTelecom).where(
                        RelatedPersonTelecom.related_person_pk == model.id
                    )
                )
                await _add_telecoms(
                    session, model.id, effective_org_id, payload.telecom, updated_by
                )

            if "address" in provided:
                await session.execute(
                    delete(RelatedPersonAddress).where(
                        RelatedPersonAddress.related_person_pk == model.id
                    )
                )
                await _add_addresses(
                    session, model.id, effective_org_id, payload.address, updated_by
                )

            if "photo" in provided:
                await session.execute(
                    delete(RelatedPersonPhoto).where(
                        RelatedPersonPhoto.related_person_pk == model.id
                    )
                )
                await _add_photos(
                    session, model.id, effective_org_id, payload.photo, updated_by
                )

            if "communication" in provided:
                # Delete grandchildren first
                await session.execute(
                    delete(RelatedPersonCommunicationLanguageCoding).where(
                        RelatedPersonCommunicationLanguageCoding.related_person_communication_id.in_(
                            select(RelatedPersonCommunication.id).where(
                                RelatedPersonCommunication.related_person_pk == model.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(RelatedPersonCommunication).where(
                        RelatedPersonCommunication.related_person_pk == model.id
                    )
                )
                await _add_communications(
                    session, model.id, effective_org_id, payload.communication, updated_by
                )

            await session.commit()

            stmt = _with_relationships(
                select(RelatedPersonModel).where(RelatedPersonModel.id == model.id)
            )
            return (await session.execute(stmt)).scalars().first()
