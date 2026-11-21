from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class AppointmentResponseIdentifier(Base):
    """Search index for the `identifier` token parameter (0..*). Derived
    from AppointmentResponseModel.content — never read to build a response.

    One row per AppointmentResponse.identifier *per Identifier.type.coding*
    (one row with no type when the identifier has no coded type), so that
    `identifier:of-type=type-system|type-code|value` can match type and value
    on the same row. A plain `identifier=` search is an EXISTS, so the
    repetition never duplicates results.

      identifier            -> system, value
      identifier:of-type    -> type_system, type_code, value
      identifier:text       -> type_text_norm / type_display_norm

    No UniqueConstraint on (system, value): FHIR R4 does not require
    identifier uniqueness — that is a profile decision, not a base rule."""

    __tablename__ = "appointment_response_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Named appointment_response_pk (not appointment_response_id) so it cannot
    # be confused with AppointmentResponseModel.appointment_response_id, the
    # public sequence id.
    appointment_response_pk = Column(
        BigInteger, ForeignKey("appointment_response.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    value = Column(String, nullable=True, index=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_text_norm = Column(String, nullable=True)
    type_display_norm = Column(String, nullable=True)

    appointment_response = relationship(
        "AppointmentResponseModel", back_populates="identifiers"
    )
