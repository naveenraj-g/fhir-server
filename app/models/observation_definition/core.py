from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Enum,
    Integer,
    Numeric,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.observation_definition.enums import (
    ObservationDefinitionPermittedDataType,
    ObservationDefinitionValueSetReferenceType,
)
from app.models.shared import TenantAuditMixin

observation_definition_pub_seq = Sequence(
    "observation_definition_pub_seq",
    start=400000,
    increment=1,
    metadata=Base.metadata,
)


class ObservationDefinitionModel(TenantAuditMixin, Base):
    """ObservationDefinition FHIR R4 resource root model.

    FHIR R4: https://www.hl7.org/fhir/R4/observationdefinition.html
    """

    __tablename__ = "observation_definition"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    observation_definition_id = Column(
        BigInteger,
        observation_definition_pub_seq,
        server_default=observation_definition_pub_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )


    # Resource-level extension support (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # code (1..1 CodeableConcept) — text on main table, codings in child table
    code_text = Column(String, nullable=True)

    # permittedDataType (0..* code) — required binding to ObservationDataType
    permitted_data_type = Column(
        ARRAY(
            Enum(
                ObservationDefinitionPermittedDataType,
                name="observation_definition_permitted_data_type",
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
            )
        ),
        nullable=True,
    )

    # multipleResultsAllowed (0..1 boolean)
    multiple_results_allowed = Column(Boolean, nullable=True)

    # method (0..1 CodeableConcept)
    method_text = Column(String, nullable=True)

    # preferredReportName (0..1 string)
    preferred_report_name = Column(String, nullable=True)

    # quantitativeDetails (0..1 BackboneElement)
    quantitative_details_customary_unit_text = Column(String, nullable=True)
    quantitative_details_unit_text = Column(String, nullable=True)
    quantitative_details_conversion_factor = Column(Numeric, nullable=True)
    quantitative_details_decimal_precision = Column(Integer, nullable=True)

    # validCodedValueSet (0..1 Reference(ValueSet))
    valid_coded_value_set_reference = Column(String, nullable=True)
    valid_coded_value_set_type = Column(
        Enum(
            ObservationDefinitionValueSetReferenceType,
            name="observation_definition_value_set_reference_type",
        ),
        nullable=True,
    )
    valid_coded_value_set_id = Column(BigInteger, nullable=True, index=True)
    valid_coded_value_set_display = Column(String, nullable=True)

    # normalCodedValueSet (0..1 Reference(ValueSet))
    normal_coded_value_set_reference = Column(String, nullable=True)
    normal_coded_value_set_type = Column(
        Enum(
            ObservationDefinitionValueSetReferenceType,
            name="observation_definition_value_set_reference_type",
        ),
        nullable=True,
    )
    normal_coded_value_set_id = Column(BigInteger, nullable=True, index=True)
    normal_coded_value_set_display = Column(String, nullable=True)

    # abnormalCodedValueSet (0..1 Reference(ValueSet))
    abnormal_coded_value_set_reference = Column(String, nullable=True)
    abnormal_coded_value_set_type = Column(
        Enum(
            ObservationDefinitionValueSetReferenceType,
            name="observation_definition_value_set_reference_type",
        ),
        nullable=True,
    )
    abnormal_coded_value_set_id = Column(BigInteger, nullable=True, index=True)
    abnormal_coded_value_set_display = Column(String, nullable=True)

    # criticalCodedValueSet (0..1 Reference(ValueSet))
    critical_coded_value_set_reference = Column(String, nullable=True)
    critical_coded_value_set_type = Column(
        Enum(
            ObservationDefinitionValueSetReferenceType,
            name="observation_definition_value_set_reference_type",
        ),
        nullable=True,
    )
    critical_coded_value_set_id = Column(BigInteger, nullable=True, index=True)
    critical_coded_value_set_display = Column(String, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    identifiers = relationship(
        "ObservationDefinitionIdentifier",
        back_populates="observation_definition",
        cascade="all, delete-orphan",
    )
    categories = relationship(
        "ObservationDefinitionCategory",
        back_populates="observation_definition",
        cascade="all, delete-orphan",
    )
    code_codings = relationship(
        "ObservationDefinitionCodeCoding",
        back_populates="observation_definition",
        cascade="all, delete-orphan",
    )
    method_codings = relationship(
        "ObservationDefinitionMethodCoding",
        back_populates="observation_definition",
        cascade="all, delete-orphan",
    )
    quantitative_details_customary_unit_codings = relationship(
        "ObservationDefinitionQuantitativeDetailsCustomaryUnitCoding",
        back_populates="observation_definition",
        cascade="all, delete-orphan",
    )
    quantitative_details_unit_codings = relationship(
        "ObservationDefinitionQuantitativeDetailsUnitCoding",
        back_populates="observation_definition",
        cascade="all, delete-orphan",
    )
    qualified_intervals = relationship(
        "ObservationDefinitionQualifiedInterval",
        back_populates="observation_definition",
        cascade="all, delete-orphan",
    )
