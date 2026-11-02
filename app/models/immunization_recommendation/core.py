from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.immunization_recommendation.enums import (
    ImmunizationRecommendationAuthorityReferenceType,
    ImmunizationRecommendationPatientReferenceType,
)
from app.models.shared import TenantAuditMixin

_seq = Sequence(
    "immunization_recommendation_pub_seq",
    start=510000,
    increment=1,
    metadata=Base.metadata,
)


class ImmunizationRecommendationModel(TenantAuditMixin, Base):
    """FHIR R4 ImmunizationRecommendation resource.

    A patient's point-in-time set of recommendations (i.e. forecasting)
    according to a published schedule with optional supporting documentation.
    """

    __tablename__ = "immunization_recommendation"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    immunization_recommendation_id = Column(
        BigInteger,
        _seq,
        server_default=_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # Resource-level extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # patient (1..1 Reference(Patient))
    patient_reference = Column(String, nullable=False)
    patient_type = Column(
        Enum(
            ImmunizationRecommendationPatientReferenceType,
            name="immunization_recommendation_patient_reference_type",
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

    # date (1..1 dateTime)
    date = Column(DateTime(timezone=True), nullable=False)

    # authority (0..1 Reference(Organization))
    authority_reference = Column(String, nullable=True)
    authority_type = Column(
        Enum(
            ImmunizationRecommendationAuthorityReferenceType,
            name="immunization_recommendation_authority_reference_type",
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

    # Child relationships
    identifiers = relationship(
        "ImmunizationRecommendationIdentifierModel",
        back_populates="immunization_recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    recommendations = relationship(
        "ImmunizationRecommendationRecommendationModel",
        back_populates="immunization_recommendation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
