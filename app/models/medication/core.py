from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Numeric,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.medication.enums import (
    MedicationManufacturerReferenceType,
    MedicationQuantityComparator,
    MedicationStatus,
)
from app.models.shared import TenantAuditMixin


class MedicationModel(Base, TenantAuditMixin):
    """Medication resource ORM model (FHIR R4).
    https://www.hl7.org/fhir/R4/medication.html
    """

    __tablename__ = "medication"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_id = Column(
        BigInteger,
        Sequence(
            "medication_pub_seq",
            start=250000,
            increment=1,
            metadata=Base.metadata,
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # Resource-level extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # code (0..1 CodeableConcept) — text flattened, codings in child table
    code_text = Column(String, nullable=True)

    # status (0..1 code)
    status = Column(
        Enum(
            MedicationStatus,
            name="medication_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # manufacturer (0..1 Reference(Organization)) with identifier fallback (15 columns)
    manufacturer_reference = Column(String, nullable=True)
    manufacturer_type = Column(
        Enum(
            MedicationManufacturerReferenceType,
            name="medication_manufacturer_reference_type",
        ),
        nullable=True,
    )
    manufacturer_id = Column(BigInteger, nullable=True, index=True)
    manufacturer_display = Column(String, nullable=True)

    manufacturer_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    manufacturer_identifier_type_system = Column(String, nullable=True)
    manufacturer_identifier_type_version = Column(String, nullable=True)
    manufacturer_identifier_type_code = Column(String, nullable=True)
    manufacturer_identifier_type_display = Column(String, nullable=True)
    manufacturer_identifier_type_user_selected = Column(Boolean, nullable=True)
    manufacturer_identifier_type_text = Column(String, nullable=True)
    manufacturer_identifier_system = Column(String, nullable=True)
    manufacturer_identifier_value = Column(String, nullable=True)
    manufacturer_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    manufacturer_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # form (0..1 CodeableConcept) — text flattened, codings in child table
    form_text = Column(String, nullable=True)

    # amount (0..1 Ratio: numerator Quantity, denominator Quantity)
    amount_numerator_value = Column(Numeric, nullable=True)
    amount_numerator_comparator = Column(
        Enum(
            MedicationQuantityComparator,
            name="medication_quantity_comparator",
        ),
        nullable=True,
    )
    amount_numerator_unit = Column(String, nullable=True)
    amount_numerator_system = Column(String, nullable=True)
    amount_numerator_code = Column(String, nullable=True)

    amount_denominator_value = Column(Numeric, nullable=True)
    amount_denominator_comparator = Column(
        Enum(
            MedicationQuantityComparator,
            name="medication_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    amount_denominator_unit = Column(String, nullable=True)
    amount_denominator_system = Column(String, nullable=True)
    amount_denominator_code = Column(String, nullable=True)

    # batch (0..1 BackboneElement) — lotNumber, expirationDate
    batch_lot_number = Column(String, nullable=True)
    batch_expiration_date = Column(DateTime(timezone=True), nullable=True)

    # 0..* child collections
    identifiers = relationship(
        "MedicationIdentifier",
        back_populates="medication",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    code_codings = relationship(
        "MedicationCodeCoding",
        back_populates="medication",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    form_codings = relationship(
        "MedicationFormCoding",
        back_populates="medication",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    ingredients = relationship(
        "MedicationIngredient",
        back_populates="medication",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
