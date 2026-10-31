from sqlalchemy import delete, func, select

from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.communication_request import (
    CommunicationRequestAbout,
    CommunicationRequestBasedOn,
    CommunicationRequestCategory,
    CommunicationRequestCategoryCoding,
    CommunicationRequestIdentifier,
    CommunicationRequestIdentifierTypeCoding,
    CommunicationRequestMedium,
    CommunicationRequestMediumCoding,
    CommunicationRequestModel,
    CommunicationRequestNote,
    CommunicationRequestPayload,
    CommunicationRequestReasonCode,
    CommunicationRequestReasonCodeCoding,
    CommunicationRequestReasonReference,
    CommunicationRequestRecipient,
    CommunicationRequestReplaces,
    CommunicationRequestStatusReasonCoding,
)
from app.schemas.communication_request import (
    CommunicationRequestCreateSchema,
    CommunicationRequestPatchSchema,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_assigner_ref,
    _parse_encounter_ref,
    _parse_generic_ref,
    _parse_reason_ref,
    _parse_recipient_ref,
    _parse_requester_ref,
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
    session, communication_request_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")

        ident = CommunicationRequestIdentifier(
            communication_request_pk=communication_request_pk,
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
                CommunicationRequestIdentifierTypeCoding(
                    communication_request_identifier_id=ident.id,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


def _add_codings(
    session, model_cls, communication_request_pk: int, org_id: str, codings, created_by: str
) -> None:
    for c in codings or []:
        session.add(
            model_cls(
                communication_request_pk=communication_request_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_categories(
    session, communication_request_pk: int, org_id: str, categories, created_by: str
) -> None:
    for c in categories or []:
        cat = CommunicationRequestCategory(
            communication_request_pk=communication_request_pk,
            tenant_id=org_id,
            text=c.text,
            created_by=created_by,
        )
        session.add(cat)
        await session.flush()

        for coding in c.coding or []:
            session.add(
                CommunicationRequestCategoryCoding(
                    communication_request_category_id=cat.id,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )


async def _add_mediums(
    session, communication_request_pk: int, org_id: str, mediums, created_by: str
) -> None:
    for m in mediums or []:
        med = CommunicationRequestMedium(
            communication_request_pk=communication_request_pk,
            tenant_id=org_id,
            text=m.text,
            created_by=created_by,
        )
        session.add(med)
        await session.flush()

        for coding in m.coding or []:
            session.add(
                CommunicationRequestMediumCoding(
                    communication_request_medium_id=med.id,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )


async def _add_reason_codes(
    session, communication_request_pk: int, org_id: str, reason_codes, created_by: str
) -> None:
    for rc in reason_codes or []:
        code_row = CommunicationRequestReasonCode(
            communication_request_pk=communication_request_pk,
            tenant_id=org_id,
            text=rc.text,
            created_by=created_by,
        )
        session.add(code_row)
        await session.flush()

        for coding in rc.coding or []:
            session.add(
                CommunicationRequestReasonCodeCoding(
                    communication_request_reason_code_id=code_row.id,
                    **_coding_kwargs(coding, org_id, created_by),
                )
            )


async def _add_based_on(
    session, communication_request_pk: int, org_id: str, references, created_by: str
) -> None:
    for r in references or []:
        ref_str = r if isinstance(r, str) else getattr(r, "reference", None)
        disp = None if isinstance(r, str) else getattr(r, "display", None)
        r_type, r_id = _parse_generic_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "based_on")
        session.add(
            CommunicationRequestBasedOn(
                communication_request_pk=communication_request_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_replaces(
    session, communication_request_pk: int, org_id: str, references, created_by: str
) -> None:
    for r in references or []:
        ref_str = r if isinstance(r, str) else getattr(r, "reference", None)
        disp = None if isinstance(r, str) else getattr(r, "display", None)
        r_type, r_id = _parse_generic_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "replaces")
        session.add(
            CommunicationRequestReplaces(
                communication_request_pk=communication_request_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_about(
    session, communication_request_pk: int, org_id: str, references, created_by: str
) -> None:
    for r in references or []:
        ref_str = r if isinstance(r, str) else getattr(r, "reference", None)
        disp = None if isinstance(r, str) else getattr(r, "display", None)
        r_type, r_id = _parse_generic_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "about")
        session.add(
            CommunicationRequestAbout(
                communication_request_pk=communication_request_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_recipients(
    session, communication_request_pk: int, org_id: str, references, created_by: str
) -> None:
    for r in references or []:
        ref_str = r if isinstance(r, str) else getattr(r, "reference", None)
        disp = None if isinstance(r, str) else getattr(r, "display", None)
        r_type, r_id = _parse_recipient_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "recipient")
        session.add(
            CommunicationRequestRecipient(
                communication_request_pk=communication_request_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_reason_references(
    session, communication_request_pk: int, org_id: str, references, created_by: str
) -> None:
    for r in references or []:
        ref_str = r if isinstance(r, str) else getattr(r, "reference", None)
        disp = None if isinstance(r, str) else getattr(r, "display", None)
        r_type, r_id = _parse_reason_ref(ref_str) if ref_str else (None, None)
        if r_type and r_id:
            await _validate_ref(session, org_id, r_type, r_id, "reason_reference")
        session.add(
            CommunicationRequestReasonReference(
                communication_request_pk=communication_request_pk,
                tenant_id=org_id,
                created_by=created_by,
                reference_reference=ref_str,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=disp,
            )
        )


async def _add_notes(
    session, communication_request_pk: int, org_id: str, notes, created_by: str
) -> None:
    for n in notes or []:
        author_ref = n.author_reference
        author_type, author_id = (
            _parse_generic_ref(author_ref) if author_ref else (None, None)
        )
        if author_type and author_id:
            await _validate_ref(session, org_id, author_type, author_id, "note.author")
        session.add(
            CommunicationRequestNote(
                communication_request_pk=communication_request_pk,
                tenant_id=org_id,
                created_by=created_by,
                author_string=n.author_string,
                author_reference=author_ref,
                author_type=author_type,
                author_id=author_id,
                author_display=n.author_display,
                time=n.time,
                text=n.text,
            )
        )


async def _add_payloads(
    session, communication_request_pk: int, org_id: str, payloads, created_by: str
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

        payload_row = CommunicationRequestPayload(
            communication_request_pk=communication_request_pk,
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


class CommunicationRequestRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_by_communication_request_id(
        self, communication_request_id: int
    ) -> CommunicationRequestModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(CommunicationRequestModel).where(
                    CommunicationRequestModel.communication_request_id
                    == communication_request_id
                )
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_by_communication_request_id_in_org(
        self, communication_request_id: int, org_id: str
    ) -> CommunicationRequestModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(CommunicationRequestModel).where(
                    CommunicationRequestModel.communication_request_id
                    == communication_request_id,
                    CommunicationRequestModel.tenant_id == org_id,
                )
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def communication_request_belongs_to_org(
        self, communication_request_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = (
                select(func.count())
                .select_from(CommunicationRequestModel)
                .where(
                    CommunicationRequestModel.communication_request_id
                    == communication_request_id,
                    CommunicationRequestModel.tenant_id == org_id,
                )
            )
            res = await session.execute(stmt)
            return bool(res.scalar() or 0)

    async def create_full(
        self,
        payload: CommunicationRequestCreateSchema,
        org_id: str,
        created_by: str,
    ) -> CommunicationRequestModel:
        async with self.session_factory() as session:
            # Validate subject
            sub_type, sub_id = (
                _parse_subject_ref(payload.subject) if payload.subject else (None, None)
            )
            if sub_type and sub_id:
                await _validate_ref(session, org_id, sub_type, sub_id, "subject")

            # Validate encounter
            enc_type, enc_id = (
                _parse_encounter_ref(payload.encounter)
                if payload.encounter
                else (None, None)
            )
            if enc_type and enc_id:
                await _validate_ref(session, org_id, enc_type, enc_id, "encounter")

            # Validate requester
            req_type, req_id = (
                _parse_requester_ref(payload.requester)
                if payload.requester
                else (None, None)
            )
            if req_type and req_id:
                await _validate_ref(session, org_id, req_type, req_id, "requester")

            # Validate sender
            snd_type, snd_id = (
                _parse_sender_ref(payload.sender) if payload.sender else (None, None)
            )
            if snd_type and snd_id:
                await _validate_ref(session, org_id, snd_type, snd_id, "sender")

            # Validate group_identifier assigner
            g_assigner_type, g_assigner_id = (
                _parse_assigner_ref(payload.group_identifier_assigner)
                if payload.group_identifier_assigner
                else (None, None)
            )
            if g_assigner_type and g_assigner_id:
                await _validate_ref(
                    session,
                    org_id,
                    g_assigner_type,
                    g_assigner_id,
                    "group_identifier_assigner",
                )

            model = CommunicationRequestModel(
                tenant_id=org_id,
                created_by=created_by,
                status=payload.status,
                status_reason_text=payload.status_reason_text,
                priority=payload.priority,
                do_not_perform=payload.do_not_perform,
                group_identifier_use=payload.group_identifier_use,
                group_identifier_system=payload.group_identifier_system,
                group_identifier_value=payload.group_identifier_value,
                group_identifier_period_start=payload.group_identifier_period_start,
                group_identifier_period_end=payload.group_identifier_period_end,
                group_identifier_assigner_reference=payload.group_identifier_assigner,
                group_identifier_assigner_type=g_assigner_type,
                group_identifier_assigner_id=g_assigner_id,
                group_identifier_assigner_display=payload.group_identifier_assigner_display,
                subject_reference=payload.subject,
                subject_type=sub_type,
                subject_id=sub_id,
                subject_display=payload.subject_display,
                encounter_reference=payload.encounter,
                encounter_type=enc_type,
                encounter_id=enc_id,
                encounter_display=payload.encounter_display,
                occurrence_date_time=payload.occurrence_date_time,
                occurrence_period_start=payload.occurrence_period_start,
                occurrence_period_end=payload.occurrence_period_end,
                authored_on=payload.authored_on,
                requester_reference=payload.requester,
                requester_type=req_type,
                requester_id=req_id,
                requester_display=payload.requester_display,
                sender_reference=payload.sender,
                sender_type=snd_type,
                sender_id=snd_id,
                sender_display=payload.sender_display,
                extension=payload.extension or [],
            )
            session.add(model)
            await session.flush()

            if payload.identifier:
                await _add_identifiers(
                    session, model.id, org_id, payload.identifier, created_by
                )

            if payload.based_on:
                await _add_based_on(
                    session, model.id, org_id, payload.based_on, created_by
                )

            if payload.replaces:
                await _add_replaces(
                    session, model.id, org_id, payload.replaces, created_by
                )

            if payload.status_reason_coding:
                _add_codings(
                    session,
                    CommunicationRequestStatusReasonCoding,
                    model.id,
                    org_id,
                    payload.status_reason_coding,
                    created_by,
                )

            if payload.category:
                await _add_categories(
                    session, model.id, org_id, payload.category, created_by
                )

            if payload.medium:
                await _add_mediums(
                    session, model.id, org_id, payload.medium, created_by
                )

            if payload.about:
                await _add_about(session, model.id, org_id, payload.about, created_by)

            if payload.payload:
                await _add_payloads(
                    session, model.id, org_id, payload.payload, created_by
                )

            if payload.recipient:
                await _add_recipients(
                    session, model.id, org_id, payload.recipient, created_by
                )

            if payload.reason_code:
                await _add_reason_codes(
                    session, model.id, org_id, payload.reason_code, created_by
                )

            if payload.reason_reference:
                await _add_reason_references(
                    session, model.id, org_id, payload.reason_reference, created_by
                )

            if payload.note:
                await _add_notes(session, model.id, org_id, payload.note, created_by)

            await session.commit()
            return await self.get_by_communication_request_id(
                model.communication_request_id
            )

    async def patch_full(
        self,
        communication_request_id: int,
        payload: CommunicationRequestPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> CommunicationRequestModel:
        async with self.session_factory() as session:
            stmt = select(CommunicationRequestModel).where(
                CommunicationRequestModel.communication_request_id
                == communication_request_id,
                CommunicationRequestModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                raise ValueError(
                    f"CommunicationRequest {communication_request_id} not found in org {org_id}"
                )

            provided = payload.model_fields_set

            if "status" in provided and payload.status is not None:
                model.status = payload.status
            if "status_reason_text" in provided:
                model.status_reason_text = payload.status_reason_text
            if "priority" in provided:
                model.priority = payload.priority
            if "do_not_perform" in provided:
                model.do_not_perform = payload.do_not_perform
            if "occurrence_date_time" in provided:
                model.occurrence_date_time = payload.occurrence_date_time
            if "occurrence_period_start" in provided:
                model.occurrence_period_start = payload.occurrence_period_start
            if "occurrence_period_end" in provided:
                model.occurrence_period_end = payload.occurrence_period_end
            if "authored_on" in provided:
                model.authored_on = payload.authored_on
            if "extension" in provided:
                model.extension = payload.extension or []

            # Group identifier fields
            if "group_identifier_use" in provided:
                model.group_identifier_use = payload.group_identifier_use
            if "group_identifier_system" in provided:
                model.group_identifier_system = payload.group_identifier_system
            if "group_identifier_value" in provided:
                model.group_identifier_value = payload.group_identifier_value
            if "group_identifier_period_start" in provided:
                model.group_identifier_period_start = (
                    payload.group_identifier_period_start
                )
            if "group_identifier_period_end" in provided:
                model.group_identifier_period_end = payload.group_identifier_period_end
            if (
                "group_identifier_assigner" in provided
                or "group_identifier_assigner_display" in provided
            ):
                g_ref = payload.group_identifier_assigner
                g_type, g_id = (
                    _parse_assigner_ref(g_ref) if g_ref else (None, None)
                )
                if g_type and g_id:
                    await _validate_ref(
                        session,
                        org_id,
                        g_type,
                        g_id,
                        "group_identifier_assigner",
                    )
                model.group_identifier_assigner_reference = g_ref
                model.group_identifier_assigner_type = g_type
                model.group_identifier_assigner_id = g_id
                if "group_identifier_assigner_display" in provided:
                    model.group_identifier_assigner_display = (
                        payload.group_identifier_assigner_display
                    )

            # References
            if "subject" in provided or "subject_display" in provided:
                sub_ref = payload.subject or model.subject_reference
                sub_type, sub_id = (
                    _parse_subject_ref(sub_ref) if sub_ref else (None, None)
                )
                if sub_type and sub_id:
                    await _validate_ref(session, org_id, sub_type, sub_id, "subject")
                model.subject_reference = sub_ref
                model.subject_type = sub_type
                model.subject_id = sub_id
                if "subject_display" in provided:
                    model.subject_display = payload.subject_display

            if "encounter" in provided or "encounter_display" in provided:
                enc_ref = payload.encounter
                enc_type, enc_id = (
                    _parse_encounter_ref(enc_ref) if enc_ref else (None, None)
                )
                if enc_type and enc_id:
                    await _validate_ref(
                        session, org_id, enc_type, enc_id, "encounter"
                    )
                model.encounter_reference = enc_ref
                model.encounter_type = enc_type
                model.encounter_id = enc_id
                if "encounter_display" in provided:
                    model.encounter_display = payload.encounter_display

            if "requester" in provided or "requester_display" in provided:
                req_ref = payload.requester
                req_type, req_id = (
                    _parse_requester_ref(req_ref) if req_ref else (None, None)
                )
                if req_type and req_id:
                    await _validate_ref(
                        session, org_id, req_type, req_id, "requester"
                    )
                model.requester_reference = req_ref
                model.requester_type = req_type
                model.requester_id = req_id
                if "requester_display" in provided:
                    model.requester_display = payload.requester_display

            if "sender" in provided or "sender_display" in provided:
                snd_ref = payload.sender
                snd_type, snd_id = (
                    _parse_sender_ref(snd_ref) if snd_ref else (None, None)
                )
                if snd_type and snd_id:
                    await _validate_ref(session, org_id, snd_type, snd_id, "sender")
                model.sender_reference = snd_ref
                model.sender_type = snd_type
                model.sender_id = snd_id
                if "sender_display" in provided:
                    model.sender_display = payload.sender_display

            model.updated_by = updated_by

            # Child tables
            if "identifier" in provided:
                await session.execute(
                    delete(CommunicationRequestIdentifier).where(
                        CommunicationRequestIdentifier.communication_request_pk
                        == model.id
                    )
                )
                if payload.identifier:
                    await _add_identifiers(
                        session, model.id, org_id, payload.identifier, updated_by
                    )

            if "based_on" in provided:
                await session.execute(
                    delete(CommunicationRequestBasedOn).where(
                        CommunicationRequestBasedOn.communication_request_pk
                        == model.id
                    )
                )
                if payload.based_on:
                    await _add_based_on(
                        session, model.id, org_id, payload.based_on, updated_by
                    )

            if "replaces" in provided:
                await session.execute(
                    delete(CommunicationRequestReplaces).where(
                        CommunicationRequestReplaces.communication_request_pk
                        == model.id
                    )
                )
                if payload.replaces:
                    await _add_replaces(
                        session, model.id, org_id, payload.replaces, updated_by
                    )

            if "status_reason_coding" in provided:
                await session.execute(
                    delete(CommunicationRequestStatusReasonCoding).where(
                        CommunicationRequestStatusReasonCoding.communication_request_pk
                        == model.id
                    )
                )
                if payload.status_reason_coding:
                    _add_codings(
                        session,
                        CommunicationRequestStatusReasonCoding,
                        model.id,
                        org_id,
                        payload.status_reason_coding,
                        updated_by,
                    )

            if "category" in provided:
                await session.execute(
                    delete(CommunicationRequestCategory).where(
                        CommunicationRequestCategory.communication_request_pk
                        == model.id
                    )
                )
                if payload.category:
                    await _add_categories(
                        session, model.id, org_id, payload.category, updated_by
                    )

            if "medium" in provided:
                await session.execute(
                    delete(CommunicationRequestMedium).where(
                        CommunicationRequestMedium.communication_request_pk
                        == model.id
                    )
                )
                if payload.medium:
                    await _add_mediums(
                        session, model.id, org_id, payload.medium, updated_by
                    )

            if "about" in provided:
                await session.execute(
                    delete(CommunicationRequestAbout).where(
                        CommunicationRequestAbout.communication_request_pk
                        == model.id
                    )
                )
                if payload.about:
                    await _add_about(
                        session, model.id, org_id, payload.about, updated_by
                    )

            if "payload" in provided:
                await session.execute(
                    delete(CommunicationRequestPayload).where(
                        CommunicationRequestPayload.communication_request_pk
                        == model.id
                    )
                )
                if payload.payload:
                    await _add_payloads(
                        session, model.id, org_id, payload.payload, updated_by
                    )

            if "recipient" in provided:
                await session.execute(
                    delete(CommunicationRequestRecipient).where(
                        CommunicationRequestRecipient.communication_request_pk
                        == model.id
                    )
                )
                if payload.recipient:
                    await _add_recipients(
                        session, model.id, org_id, payload.recipient, updated_by
                    )

            if "reason_code" in provided:
                await session.execute(
                    delete(CommunicationRequestReasonCode).where(
                        CommunicationRequestReasonCode.communication_request_pk
                        == model.id
                    )
                )
                if payload.reason_code:
                    await _add_reason_codes(
                        session, model.id, org_id, payload.reason_code, updated_by
                    )

            if "reason_reference" in provided:
                await session.execute(
                    delete(CommunicationRequestReasonReference).where(
                        CommunicationRequestReasonReference.communication_request_pk
                        == model.id
                    )
                )
                if payload.reason_reference:
                    await _add_reason_references(
                        session, model.id, org_id, payload.reason_reference, updated_by
                    )

            if "note" in provided:
                await session.execute(
                    delete(CommunicationRequestNote).where(
                        CommunicationRequestNote.communication_request_pk == model.id
                    )
                )
                if payload.note:
                    await _add_notes(
                        session, model.id, org_id, payload.note, updated_by
                    )

            await session.commit()
            return await self.get_by_communication_request_id(
                model.communication_request_id
            )

    async def list(
        self,
        org_id: str,
        subject: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        encounter: str | None = None,
        requester: str | None = None,
        sender: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[CommunicationRequestModel], int]:
        async with self.session_factory() as session:
            stmt = select(CommunicationRequestModel).where(
                CommunicationRequestModel.tenant_id == org_id
            )

            if subject:
                s_type, s_id = _parse_subject_ref(subject)
                if s_type and s_id:
                    stmt = stmt.where(
                        CommunicationRequestModel.subject_type == s_type,
                        CommunicationRequestModel.subject_id == s_id,
                    )
                else:
                    stmt = stmt.where(
                        CommunicationRequestModel.subject_reference == subject
                    )

            if status:
                stmt = stmt.where(CommunicationRequestModel.status == status)

            if priority:
                stmt = stmt.where(CommunicationRequestModel.priority == priority)

            if encounter:
                e_type, e_id = _parse_encounter_ref(encounter)
                if e_type and e_id:
                    stmt = stmt.where(
                        CommunicationRequestModel.encounter_type == e_type,
                        CommunicationRequestModel.encounter_id == e_id,
                    )
                else:
                    stmt = stmt.where(
                        CommunicationRequestModel.encounter_reference == encounter
                    )

            if requester:
                r_type, r_id = _parse_requester_ref(requester)
                if r_type and r_id:
                    stmt = stmt.where(
                        CommunicationRequestModel.requester_type == r_type,
                        CommunicationRequestModel.requester_id == r_id,
                    )
                else:
                    stmt = stmt.where(
                        CommunicationRequestModel.requester_reference == requester
                    )

            if sender:
                snd_type, snd_id = _parse_sender_ref(sender)
                if snd_type and snd_id:
                    stmt = stmt.where(
                        CommunicationRequestModel.sender_type == snd_type,
                        CommunicationRequestModel.sender_id == snd_id,
                    )
                else:
                    stmt = stmt.where(
                        CommunicationRequestModel.sender_reference == sender
                    )

            # Count total
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_res = await session.execute(count_stmt)
            total = total_res.scalar() or 0

            # Sorting
            sort_col, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                CommunicationRequestModel.communication_request_id,
                default_desc=True,
            )
            stmt = (
                stmt.order_by(sort_col.desc() if sort_desc else sort_col.asc())
                .limit(limit)
                .offset(offset)
            )
            stmt = _with_relationships(stmt)

            res = await session.execute(stmt)
            items = list(res.scalars().all())
            return items, total

    async def delete(self, communication_request_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = delete(CommunicationRequestModel).where(
                CommunicationRequestModel.communication_request_id
                == communication_request_id,
                CommunicationRequestModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            await session.commit()
            return (res.rowcount or 0) > 0
