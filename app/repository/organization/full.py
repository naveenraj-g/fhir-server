from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.errors.domain import BusinessRuleViolationError
from app.models.organization import (
    OrganizationAddress,
    OrganizationAlias,
    OrganizationContact,
    OrganizationContactPurposeCoding,
    OrganizationContactTelecom,
    OrganizationEndpoint,
    OrganizationIdentifier,
    OrganizationIdentifierTypeCoding,
    OrganizationModel,
    OrganizationTelecom,
    OrganizationType,
    OrganizationTypeCoding,
)
from app.schemas.organization import OrganizationCreateSchema, OrganizationPatchSchema

from ._shared import (
    _org_ref_kwargs,
    _parse_endpoint_ref,
    _parse_org_ref,
    _partof_chain_contains,
    _reference_kwargs,
    _validate_reference,
)

logger = get_logger(__name__)


def _coding_kwargs(coding, created_by: str | None) -> dict:
    """Build constructor kwargs for one OrganizationCodingInput entry,
    targeting any of the three dedicated coding[] child tables
    (OrganizationTypeCoding/OrganizationContactPurposeCoding/
    OrganizationIdentifierTypeCoding) — all three share the same shape via
    FhirCodingMixin, so one helper covers all of them."""
    return {
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators
    that touch all 7 sub-resource types (plus core scalar fields) in one
    transaction."""

    async def create_full(
        self,
        payload: OrganizationCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> OrganizationModel:
        """Create an Organization plus any combination of its 7 sub-resource
        lists, atomically in one DB transaction. Every list on the payload is
        optional; only the ones supplied get inserted."""
        po_type, po_id = (
            _parse_org_ref(payload.partof) if payload.partof else (None, None)
        )
        async with self.session_factory() as session:
            await _validate_reference(session, org_id, po_type, po_id, "partOf")
            org = OrganizationModel(
                tenant_id=org_id,
                created_by=created_by,
                active=payload.active,
                name=payload.name,
                extension=payload.extension or [],
                partof_reference=payload.partof,
                **_org_ref_kwargs("partof", payload.partof, payload.partof_display),
                **_reference_kwargs("partof", payload),
            )
            session.add(org)
            await session.flush()

            if payload.identifier:
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, a_type, a_id, "identifier.assigner"
                    )
                    identifier = OrganizationIdentifier(
                        organization_pk=org.id,
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
                                OrganizationIdentifierTypeCoding(
                                    organization_identifier_id=identifier.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.type:
                for t in payload.type:
                    org_type = OrganizationType(
                        organization_pk=org.id,
                        tenant_id=org_id,
                        text=t.text,
                        created_by=created_by,
                    )
                    session.add(org_type)
                    if t.coding:
                        await session.flush()
                        for coding in t.coding:
                            session.add(
                                OrganizationTypeCoding(
                                    organization_type_id=org_type.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )

            if payload.alias:
                for a in payload.alias:
                    session.add(
                        OrganizationAlias(
                            organization_pk=org.id,
                            tenant_id=org_id,
                            value=a.value,
                            created_by=created_by,
                        )
                    )

            if payload.telecom:
                for t in payload.telecom:
                    session.add(
                        OrganizationTelecom(
                            organization_pk=org.id,
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

            if payload.address:
                for a in payload.address:
                    session.add(
                        OrganizationAddress(
                            organization_pk=org.id,
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

            if payload.contact:
                for c in payload.contact:
                    contact = OrganizationContact(
                        organization_pk=org.id,
                        tenant_id=org_id,
                        purpose_text=c.purpose_text,
                        name_use=c.name_use,
                        name_text=c.name_text,
                        name_family=c.name_family,
                        name_given=c.name_given,
                        name_prefix=c.name_prefix,
                        name_suffix=c.name_suffix,
                        name_period_start=c.name_period_start,
                        name_period_end=c.name_period_end,
                        use=c.address_use,
                        type=c.address_type,
                        text=c.address_text,
                        line=c.address_line,
                        city=c.address_city,
                        district=c.address_district,
                        state=c.address_state,
                        postal_code=c.address_postal_code,
                        country=c.address_country,
                        period_start=c.address_period_start,
                        period_end=c.address_period_end,
                        created_by=created_by,
                    )
                    session.add(contact)
                    await session.flush()
                    if c.purpose_coding:
                        for coding in c.purpose_coding:
                            session.add(
                                OrganizationContactPurposeCoding(
                                    contact_id=contact.id,
                                    tenant_id=org_id,
                                    **_coding_kwargs(coding, created_by),
                                )
                            )
                    if c.telecom:
                        for t in c.telecom:
                            session.add(
                                OrganizationContactTelecom(
                                    contact_id=contact.id,
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

            if payload.endpoint:
                for e in payload.endpoint:
                    ep_type, ep_id = (
                        _parse_endpoint_ref(e.reference)
                        if e.reference
                        else (None, None)
                    )
                    session.add(
                        OrganizationEndpoint(
                            organization_pk=org.id,
                            tenant_id=org_id,
                            reference_reference=e.reference,
                            reference_type=ep_type,
                            reference_id=ep_id,
                            reference_display=e.reference_display,
                            **_reference_kwargs("reference", e),
                            created_by=created_by,
                        )
                    )

            try:
                await session.commit()
                await session.refresh(org)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_organization_id(org.organization_id)

    async def patch_full(
        self,
        organization_id: int,
        payload: OrganizationPatchSchema,
        updated_by: str | None = None,
    ) -> OrganizationModel | None:
        """Patches core scalar fields (same semantics as patch()) and, for
        each sub-resource list that is supplied — even `[]` — atomically
        deletes all existing rows and inserts the new ones. Lists omitted
        from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(OrganizationModel).where(
                OrganizationModel.organization_id == organization_id
            )
            org = (await session.execute(stmt)).scalars().first()
            if not org:
                return None

            _SUB = {
                "identifier",
                "type",
                "alias",
                "telecom",
                "address",
                "contact",
                "endpoint",
            }
            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                if field in _SUB:
                    continue
                if field == "partof":
                    if value is not None:
                        po_type, po_id = _parse_org_ref(value)
                        await _validate_reference(
                            session, org.tenant_id, po_type, po_id, "partOf"
                        )
                        if await _partof_chain_contains(
                            session, org.tenant_id, po_id, org.organization_id
                        ):
                            raise BusinessRuleViolationError(
                                f"Setting partOf to Organization/{po_id} would create a "
                                "circular organization hierarchy."
                            )
                        org.partof_reference = value
                        org.partof_type = po_type
                        org.partof_id = po_id
                    else:
                        org.partof_reference = None
                        org.partof_type = None
                        org.partof_id = None
                else:
                    setattr(org, field, value)
            if updated_by is not None:
                org.updated_by = updated_by

            if payload.identifier is not None:
                await session.execute(
                    delete(OrganizationIdentifier).where(
                        OrganizationIdentifier.organization_pk == org.id
                    )
                )
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, org.tenant_id, a_type, a_id, "identifier.assigner"
                    )
                    identifier = OrganizationIdentifier(
                        organization_pk=org.id,
                        tenant_id=org.tenant_id,
                        use=i.use,
                        type_text=i.type_text,
                        system=i.system,
                        value=i.value,
                        period_start=i.period_start,
                        period_end=i.period_end,
                        assigner_reference=i.assigner,
                        **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
                        **_reference_kwargs("assigner", i),
                        created_by=updated_by,
                    )
                    session.add(identifier)
                    if i.type_coding:
                        await session.flush()
                        for coding in i.type_coding:
                            session.add(
                                OrganizationIdentifierTypeCoding(
                                    organization_identifier_id=identifier.id,
                                    tenant_id=org.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.type is not None:
                await session.execute(
                    delete(OrganizationType).where(
                        OrganizationType.organization_pk == org.id
                    )
                )
                for t in payload.type:
                    org_type = OrganizationType(
                        organization_pk=org.id,
                        tenant_id=org.tenant_id,
                        text=t.text,
                        created_by=updated_by,
                    )
                    session.add(org_type)
                    if t.coding:
                        await session.flush()
                        for coding in t.coding:
                            session.add(
                                OrganizationTypeCoding(
                                    organization_type_id=org_type.id,
                                    tenant_id=org.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )

            if payload.alias is not None:
                await session.execute(
                    delete(OrganizationAlias).where(
                        OrganizationAlias.organization_pk == org.id
                    )
                )
                for a in payload.alias:
                    session.add(
                        OrganizationAlias(
                            organization_pk=org.id,
                            tenant_id=org.tenant_id,
                            value=a.value,
                            created_by=updated_by,
                        )
                    )

            if payload.telecom is not None:
                await session.execute(
                    delete(OrganizationTelecom).where(
                        OrganizationTelecom.organization_pk == org.id
                    )
                )
                for t in payload.telecom:
                    session.add(
                        OrganizationTelecom(
                            organization_pk=org.id,
                            tenant_id=org.tenant_id,
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
                    delete(OrganizationAddress).where(
                        OrganizationAddress.organization_pk == org.id
                    )
                )
                for a in payload.address:
                    session.add(
                        OrganizationAddress(
                            organization_pk=org.id,
                            tenant_id=org.tenant_id,
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

            if payload.contact is not None:
                contact_ids = list(
                    (
                        await session.execute(
                            select(OrganizationContact.id).where(
                                OrganizationContact.organization_pk == org.id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if contact_ids:
                    await session.execute(
                        delete(OrganizationContactTelecom).where(
                            OrganizationContactTelecom.contact_id.in_(contact_ids)
                        )
                    )
                    await session.execute(
                        delete(OrganizationContactPurposeCoding).where(
                            OrganizationContactPurposeCoding.contact_id.in_(
                                contact_ids
                            )
                        )
                    )
                await session.execute(
                    delete(OrganizationContact).where(
                        OrganizationContact.organization_pk == org.id
                    )
                )
                for c in payload.contact:
                    contact = OrganizationContact(
                        organization_pk=org.id,
                        tenant_id=org.tenant_id,
                        purpose_text=c.purpose_text,
                        name_use=c.name_use,
                        name_text=c.name_text,
                        name_family=c.name_family,
                        name_given=c.name_given,
                        name_prefix=c.name_prefix,
                        name_suffix=c.name_suffix,
                        name_period_start=c.name_period_start,
                        name_period_end=c.name_period_end,
                        use=c.address_use,
                        type=c.address_type,
                        text=c.address_text,
                        line=c.address_line,
                        city=c.address_city,
                        district=c.address_district,
                        state=c.address_state,
                        postal_code=c.address_postal_code,
                        country=c.address_country,
                        period_start=c.address_period_start,
                        period_end=c.address_period_end,
                        created_by=updated_by,
                    )
                    session.add(contact)
                    await session.flush()
                    if c.purpose_coding:
                        for coding in c.purpose_coding:
                            session.add(
                                OrganizationContactPurposeCoding(
                                    contact_id=contact.id,
                                    tenant_id=org.tenant_id,
                                    **_coding_kwargs(coding, updated_by),
                                )
                            )
                    if c.telecom:
                        for t in c.telecom:
                            session.add(
                                OrganizationContactTelecom(
                                    contact_id=contact.id,
                                    tenant_id=org.tenant_id,
                                    system=t.system,
                                    value=t.value,
                                    use=t.use,
                                    rank=t.rank,
                                    period_start=t.period_start,
                                    period_end=t.period_end,
                                    created_by=updated_by,
                                )
                            )

            if payload.endpoint is not None:
                await session.execute(
                    delete(OrganizationEndpoint).where(
                        OrganizationEndpoint.organization_pk == org.id
                    )
                )
                for e in payload.endpoint:
                    ep_type, ep_id = (
                        _parse_endpoint_ref(e.reference)
                        if e.reference
                        else (None, None)
                    )
                    session.add(
                        OrganizationEndpoint(
                            organization_pk=org.id,
                            tenant_id=org.tenant_id,
                            reference_reference=e.reference,
                            reference_type=ep_type,
                            reference_id=ep_id,
                            reference_display=e.reference_display,
                            **_reference_kwargs("reference", e),
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
            replaced = sorted(_SUB & set(data.keys()))
            if replaced:
                logger.debug(
                    "Organization sub-resource lists replaced",
                    extra={
                        "event": "organization.sublists_replaced",
                        "organization_id": organization_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_organization_id(organization_id)
