from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class EndpointPayloadType(Base):
    """Search index for the `payload-type` token parameter (1..*): one row
    per Endpoint.payloadType[].coding[] (a token search matches any coding of
    any entry) — plus one code-less row for an entry that has only `text`, so
    `payload-type:text` still finds it. Derived from EndpointModel.content —
    never read to build a response.

      payload-type            -> system, code
      payload-type:text       -> text_norm (CodeableConcept.text) / display_norm
      payload-type:in/:below  -> system, code, resolved through the terminology service"""

    __tablename__ = "endpoint_payload_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    endpoint_pk = Column(BigInteger, ForeignKey("endpoint.id"), nullable=False, index=True)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    endpoint = relationship("EndpointModel", back_populates="payload_types")
