from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.models.enums import IdentifierUse as IdentifierUseModel
from app.models.specimen import (
    SpecimenAccessionIdentifierTypeCoding,
    SpecimenCollectionBodySiteCoding,
    SpecimenCollectionFastingStatusCoding,
    SpecimenCollectionMethodCoding,
    SpecimenCondition,
    SpecimenConditionCoding,
    SpecimenContainer,
    SpecimenContainerAdditiveCoding,
    SpecimenContainerIdentifier,
    SpecimenContainerIdentifierTypeCoding,
    SpecimenContainerTypeCoding,
    SpecimenIdentifier,
    SpecimenIdentifierTypeCoding,
    SpecimenModel,
    SpecimenNote,
    SpecimenParent,
    SpecimenProcessing,
    SpecimenProcessingAdditive,
    SpecimenProcessingProcedureCoding,
    SpecimenQuantityComparator as SpecimenQuantityComparatorModel,
    SpecimenRequest,
    SpecimenStatus as SpecimenStatusModel,
    SpecimenTypeCoding,
)
from app.schemas.specimen import SpecimenCreateSchema, SpecimenPatchSchema

from ._shared import (
    _parse_additive_ref,
    _parse_collector_ref,
    _parse_note_author_ref,
    _parse_org_ref,
    _parse_parent_ref,
    _parse_request_ref,
    _parse_subject_ref,
    _reference_kwargs,
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


async def _add_identifiers(session, specimen_pk: int, org_id: str, identifiers, created_by: str) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_org_ref(i.assigner) if i.assigner else (None, None)
        await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")
        ident = SpecimenIdentifier(
            specimen_pk=specimen_pk,
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
                    SpecimenIdentifierTypeCoding(
                        specimen_identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


def _add_accession_type_codings(session, specimen_pk: int, org_id: str, acc, created_by: str) -> None:
    if acc and acc.type_coding:
        for c in acc.type_coding:
            session.add(
                SpecimenAccessionIdentifierTypeCoding(
                    specimen_pk=specimen_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


def _add_type_codings(session, specimen_pk: int, org_id: str, type_concept, created_by: str) -> None:
    if type_concept and type_concept.coding:
        for c in type_concept.coding:
            session.add(
                SpecimenTypeCoding(
                    specimen_pk=specimen_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_parents(session, specimen_pk: int, org_id: str, parents, created_by: str) -> None:
    for p in parents or []:
        p_type, p_id = _parse_parent_ref(p.reference) if p.reference else (None, None)
        await _validate_ref(session, org_id, p_type, p_id, "parent")
        session.add(
            SpecimenParent(
                specimen_pk=specimen_pk,
                tenant_id=org_id,
                reference_reference=p.reference,
                reference_type=p_type,
                reference_id=p_id,
                reference_display=p.reference_display,
                reference_identifier_use=(
                    IdentifierUseModel[p.reference_identifier_use.name]
                    if p.reference_identifier_use
                    else None
                ),
                reference_identifier_system=p.reference_identifier_system,
                reference_identifier_value=p.reference_identifier_value,
                reference_identifier_type_text=p.reference_identifier_type_text,
                created_by=created_by,
            )
        )


async def _add_requests(session, specimen_pk: int, org_id: str, requests, created_by: str) -> None:
    for r in requests or []:
        r_type, r_id = _parse_request_ref(r.reference) if r.reference else (None, None)
        await _validate_ref(session, org_id, r_type, r_id, "request")
        session.add(
            SpecimenRequest(
                specimen_pk=specimen_pk,
                tenant_id=org_id,
                reference_reference=r.reference,
                reference_type=r_type,
                reference_id=r_id,
                reference_display=r.reference_display,
                reference_identifier_use=(
                    IdentifierUseModel[r.reference_identifier_use.name]
                    if r.reference_identifier_use
                    else None
                ),
                reference_identifier_system=r.reference_identifier_system,
                reference_identifier_value=r.reference_identifier_value,
                reference_identifier_type_text=r.reference_identifier_type_text,
                created_by=created_by,
            )
        )


def _add_collection_codings(session, specimen_pk: int, org_id: str, collection, created_by: str) -> None:
    if not collection:
        return
    if collection.method and collection.method.coding:
        for c in collection.method.coding:
            session.add(
                SpecimenCollectionMethodCoding(
                    specimen_pk=specimen_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )
    if collection.body_site and collection.body_site.coding:
        for c in collection.body_site.coding:
            session.add(
                SpecimenCollectionBodySiteCoding(
                    specimen_pk=specimen_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )
    if collection.fasting_status_codeable_concept and collection.fasting_status_codeable_concept.coding:
        for c in collection.fasting_status_codeable_concept.coding:
            session.add(
                SpecimenCollectionFastingStatusCoding(
                    specimen_pk=specimen_pk,
                    **_coding_kwargs(c, org_id, created_by),
                )
            )


async def _add_processings(session, specimen_pk: int, org_id: str, processings, created_by: str) -> None:
    for p in processings or []:
        proc = SpecimenProcessing(
            specimen_pk=specimen_pk,
            tenant_id=org_id,
            description=p.description,
            procedure_text=p.procedure.text if p.procedure else None,
            time_date_time=p.time_date_time,
            time_period_start=p.time_period_start,
            time_period_end=p.time_period_end,
            created_by=created_by,
        )
        session.add(proc)
        await session.flush()

        if p.procedure and p.procedure.coding:
            for c in p.procedure.coding:
                session.add(
                    SpecimenProcessingProcedureCoding(
                        specimen_processing_id=proc.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )

        for a in p.additive or []:
            ad_type, ad_id = _parse_additive_ref(a.reference) if a.reference else (None, None)
            await _validate_ref(session, org_id, ad_type, ad_id, "processing.additive")
            session.add(
                SpecimenProcessingAdditive(
                    specimen_processing_id=proc.id,
                    tenant_id=org_id,
                    reference_reference=a.reference,
                    reference_type=ad_type,
                    reference_id=ad_id,
                    reference_display=a.reference_display,
                    reference_identifier_use=(
                        IdentifierUseModel[a.reference_identifier_use.name]
                        if a.reference_identifier_use
                        else None
                    ),
                    reference_identifier_system=a.reference_identifier_system,
                    reference_identifier_value=a.reference_identifier_value,
                    reference_identifier_type_text=a.reference_identifier_type_text,
                    created_by=created_by,
                )
            )


async def _add_containers(session, specimen_pk: int, org_id: str, containers, created_by: str) -> None:
    for c in containers or []:
        ad_type, ad_id = (
            _parse_additive_ref(c.additive_reference.reference)
            if c.additive_reference and c.additive_reference.reference
            else (None, None)
        )
        await _validate_ref(session, org_id, ad_type, ad_id, "container.additiveReference")

        cont = SpecimenContainer(
            specimen_pk=specimen_pk,
            tenant_id=org_id,
            description=c.description,
            type_text=c.type.text if c.type else None,
            capacity_value=c.capacity_value,
            capacity_unit=c.capacity_unit,
            capacity_system=c.capacity_system,
            capacity_code=c.capacity_code,
            specimen_quantity_value=c.specimen_quantity_value,
            specimen_quantity_unit=c.specimen_quantity_unit,
            specimen_quantity_system=c.specimen_quantity_system,
            specimen_quantity_code=c.specimen_quantity_code,
            additive_codeable_concept_text=(
                c.additive_codeable_concept.text if c.additive_codeable_concept else None
            ),
            additive_reference_reference=(
                c.additive_reference.reference if c.additive_reference else None
            ),
            additive_reference_type=ad_type,
            additive_reference_id=ad_id,
            additive_reference_display=(
                c.additive_reference.reference_display if c.additive_reference else None
            ),
            additive_reference_identifier_use=(
                IdentifierUseModel[c.additive_reference.reference_identifier_use.name]
                if c.additive_reference and c.additive_reference.reference_identifier_use
                else None
            ),
            additive_reference_identifier_system=(
                c.additive_reference.reference_identifier_system
                if c.additive_reference
                else None
            ),
            additive_reference_identifier_value=(
                c.additive_reference.reference_identifier_value
                if c.additive_reference
                else None
            ),
            additive_reference_identifier_type_text=(
                c.additive_reference.reference_identifier_type_text
                if c.additive_reference
                else None
            ),
            created_by=created_by,
        )
        session.add(cont)
        await session.flush()

        if c.type and c.type.coding:
            for tc in c.type.coding:
                session.add(
                    SpecimenContainerTypeCoding(
                        specimen_container_id=cont.id,
                        **_coding_kwargs(tc, org_id, created_by),
                    )
                )

        if c.additive_codeable_concept and c.additive_codeable_concept.coding:
            for ac in c.additive_codeable_concept.coding:
                session.add(
                    SpecimenContainerAdditiveCoding(
                        specimen_container_id=cont.id,
                        **_coding_kwargs(ac, org_id, created_by),
                    )
                )

        for ci in c.identifier or []:
            a_type, a_id = _parse_org_ref(ci.assigner) if ci.assigner else (None, None)
            await _validate_ref(session, org_id, a_type, a_id, "container.identifier.assigner")
            c_ident = SpecimenContainerIdentifier(
                specimen_container_id=cont.id,
                tenant_id=org_id,
                use=IdentifierUseModel[ci.use.name] if ci.use else None,
                type_text=ci.type_text,
                system=ci.system,
                value=ci.value,
                period_start=ci.period_start,
                period_end=ci.period_end,
                assigner_reference=ci.assigner,
                assigner_type=a_type,
                assigner_id=a_id,
                assigner_display=ci.assigner_display,
                assigner_identifier_use=(
                    IdentifierUseModel[ci.assigner_identifier_use.name]
                    if ci.assigner_identifier_use
                    else None
                ),
                assigner_identifier_system=ci.assigner_identifier_system,
                assigner_identifier_value=ci.assigner_identifier_value,
                assigner_identifier_type_text=ci.assigner_identifier_type_text,
                created_by=created_by,
            )
            session.add(c_ident)
            if ci.type_coding:
                await session.flush()
                for tc in ci.type_coding:
                    session.add(
                        SpecimenContainerIdentifierTypeCoding(
                            specimen_container_identifier_id=c_ident.id,
                            **_coding_kwargs(tc, org_id, created_by),
                        )
                    )


async def _add_conditions(session, specimen_pk: int, org_id: str, conditions, created_by: str) -> None:
    for cond in conditions or []:
        sc = SpecimenCondition(
            specimen_pk=specimen_pk,
            tenant_id=org_id,
            text=cond.text,
            created_by=created_by,
        )
        session.add(sc)
        if cond.coding:
            await session.flush()
            for c in cond.coding:
                session.add(
                    SpecimenConditionCoding(
                        specimen_condition_id=sc.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_notes(session, specimen_pk: int, org_id: str, notes, created_by: str) -> None:
    for n in notes or []:
        a_type, a_id = (
            _parse_note_author_ref(n.author_reference)
            if n.author_reference
            else (None, None)
        )
        await _validate_ref(session, org_id, a_type, a_id, "note.author")
        session.add(
            SpecimenNote(
                specimen_pk=specimen_pk,
                tenant_id=org_id,
                author_string=n.author_string,
                author_reference=n.author_reference,
                author_type=a_type,
                author_id=a_id,
                author_display=n.author_display,
                author_identifier_use=(
                    IdentifierUseModel[n.author_identifier_use.name]
                    if n.author_identifier_use
                    else None
                ),
                author_identifier_system=n.author_identifier_system,
                author_identifier_value=n.author_identifier_value,
                author_identifier_type_text=n.author_identifier_type_text,
                time=n.time,
                text=n.text,
                created_by=created_by,
            )
        )


class _FullMixin:
    """Full-payload create and patch operations for Specimen."""

    async def create_full(
        self,
        payload: SpecimenCreateSchema,
        org_id: str,
        created_by: str,
    ) -> SpecimenModel:
        async with self.session_factory() as session:
            # Validate optional subject reference
            s_type, s_id = (
                _parse_subject_ref(payload.subject.reference)
                if payload.subject and payload.subject.reference
                else (None, None)
            )
            await _validate_ref(session, org_id, s_type, s_id, "subject")

            # Validate optional accession identifier assigner
            acc_a_type, acc_a_id = (
                _parse_org_ref(payload.accession_identifier.assigner)
                if payload.accession_identifier and payload.accession_identifier.assigner
                else (None, None)
            )
            await _validate_ref(session, org_id, acc_a_type, acc_a_id, "accession_identifier.assigner")

            # Validate optional collection collector reference
            col_type, col_id = (
                _parse_collector_ref(payload.collection.collector.reference)
                if payload.collection and payload.collection.collector and payload.collection.collector.reference
                else (None, None)
            )
            await _validate_ref(session, org_id, col_type, col_id, "collection.collector")

            specimen = SpecimenModel(
                tenant_id=org_id,
                created_by=created_by,
                updated_by=created_by,
                status=SpecimenStatusModel[payload.status.name] if payload.status else None,
                type_text=payload.type.text if payload.type else None,
                subject_reference=payload.subject.reference if payload.subject else None,
                subject_type=s_type,
                subject_id=s_id,
                subject_display=payload.subject.reference_display if payload.subject else None,
                received_time=payload.received_time,
                extension=payload.extension or [],
                **_reference_kwargs("subject", payload.subject),
            )

            if payload.accession_identifier:
                acc = payload.accession_identifier
                specimen.accession_identifier_use = IdentifierUseModel[acc.use.name] if acc.use else None
                specimen.accession_identifier_type_text = acc.type_text
                specimen.accession_identifier_system = acc.system
                specimen.accession_identifier_value = acc.value
                specimen.accession_identifier_period_start = acc.period_start
                specimen.accession_identifier_period_end = acc.period_end
                specimen.accession_identifier_assigner_reference = acc.assigner
                specimen.accession_identifier_assigner_type = acc_a_type
                specimen.accession_identifier_assigner_id = acc_a_id
                specimen.accession_identifier_assigner_display = acc.assigner_display
                specimen.accession_identifier_assigner_identifier_use = (
                    IdentifierUseModel[acc.assigner_identifier_use.name]
                    if acc.assigner_identifier_use
                    else None
                )
                specimen.accession_identifier_assigner_identifier_system = acc.assigner_identifier_system
                specimen.accession_identifier_assigner_identifier_value = acc.assigner_identifier_value
                specimen.accession_identifier_assigner_identifier_type_text = acc.assigner_identifier_type_text

            if payload.collection:
                col = payload.collection
                specimen.collection_collector_reference = col.collector.reference if col.collector else None
                specimen.collection_collector_type = col_type
                specimen.collection_collector_id = col_id
                specimen.collection_collector_display = col.collector.reference_display if col.collector else None
                for k, v in _reference_kwargs("collection_collector", col.collector).items():
                    setattr(specimen, k, v)
                specimen.collection_collected_date_time = col.collected_date_time
                specimen.collection_collected_period_start = col.collected_period_start
                specimen.collection_collected_period_end = col.collected_period_end
                specimen.collection_duration_value = col.duration_value
                specimen.collection_duration_comparator = (
                    SpecimenQuantityComparatorModel[col.duration_comparator.name]
                    if col.duration_comparator
                    else None
                )
                specimen.collection_duration_unit = col.duration_unit
                specimen.collection_duration_system = col.duration_system
                specimen.collection_duration_code = col.duration_code
                specimen.collection_quantity_value = col.quantity_value
                specimen.collection_quantity_unit = col.quantity_unit
                specimen.collection_quantity_system = col.quantity_system
                specimen.collection_quantity_code = col.quantity_code
                specimen.collection_method_text = col.method.text if col.method else None
                specimen.collection_body_site_text = col.body_site.text if col.body_site else None
                specimen.collection_fasting_status_text = (
                    col.fasting_status_codeable_concept.text
                    if col.fasting_status_codeable_concept
                    else None
                )
                specimen.collection_fasting_status_duration_value = col.fasting_status_duration_value
                specimen.collection_fasting_status_duration_comparator = (
                    SpecimenQuantityComparatorModel[col.fasting_status_duration_comparator.name]
                    if col.fasting_status_duration_comparator
                    else None
                )
                specimen.collection_fasting_status_duration_unit = col.fasting_status_duration_unit
                specimen.collection_fasting_status_duration_system = col.fasting_status_duration_system
                specimen.collection_fasting_status_duration_code = col.fasting_status_duration_code

            session.add(specimen)
            await session.flush()

            # Add sub-resources
            await _add_identifiers(session, specimen.id, org_id, payload.identifier, created_by)
            _add_accession_type_codings(session, specimen.id, org_id, payload.accession_identifier, created_by)
            _add_type_codings(session, specimen.id, org_id, payload.type, created_by)
            await _add_parents(session, specimen.id, org_id, payload.parent, created_by)
            await _add_requests(session, specimen.id, org_id, payload.request, created_by)
            _add_collection_codings(session, specimen.id, org_id, payload.collection, created_by)
            await _add_processings(session, specimen.id, org_id, payload.processing, created_by)
            await _add_containers(session, specimen.id, org_id, payload.container, created_by)
            await _add_conditions(session, specimen.id, org_id, payload.condition, created_by)
            await _add_notes(session, specimen.id, org_id, payload.note, created_by)

            await session.commit()

            # Re-fetch with relationships
            stmt = _with_relationships(
                select(SpecimenModel).where(SpecimenModel.id == specimen.id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def patch_full(
        self,
        specimen_id: int,
        payload: SpecimenPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> SpecimenModel | None:
        async with self.session_factory() as session:
            stmt = select(SpecimenModel).where(
                SpecimenModel.specimen_id == specimen_id,
                SpecimenModel.tenant_id == org_id,
            )
            specimen = (await session.execute(stmt)).scalars().first()
            if not specimen:
                return None

            provided = payload.model_dump(exclude_unset=True)

            specimen.updated_by = updated_by


            if "status" in provided:
                specimen.status = SpecimenStatusModel[payload.status.name] if payload.status else None

            if "received_time" in provided:
                specimen.received_time = payload.received_time

            if "extension" in provided:
                specimen.extension = payload.extension or []

            if "type" in provided:
                specimen.type_text = payload.type.text if payload.type else None
                await session.execute(
                    delete(SpecimenTypeCoding).where(SpecimenTypeCoding.specimen_pk == specimen.id)
                )
                _add_type_codings(session, specimen.id, org_id, payload.type, updated_by)

            if "subject" in provided:
                if payload.subject and payload.subject.reference:
                    s_type, s_id = _parse_subject_ref(payload.subject.reference)
                    await _validate_ref(session, org_id, s_type, s_id, "subject")
                    specimen.subject_reference = payload.subject.reference
                    specimen.subject_type = s_type
                    specimen.subject_id = s_id
                    specimen.subject_display = payload.subject.reference_display
                    for k, v in _reference_kwargs("subject", payload.subject).items():
                        setattr(specimen, k, v)
                else:
                    specimen.subject_reference = None
                    specimen.subject_type = None
                    specimen.subject_id = None
                    specimen.subject_display = None

            if "accession_identifier" in provided:
                await session.execute(
                    delete(SpecimenAccessionIdentifierTypeCoding).where(
                        SpecimenAccessionIdentifierTypeCoding.specimen_pk == specimen.id
                    )
                )
                if payload.accession_identifier:
                    acc = payload.accession_identifier
                    acc_a_type, acc_a_id = (
                        _parse_org_ref(acc.assigner) if acc.assigner else (None, None)
                    )
                    await _validate_ref(session, org_id, acc_a_type, acc_a_id, "accession_identifier.assigner")
                    specimen.accession_identifier_use = IdentifierUseModel[acc.use.name] if acc.use else None
                    specimen.accession_identifier_type_text = acc.type_text
                    specimen.accession_identifier_system = acc.system
                    specimen.accession_identifier_value = acc.value
                    specimen.accession_identifier_period_start = acc.period_start
                    specimen.accession_identifier_period_end = acc.period_end
                    specimen.accession_identifier_assigner_reference = acc.assigner
                    specimen.accession_identifier_assigner_type = acc_a_type
                    specimen.accession_identifier_assigner_id = acc_a_id
                    specimen.accession_identifier_assigner_display = acc.assigner_display
                    specimen.accession_identifier_assigner_identifier_use = (
                        IdentifierUseModel[acc.assigner_identifier_use.name]
                        if acc.assigner_identifier_use
                        else None
                    )
                    specimen.accession_identifier_assigner_identifier_system = acc.assigner_identifier_system
                    specimen.accession_identifier_assigner_identifier_value = acc.assigner_identifier_value
                    specimen.accession_identifier_assigner_identifier_type_text = acc.assigner_identifier_type_text
                    _add_accession_type_codings(session, specimen.id, org_id, acc, updated_by)
                else:
                    specimen.accession_identifier_use = None
                    specimen.accession_identifier_type_text = None
                    specimen.accession_identifier_system = None
                    specimen.accession_identifier_value = None
                    specimen.accession_identifier_period_start = None
                    specimen.accession_identifier_period_end = None
                    specimen.accession_identifier_assigner_reference = None
                    specimen.accession_identifier_assigner_type = None
                    specimen.accession_identifier_assigner_id = None
                    specimen.accession_identifier_assigner_display = None
                    specimen.accession_identifier_assigner_identifier_use = None
                    specimen.accession_identifier_assigner_identifier_system = None
                    specimen.accession_identifier_assigner_identifier_value = None
                    specimen.accession_identifier_assigner_identifier_type_text = None

            if "collection" in provided:
                await session.execute(
                    delete(SpecimenCollectionMethodCoding).where(
                        SpecimenCollectionMethodCoding.specimen_pk == specimen.id
                    )
                )
                await session.execute(
                    delete(SpecimenCollectionBodySiteCoding).where(
                        SpecimenCollectionBodySiteCoding.specimen_pk == specimen.id
                    )
                )
                await session.execute(
                    delete(SpecimenCollectionFastingStatusCoding).where(
                        SpecimenCollectionFastingStatusCoding.specimen_pk == specimen.id
                    )
                )
                if payload.collection:
                    col = payload.collection
                    col_type, col_id = (
                        _parse_collector_ref(col.collector.reference)
                        if col.collector and col.collector.reference
                        else (None, None)
                    )
                    await _validate_ref(session, org_id, col_type, col_id, "collection.collector")
                    specimen.collection_collector_reference = col.collector.reference if col.collector else None
                    specimen.collection_collector_type = col_type
                    specimen.collection_collector_id = col_id
                    specimen.collection_collector_display = col.collector.reference_display if col.collector else None
                    for k, v in _reference_kwargs("collection_collector", col.collector).items():
                        setattr(specimen, k, v)
                    specimen.collection_collected_date_time = col.collected_date_time
                    specimen.collection_collected_period_start = col.collected_period_start
                    specimen.collection_collected_period_end = col.collected_period_end
                    specimen.collection_duration_value = col.duration_value
                    specimen.collection_duration_comparator = (
                        SpecimenQuantityComparatorModel[col.duration_comparator.name]
                        if col.duration_comparator
                        else None
                    )
                    specimen.collection_duration_unit = col.duration_unit
                    specimen.collection_duration_system = col.duration_system
                    specimen.collection_duration_code = col.duration_code
                    specimen.collection_quantity_value = col.quantity_value
                    specimen.collection_quantity_unit = col.quantity_unit
                    specimen.collection_quantity_system = col.quantity_system
                    specimen.collection_quantity_code = col.quantity_code
                    specimen.collection_method_text = col.method.text if col.method else None
                    specimen.collection_body_site_text = col.body_site.text if col.body_site else None
                    specimen.collection_fasting_status_text = (
                        col.fasting_status_codeable_concept.text
                        if col.fasting_status_codeable_concept
                        else None
                    )
                    specimen.collection_fasting_status_duration_value = col.fasting_status_duration_value
                    specimen.collection_fasting_status_duration_comparator = (
                        SpecimenQuantityComparatorModel[col.fasting_status_duration_comparator.name]
                        if col.fasting_status_duration_comparator
                        else None
                    )
                    specimen.collection_fasting_status_duration_unit = col.fasting_status_duration_unit
                    specimen.collection_fasting_status_duration_system = col.fasting_status_duration_system
                    specimen.collection_fasting_status_duration_code = col.fasting_status_duration_code
                    _add_collection_codings(session, specimen.id, org_id, col, updated_by)
                else:
                    specimen.collection_collector_reference = None
                    specimen.collection_collector_type = None
                    specimen.collection_collector_id = None
                    specimen.collection_collector_display = None
                    specimen.collection_collected_date_time = None
                    specimen.collection_collected_period_start = None
                    specimen.collection_collected_period_end = None
                    specimen.collection_duration_value = None
                    specimen.collection_duration_comparator = None
                    specimen.collection_duration_unit = None
                    specimen.collection_duration_system = None
                    specimen.collection_duration_code = None
                    specimen.collection_quantity_value = None
                    specimen.collection_quantity_unit = None
                    specimen.collection_quantity_system = None
                    specimen.collection_quantity_code = None
                    specimen.collection_method_text = None
                    specimen.collection_body_site_text = None
                    specimen.collection_fasting_status_text = None
                    specimen.collection_fasting_status_duration_value = None
                    specimen.collection_fasting_status_duration_comparator = None
                    specimen.collection_fasting_status_duration_unit = None
                    specimen.collection_fasting_status_duration_system = None
                    specimen.collection_fasting_status_duration_code = None

            if "identifier" in provided:
                ident_sub = select(SpecimenIdentifier.id).where(
                    SpecimenIdentifier.specimen_pk == specimen.id
                )
                await session.execute(
                    delete(SpecimenIdentifierTypeCoding).where(
                        SpecimenIdentifierTypeCoding.specimen_identifier_id.in_(ident_sub)
                    )
                )
                await session.execute(
                    delete(SpecimenIdentifier).where(
                        SpecimenIdentifier.specimen_pk == specimen.id
                    )
                )
                await _add_identifiers(session, specimen.id, org_id, payload.identifier, updated_by)

            if "parent" in provided:
                await session.execute(
                    delete(SpecimenParent).where(SpecimenParent.specimen_pk == specimen.id)
                )
                await _add_parents(session, specimen.id, org_id, payload.parent, updated_by)

            if "request" in provided:
                await session.execute(
                    delete(SpecimenRequest).where(SpecimenRequest.specimen_pk == specimen.id)
                )
                await _add_requests(session, specimen.id, org_id, payload.request, updated_by)

            if "processing" in provided:
                proc_sub = select(SpecimenProcessing.id).where(
                    SpecimenProcessing.specimen_pk == specimen.id
                )
                await session.execute(
                    delete(SpecimenProcessingProcedureCoding).where(
                        SpecimenProcessingProcedureCoding.specimen_processing_id.in_(proc_sub)
                    )
                )
                await session.execute(
                    delete(SpecimenProcessingAdditive).where(
                        SpecimenProcessingAdditive.specimen_processing_id.in_(proc_sub)
                    )
                )
                await session.execute(
                    delete(SpecimenProcessing).where(
                        SpecimenProcessing.specimen_pk == specimen.id
                    )
                )
                await _add_processings(session, specimen.id, org_id, payload.processing, updated_by)

            if "container" in provided:
                cont_sub = select(SpecimenContainer.id).where(
                    SpecimenContainer.specimen_pk == specimen.id
                )
                c_ident_sub = select(SpecimenContainerIdentifier.id).where(
                    SpecimenContainerIdentifier.specimen_container_id.in_(cont_sub)
                )
                await session.execute(
                    delete(SpecimenContainerIdentifierTypeCoding).where(
                        SpecimenContainerIdentifierTypeCoding.specimen_container_identifier_id.in_(c_ident_sub)
                    )
                )
                await session.execute(
                    delete(SpecimenContainerIdentifier).where(
                        SpecimenContainerIdentifier.specimen_container_id.in_(cont_sub)
                    )
                )
                await session.execute(
                    delete(SpecimenContainerTypeCoding).where(
                        SpecimenContainerTypeCoding.specimen_container_id.in_(cont_sub)
                    )
                )
                await session.execute(
                    delete(SpecimenContainerAdditiveCoding).where(
                        SpecimenContainerAdditiveCoding.specimen_container_id.in_(cont_sub)
                    )
                )
                await session.execute(
                    delete(SpecimenContainer).where(
                        SpecimenContainer.specimen_pk == specimen.id
                    )
                )
                await _add_containers(session, specimen.id, org_id, payload.container, updated_by)

            if "condition" in provided:
                cond_sub = select(SpecimenCondition.id).where(
                    SpecimenCondition.specimen_pk == specimen.id
                )
                await session.execute(
                    delete(SpecimenConditionCoding).where(
                        SpecimenConditionCoding.specimen_condition_id.in_(cond_sub)
                    )
                )
                await session.execute(
                    delete(SpecimenCondition).where(
                        SpecimenCondition.specimen_pk == specimen.id
                    )
                )
                await _add_conditions(session, specimen.id, org_id, payload.condition, updated_by)

            if "note" in provided:
                await session.execute(
                    delete(SpecimenNote).where(SpecimenNote.specimen_pk == specimen.id)
                )
                await _add_notes(session, specimen.id, org_id, payload.note, updated_by)

            await session.commit()

            stmt = _with_relationships(
                select(SpecimenModel).where(SpecimenModel.id == specimen.id)
            )
            return (await session.execute(stmt)).scalars().first()
