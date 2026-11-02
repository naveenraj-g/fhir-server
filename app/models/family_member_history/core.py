from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Numeric,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.family_member_history.enums import (
    FamilyMemberHistoryPatientReferenceType,
    FamilyMemberHistoryQuantityComparator,
    FamilyMemberHistoryStatus,
)
from app.models.shared import TenantAuditMixin

family_member_history_id_seq = Sequence(
    "family_member_history_pub_seq",
    start=490000,
    increment=1,
    metadata=Base.metadata,
)


class FamilyMemberHistoryModel(TenantAuditMixin, Base):
    """SQLAlchemy ORM model for FHIR R4 FamilyMemberHistory resource."""

    __tablename__ = "family_member_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_id = Column(
        BigInteger,
        family_member_history_id_seq,
        server_default=family_member_history_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    instantiates_canonical = Column(ARRAY(String), nullable=True)
    instantiates_uri = Column(ARRAY(String), nullable=True)

    status = Column(
        Enum(
            FamilyMemberHistoryStatus,
            name="family_member_history_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    data_absent_reason_text = Column(String, nullable=True)

    # patient (1..1 Reference(Patient))
    patient_reference = Column(String, nullable=False)
    patient_type = Column(
        Enum(
            FamilyMemberHistoryPatientReferenceType,
            name="family_member_history_patient_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    patient_id = Column(BigInteger, nullable=True, index=True)
    patient_display = Column(String, nullable=True)

    # patient.identifier fallback (11 columns)
    patient_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    patient_identifier_type_system = Column(String, nullable=True)
    patient_identifier_type_version = Column(String, nullable=True)
    patient_identifier_type_code = Column(String, nullable=True)
    patient_identifier_type_display = Column(String, nullable=True)
    patient_identifier_type_user_selected = Column(Boolean, nullable=True)
    patient_identifier_type_text = Column(String, nullable=True)
    patient_identifier_system = Column(String, nullable=True)
    patient_identifier_value = Column(String, nullable=True)
    patient_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    patient_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    date = Column(DateTime(timezone=True), nullable=True)
    name = Column(String, nullable=True)
    relationship_text = Column(String, nullable=True)
    sex_text = Column(String, nullable=True)

    # born[x] (0..1 choice: Period | date | string)
    born_period_start = Column(DateTime(timezone=True), nullable=True)
    born_period_end = Column(DateTime(timezone=True), nullable=True)
    born_date = Column(Date, nullable=True)
    born_string = Column(String, nullable=True)

    # age[x] (0..1 choice: Age (Quantity) | Range | string)
    age_age_value = Column(Numeric, nullable=True)
    age_age_comparator = Column(
        Enum(
            FamilyMemberHistoryQuantityComparator,
            name="family_member_history_quantity_comparator",
        ),
        nullable=True,
    )
    age_age_unit = Column(String, nullable=True)
    age_age_system = Column(String, nullable=True)
    age_age_code = Column(String, nullable=True)

    age_range_low_value = Column(Numeric, nullable=True)
    age_range_low_unit = Column(String, nullable=True)
    age_range_low_system = Column(String, nullable=True)
    age_range_low_code = Column(String, nullable=True)
    age_range_high_value = Column(Numeric, nullable=True)
    age_range_high_unit = Column(String, nullable=True)
    age_range_high_system = Column(String, nullable=True)
    age_range_high_code = Column(String, nullable=True)

    age_string = Column(String, nullable=True)
    estimated_age = Column(Boolean, nullable=True)

    # deceased[x] (0..1 choice: boolean | Age (Quantity) | Range | date | string)
    deceased_boolean = Column(Boolean, nullable=True)
    deceased_age_value = Column(Numeric, nullable=True)
    deceased_age_comparator = Column(
        Enum(
            FamilyMemberHistoryQuantityComparator,
            name="family_member_history_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    deceased_age_unit = Column(String, nullable=True)
    deceased_age_system = Column(String, nullable=True)
    deceased_age_code = Column(String, nullable=True)

    deceased_range_low_value = Column(Numeric, nullable=True)
    deceased_range_low_unit = Column(String, nullable=True)
    deceased_range_low_system = Column(String, nullable=True)
    deceased_range_low_code = Column(String, nullable=True)
    deceased_range_high_value = Column(Numeric, nullable=True)
    deceased_range_high_unit = Column(String, nullable=True)
    deceased_range_high_system = Column(String, nullable=True)
    deceased_range_high_code = Column(String, nullable=True)

    deceased_date = Column(Date, nullable=True)
    deceased_string = Column(String, nullable=True)

    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
    identifiers = relationship(
        "FamilyMemberHistoryIdentifier",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
    data_absent_reason_codings = relationship(
        "FamilyMemberHistoryDataAbsentReasonCoding",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
    relationship_codings = relationship(
        "FamilyMemberHistoryRelationshipCoding",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
    sex_codings = relationship(
        "FamilyMemberHistorySexCoding",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
    reason_codes = relationship(
        "FamilyMemberHistoryReasonCode",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
    reason_references = relationship(
        "FamilyMemberHistoryReasonReference",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "FamilyMemberHistoryNote",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
    conditions = relationship(
        "FamilyMemberHistoryCondition",
        back_populates="family_member_history",
        cascade="all, delete-orphan",
    )
