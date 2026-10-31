from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.document_reference import (
    DocumentReferenceAuthor,
    DocumentReferenceCategory,
    DocumentReferenceCategoryCoding,
    DocumentReferenceContent,
    DocumentReferenceContextEncounter,
    DocumentReferenceContextEvent,
    DocumentReferenceContextEventCoding,
    DocumentReferenceContextFacilityTypeCoding,
    DocumentReferenceContextPracticeSettingCoding,
    DocumentReferenceContextRelated,
    DocumentReferenceDocStatus as DocumentReferenceDocStatusModel,
    DocumentReferenceIdentifier,
    DocumentReferenceIdentifierTypeCoding,
    DocumentReferenceMasterIdentifierTypeCoding,
    DocumentReferenceModel,
    DocumentReferenceRelatesTo,
    DocumentReferenceSecurityLabel,
    DocumentReferenceSecurityLabelCoding,
    DocumentReferenceStatus as DocumentReferenceStatusModel,
    DocumentReferenceTypeCoding,
    DocumentRelationshipType as DocumentRelationshipTypeModel,
)
from app.models.enums import IdentifierUse as IdentifierUseModel
from app.schemas.document_reference import DocumentReferenceCreateSchema, DocumentReferencePatchSchema

from ._shared import (
    _parse_authenticator_ref,
    _parse_author_ref,
    _parse_context_encounter_ref,
    _parse_context_patient_ref,
    _parse_custodian_ref,
    _parse_open_ref,
    _parse_subject_ref,
    _parse_target_ref,
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


async def _add_identifiers(session, doc_pk: int, org_id: str, identifiers, created_by: str) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_custodian_ref(i.assigner) if i.assigner else (None, None)
        await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")
        ident = DocumentReferenceIdentifier(
            document_reference_pk=doc_pk,
            tenant_id=org_id,
            use=IdentifierUseModel[i.use.name] if i.use else None,
            type_text=i.type_text,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner_reference=i.assigner,
            assigner_type=a_type,
            assigner_id=a_id,
            assigner_display=i.assigner_display,
            assigner_identifier_use=(
                IdentifierUseModel[i.assigner_identifier_use.name]
                if i.assigner_identifier_use
                else None
            ),
            assigner_identifier_system=i.assigner_identifier_system,
            assigner_identifier_value=i.assigner_identifier_value,
            assigner_identifier_type_text=i.assigner_identifier_type_text,
            created_by=created_by,
        )
        session.add(ident)
        if i.type_coding:
            await session.flush()
            for c in i.type_coding:
                session.add(
                    DocumentReferenceIdentifierTypeCoding(
                        document_reference_identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


def _add_master_identifier_type_codings(session, doc_pk: int, org_id: str, mid, created_by: str) -> None:
    if mid and mid.type_coding:
        for c in mid.type_coding:
            session.add(
                DocumentReferenceMasterIdentifierTypeCoding(
                    document_reference_pk=doc_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


def _add_type_codings(session, doc_pk: int, org_id: str, concept, created_by: str) -> None:
    if concept and concept.coding:
        for c in concept.coding:
            session.add(
                DocumentReferenceTypeCoding(
                    document_reference_pk=doc_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_categories(session, doc_pk: int, org_id: str, categories, created_by: str) -> None:
    for cat in categories or []:
        c_obj = DocumentReferenceCategory(
            document_reference_pk=doc_pk,
            tenant_id=org_id,
            text=cat.text,
            created_by=created_by,
        )
        session.add(c_obj)
        if cat.coding:
            await session.flush()
            for c in cat.coding:
                session.add(
                    DocumentReferenceCategoryCoding(
                        document_reference_category_id=c_obj.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_authors(session, doc_pk: int, org_id: str, authors, created_by: str) -> None:
    for a in authors or []:
        a_type, a_id = _parse_author_ref(a)
        await _validate_ref(session, org_id, a_type, a_id, "author")
        session.add(
            DocumentReferenceAuthor(
                document_reference_pk=doc_pk,
                tenant_id=org_id,
                author_reference=a,
                author_type=a_type,
                author_id=a_id,
                created_by=created_by,
            )
        )


async def _add_relates_to(session, doc_pk: int, org_id: str, relates_to, created_by: str) -> None:
    for r in relates_to or []:
        t_type, t_id = _parse_target_ref(r.target)
        await _validate_ref(session, org_id, t_type, t_id, "relates_to.target")
        session.add(
            DocumentReferenceRelatesTo(
                document_reference_pk=doc_pk,
                tenant_id=org_id,
                code=DocumentRelationshipTypeModel[r.code.name],
                target_reference=r.target,
                target_type=t_type,
                target_id=t_id,
                target_display=r.target_display,
                created_by=created_by,
            )
        )


async def _add_security_labels(session, doc_pk: int, org_id: str, labels, created_by: str) -> None:
    for s in labels or []:
        s_obj = DocumentReferenceSecurityLabel(
            document_reference_pk=doc_pk,
            tenant_id=org_id,
            text=s.text,
            created_by=created_by,
        )
        session.add(s_obj)
        if s.coding:
            await session.flush()
            for c in s.coding:
                session.add(
                    DocumentReferenceSecurityLabelCoding(
                        document_reference_security_label_id=s_obj.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


def _add_contents(session, doc_pk: int, org_id: str, contents, created_by: str) -> None:
    for c in contents or []:
        att = c.attachment
        fmt = c.format
        session.add(
            DocumentReferenceContent(
                document_reference_pk=doc_pk,
                tenant_id=org_id,
                content_type=att.content_type,
                language=att.language,
                data=att.data,
                url=att.url,
                size=att.size,
                hash=att.hash,
                title=att.title,
                creation=att.creation,
                format_system=fmt.system if fmt else None,
                format_version=fmt.version if fmt else None,
                format_code=fmt.code if fmt else None,
                format_display=fmt.display if fmt else None,
                format_user_selected=fmt.user_selected if fmt else None,
                created_by=created_by,
            )
        )


async def _add_context(session, doc_pk: int, org_id: str, context, created_by: str) -> None:
    if not context:
        return

    if context.encounter:
        for e in context.encounter:
            e_type, e_id = _parse_context_encounter_ref(e)
            await _validate_ref(session, org_id, e_type, e_id, "context.encounter")
            session.add(
                DocumentReferenceContextEncounter(
                    document_reference_pk=doc_pk,
                    tenant_id=org_id,
                    reference_reference=e,
                    reference_type=e_type,
                    reference_id=e_id,
                    created_by=created_by,
                )
            )

    if context.event:
        for ev in context.event:
            ev_obj = DocumentReferenceContextEvent(
                document_reference_pk=doc_pk,
                tenant_id=org_id,
                text=ev.text,
                created_by=created_by,
            )
            session.add(ev_obj)
            if ev.coding:
                await session.flush()
                for c in ev.coding:
                    session.add(
                        DocumentReferenceContextEventCoding(
                            document_reference_context_event_id=ev_obj.id,
                            **_coding_kwargs(c, org_id, created_by),
                        )
                    )

    if context.facility_type and context.facility_type.coding:
        for c in context.facility_type.coding:
            session.add(
                DocumentReferenceContextFacilityTypeCoding(
                    document_reference_pk=doc_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )

    if context.practice_setting and context.practice_setting.coding:
        for c in context.practice_setting.coding:
            session.add(
                DocumentReferenceContextPracticeSettingCoding(
                    document_reference_pk=doc_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )

    if context.related:
        for r in context.related:
            raw, r_type, r_id, _ = _parse_open_ref(r)
            if r_type and r_id:
                await _validate_ref(session, org_id, r_type, r_id, "context.related")
            session.add(
                DocumentReferenceContextRelated(
                    document_reference_pk=doc_pk,
                    tenant_id=org_id,
                    reference_reference=r,
                    reference_type=r_type,
                    reference_id=r_id,
                    created_by=created_by,
                )
            )


class _FullMixin:
    """Full nested create and patch implementations for DocumentReference."""

    async def create_full(
        self,
        payload: DocumentReferenceCreateSchema,
        org_id: str,
        created_by: str,
    ) -> DocumentReferenceModel:
        async with self.session_factory() as session:
            # Validate references
            s_type, s_id = _parse_subject_ref(payload.subject) if payload.subject else (None, None)
            await _validate_ref(session, org_id, s_type, s_id, "subject")

            auth_type, auth_id = (
                _parse_authenticator_ref(payload.authenticator) if payload.authenticator else (None, None)
            )
            await _validate_ref(session, org_id, auth_type, auth_id, "authenticator")

            cust_type, cust_id = (
                _parse_custodian_ref(payload.custodian) if payload.custodian else (None, None)
            )
            await _validate_ref(session, org_id, cust_type, cust_id, "custodian")

            pat_type, pat_id = (
                _parse_context_patient_ref(payload.context.source_patient_info)
                if (payload.context and payload.context.source_patient_info)
                else (None, None)
            )
            await _validate_ref(session, org_id, pat_type, pat_id, "context.source_patient_info")

            mid = payload.master_identifier
            mid_a_type, mid_a_id = (
                _parse_custodian_ref(mid.assigner) if (mid and mid.assigner) else (None, None)
            )
            await _validate_ref(session, org_id, mid_a_type, mid_a_id, "master_identifier.assigner")

            doc = DocumentReferenceModel(
                tenant_id=org_id,
                created_by=created_by,
                status=DocumentReferenceStatusModel[payload.status.name],
                doc_status=DocumentReferenceDocStatusModel[payload.doc_status.name] if payload.doc_status else None,
                type_text=payload.type.text if payload.type else None,
                subject_reference=payload.subject,
                subject_type=s_type,
                subject_id=s_id,
                date=payload.date,
                authenticator_reference=payload.authenticator,
                authenticator_type=auth_type,
                authenticator_id=auth_id,
                custodian_reference=payload.custodian,
                custodian_type=cust_type,
                custodian_id=cust_id,
                description=payload.description,
                # Master identifier
                master_identifier_use=IdentifierUseModel[mid.use.name] if (mid and mid.use) else None,
                master_identifier_type_text=mid.type_text if mid else None,
                master_identifier_system=mid.system if mid else None,
                master_identifier_value=mid.value if mid else None,
                master_identifier_period_start=mid.period_start if mid else None,
                master_identifier_period_end=mid.period_end if mid else None,
                master_identifier_assigner_reference=mid.assigner if mid else None,
                master_identifier_assigner_type=mid_a_type,
                master_identifier_assigner_id=mid_a_id,
                master_identifier_assigner_display=mid.assigner_display if mid else None,
                master_identifier_assigner_identifier_use=(
                    IdentifierUseModel[mid.assigner_identifier_use.name]
                    if (mid and mid.assigner_identifier_use)
                    else None
                ),
                master_identifier_assigner_identifier_system=mid.assigner_identifier_system if mid else None,
                master_identifier_assigner_identifier_value=mid.assigner_identifier_value if mid else None,
                master_identifier_assigner_identifier_type_text=mid.assigner_identifier_type_text if mid else None,
                # Context 0..1 fields
                context_period_start=payload.context.period_start if payload.context else None,
                context_period_end=payload.context.period_end if payload.context else None,
                context_facility_type_text=payload.context.facility_type.text if (payload.context and payload.context.facility_type) else None,
                context_practice_setting_text=payload.context.practice_setting.text if (payload.context and payload.context.practice_setting) else None,
                context_source_patient_info_reference=payload.context.source_patient_info if payload.context else None,
                context_source_patient_info_type=pat_type,
                context_source_patient_info_id=pat_id,
            )
            session.add(doc)
            await session.flush()

            _add_master_identifier_type_codings(session, doc.id, org_id, mid, created_by)
            await _add_identifiers(session, doc.id, org_id, payload.identifier, created_by)
            _add_type_codings(session, doc.id, org_id, payload.type, created_by)
            await _add_categories(session, doc.id, org_id, payload.category, created_by)
            await _add_authors(session, doc.id, org_id, payload.author, created_by)
            await _add_relates_to(session, doc.id, org_id, payload.relates_to, created_by)
            await _add_security_labels(session, doc.id, org_id, payload.security_label, created_by)
            _add_contents(session, doc.id, org_id, payload.content, created_by)
            await _add_context(session, doc.id, org_id, payload.context, created_by)

            await session.commit()
            return await self.get_by_document_reference_id_in_org(doc.document_reference_id, org_id)

    async def patch_full(
        self,
        document_reference_id: int,
        payload: DocumentReferencePatchSchema,
        org_id: str,
        updated_by: str,
    ) -> DocumentReferenceModel:
        async with self.session_factory() as session:
            stmt = select(DocumentReferenceModel).where(
                DocumentReferenceModel.document_reference_id == document_reference_id,
                DocumentReferenceModel.tenant_id == org_id,
            )
            doc = (await session.execute(stmt)).scalars().first()
            if not doc:
                return None

            fields_set = payload.model_fields_set

            if "status" in fields_set and payload.status is not None:
                doc.status = DocumentReferenceStatusModel[payload.status.name]
            if "doc_status" in fields_set:
                doc.doc_status = (
                    DocumentReferenceDocStatusModel[payload.doc_status.name]
                    if payload.doc_status
                    else None
                )
            if "description" in fields_set:
                doc.description = payload.description
            if "date" in fields_set:
                doc.date = payload.date

            if "subject" in fields_set:
                s_type, s_id = _parse_subject_ref(payload.subject) if payload.subject else (None, None)
                await _validate_ref(session, org_id, s_type, s_id, "subject")
                doc.subject_reference = payload.subject
                doc.subject_type = s_type
                doc.subject_id = s_id

            if "authenticator" in fields_set:
                auth_type, auth_id = (
                    _parse_authenticator_ref(payload.authenticator) if payload.authenticator else (None, None)
                )
                await _validate_ref(session, org_id, auth_type, auth_id, "authenticator")
                doc.authenticator_reference = payload.authenticator
                doc.authenticator_type = auth_type
                doc.authenticator_id = auth_id

            if "custodian" in fields_set:
                cust_type, cust_id = (
                    _parse_custodian_ref(payload.custodian) if payload.custodian else (None, None)
                )
                await _validate_ref(session, org_id, cust_type, cust_id, "custodian")
                doc.custodian_reference = payload.custodian
                doc.custodian_type = cust_type
                doc.custodian_id = cust_id

            # Master identifier
            if "master_identifier" in fields_set:
                mid = payload.master_identifier
                mid_a_type, mid_a_id = (
                    _parse_custodian_ref(mid.assigner) if (mid and mid.assigner) else (None, None)
                )
                await _validate_ref(session, org_id, mid_a_type, mid_a_id, "master_identifier.assigner")
                doc.master_identifier_use = IdentifierUseModel[mid.use.name] if (mid and mid.use) else None
                doc.master_identifier_type_text = mid.type_text if mid else None
                doc.master_identifier_system = mid.system if mid else None
                doc.master_identifier_value = mid.value if mid else None
                doc.master_identifier_period_start = mid.period_start if mid else None
                doc.master_identifier_period_end = mid.period_end if mid else None
                doc.master_identifier_assigner_reference = mid.assigner if mid else None
                doc.master_identifier_assigner_type = mid_a_type
                doc.master_identifier_assigner_id = mid_a_id
                doc.master_identifier_assigner_display = mid.assigner_display if mid else None
                doc.master_identifier_assigner_identifier_use = (
                    IdentifierUseModel[mid.assigner_identifier_use.name]
                    if (mid and mid.assigner_identifier_use)
                    else None
                )
                doc.master_identifier_assigner_identifier_system = mid.assigner_identifier_system if mid else None
                doc.master_identifier_assigner_identifier_value = mid.assigner_identifier_value if mid else None
                doc.master_identifier_assigner_identifier_type_text = mid.assigner_identifier_type_text if mid else None

                await session.execute(
                    delete(DocumentReferenceMasterIdentifierTypeCoding).where(
                        DocumentReferenceMasterIdentifierTypeCoding.document_reference_pk == doc.id
                    )
                )
                _add_master_identifier_type_codings(session, doc.id, org_id, mid, updated_by)

            # Type
            if "type" in fields_set:
                doc.type_text = payload.type.text if payload.type else None
                await session.execute(
                    delete(DocumentReferenceTypeCoding).where(
                        DocumentReferenceTypeCoding.document_reference_pk == doc.id
                    )
                )
                _add_type_codings(session, doc.id, org_id, payload.type, updated_by)

            # Identifiers
            if "identifier" in fields_set:
                await session.execute(
                    delete(DocumentReferenceIdentifierTypeCoding).where(
                        DocumentReferenceIdentifierTypeCoding.document_reference_identifier_id.in_(
                            select(DocumentReferenceIdentifier.id).where(
                                DocumentReferenceIdentifier.document_reference_pk == doc.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(DocumentReferenceIdentifier).where(
                        DocumentReferenceIdentifier.document_reference_pk == doc.id
                    )
                )
                await _add_identifiers(session, doc.id, org_id, payload.identifier, updated_by)

            # Categories
            if "category" in fields_set:
                await session.execute(
                    delete(DocumentReferenceCategoryCoding).where(
                        DocumentReferenceCategoryCoding.document_reference_category_id.in_(
                            select(DocumentReferenceCategory.id).where(
                                DocumentReferenceCategory.document_reference_pk == doc.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(DocumentReferenceCategory).where(
                        DocumentReferenceCategory.document_reference_pk == doc.id
                    )
                )
                await _add_categories(session, doc.id, org_id, payload.category, updated_by)

            # Authors
            if "author" in fields_set:
                await session.execute(
                    delete(DocumentReferenceAuthor).where(
                        DocumentReferenceAuthor.document_reference_pk == doc.id
                    )
                )
                await _add_authors(session, doc.id, org_id, payload.author, updated_by)

            # Relates to
            if "relates_to" in fields_set:
                await session.execute(
                    delete(DocumentReferenceRelatesTo).where(
                        DocumentReferenceRelatesTo.document_reference_pk == doc.id
                    )
                )
                await _add_relates_to(session, doc.id, org_id, payload.relates_to, updated_by)

            # Security label
            if "security_label" in fields_set:
                await session.execute(
                    delete(DocumentReferenceSecurityLabelCoding).where(
                        DocumentReferenceSecurityLabelCoding.document_reference_security_label_id.in_(
                            select(DocumentReferenceSecurityLabel.id).where(
                                DocumentReferenceSecurityLabel.document_reference_pk == doc.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(DocumentReferenceSecurityLabel).where(
                        DocumentReferenceSecurityLabel.document_reference_pk == doc.id
                    )
                )
                await _add_security_labels(session, doc.id, org_id, payload.security_label, updated_by)

            # Contents
            if "content" in fields_set:
                await session.execute(
                    delete(DocumentReferenceContent).where(
                        DocumentReferenceContent.document_reference_pk == doc.id
                    )
                )
                _add_contents(session, doc.id, org_id, payload.content, updated_by)

            # Context
            if "context" in fields_set:
                ctx = payload.context
                pat_type, pat_id = (
                    _parse_context_patient_ref(ctx.source_patient_info)
                    if (ctx and ctx.source_patient_info)
                    else (None, None)
                )
                await _validate_ref(session, org_id, pat_type, pat_id, "context.source_patient_info")

                doc.context_period_start = ctx.period_start if ctx else None
                doc.context_period_end = ctx.period_end if ctx else None
                doc.context_facility_type_text = ctx.facility_type.text if (ctx and ctx.facility_type) else None
                doc.context_practice_setting_text = ctx.practice_setting.text if (ctx and ctx.practice_setting) else None
                doc.context_source_patient_info_reference = ctx.source_patient_info if ctx else None
                doc.context_source_patient_info_type = pat_type
                doc.context_source_patient_info_id = pat_id

                await session.execute(
                    delete(DocumentReferenceContextEventCoding).where(
                        DocumentReferenceContextEventCoding.document_reference_context_event_id.in_(
                            select(DocumentReferenceContextEvent.id).where(
                                DocumentReferenceContextEvent.document_reference_pk == doc.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(DocumentReferenceContextEvent).where(
                        DocumentReferenceContextEvent.document_reference_pk == doc.id
                    )
                )
                await session.execute(
                    delete(DocumentReferenceContextEncounter).where(
                        DocumentReferenceContextEncounter.document_reference_pk == doc.id
                    )
                )
                await session.execute(
                    delete(DocumentReferenceContextFacilityTypeCoding).where(
                        DocumentReferenceContextFacilityTypeCoding.document_reference_pk == doc.id
                    )
                )
                await session.execute(
                    delete(DocumentReferenceContextPracticeSettingCoding).where(
                        DocumentReferenceContextPracticeSettingCoding.document_reference_pk == doc.id
                    )
                )
                await session.execute(
                    delete(DocumentReferenceContextRelated).where(
                        DocumentReferenceContextRelated.document_reference_pk == doc.id
                    )
                )
                await _add_context(session, doc.id, org_id, ctx, updated_by)

            doc.updated_by = updated_by
            await session.commit()
            return await self.get_by_document_reference_id_in_org(doc.document_reference_id, org_id)
