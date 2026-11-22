from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in ServiceRequestToken, and the ServiceRequest element each reads
# (`body-site` -> bodySite, `performer-type` -> performerType; the others read the element
# of the same name).
TOKEN_PARAMS = {
    "category": "category",
    "code": "code",
    "body-site": "bodySite",
    "performer-type": "performerType",
}


class ServiceRequestToken(Base):
    """Search index for the four CodeableConcept token parameters (`category`,
    `code`, `body-site`, `performer-type`): one row per coding of each concept — a token search
    matches any coding of any entry — plus one code-less row for a concept with
    only `text`, so `:text` still finds it. `param` says which search parameter
    the row belongs to (see TOKEN_PARAMS). Derived from ServiceRequestModel.content —
    never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service

    One shared table instead of three identical ones."""

    __tablename__ = "service_request_token"
    __table_args__ = (Index("ix_service_request_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    service_request = relationship("ServiceRequestModel", back_populates="tokens")
