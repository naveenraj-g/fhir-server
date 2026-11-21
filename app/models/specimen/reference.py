from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The reference parameter held in SpecimenReference, and the element it reads.
REFERENCE_PARAMS = {
    "parent": "parent",
}
# R4 target of `parent`.
PARENT_TYPES = ("Specimen",)
REFERENCE_TYPES = {"parent": PARENT_TYPES}


class SpecimenReference(Base):
    """Search index for the repeating reference parameter `parent` (Specimen.parent, 0..*): one
    row per Reference that has a `reference` or an `identifier` (one with only `display` cannot
    be matched by a reference search). `param` says which parameter the row belongs to (see
    REFERENCE_PARAMS). Derived from SpecimenModel.content — never read to build a response.

      <param>             -> reference_type/reference_id or reference_reference
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` and no UniqueConstraint: R4 does not forbid listing the same
    reference twice."""

    __tablename__ = "specimen_reference"
    __table_args__ = (
        Index(
            "ix_specimen_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    specimen = relationship("SpecimenModel", back_populates="references")
