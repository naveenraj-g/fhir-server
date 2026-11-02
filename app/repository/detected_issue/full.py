from sqlalchemy import delete, select

from app.core.filters import parse_reference
from app.core.logging import get_logger
from app.models.enums import (
    IdentifierUse as IdentifierUseModel,
    OrganizationReferenceType,
)
from app.models.detected_issue import (
    DetectedIssueAuthorReferenceType,
    DetectedIssueCodeCodingModel,
    DetectedIssueEvidenceCodeCodingModel,
    DetectedIssueEvidenceCodeModel,
    DetectedIssueEvidenceDetailModel,
    DetectedIssueEvidenceModel,
    DetectedIssueIdentifierModel,
    DetectedIssueIdentifierTypeCodingModel,
    DetectedIssueImplicatedModel,
    DetectedIssueMitigationActionCodingModel,
    DetectedIssueMitigationAuthorReferenceType,
    DetectedIssueMitigationModel,
    DetectedIssueModel,
    DetectedIssuePatientReferenceType,
)
from app.schemas.detected_issue import (
    DetectedIssueCreateSchema,
    DetectedIssuePatchSchema,
)

from ._shared import (
    _list_reference_kwargs,
    _single_reference_kwargs,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)


class _FullMixin:
    """Atomic full Create & Patch operations for DetectedIssue."""

    async def create(
        self,
        payload: DetectedIssueCreateSchema,
        org_id: str,
        actor_id: str,
    ) -> DetectedIssueModel:
        async with self.session_factory() as session:
            # 1. References validation
            patient_kwargs = _single_reference_kwargs(
                "patient", payload.patient, DetectedIssuePatientReferenceType
            )
            if payload.patient:
                await _validate_ref(
                    session,
                    patient_kwargs["patient_type"],
                    patient_kwargs["patient_id"],
                    org_id,
                    "patient",
                )

            author_kwargs = _single_reference_kwargs(
                "author", payload.author, DetectedIssueAuthorReferenceType
            )
            if payload.author:
                await _validate_ref(
                    session,
                    author_kwargs["author_type"],
                    author_kwargs["author_id"],
                    org_id,
                    "author",
                )

            if payload.implicated:
                for imp in payload.implicated:
                    imp_kwargs = _list_reference_kwargs(imp, None, prefix="implicated")
                    await _validate_ref(
                        session,
                        imp_kwargs["implicated_type"],
                        imp_kwargs["implicated_id"],
                        org_id,
                        "implicated",
                    )

            if payload.evidence:
                for ev in payload.evidence:
                    if ev.detail:
                        for d in ev.detail:
                            d_kwargs = _list_reference_kwargs(d, None, prefix="detail")
                            await _validate_ref(
                                session,
                                d_kwargs["detail_type"],
                                d_kwargs["detail_id"],
                                org_id,
                                "evidence.detail",
                            )

            if payload.mitigation:
                for m in payload.mitigation:
                    if m.author:
                        m_author_kwargs = _single_reference_kwargs(
                            "author", m.author, DetectedIssueMitigationAuthorReferenceType
                        )
                        await _validate_ref(
                            session,
                            m_author_kwargs["author_type"],
                            m_author_kwargs["author_id"],
                            org_id,
                            "mitigation.author",
                        )

            if payload.identifier:
                for ident in payload.identifier:
                    if ident.assigner:
                        assigner_type, assigner_id = parse_reference(
                            ident.assigner, OrganizationReferenceType
                        )
                        await _validate_ref(
                            session,
                            assigner_type,
                            assigner_id,
                            org_id,
                            "identifier.assigner",
                        )

            # 2. Construct parent model
            model = DetectedIssueModel(
                tenant_id=org_id,
                created_by=actor_id,
                updated_by=actor_id,
                status=payload.status,
                code_text=payload.code.text if payload.code else None,
                severity=payload.severity,
                identified_date_time=payload.identified_date_time,
                identified_period_start=payload.identified_period_start,
                identified_period_end=payload.identified_period_end,
                detail=payload.detail,
                reference=payload.reference,
                extension=payload.extension,
                **patient_kwargs,
                **author_kwargs,
            )
            session.add(model)
            await session.flush()

            # 3. Add code codings
            if payload.code and payload.code.coding:
                for c in payload.code.coding:
                    session.add(
                        DetectedIssueCodeCodingModel(
                            detected_issue_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            updated_by=actor_id,
                            system=c.system,
                            version=c.version,
                            code=c.code,
                            display=c.display,
                            user_selected=c.user_selected,
                        )
                    )

            # 4. Add implicated resources
            if payload.implicated:
                for imp in payload.implicated:
                    imp_kwargs = _list_reference_kwargs(imp, None, prefix="implicated")
                    session.add(
                        DetectedIssueImplicatedModel(
                            detected_issue_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            updated_by=actor_id,
                            **imp_kwargs,
                        )
                    )

            # 5. Add evidence list
            if payload.evidence:
                for ev in payload.evidence:
                    ev_model = DetectedIssueEvidenceModel(
                        detected_issue_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                    session.add(ev_model)
                    await session.flush()

                    if ev.code:
                        for ev_c in ev.code:
                            ev_code_model = DetectedIssueEvidenceCodeModel(
                                detected_issue_evidence_id=ev_model.id,
                                tenant_id=org_id,
                                created_by=actor_id,
                                updated_by=actor_id,
                                text=ev_c.text,
                            )
                            session.add(ev_code_model)
                            await session.flush()

                            if ev_c.coding:
                                for c in ev_c.coding:
                                    session.add(
                                        DetectedIssueEvidenceCodeCodingModel(
                                            detected_issue_evidence_code_id=ev_code_model.id,
                                            tenant_id=org_id,
                                            created_by=actor_id,
                                            updated_by=actor_id,
                                            system=c.system,
                                            version=c.version,
                                            code=c.code,
                                            display=c.display,
                                            user_selected=c.user_selected,
                                        )
                                    )

                    if ev.detail:
                        for d in ev.detail:
                            d_kwargs = _list_reference_kwargs(d, None, prefix="detail")
                            session.add(
                                DetectedIssueEvidenceDetailModel(
                                    detected_issue_evidence_id=ev_model.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    updated_by=actor_id,
                                    **d_kwargs,
                                )
                            )

            # 6. Add mitigations
            if payload.mitigation:
                for m in payload.mitigation:
                    m_author_kwargs = (
                        _single_reference_kwargs(
                            "author", m.author, DetectedIssueMitigationAuthorReferenceType
                        )
                        if m.author
                        else _single_reference_kwargs(
                            "author", None, DetectedIssueMitigationAuthorReferenceType
                        )
                    )
                    m_model = DetectedIssueMitigationModel(
                        detected_issue_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        updated_by=actor_id,
                        action_text=m.action.text if m.action else None,
                        date=m.date,
                        **m_author_kwargs,
                    )
                    session.add(m_model)
                    await session.flush()

                    if m.action and m.action.coding:
                        for c in m.action.coding:
                            session.add(
                                DetectedIssueMitigationActionCodingModel(
                                    detected_issue_mitigation_id=m_model.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    updated_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )

            # 7. Add identifiers
            if payload.identifier:
                for ident in payload.identifier:
                    assigner_ref = ident.assigner
                    assigner_type, assigner_id = (
                        parse_reference(assigner_ref, OrganizationReferenceType)
                        if assigner_ref
                        else (None, None)
                    )
                    ident_model = DetectedIssueIdentifierModel(
                        detected_issue_pk=model.id,
                        tenant_id=org_id,
                        created_by=actor_id,
                        updated_by=actor_id,
                        use=(
                            IdentifierUseModel[ident.use.name]
                            if ident.use
                            else None
                        ),
                        system=ident.system,
                        value=ident.value,
                        period_start=ident.period_start,
                        period_end=ident.period_end,
                        assigner_reference=assigner_ref,
                        assigner_type=assigner_type,
                        assigner_id=assigner_id,
                        assigner_display=ident.assigner_display,
                        type_text=ident.type.text if ident.type else None,
                        assigner_identifier_use=(
                            IdentifierUseModel[ident.assigner_identifier_use.name]
                            if ident.assigner_identifier_use
                            else None
                        ),
                        assigner_identifier_type_system=ident.assigner_identifier_type_system,
                        assigner_identifier_type_version=ident.assigner_identifier_type_version,
                        assigner_identifier_type_code=ident.assigner_identifier_type_code,
                        assigner_identifier_type_display=ident.assigner_identifier_type_display,
                        assigner_identifier_type_user_selected=ident.assigner_identifier_type_user_selected,
                        assigner_identifier_type_text=ident.assigner_identifier_type_text,
                        assigner_identifier_system=ident.assigner_identifier_system,
                        assigner_identifier_value=ident.assigner_identifier_value,
                        assigner_identifier_period_start=ident.assigner_identifier_period_start,
                        assigner_identifier_period_end=ident.assigner_identifier_period_end,
                    )
                    session.add(ident_model)
                    await session.flush()

                    if ident.type and ident.type.coding:
                        for c in ident.type.coding:
                            session.add(
                                DetectedIssueIdentifierTypeCodingModel(
                                    detected_issue_identifier_id=ident_model.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    updated_by=actor_id,
                                    system=c.system,
                                    version=c.version,
                                    code=c.code,
                                    display=c.display,
                                    user_selected=c.user_selected,
                                )
                            )

            await session.commit()
            return await self.get_by_detected_issue_id_in_org(
                model.detected_issue_id, org_id
            )

    async def patch(
        self,
        detected_issue_id: int,
        payload: DetectedIssuePatchSchema,
        org_id: str,
        actor_id: str,
    ) -> DetectedIssueModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(DetectedIssueModel).where(
                    DetectedIssueModel.detected_issue_id == detected_issue_id,
                    DetectedIssueModel.tenant_id == org_id,
                )
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            provided = payload.model_dump(exclude_unset=True)
            model.updated_by = actor_id

            # Simple scalar fields
            if "status" in provided:
                model.status = payload.status
            if "severity" in provided:
                model.severity = payload.severity
            if "detail" in provided:
                model.detail = payload.detail
            if "reference" in provided:
                model.reference = payload.reference
            if "extension" in provided:
                model.extension = payload.extension

            # identified[x] choice fields
            if (
                "identified_date_time" in provided
                or "identified_period_start" in provided
                or "identified_period_end" in provided
            ):
                model.identified_date_time = payload.identified_date_time
                model.identified_period_start = payload.identified_period_start
                model.identified_period_end = payload.identified_period_end

            # Single reference: patient
            if "patient" in provided:
                patient_kwargs = _single_reference_kwargs(
                    "patient", payload.patient, DetectedIssuePatientReferenceType
                )
                if payload.patient:
                    await _validate_ref(
                        session,
                        patient_kwargs["patient_type"],
                        patient_kwargs["patient_id"],
                        org_id,
                        "patient",
                    )
                for k, v in patient_kwargs.items():
                    setattr(model, k, v)

            # Single reference: author
            if "author" in provided:
                author_kwargs = _single_reference_kwargs(
                    "author", payload.author, DetectedIssueAuthorReferenceType
                )
                if payload.author:
                    await _validate_ref(
                        session,
                        author_kwargs["author_type"],
                        author_kwargs["author_id"],
                        org_id,
                        "author",
                    )
                for k, v in author_kwargs.items():
                    setattr(model, k, v)

            # CodeableConcept: code
            if "code" in provided:
                await session.execute(
                    delete(DetectedIssueCodeCodingModel).where(
                        DetectedIssueCodeCodingModel.detected_issue_pk == model.id
                    )
                )
                model.code_text = payload.code.text if payload.code else None
                if payload.code and payload.code.coding:
                    for c in payload.code.coding:
                        session.add(
                            DetectedIssueCodeCodingModel(
                                detected_issue_pk=model.id,
                                tenant_id=org_id,
                                created_by=actor_id,
                                updated_by=actor_id,
                                system=c.system,
                                version=c.version,
                                code=c.code,
                                display=c.display,
                                user_selected=c.user_selected,
                            )
                        )

            # List: implicated
            if "implicated" in provided:
                await session.execute(
                    delete(DetectedIssueImplicatedModel).where(
                        DetectedIssueImplicatedModel.detected_issue_pk == model.id
                    )
                )
                if payload.implicated:
                    for imp in payload.implicated:
                        imp_kwargs = _list_reference_kwargs(imp, None, prefix="implicated")
                        await _validate_ref(
                            session,
                            imp_kwargs["implicated_type"],
                            imp_kwargs["implicated_id"],
                            org_id,
                            "implicated",
                        )
                        session.add(
                            DetectedIssueImplicatedModel(
                                detected_issue_pk=model.id,
                                tenant_id=org_id,
                                created_by=actor_id,
                                updated_by=actor_id,
                                **imp_kwargs,
                            )
                        )

            # List: evidence
            if "evidence" in provided:
                ev_ids = (
                    await session.execute(
                        select(DetectedIssueEvidenceModel.id).where(
                            DetectedIssueEvidenceModel.detected_issue_pk == model.id
                        )
                    )
                ).scalars().all()
                if ev_ids:
                    code_ids = (
                        await session.execute(
                            select(DetectedIssueEvidenceCodeModel.id).where(
                                DetectedIssueEvidenceCodeModel.detected_issue_evidence_id.in_(
                                    ev_ids
                                )
                            )
                        )
                    ).scalars().all()
                    if code_ids:
                        await session.execute(
                            delete(DetectedIssueEvidenceCodeCodingModel).where(
                                DetectedIssueEvidenceCodeCodingModel.detected_issue_evidence_code_id.in_(
                                    code_ids
                                )
                            )
                        )
                        await session.execute(
                            delete(DetectedIssueEvidenceCodeModel).where(
                                DetectedIssueEvidenceCodeModel.detected_issue_evidence_id.in_(
                                    ev_ids
                                )
                            )
                        )

                    await session.execute(
                        delete(DetectedIssueEvidenceDetailModel).where(
                            DetectedIssueEvidenceDetailModel.detected_issue_evidence_id.in_(
                                ev_ids
                            )
                        )
                    )
                    await session.execute(
                        delete(DetectedIssueEvidenceModel).where(
                            DetectedIssueEvidenceModel.detected_issue_pk == model.id
                        )
                    )

                if payload.evidence:
                    for ev in payload.evidence:
                        ev_model = DetectedIssueEvidenceModel(
                            detected_issue_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            updated_by=actor_id,
                        )
                        session.add(ev_model)
                        await session.flush()

                        if ev.code:
                            for ev_c in ev.code:
                                ev_code_model = DetectedIssueEvidenceCodeModel(
                                    detected_issue_evidence_id=ev_model.id,
                                    tenant_id=org_id,
                                    created_by=actor_id,
                                    updated_by=actor_id,
                                    text=ev_c.text,
                                )
                                session.add(ev_code_model)
                                await session.flush()

                                if ev_c.coding:
                                    for c in ev_c.coding:
                                        session.add(
                                            DetectedIssueEvidenceCodeCodingModel(
                                                detected_issue_evidence_code_id=ev_code_model.id,
                                                tenant_id=org_id,
                                                created_by=actor_id,
                                                updated_by=actor_id,
                                                system=c.system,
                                                version=c.version,
                                                code=c.code,
                                                display=c.display,
                                                user_selected=c.user_selected,
                                            )
                                        )

                        if ev.detail:
                            for d in ev.detail:
                                d_kwargs = _list_reference_kwargs(d, None, prefix="detail")
                                await _validate_ref(
                                    session,
                                    d_kwargs["detail_type"],
                                    d_kwargs["detail_id"],
                                    org_id,
                                    "evidence.detail",
                                )
                                session.add(
                                    DetectedIssueEvidenceDetailModel(
                                        detected_issue_evidence_id=ev_model.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        updated_by=actor_id,
                                        **d_kwargs,
                                    )
                                )

            # List: mitigation
            if "mitigation" in provided:
                mit_ids = (
                    await session.execute(
                        select(DetectedIssueMitigationModel.id).where(
                            DetectedIssueMitigationModel.detected_issue_pk == model.id
                        )
                    )
                ).scalars().all()
                if mit_ids:
                    await session.execute(
                        delete(DetectedIssueMitigationActionCodingModel).where(
                            DetectedIssueMitigationActionCodingModel.detected_issue_mitigation_id.in_(
                                mit_ids
                            )
                        )
                    )
                    await session.execute(
                        delete(DetectedIssueMitigationModel).where(
                            DetectedIssueMitigationModel.detected_issue_pk == model.id
                        )
                    )

                if payload.mitigation:
                    for m in payload.mitigation:
                        m_author_kwargs = (
                            _single_reference_kwargs(
                                "author",
                                m.author,
                                DetectedIssueMitigationAuthorReferenceType,
                            )
                            if m.author
                            else _single_reference_kwargs(
                                "author",
                                None,
                                DetectedIssueMitigationAuthorReferenceType,
                            )
                        )
                        if m.author:
                            await _validate_ref(
                                session,
                                m_author_kwargs["author_type"],
                                m_author_kwargs["author_id"],
                                org_id,
                                "mitigation.author",
                            )
                        m_model = DetectedIssueMitigationModel(
                            detected_issue_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            updated_by=actor_id,
                            action_text=m.action.text if m.action else None,
                            date=m.date,
                            **m_author_kwargs,
                        )
                        session.add(m_model)
                        await session.flush()

                        if m.action and m.action.coding:
                            for c in m.action.coding:
                                session.add(
                                    DetectedIssueMitigationActionCodingModel(
                                        detected_issue_mitigation_id=m_model.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        updated_by=actor_id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                    )
                                )

            # List: identifier
            if "identifier" in provided:
                ident_ids = (
                    await session.execute(
                        select(DetectedIssueIdentifierModel.id).where(
                            DetectedIssueIdentifierModel.detected_issue_pk == model.id
                        )
                    )
                ).scalars().all()
                if ident_ids:
                    await session.execute(
                        delete(DetectedIssueIdentifierTypeCodingModel).where(
                            DetectedIssueIdentifierTypeCodingModel.detected_issue_identifier_id.in_(
                                ident_ids
                            )
                        )
                    )
                    await session.execute(
                        delete(DetectedIssueIdentifierModel).where(
                            DetectedIssueIdentifierModel.detected_issue_pk == model.id
                        )
                    )

                if payload.identifier:
                    for ident in payload.identifier:
                        assigner_ref = ident.assigner
                        assigner_type, assigner_id = (
                            parse_reference(assigner_ref, OrganizationReferenceType)
                            if assigner_ref
                            else (None, None)
                        )
                        if assigner_ref:
                            await _validate_ref(
                                session,
                                assigner_type,
                                assigner_id,
                                org_id,
                                "identifier.assigner",
                            )
                        ident_model = DetectedIssueIdentifierModel(
                            detected_issue_pk=model.id,
                            tenant_id=org_id,
                            created_by=actor_id,
                            updated_by=actor_id,
                            use=(
                                IdentifierUseModel[ident.use.name]
                                if ident.use
                                else None
                            ),
                            system=ident.system,
                            value=ident.value,
                            period_start=ident.period_start,
                            period_end=ident.period_end,
                            assigner_reference=assigner_ref,
                            assigner_type=assigner_type,
                            assigner_id=assigner_id,
                            assigner_display=ident.assigner_display,
                            type_text=ident.type.text if ident.type else None,
                            assigner_identifier_use=(
                                IdentifierUseModel[ident.assigner_identifier_use.name]
                                if ident.assigner_identifier_use
                                else None
                            ),
                            assigner_identifier_type_system=ident.assigner_identifier_type_system,
                            assigner_identifier_type_version=ident.assigner_identifier_type_version,
                            assigner_identifier_type_code=ident.assigner_identifier_type_code,
                            assigner_identifier_type_display=ident.assigner_identifier_type_display,
                            assigner_identifier_type_user_selected=ident.assigner_identifier_type_user_selected,
                            assigner_identifier_type_text=ident.assigner_identifier_type_text,
                            assigner_identifier_system=ident.assigner_identifier_system,
                            assigner_identifier_value=ident.assigner_identifier_value,
                            assigner_identifier_period_start=ident.assigner_identifier_period_start,
                            assigner_identifier_period_end=ident.assigner_identifier_period_end,
                        )
                        session.add(ident_model)
                        await session.flush()

                        if ident.type and ident.type.coding:
                            for c in ident.type.coding:
                                session.add(
                                    DetectedIssueIdentifierTypeCodingModel(
                                        detected_issue_identifier_id=ident_model.id,
                                        tenant_id=org_id,
                                        created_by=actor_id,
                                        updated_by=actor_id,
                                        system=c.system,
                                        version=c.version,
                                        code=c.code,
                                        display=c.display,
                                        user_selected=c.user_selected,
                                    )
                                )

            await session.commit()
            return await self.get_by_detected_issue_id_in_org(
                detected_issue_id, org_id
            )

    create_full = create
    patch_full = patch

