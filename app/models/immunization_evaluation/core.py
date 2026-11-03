from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Integer,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.immunization_evaluation.enums import (
    ImmunizationEvaluationAuthorityReferenceType,
    ImmunizationEvaluationImmunizationEventReferenceType,
    ImmunizationEvaluationPatientReferenceType,
    ImmunizationEvaluationStatus,
)
from app.models.shared import TenantAuditMixin

_seq = Sequence(
    "immunization_evaluation_pub_seq",
    start=610000,
    increment=1,
    metadata=Base.metadata,
)


class ImmunizationEvaluationModel(TenantAuditMixin, Base):
    """FHIR R4 ImmunizationEvaluation resource.
    https://www.hl7.org/fhir/R4/immunizationevaluation.html

    Describes a comparison of an immunization event against published
    recommendations to determine if the administration is 'valid' in relation
    to a specific protocol.
    """

    __tablename__ = "immunization_evaluation"

    __table_args__ = (
        CheckConstraint(
            "dose_number_positive_int IS NULL OR dose_number_string IS NULL",
            name="ck_immunization_evaluation_dose_number_choice",
        ),
        CheckConstraint(
            "series_doses_positive_int IS NULL OR series_doses_string IS NULL",
            name="ck_immunization_evaluation_series_doses_choice",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    immunization_evaluation_id = Column(
        BigInteger,
        _seq,
        server_default=_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # Resource-level extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # status (1..1 code)
    status = Column(
        Enum(
            ImmunizationEvaluationStatus,
            name="immunization_evaluation_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )

    # patient (1..1 Reference(Patient))
    patient_reference = Column(String, nullable=False)
    patient_type = Column(
        Enum(
            ImmunizationEvaluationPatientReferenceType,
            name="immunization_evaluation_patient_reference_type",
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

    # date (0..1 dateTime)
    date = Column(DateTime(timezone=True), nullable=True)

    # authority (0..1 Reference(Organization))
    authority_reference = Column(String, nullable=True)
    authority_type = Column(
        Enum(
            ImmunizationEvaluationAuthorityReferenceType,
            name="immunization_evaluation_authority_reference_type",
        ),
        nullable=True,
    )
    authority_id = Column(BigInteger, nullable=True, index=True)
    authority_display = Column(String, nullable=True)

    # authority.identifier fallback (11 columns)
    authority_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    authority_identifier_type_system = Column(String, nullable=True)
    authority_identifier_type_version = Column(String, nullable=True)
    authority_identifier_type_code = Column(String, nullable=True)
    authority_identifier_type_display = Column(String, nullable=True)
    authority_identifier_type_user_selected = Column(Boolean, nullable=True)
    authority_identifier_type_text = Column(String, nullable=True)
    authority_identifier_system = Column(String, nullable=True)
    authority_identifier_value = Column(String, nullable=True)
    authority_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    authority_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # targetDisease (1..1 CodeableConcept) — text flattened, codings in child table
    target_disease_text = Column(String, nullable=True)

    # immunizationEvent (1..1 Reference(Immunization))
    immunization_event_reference = Column(String, nullable=False)
    immunization_event_type = Column(
        Enum(
            ImmunizationEvaluationImmunizationEventReferenceType,
            name="immunization_evaluation_immunization_event_reference_type",
        ),
        nullable=False,
    )
    immunization_event_id = Column(BigInteger, nullable=True, index=True)
    immunization_event_display = Column(String, nullable=True)

    # immunizationEvent.identifier fallback (11 columns)
    immunization_event_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    immunization_event_identifier_type_system = Column(String, nullable=True)
    immunization_event_identifier_type_version = Column(String, nullable=True)
    immunization_event_identifier_type_code = Column(String, nullable=True)
    immunization_event_identifier_type_display = Column(String, nullable=True)
    immunization_event_identifier_type_user_selected = Column(Boolean, nullable=True)
    immunization_event_identifier_type_text = Column(String, nullable=True)
    immunization_event_identifier_system = Column(String, nullable=True)
    immunization_event_identifier_value = Column(String, nullable=True)
    immunization_event_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    immunization_event_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # doseStatus (1..1 CodeableConcept) — text flattened, codings in child table
    dose_status_text = Column(String, nullable=True)

    # description (0..1 string)
    description = Column(String, nullable=True)

    # series (0..1 string)
    series = Column(String, nullable=True)

    # doseNumber[x] (0..1 positiveInt | string)
    dose_number_positive_int = Column(Integer, nullable=True)
    dose_number_string = Column(String, nullable=True)

    # seriesDoses[x] (0..1 positiveInt | string)
    series_doses_positive_int = Column(Integer, nullable=True)
    series_doses_string = Column(String, nullable=True)

    # Child relationships
    identifiers = relationship(
        "ImmunizationEvaluationIdentifierModel",
        back_populates="immunization_evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    target_disease_codings = relationship(
        "ImmunizationEvaluationTargetDiseaseCodingModel",
        back_populates="immunization_evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    dose_status_codings = relationship(
        "ImmunizationEvaluationDoseStatusCodingModel",
        back_populates="immunization_evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    dose_status_reasons = relationship(
        "ImmunizationEvaluationDoseStatusReasonModel",
        back_populates="immunization_evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
