from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import (
    apply_child_exists_filter,
    apply_token_filter,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.related_person import (
    RelatedPersonAddress,
    RelatedPersonIdentifier,
    RelatedPersonModel,
    RelatedPersonName,
    RelatedPersonRelationship,
    RelatedPersonRelationshipCoding,
    RelatedPersonTelecom,
)

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_patient_ref,
    _with_relationships,
)
from .full import _FullMixin

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD and list operations for RelatedPerson."""

    async def get_by_related_person_id(
        self, related_person_id: int
    ) -> RelatedPersonModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(RelatedPersonModel).where(
                    RelatedPersonModel.related_person_id == related_person_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_related_person_id_in_org(
        self, related_person_id: int, org_id: str
    ) -> RelatedPersonModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the resource exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(RelatedPersonModel).where(
                    RelatedPersonModel.related_person_id == related_person_id,
                    RelatedPersonModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def related_person_belongs_to_org(
        self, related_person_id: int, org_id: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(RelatedPersonModel.id).where(
                RelatedPersonModel.related_person_id == related_person_id,
                RelatedPersonModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id: str | None = None,
        active: bool | None = None,
        patient: str | None = None,
        relationship: str | None = None,
        name: str | None = None,
        telecom: str | None = None,
        gender: str | None = None,
        birth_date: date | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        identifier: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ):
        if org_id:
            stmt = stmt.where(RelatedPersonModel.tenant_id == org_id)

        if active is not None:
            stmt = apply_token_filter(stmt, RelatedPersonModel.active, active)

        if gender:
            stmt = apply_token_filter(stmt, RelatedPersonModel.gender, gender)

        if birth_date:
            stmt = stmt.where(RelatedPersonModel.birth_date == birth_date)

        if patient:
            p_type, p_id = _parse_patient_ref(patient)
            if p_id is not None:
                stmt = stmt.where(
                    or_(
                        RelatedPersonModel.patient_reference == patient,
                        RelatedPersonModel.patient_id == p_id,
                    )
                )
            else:
                stmt = stmt.where(RelatedPersonModel.patient_reference == patient)

        if relationship:
            rel_pattern = f"%{relationship}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonRelationship.id).where(
                    RelatedPersonRelationship.related_person_pk == RelatedPersonModel.id,
                    or_(
                        RelatedPersonRelationship.text.ilike(rel_pattern),
                        RelatedPersonRelationship.id.in_(
                            select(
                                RelatedPersonRelationshipCoding.related_person_relationship_id
                            ).where(
                                or_(
                                    RelatedPersonRelationshipCoding.code == relationship,
                                    RelatedPersonRelationshipCoding.display.ilike(rel_pattern),
                                )
                            )
                        ),
                    ),
                ),
            )

        if name:
            name_pattern = f"%{name}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonName.id).where(
                    RelatedPersonName.related_person_pk == RelatedPersonModel.id,
                    or_(
                        RelatedPersonName.text.ilike(name_pattern),
                        RelatedPersonName.family.ilike(name_pattern),
                        func.array_to_string(RelatedPersonName.given, " ").ilike(name_pattern),
                        func.array_to_string(RelatedPersonName.prefix, " ").ilike(name_pattern),
                        func.array_to_string(RelatedPersonName.suffix, " ").ilike(name_pattern),
                    ),
                ),
            )

        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonIdentifier.id).where(
                    RelatedPersonIdentifier.related_person_pk == RelatedPersonModel.id,
                    RelatedPersonIdentifier.value == identifier,
                ),
            )

        if telecom:
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonTelecom.id).where(
                    RelatedPersonTelecom.related_person_pk == RelatedPersonModel.id,
                    RelatedPersonTelecom.value == telecom,
                ),
            )

        if phone:
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonTelecom.id).where(
                    RelatedPersonTelecom.related_person_pk == RelatedPersonModel.id,
                    RelatedPersonTelecom.system == "phone",
                    RelatedPersonTelecom.value == phone,
                ),
            )

        if email:
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonTelecom.id).where(
                    RelatedPersonTelecom.related_person_pk == RelatedPersonModel.id,
                    RelatedPersonTelecom.system == "email",
                    RelatedPersonTelecom.value == email,
                ),
            )

        if address:
            addr_pattern = f"%{address}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonAddress.id).where(
                    RelatedPersonAddress.related_person_pk == RelatedPersonModel.id,
                    or_(
                        func.array_to_string(RelatedPersonAddress.line, " ").ilike(addr_pattern),
                        RelatedPersonAddress.city.ilike(addr_pattern),
                        RelatedPersonAddress.district.ilike(addr_pattern),
                        RelatedPersonAddress.state.ilike(addr_pattern),
                        RelatedPersonAddress.country.ilike(addr_pattern),
                        RelatedPersonAddress.postal_code.ilike(addr_pattern),
                        RelatedPersonAddress.text.ilike(addr_pattern),
                    ),
                ),
            )

        if address_city:
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonAddress.id).where(
                    RelatedPersonAddress.related_person_pk == RelatedPersonModel.id,
                    RelatedPersonAddress.city.ilike(f"%{address_city}%"),
                ),
            )

        if address_state:
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonAddress.id).where(
                    RelatedPersonAddress.related_person_pk == RelatedPersonModel.id,
                    RelatedPersonAddress.state.ilike(f"%{address_state}%"),
                ),
            )

        if address_postal_code:
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonAddress.id).where(
                    RelatedPersonAddress.related_person_pk == RelatedPersonModel.id,
                    RelatedPersonAddress.postal_code == address_postal_code,
                ),
            )

        if address_country:
            stmt = apply_child_exists_filter(
                stmt,
                select(RelatedPersonAddress.id).where(
                    RelatedPersonAddress.related_person_pk == RelatedPersonModel.id,
                    RelatedPersonAddress.country.ilike(f"%{address_country}%"),
                ),
            )

        return stmt

    async def list(
        self,
        org_id: str | None = None,
        active: bool | None = None,
        patient: str | None = None,
        relationship: str | None = None,
        name: str | None = None,
        telecom: str | None = None,
        gender: str | None = None,
        birth_date: date | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        identifier: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[int, list[RelatedPersonModel]]:
        async with self.session_factory() as session:
            base_stmt = select(RelatedPersonModel)
            filtered_stmt = self._apply_list_filters(
                base_stmt,
                org_id=org_id,
                active=active,
                patient=patient,
                relationship=relationship,
                name=name,
                telecom=telecom,
                gender=gender,
                birth_date=birth_date,
                address=address,
                address_city=address_city,
                address_state=address_state,
                address_postal_code=address_postal_code,
                address_country=address_country,
                identifier=identifier,
                email=email,
                phone=phone,
            )

            count_stmt = select(func.count()).select_from(filtered_stmt.subquery())
            total = (await session.execute(count_stmt)).scalar_one()

            sort_col, ascending = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                RelatedPersonModel.related_person_id,
            )
            data_stmt = (
                _with_relationships(filtered_stmt)
                .order_by(sort_col.asc() if ascending else sort_col.desc())
                .limit(limit)
                .offset(offset)
            )
            rows = (await session.execute(data_stmt)).scalars().all()

            return total, list(rows)

    async def delete(
        self, related_person_id: int, org_id: str | None = None
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(RelatedPersonModel).where(
                RelatedPersonModel.related_person_id == related_person_id
            )
            if org_id is not None:
                stmt = stmt.where(RelatedPersonModel.tenant_id == org_id)

            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False

            await session.delete(model)
            await session.commit()
            return True


class RelatedPersonRepository(_CoreMixin, _FullMixin):
    """Repository managing RelatedPerson and its child models."""

    def __init__(self, session_factory):
        self.session_factory = session_factory
