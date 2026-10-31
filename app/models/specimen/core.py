from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Numeric,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import TenantAuditMixin
from app.models.specimen.enums import (
    SpecimenCollectorReferenceType,
    SpecimenQuantityComparator,
    SpecimenStatus,
    SpecimenSubjectReferenceType,
)

specimen_id_seq = Sequence(
    "specimen_pub_seq", start=310000, metadata=Base.metadata
)


class SpecimenModel(TenantAuditMixin, Base):
    """FHIR R4 Specimen model — https://www.hl7.org/fhir/R4/specimen.html

    A sample to be used for analysis.
    """

    __tablename__ = "specimen"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_id = Column(
        BigInteger,
        specimen_id_seq,
        server_default=specimen_id_seq.next_value(),
        unique=True,
        nullable=False,
        index=True,
    )

    # accessionIdentifier (0..1 Identifier) flattened
    accession_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    accession_identifier_type_text = Column(String, nullable=True)
    accession_identifier_system = Column(String, nullable=True)
    accession_identifier_value = Column(String, nullable=True)
    accession_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    accession_identifier_period_end = Column(DateTime(timezone=True), nullable=True)
    accession_identifier_assigner_reference = Column(String, nullable=True)
    accession_identifier_assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    accession_identifier_assigner_id = Column(BigInteger, nullable=True, index=True)
    accession_identifier_assigner_display = Column(String, nullable=True)
    accession_identifier_assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    accession_identifier_assigner_identifier_system = Column(String, nullable=True)
    accession_identifier_assigner_identifier_value = Column(String, nullable=True)
    accession_identifier_assigner_identifier_type_text = Column(String, nullable=True)

    # status (0..1 code)
    status = Column(
        Enum(SpecimenStatus, name="specimen_status"), nullable=True
    )

    # type (0..1 CodeableConcept) — codings in specimen_type_coding
    type_text = Column(String, nullable=True)

    # subject (0..1 Reference(Patient | Group | Device | Substance | Location))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            SpecimenSubjectReferenceType,
            name="specimen_subject_reference_type",
        ),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)
    subject_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)
    subject_identifier_type_text = Column(String, nullable=True)

    # receivedTime (0..1 dateTime)
    received_time = Column(DateTime(timezone=True), nullable=True)

    # collection (0..1 BackboneElement) flattened
    collection_collector_reference = Column(String, nullable=True)
    collection_collector_type = Column(
        Enum(
            SpecimenCollectorReferenceType,
            name="specimen_collector_reference_type",
        ),
        nullable=True,
    )
    collection_collector_id = Column(BigInteger, nullable=True, index=True)
    collection_collector_display = Column(String, nullable=True)
    collection_collector_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    collection_collector_identifier_system = Column(String, nullable=True)
    collection_collector_identifier_value = Column(String, nullable=True)
    collection_collector_identifier_type_text = Column(String, nullable=True)

    # collection.collected[x] (0..1 dateTime | Period)
    collection_collected_date_time = Column(DateTime(timezone=True), nullable=True)
    collection_collected_period_start = Column(DateTime(timezone=True), nullable=True)
    collection_collected_period_end = Column(DateTime(timezone=True), nullable=True)

    # collection.duration (0..1 Duration)
    collection_duration_value = Column(Numeric, nullable=True)
    collection_duration_comparator = Column(
        Enum(
            SpecimenQuantityComparator,
            name="specimen_quantity_comparator",
        ),
        nullable=True,
    )
    collection_duration_unit = Column(String, nullable=True)
    collection_duration_system = Column(String, nullable=True)
    collection_duration_code = Column(String, nullable=True)

    # collection.quantity (0..1 SimpleQuantity)
    collection_quantity_value = Column(Numeric, nullable=True)
    collection_quantity_unit = Column(String, nullable=True)
    collection_quantity_system = Column(String, nullable=True)
    collection_quantity_code = Column(String, nullable=True)

    # collection.method (0..1 CodeableConcept) — codings in specimen_collection_method_coding
    collection_method_text = Column(String, nullable=True)

    # collection.bodySite (0..1 CodeableConcept) — codings in specimen_collection_body_site_coding
    collection_body_site_text = Column(String, nullable=True)

    # collection.fastingStatus[x] (0..1 CodeableConcept | Duration)
    collection_fasting_status_text = Column(String, nullable=True)
    collection_fasting_status_duration_value = Column(Numeric, nullable=True)
    collection_fasting_status_duration_comparator = Column(
        Enum(
            SpecimenQuantityComparator,
            name="specimen_quantity_comparator",
        ),
        nullable=True,
    )
    collection_fasting_status_duration_unit = Column(String, nullable=True)
    collection_fasting_status_duration_system = Column(String, nullable=True)
    collection_fasting_status_duration_code = Column(String, nullable=True)

    # DomainResource extension
    extension = Column(JSONB, nullable=False, server_default="[]")

    # Relationships
    identifiers = relationship(
        "SpecimenIdentifier",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    accession_identifier_type_codings = relationship(
        "SpecimenAccessionIdentifierTypeCoding",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    type_codings = relationship(
        "SpecimenTypeCoding",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    parents = relationship(
        "SpecimenParent",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    requests = relationship(
        "SpecimenRequest",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    collection_method_codings = relationship(
        "SpecimenCollectionMethodCoding",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    collection_body_site_codings = relationship(
        "SpecimenCollectionBodySiteCoding",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    collection_fasting_status_codings = relationship(
        "SpecimenCollectionFastingStatusCoding",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    processings = relationship(
        "SpecimenProcessing",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    containers = relationship(
        "SpecimenContainer",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    conditions = relationship(
        "SpecimenCondition",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "SpecimenNote",
        back_populates="specimen",
        cascade="all, delete-orphan",
    )
