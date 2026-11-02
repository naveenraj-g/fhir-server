from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse,
    SubjectReferenceType,
)
from app.models.shared import TenantAuditMixin

from .enums import (
    ClinicalImpressionAssessorReferenceType,
    ClinicalImpressionPreviousReferenceType,
    ClinicalImpressionStatus,
)


class ClinicalImpressionModel(TenantAuditMixin, Base):
    """ClinicalImpression main resource table.
    Targets FHIR R4: https://www.hl7.org/fhir/R4/clinicalimpression.html
    Public sequence start=530000.
    """

    __tablename__ = "clinical_impression"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_id = Column(
        BigInteger,
        Sequence(
            "clinical_impression_pub_seq",
            start=530000,
            increment=1,
            metadata=Base.metadata,
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # Base DomainResource extension JSONB
    extension = Column(JSONB, nullable=True, default=list)

    # status (1..1 code)
    status = Column(
        Enum(
            ClinicalImpressionStatus,
            name="clinical_impression_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        index=True,
    )

    # statusReason (0..1 CodeableConcept text)
    status_reason_text = Column(String, nullable=True)

    # code (0..1 CodeableConcept text)
    code_text = Column(String, nullable=True)

    # description (0..1 string)
    description = Column(String, nullable=True)

    # subject (1..1 Reference(Patient | Group))
    subject_reference = Column(String, nullable=False)
    subject_type = Column(
        Enum(SubjectReferenceType, name="subject_reference_type", create_type=False),
        nullable=False,
    )
    subject_id = Column(BigInteger, nullable=False, index=True)
    subject_display = Column(String, nullable=True)

    subject_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    subject_identifier_type_system = Column(String, nullable=True)
    subject_identifier_type_version = Column(String, nullable=True)
    subject_identifier_type_code = Column(String, nullable=True)
    subject_identifier_type_display = Column(String, nullable=True)
    subject_identifier_type_user_selected = Column(Boolean, nullable=True)
    subject_identifier_type_text = Column(String, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)
    subject_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    subject_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(EncounterReferenceType, name="encounter_reference_type", create_type=False),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    encounter_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    encounter_identifier_type_system = Column(String, nullable=True)
    encounter_identifier_type_version = Column(String, nullable=True)
    encounter_identifier_type_code = Column(String, nullable=True)
    encounter_identifier_type_display = Column(String, nullable=True)
    encounter_identifier_type_user_selected = Column(Boolean, nullable=True)
    encounter_identifier_type_text = Column(String, nullable=True)
    encounter_identifier_system = Column(String, nullable=True)
    encounter_identifier_value = Column(String, nullable=True)
    encounter_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    encounter_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # effective[x] (0..1 dateTime | Period)
    effective_date_time = Column(DateTime(timezone=True), nullable=True)
    effective_period_start = Column(DateTime(timezone=True), nullable=True)
    effective_period_end = Column(DateTime(timezone=True), nullable=True)

    # date (0..1 dateTime)
    date = Column(DateTime(timezone=True), nullable=True)

    # assessor (0..1 Reference(Practitioner | PractitionerRole))
    assessor_reference = Column(String, nullable=True)
    assessor_type = Column(
        Enum(
            ClinicalImpressionAssessorReferenceType,
            name="clinical_impression_assessor_reference_type",
        ),
        nullable=True,
    )
    assessor_id = Column(BigInteger, nullable=True, index=True)
    assessor_display = Column(String, nullable=True)

    assessor_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    assessor_identifier_type_system = Column(String, nullable=True)
    assessor_identifier_type_version = Column(String, nullable=True)
    assessor_identifier_type_code = Column(String, nullable=True)
    assessor_identifier_type_display = Column(String, nullable=True)
    assessor_identifier_type_user_selected = Column(Boolean, nullable=True)
    assessor_identifier_type_text = Column(String, nullable=True)
    assessor_identifier_system = Column(String, nullable=True)
    assessor_identifier_value = Column(String, nullable=True)
    assessor_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    assessor_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # previous (0..1 Reference(ClinicalImpression))
    previous_reference = Column(String, nullable=True)
    previous_type = Column(
        Enum(
            ClinicalImpressionPreviousReferenceType,
            name="clinical_impression_previous_reference_type",
        ),
        nullable=True,
    )
    previous_id = Column(BigInteger, nullable=True, index=True)
    previous_display = Column(String, nullable=True)

    previous_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    previous_identifier_type_system = Column(String, nullable=True)
    previous_identifier_type_version = Column(String, nullable=True)
    previous_identifier_type_code = Column(String, nullable=True)
    previous_identifier_type_display = Column(String, nullable=True)
    previous_identifier_type_user_selected = Column(Boolean, nullable=True)
    previous_identifier_type_text = Column(String, nullable=True)
    previous_identifier_system = Column(String, nullable=True)
    previous_identifier_value = Column(String, nullable=True)
    previous_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    previous_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # summary (0..1 string)
    summary = Column(Text, nullable=True)

    # Relationships
    identifiers = relationship(
        "ClinicalImpressionIdentifierModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    status_reason_codings = relationship(
        "ClinicalImpressionStatusReasonCodingModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    code_codings = relationship(
        "ClinicalImpressionCodeCodingModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    problems = relationship(
        "ClinicalImpressionProblemModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    investigations = relationship(
        "ClinicalImpressionInvestigationModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    protocols = relationship(
        "ClinicalImpressionProtocolModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    findings = relationship(
        "ClinicalImpressionFindingModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    prognosis_codeable_concepts = relationship(
        "ClinicalImpressionPrognosisCodeableConceptModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    prognosis_references = relationship(
        "ClinicalImpressionPrognosisReferenceModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    supporting_info = relationship(
        "ClinicalImpressionSupportingInfoModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notes = relationship(
        "ClinicalImpressionNoteModel",
        back_populates="clinical_impression",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
