from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class ProcedureInstantiatesUri(Base):
    """Search index for `instantiates-uri` (Procedure.instantiatesUri, 0..* uri):
    one row per URI. A `uri` search matches exactly (case-sensitive); `:below`
    matches stored URIs that start with the value and `:above` stored URIs that
    are a prefix of it. Derived from ProcedureModel.content — never read to build
    a response."""

    __tablename__ = "procedure_instantiates_uri"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id"), nullable=False, index=True
    )
    uri = Column(String, nullable=False, index=True)

    procedure = relationship("ProcedureModel", back_populates="instantiates_uris")
