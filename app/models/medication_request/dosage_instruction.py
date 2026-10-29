from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# dosageInstruction (0..*) Dosage child table
# ---------------------------------------------------------------------------


class MedicationRequestDosageInstruction(TenantAuditMixin, Base):
    """MedicationRequest.dosageInstruction (0..* Dosage) —
    https://www.hl7.org/fhir/R4/datatypes.html#Dosage — this codebase's
    first use of the Dosage datatype.

    `additionalInstruction` (0..* CodeableConcept) gets its own real
    child/grandchild table (MedicationRequestDosageAdditionalInstruction
    + its own `.coding`). `site`/`route`/`method` (each 0..1
    CodeableConcept) and the `asNeededCodeableConcept` choice variant are
    each flattened with `_text` here, their own `coding[]` promoted to a
    dedicated direct-child table — same promotion pattern as every other
    0..1 CodeableConcept in this codebase.

    `timing` (0..1 Timing) and `doseAndRate` (0..* BackboneElement: type
    CodeableConcept, dose[x] Range|Quantity, rate[x] Ratio|Range|Quantity)
    and `maxDosePerPeriod` (0..1 Ratio) are all stored as raw JSONB,
    verbatim — the same deliberate scope decision as
    ServiceRequest.occurrenceTiming (see that model's own docstring):
    Timing is FHIR's most structurally complex datatype, doseAndRate's
    own triple choice-type nesting has no precedent-worthy flattening
    shape in this codebase yet, and Ratio hit a confirmed GraphQL-layer
    bug when nested inside a typed object (see ServiceRequest's own
    `quantityRatio` handling) — raw JSONB sidesteps all three at once.
    `maxDosePerAdministration`/`maxDosePerLifetime` (each a SimpleQuantity,
    structurally simple) ARE flattened normally.
    """

    __tablename__ = "medication_request_dosage_instruction"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    sequence = Column(Integer, nullable=True)
    text = Column(Text, nullable=True)
    patient_instruction = Column(Text, nullable=True)

    # timing (0..1 Timing) — raw, verbatim.
    timing = Column(JSONB, nullable=True)

    # asNeeded[x] (0..1 choice: boolean | CodeableConcept)
    as_needed_boolean = Column(Boolean, nullable=True)
    as_needed_codeable_concept_text = Column(String, nullable=True)

    # site / route / method (each 0..1 CodeableConcept) — text flattened.
    site_text = Column(String, nullable=True)
    route_text = Column(String, nullable=True)
    method_text = Column(String, nullable=True)

    # doseAndRate (0..*) — raw, verbatim (see class docstring).
    dose_and_rate = Column(JSONB, nullable=True)

    # maxDosePerPeriod (0..1 Ratio) — raw, verbatim (see class docstring).
    max_dose_per_period = Column(JSONB, nullable=True)

    # maxDosePerAdministration / maxDosePerLifetime (each 0..1 SimpleQuantity)
    max_dose_per_administration_value = Column(Numeric, nullable=True)
    max_dose_per_administration_unit = Column(String, nullable=True)
    max_dose_per_administration_system = Column(String, nullable=True)
    max_dose_per_administration_code = Column(String, nullable=True)

    max_dose_per_lifetime_value = Column(Numeric, nullable=True)
    max_dose_per_lifetime_unit = Column(String, nullable=True)
    max_dose_per_lifetime_system = Column(String, nullable=True)
    max_dose_per_lifetime_code = Column(String, nullable=True)

    medication_request = relationship("MedicationRequestModel", back_populates="dosage_instructions")
    additional_instructions = relationship(
        "MedicationRequestDosageAdditionalInstruction", back_populates="dosage_instruction", cascade="all, delete-orphan"
    )
    site_codings = relationship(
        "MedicationRequestDosageSiteCoding", back_populates="dosage_instruction", cascade="all, delete-orphan"
    )
    route_codings = relationship(
        "MedicationRequestDosageRouteCoding", back_populates="dosage_instruction", cascade="all, delete-orphan"
    )
    method_codings = relationship(
        "MedicationRequestDosageMethodCoding", back_populates="dosage_instruction", cascade="all, delete-orphan"
    )
    as_needed_codings = relationship(
        "MedicationRequestDosageAsNeededCoding", back_populates="dosage_instruction", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# dosageInstruction.additionalInstruction (0..*) CodeableConcept
# child/grandchild table
# ---------------------------------------------------------------------------


class MedicationRequestDosageAdditionalInstruction(TenantAuditMixin, Base):
    """One entry of MedicationRequest.dosageInstruction.additionalInstruction (0..*)."""

    __tablename__ = "medication_request_dosage_additional_instruction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_dosage_instruction_id = Column(
        BigInteger, ForeignKey("medication_request_dosage_instruction.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    dosage_instruction = relationship("MedicationRequestDosageInstruction", back_populates="additional_instructions")
    codings = relationship(
        "MedicationRequestDosageAdditionalInstructionCoding",
        back_populates="additional_instruction",
        cascade="all, delete-orphan",
    )


class MedicationRequestDosageAdditionalInstructionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of .dosageInstruction.additionalInstruction.coding (0..*)."""

    __tablename__ = "medication_request_dosage_additional_instruction_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_dosage_additional_instruction_id = Column(
        BigInteger, ForeignKey("medication_request_dosage_additional_instruction.id"), nullable=False, index=True
    )

    additional_instruction = relationship("MedicationRequestDosageAdditionalInstruction", back_populates="codings")


# ---------------------------------------------------------------------------
# dosageInstruction.{site,route,method,asNeededCodeableConcept}.coding —
# each a direct-child coding table of the dosage_instruction row
# ---------------------------------------------------------------------------


class MedicationRequestDosageSiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of .dosageInstruction.site.coding (0..*)."""

    __tablename__ = "medication_request_dosage_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_dosage_instruction_id = Column(
        BigInteger, ForeignKey("medication_request_dosage_instruction.id"), nullable=False, index=True
    )

    dosage_instruction = relationship("MedicationRequestDosageInstruction", back_populates="site_codings")


class MedicationRequestDosageRouteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of .dosageInstruction.route.coding (0..*)."""

    __tablename__ = "medication_request_dosage_route_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_dosage_instruction_id = Column(
        BigInteger, ForeignKey("medication_request_dosage_instruction.id"), nullable=False, index=True
    )

    dosage_instruction = relationship("MedicationRequestDosageInstruction", back_populates="route_codings")


class MedicationRequestDosageMethodCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of .dosageInstruction.method.coding (0..*)."""

    __tablename__ = "medication_request_dosage_method_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_dosage_instruction_id = Column(
        BigInteger, ForeignKey("medication_request_dosage_instruction.id"), nullable=False, index=True
    )

    dosage_instruction = relationship("MedicationRequestDosageInstruction", back_populates="method_codings")


class MedicationRequestDosageAsNeededCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of .dosageInstruction.asNeededCodeableConcept.coding (0..*)."""

    __tablename__ = "medication_request_dosage_as_needed_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_dosage_instruction_id = Column(
        BigInteger, ForeignKey("medication_request_dosage_instruction.id"), nullable=False, index=True
    )

    dosage_instruction = relationship("MedicationRequestDosageInstruction", back_populates="as_needed_codings")
