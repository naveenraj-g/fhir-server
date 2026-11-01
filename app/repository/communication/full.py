from sqlalchemy import delete, func, select

from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.communication import (
    CommunicationAbout,
    CommunicationBasedOn,
    CommunicationCategory,
    CommunicationCategoryCoding,
    CommunicationIdentifier,
    CommunicationIdentifierTypeCoding,
    CommunicationInResponseTo,
    CommunicationMedium,
    CommunicationMediumCoding,
    CommunicationModel,
    CommunicationNote,
    CommunicationPartOf,
    CommunicationPayload,
    CommunicationReasonCode,
    CommunicationReasonCodeCoding,
    CommunicationReasonReference,
    CommunicationRecipient,
    CommunicationStatusReasonCoding,
    CommunicationTopicCoding,
)
from app.schemas.communication import (
    CommunicationCreateSchema,
    CommunicationPatchSchema,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_assigner_ref,
    _parse_encounter_ref,
    _parse_generic_ref,
    _parse_in_response_to_ref,
    _parse_reason_ref,
    _parse_recipient_ref,
    _parse_sender_ref,
    _parse_subject_ref,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    if isinstance(coding, dict):
        return {
            "tenant_id": org_id,
            "system": coding.get("system"),
            "version": coding.get("version"),
            "code": coding.get("code"),
            "display": coding.get("display"),
            "user_selected": coding.get("user_selected") or coding.get("userSelected"),
            "created_by": created_by,
        }
    return {
        "tenant_id": org_id,
        "system": getattr(coding, "system", None),
        "version": getattr(coding, "version", None),
        "code": getattr(coding, "code", None),
        "display": getattr(coding, "display", None),
        "user_selected": getattr(coding, "user_selected", None),
        "created_by": created_by,
    }


async def _add_identifiers(
    session, communication_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")

        ident = CommunicationIdentifier(
            communication_pk=communication_pk,
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
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()

        for c in i.type_coding or []:
            session.add(
                CommunicationIdentifierTypeCoding(
                    communication_identifier_id=ident.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


def _add_status_reason_codings(
    session, communication_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            CommunicationStatusReasonCoding(
                communication_pk=communication_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


def _add_topic_codings(
    session, communication_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            CommunicationTopicCoding(
                communication_pk=communication_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_categories(
    session, communication_pk: int, org_id: str, categories, created_by: str
) -> None:
    for cat in categories or []:
        c_row = CommunicationCategory(
            communication_pk=communication_pk,
            tenant_id=org_id,
            text=cat.text,
            created_by=created_by,
        )
        session.add(c_row)
        await session.flush()
        for c in cat.coding or []:
            session.add(
                CommunicationCategoryCoding(
                    communication_category_id=c_row.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_medium(
    session, communication_pk: int, org_id: str, medium_list, created_by: str
) -> None:
    for med in medium_list or []:
        m_row = CommunicationMedium(
            communication_pk=communication_pk,
            tenant_id=org_id,
            text=med.text,
            created_by=created_by,
        )
        session.add(m_row)
        await session.flush()
        for c in med.coding or []:
            session.add(
                CommunicationMediumCoding(
                    communication_medium_id=m_row.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_reason_codes(
    session, communication_pk: int, org_id: str, reason_codes, created_by: str
) -> None:
    for rc in reason_codes or []:
        rc_row = CommunicationReasonCode(
            communication_pk=communication_pk,
            tenant_id=org_id,
            text=rc.text,
            created_by=created_by,
        )
        session.add(rc_row)
        await session.flush()
        for c in rc.coding or []:
            session.add(
                CommunicationReasonCodeCoding(
                    communication_reason_code_id=rc_row.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_based_on(
    session, communication_pk: int, org_id: str, based_on_list, created_by: str
) -> None:
    for b in based_on_list or []:
        raw_ref = b if isinstance(b, str) else getattr(b, "reference", None)
        disp = None if isinstance(b, str) else getattr(b, "display", None)
        r_type, r_id = _parse_generic_ref(raw_ref) if raw_ref else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "based_on")
        session.add(
            CommunicationBasedOn(
                communication_pk=communication_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=raw_ref,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_part_of(
    session, communication_pk: int, org_id: str, part_of_list, created_by: str
) -> None:
    for p in part_of_list or []:
        raw_ref = p if isinstance(p, str) else getattr(p, "reference", None)
        disp = None if isinstance(p, str) else getattr(p, "display", None)
        r_type, r_id = _parse_generic_ref(raw_ref) if raw_ref else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "part_of")
        session.add(
            CommunicationPartOf(
                communication_pk=communication_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=raw_ref,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_in_response_to(
    session, communication_pk: int, org_id: str, in_response_to_list, created_by: str
) -> None:
    for r in in_response_to_list or []:
        raw_ref = r if isinstance(r, str) else getattr(r, "reference", None)
        disp = None if isinstance(r, str) else getattr(r, "display", None)
        r_type, r_id = _parse_in_response_to_ref(raw_ref) if raw_ref else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "in_response_to")
        session.add(
            CommunicationInResponseTo(
                communication_pk=communication_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=raw_ref,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_about(
    session, communication_pk: int, org_id: str, about_list, created_by: str
) -> None:
    for a in about_list or []:
        raw_ref = a if isinstance(a, str) else getattr(a, "reference", None)
        disp = None if isinstance(a, str) else getattr(a, "display", None)
        r_type, r_id = _parse_generic_ref(raw_ref) if raw_ref else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "about")
        session.add(
            CommunicationAbout(
                communication_pk=communication_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=raw_ref,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_recipients(
    session, communication_pk: int, org_id: str, recipients, created_by: str
) -> None:
    for rec in recipients or []:
        raw_ref = rec if isinstance(rec, str) else getattr(rec, "reference", None)
        disp = None if isinstance(rec, str) else getattr(rec, "display", None)
        r_type, r_id = _parse_recipient_ref(raw_ref) if raw_ref else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "recipient")
        session.add(
            CommunicationRecipient(
                communication_pk=communication_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=raw_ref,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_reason_references(
    session, communication_pk: int, org_id: str, reason_references, created_by: str
) -> None:
    for rr in reason_references or []:
        raw_ref = rr if isinstance(rr, str) else getattr(rr, "reference", None)
        disp = None if isinstance(rr, str) else getattr(rr, "display", None)
        r_type, r_id = _parse_reason_ref(raw_ref) if raw_ref else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "reason_reference")
        session.add(
            CommunicationReasonReference(
                communication_pk=communication_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=raw_ref,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_payloads(
    session, communication_pk: int, org_id: str, payloads, created_by: str
) -> None:
    for p in payloads or []:
        c_str = p.content_string
        att = p.content_attachment
        c_ref = p.content_reference
        c_ref_disp = p.content_reference_display

        r_type, r_id = _parse_generic_ref(c_ref) if c_ref else (None, None)
        if r_type and r_id:
            await _validate_ref(
                session, org_id, r_type, r_id, "payload.content_reference"
            )

        payload_row = CommunicationPayload(
            communication_pk=communication_pk,
            tenant_id=org_id,
            created_by=created_by,
            content_string=c_str,
            content_reference_reference=c_ref,
            content_reference_type=r_type,
            content_reference_id=r_id,
            content_reference_display=c_ref_disp,
            content_type=getattr(att, "content_type", None) if att else None,
            language=getattr(att, "language", None) if att else None,
            data=getattr(att, "data", None) if att else None,
            url=getattr(att, "url", None) if att else None,
            size=getattr(att, "size", None) if att else None,
            hash=getattr(att, "hash", None) if att else None,
            title=getattr(att, "title", None) if att else None,
            creation=getattr(att, "creation", None) if att else None,
        )
        session.add(payload_row)


async def _add_notes(
    session, communication_pk: int, org_id: str, notes, created_by: str
) -> None:
    for n in notes or []:
        r_type, r_id = (
            _parse_generic_ref(n.author_reference)
            if n.author_reference
            else (None, None)
        )
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "note.author_reference")
        session.add(
            CommunicationNote(
                communication_pk=communication_pk,
                tenant_id=org_id,
                created_by=created_by,
                author_string=n.author_string,
                author_reference=n.author_reference,
                author_type=r_type,
                author_id=r_id,
                author_display=n.author_display,
                time=n.time,
                text=n.text,
            )
        )


class CommunicationRepository:
    """All DB I/O for FHIR R4 Communication resources."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create_full(
        self, payload: CommunicationCreateSchema, org_id: str, created_by: str
    ) -> CommunicationModel:
        async with self.session_factory() as session:
            # 1. Resolve & validate subject
            s_type, s_id = (
                _parse_subject_ref(payload.subject) if payload.subject else (None, None)
            )
            if s_type and s_id:
                await _validate_ref(session, org_id, s_type, s_id, "subject")

            # 2. Resolve & validate encounter
            e_type, e_id = (
                _parse_encounter_ref(payload.encounter)
                if payload.encounter
                else (None, None)
            )
            if e_type and e_id:
                await _validate_ref(session, org_id, e_type, e_id, "encounter")

            # 3. Resolve & validate sender
            snd_type, snd_id = (
                _parse_sender_ref(payload.sender) if payload.sender else (None, None)
            )
            if snd_type and snd_id:
                await _validate_ref(session, org_id, snd_type, snd_id, "sender")

            # 4. Construct main Communication model row
            model = CommunicationModel(
                tenant_id=org_id,
                created_by=created_by,
                instantiates_canonical=payload.instantiates_canonical,
                instantiates_uri=payload.instantiates_uri,
                status=payload.status,
                status_reason_text=payload.status_reason_text,
                priority=payload.priority,
                subject_reference=payload.subject,
                subject_type=s_type,
                subject_id=s_id,
                subject_display=payload.subject_display,
                topic_text=payload.topic_text,
                encounter_reference=payload.encounter,
                encounter_type=e_type,
                encounter_id=e_id,
                encounter_display=payload.encounter_display,
                sent=payload.sent,
                received=payload.received,
                sender_reference=payload.sender,
                sender_type=snd_type,
                sender_id=snd_id,
                sender_display=payload.sender_display,
                extension=payload.extension or [],
            )
            session.add(model)
            await session.flush()

            pk = model.id

            # 5. Insert child collections
            if payload.identifier:
                await _add_identifiers(session, pk, org_id, payload.identifier, created_by)

            if payload.status_reason_coding:
                _add_status_reason_codings(
                    session, pk, org_id, payload.status_reason_coding, created_by
                )

            if payload.category:
                await _add_categories(session, pk, org_id, payload.category, created_by)

            if payload.medium:
                await _add_medium(session, pk, org_id, payload.medium, created_by)

            if payload.topic_coding:
                _add_topic_codings(session, pk, org_id, payload.topic_coding, created_by)

            if payload.based_on:
                await _add_based_on(session, pk, org_id, payload.based_on, created_by)

            if payload.part_of:
                await _add_part_of(session, pk, org_id, payload.part_of, created_by)

            if payload.in_response_to:
                await _add_in_response_to(
                    session, pk, org_id, payload.in_response_to, created_by
                )

            if payload.about:
                await _add_about(session, pk, org_id, payload.about, created_by)

            if payload.recipient:
                await _add_recipients(session, pk, org_id, payload.recipient, created_by)

            if payload.reason_code:
                await _add_reason_codes(session, pk, org_id, payload.reason_code, created_by)

            if payload.reason_reference:
                await _add_reason_references(
                    session, pk, org_id, payload.reason_reference, created_by
                )

            if payload.payload:
                await _add_payloads(session, pk, org_id, payload.payload, created_by)

            if payload.note:
                await _add_notes(session, pk, org_id, payload.note, created_by)

            comm_id = model.communication_id
            await session.commit()

        return await self.get_by_communication_id(comm_id)

    async def get_by_communication_id(
        self, communication_id: int
    ) -> CommunicationModel | None:
        async with self.session_factory() as session:
            stmt = select(CommunicationModel).where(
                CommunicationModel.communication_id == communication_id
            )
            stmt = _with_relationships(stmt)
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_by_communication_id_in_org(
        self, communication_id: int, org_id: str
    ) -> CommunicationModel | None:
        async with self.session_factory() as session:
            stmt = select(CommunicationModel).where(
                CommunicationModel.communication_id == communication_id,
                CommunicationModel.tenant_id == org_id,
            )
            stmt = _with_relationships(stmt)
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def communication_belongs_to_org(
        self, communication_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = (
                select(func.count())
                .select_from(CommunicationModel)
                .where(
                    CommunicationModel.communication_id == communication_id,
                    CommunicationModel.tenant_id == org_id,
                )
            )
            res = await session.execute(stmt)
            return (res.scalar() or 0) > 0

    async def patch_full(
        self,
        communication_id: int,
        payload: CommunicationPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> CommunicationModel | None:
        async with self.session_factory() as session:
            stmt = select(CommunicationModel).where(
                CommunicationModel.communication_id == communication_id,
                CommunicationModel.tenant_id == org_id,
            )
            stmt = _with_relationships(stmt)
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            if not row:
                return None

            pk = row.id
            touched = payload.model_fields_set

            # Flat scalar updates
            if "status" in touched:
                row.status = payload.status
            if "priority" in touched:
                row.priority = payload.priority
            if "sent" in touched:
                row.sent = payload.sent
            if "received" in touched:
                row.received = payload.received
            if "status_reason_text" in touched:
                row.status_reason_text = payload.status_reason_text
            if "topic_text" in touched:
                row.topic_text = payload.topic_text
            if "instantiates_canonical" in touched:
                row.instantiates_canonical = payload.instantiates_canonical
            if "instantiates_uri" in touched:
                row.instantiates_uri = payload.instantiates_uri
            if "extension" in touched:
                row.extension = payload.extension or []

            # Reference fields
            if "subject" in touched or "subject_display" in touched:
                s_ref = payload.subject if "subject" in touched else row.subject_reference
                s_type, s_id = _parse_subject_ref(s_ref) if s_ref else (None, None)
                if s_type and s_id:
                    await _validate_ref(session, org_id, s_type, s_id, "subject")
                row.subject_reference = s_ref
                row.subject_type = s_type
                row.subject_id = s_id
                if "subject_display" in touched:
                    row.subject_display = payload.subject_display

            if "encounter" in touched or "encounter_display" in touched:
                e_ref = payload.encounter if "encounter" in touched else row.encounter_reference
                e_type, e_id = _parse_encounter_ref(e_ref) if e_ref else (None, None)
                if e_type and e_id:
                    await _validate_ref(session, org_id, e_type, e_id, "encounter")
                row.encounter_reference = e_ref
                row.encounter_type = e_type
                row.encounter_id = e_id
                if "encounter_display" in touched:
                    row.encounter_display = payload.encounter_display

            if "sender" in touched or "sender_display" in touched:
                snd_ref = payload.sender if "sender" in touched else row.sender_reference
                snd_type, snd_id = _parse_sender_ref(snd_ref) if snd_ref else (None, None)
                if snd_type and snd_id:
                    await _validate_ref(session, org_id, snd_type, snd_id, "sender")
                row.sender_reference = snd_ref
                row.sender_type = snd_type
                row.sender_id = snd_id
                if "sender_display" in touched:
                    row.sender_display = payload.sender_display

            # Child collections replacement if touched
            if "identifier" in touched:
                await session.execute(
                    delete(CommunicationIdentifier).where(
                        CommunicationIdentifier.communication_pk == pk
                    )
                )
                if payload.identifier:
                    await _add_identifiers(
                        session, pk, org_id, payload.identifier, updated_by
                    )

            if "status_reason_coding" in touched:
                await session.execute(
                    delete(CommunicationStatusReasonCoding).where(
                        CommunicationStatusReasonCoding.communication_pk == pk
                    )
                )
                if payload.status_reason_coding:
                    _add_status_reason_codings(
                        session, pk, org_id, payload.status_reason_coding, updated_by
                    )

            if "category" in touched:
                await session.execute(
                    delete(CommunicationCategory).where(
                        CommunicationCategory.communication_pk == pk
                    )
                )
                if payload.category:
                    await _add_categories(
                        session, pk, org_id, payload.category, updated_by
                    )

            if "medium" in touched:
                await session.execute(
                    delete(CommunicationMedium).where(
                        CommunicationMedium.communication_pk == pk
                    )
                )
                if payload.medium:
                    await _add_medium(
                        session, pk, org_id, payload.medium, updated_by
                    )

            if "topic_coding" in touched:
                await session.execute(
                    delete(CommunicationTopicCoding).where(
                        CommunicationTopicCoding.communication_pk == pk
                    )
                )
                if payload.topic_coding:
                    _add_topic_codings(
                        session, pk, org_id, payload.topic_coding, updated_by
                    )

            if "based_on" in touched:
                await session.execute(
                    delete(CommunicationBasedOn).where(
                        CommunicationBasedOn.communication_pk == pk
                    )
                )
                if payload.based_on:
                    await _add_based_on(
                        session, pk, org_id, payload.based_on, updated_by
                    )

            if "part_of" in touched:
                await session.execute(
                    delete(CommunicationPartOf).where(
                        CommunicationPartOf.communication_pk == pk
                    )
                )
                if payload.part_of:
                    await _add_part_of(
                        session, pk, org_id, payload.part_of, updated_by
                    )

            if "in_response_to" in touched:
                await session.execute(
                    delete(CommunicationInResponseTo).where(
                        CommunicationInResponseTo.communication_pk == pk
                    )
                )
                if payload.in_response_to:
                    await _add_in_response_to(
                        session, pk, org_id, payload.in_response_to, updated_by
                    )

            if "about" in touched:
                await session.execute(
                    delete(CommunicationAbout).where(
                        CommunicationAbout.communication_pk == pk
                    )
                )
                if payload.about:
                    await _add_about(
                        session, pk, org_id, payload.about, updated_by
                    )

            if "recipient" in touched:
                await session.execute(
                    delete(CommunicationRecipient).where(
                        CommunicationRecipient.communication_pk == pk
                    )
                )
                if payload.recipient:
                    await _add_recipients(
                        session, pk, org_id, payload.recipient, updated_by
                    )

            if "reason_code" in touched:
                await session.execute(
                    delete(CommunicationReasonCode).where(
                        CommunicationReasonCode.communication_pk == pk
                    )
                )
                if payload.reason_code:
                    await _add_reason_codes(
                        session, pk, org_id, payload.reason_code, updated_by
                    )

            if "reason_reference" in touched:
                await session.execute(
                    delete(CommunicationReasonReference).where(
                        CommunicationReasonReference.communication_pk == pk
                    )
                )
                if payload.reason_reference:
                    await _add_reason_references(
                        session, pk, org_id, payload.reason_reference, updated_by
                    )

            if "payload" in touched:
                await session.execute(
                    delete(CommunicationPayload).where(
                        CommunicationPayload.communication_pk == pk
                    )
                )
                if payload.payload:
                    await _add_payloads(
                        session, pk, org_id, payload.payload, updated_by
                    )

            if "note" in touched:
                await session.execute(
                    delete(CommunicationNote).where(
                        CommunicationNote.communication_pk == pk
                    )
                )
                if payload.note:
                    await _add_notes(
                        session, pk, org_id, payload.note, updated_by
                    )

            row.updated_by = updated_by
            await session.commit()

        return await self.get_by_communication_id(communication_id)

    async def list(
        self,
        org_id: str,
        subject: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        encounter: str | None = None,
        sender: str | None = None,
        recipient: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[int, list[CommunicationModel]]:
        async with self.session_factory() as session:
            base_stmt = select(CommunicationModel).where(
                CommunicationModel.tenant_id == org_id
            )

            if subject:
                if "/" in subject:
                    s_type, s_id = _parse_subject_ref(subject)
                    if s_type and s_id:
                        base_stmt = base_stmt.where(
                            CommunicationModel.subject_type == s_type,
                            CommunicationModel.subject_id == s_id,
                        )
                    else:
                        base_stmt = base_stmt.where(
                            CommunicationModel.subject_reference == subject
                        )
                elif subject.isdigit():
                    base_stmt = base_stmt.where(
                        CommunicationModel.subject_id == int(subject)
                    )
                else:
                    base_stmt = base_stmt.where(
                        CommunicationModel.subject_reference == subject
                    )

            if status:
                base_stmt = base_stmt.where(CommunicationModel.status == status)

            if priority:
                base_stmt = base_stmt.where(CommunicationModel.priority == priority)

            if encounter:
                if "/" in encounter:
                    e_type, e_id = _parse_encounter_ref(encounter)
                    if e_type and e_id:
                        base_stmt = base_stmt.where(
                            CommunicationModel.encounter_type == e_type,
                            CommunicationModel.encounter_id == e_id,
                        )
                    else:
                        base_stmt = base_stmt.where(
                            CommunicationModel.encounter_reference == encounter
                        )
                elif encounter.isdigit():
                    base_stmt = base_stmt.where(
                        CommunicationModel.encounter_id == int(encounter)
                    )
                else:
                    base_stmt = base_stmt.where(
                        CommunicationModel.encounter_reference == encounter
                    )

            if sender:
                if "/" in sender:
                    snd_type, snd_id = _parse_sender_ref(sender)
                    if snd_type and snd_id:
                        base_stmt = base_stmt.where(
                            CommunicationModel.sender_type == snd_type,
                            CommunicationModel.sender_id == snd_id,
                        )
                    else:
                        base_stmt = base_stmt.where(
                            CommunicationModel.sender_reference == sender
                        )
                elif sender.isdigit():
                    base_stmt = base_stmt.where(
                        CommunicationModel.sender_id == int(sender)
                    )
                else:
                    base_stmt = base_stmt.where(
                        CommunicationModel.sender_reference == sender
                    )

            if recipient:
                rec_subquery = select(CommunicationRecipient.communication_pk).where(
                    CommunicationRecipient.tenant_id == org_id
                )
                if "/" in recipient:
                    r_type, r_id = _parse_recipient_ref(recipient)
                    if r_type and r_id:
                        rec_subquery = rec_subquery.where(
                            CommunicationRecipient.reference_type == r_type,
                            CommunicationRecipient.reference_id == r_id,
                        )
                    else:
                        rec_subquery = rec_subquery.where(
                            CommunicationRecipient.reference_reference == recipient
                        )
                elif recipient.isdigit():
                    rec_subquery = rec_subquery.where(
                        CommunicationRecipient.reference_id == int(recipient)
                    )
                else:
                    rec_subquery = rec_subquery.where(
                        CommunicationRecipient.reference_reference == recipient
                    )
                base_stmt = base_stmt.where(
                    CommunicationModel.id.in_(rec_subquery)
                )

            # Count query
            count_stmt = select(func.count()).select_from(base_stmt.subquery())
            total_res = await session.execute(count_stmt)
            total = total_res.scalar() or 0

            # Sorting & pagination
            sort_col, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                CommunicationModel.communication_id,
                default_desc=True,
            )
            data_stmt = (
                base_stmt.order_by(sort_col.desc() if sort_desc else sort_col.asc())
                .limit(limit)
                .offset(offset)
            )
            data_stmt = _with_relationships(data_stmt)
            items_res = await session.execute(data_stmt)
            items = list(items_res.scalars().all())

            return total, items

    async def delete(self, communication_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(CommunicationModel).where(
                CommunicationModel.communication_id == communication_id,
                CommunicationModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            if not row:
                return False
            await session.delete(row)
            await session.commit()
            return True

    create = create_full
    patch = patch_full
