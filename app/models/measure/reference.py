from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in MeasureReference, and the Measure element each
# reads: the five relatedArtifact types (`resource`, a canonical URL) and, for `depends-on`, also
# `library` (a canonical(Library)).
REFERENCE_PARAMS = {
    "composed-of": "relatedArtifact.where(type='composed-of').resource",
    "depends-on": "relatedArtifact.where(type='depends-on').resource | library",
    "derived-from": "relatedArtifact.where(type='derived-from').resource",
    "predecessor": "relatedArtifact.where(type='predecessor').resource",
    "successor": "relatedArtifact.where(type='successor').resource",
}


class MeasureReference(Base):
    """Search index for the five `relatedArtifact` reference parameters (`composed-of`,
    `depends-on`, `derived-from`, `predecessor`, `successor`): one row per canonical URL. `param`
    says which search parameter the row belongs to (see REFERENCE_PARAMS). Derived from
    MeasureModel.content - never read to build a response.

    R4's `RelatedArtifact.resource` is a canonical URL (a string, not a Reference object): the
    row keeps the raw string in `reference_reference` (a versioned `url|1.0` is also found by the
    unversioned `url`), and a relative `Type/<id>` is additionally resolved into
    `reference_type` / `reference_id` (a plain string, not a Postgres enum) so a search by
    `Type/<id>`, chaining and `_include` work for it.

    No ForeignKey on `reference_id` (the public id of another resource) and no UniqueConstraint:
    R4 does not forbid listing the same artifact twice."""

    __tablename__ = "measure_reference"
    __table_args__ = (
        Index(
            "ix_measure_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)

    measure = relationship("MeasureModel", back_populates="references")
