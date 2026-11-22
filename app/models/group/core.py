from sqlalchemy import Boolean, BigInteger, Column, Enum, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import GroupType

group_id_seq = Sequence(
    "group_pub_seq", start=430000, increment=1, metadata=Base.metadata
)

# R4 target of Group.managingEntity.
MANAGING_ENTITY_TYPES = (
    "Organization",
    "RelatedPerson",
    "Practitioner",
    "PractitionerRole",
)


class GroupModel(TenantAuditMixin, Base):
    """FHIR R4 Group - Medplum-style storage, same as Patient, Encounter, Condition,
    Procedure, ServiceRequest, Medication and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read
    time from this row's own columns - see app.fhir.mappers.group). Nothing else in this table
    or its child tables is a second copy of the resource: every other column exists only
    because a FHIR R4 Group search parameter filters on it
    (https://www.hl7.org/fhir/R4/group.html#search), and is derived from `content` on every
    write by app.repository.group._indexer.

    Search parameter -> storage:
      type             -> type (1..1 code, Enum column, stored by value)
      actual           -> actual (1..1 boolean, column)
      managing-entity  -> managing_entity_reference/_type/_id + managing_entity_identifier_*
                          (0..1 Reference(Organization | RelatedPerson | Practitioner |
                          PractitionerRole), columns)
      identifier       -> GroupIdentifier (0..*)
      code, characteristic, value, exclude
                       -> GroupToken (one shared table; `code` reads Group.code at slot 0,
                          the others read each characteristic at slot n = its position:
                          `characteristic` its code, `value` its valueCodeableConcept or
                          valueBoolean, `exclude` its boolean)
      characteristic-value
                       -> a composite over GroupToken: a `characteristic` row and a `value` row
                          with the same slot (the same characteristic)
      member           -> GroupMember (one row per member.entity)
      _id              -> group_id;  _lastUpdated -> updated_at/created_at

    `name`, `quantity`, `active`, `characteristic.value[x]` other than a CodeableConcept or a
    boolean (a Quantity, a Range or a Reference), `characteristic.period`, `member.period`,
    `member.inactive` and `extension` have no search parameter and live only in `content`.

    `member` can point at seven resource types, so `reference_type` records which one a
    relative `Type/<id>` names (a plain string, not a Postgres enum): a search by bare id is
    ambiguous (`member=Type/id` or `member:Type=id`); `managing-entity` has four targets, so
    the same holds.

    All index columns are nullable: R4 makes `type` and `actual` mandatory, but that is the
    validator's rule (enforced by the `java_validator` backend), not the database's. No
    `user_id`: a Group is a shared tenant-level entity. No DB-level CHECK constraints (rule
    grp-1, `member` only if `actual`, is the validator's)."""

    __tablename__ = "group"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    group_id = Column(
        BigInteger,
        group_id_seq,
        server_default=group_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    type = Column(
        Enum(
            GroupType,
            name="group_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    actual = Column(Boolean, nullable=True)

    # managingEntity (0..1 Reference of four types)
    managing_entity_reference = Column(String, nullable=True)
    managing_entity_type = Column(String, nullable=True)
    managing_entity_id = Column(BigInteger, nullable=True, index=True)
    managing_entity_identifier_system = Column(String, nullable=True)
    managing_entity_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "GroupIdentifier", back_populates="group", cascade="all, delete-orphan"
    )
    tokens = relationship(
        "GroupToken", back_populates="group", cascade="all, delete-orphan"
    )
    members = relationship(
        "GroupMember", back_populates="group", cascade="all, delete-orphan"
    )
