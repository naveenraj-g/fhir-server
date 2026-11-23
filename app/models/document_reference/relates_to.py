from sqlalchemy import BigInteger, Column, Enum, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

from .enums import DocumentRelationshipType

# The one R4 target of DocumentReference.relatesTo.target.
RELATES_TO_TYPES = ("DocumentReference",)
RELATION_SYSTEM = "http://hl7.org/fhir/document-relationship-type"


class DocumentReferenceRelatesTo(Base):
    """Search index for `relatesto`, `relation` and the `relationship` composite, which read
    DocumentReference.relatesTo (0..*; each entry has a `code` and a `target` Reference): one row
    per relatesTo entry that has a code or a target. Derived from DocumentReferenceModel.content -
    never read to build a response.

    Code and target stay on one row so `relationship=<target>$<code>` pairs the two of the *same*
    entry (a document that replaces A and appends to B does not match `A$appends`).

      relation               -> code (Enum, required binding document-relationship-type)
      relatesto              -> target_type/target_id (a relative DocumentReference/<id>) or
                                target_reference (the raw string, for an absolute URL)
      relatesto:identifier   -> target_identifier_system/_value
      relationship           -> both of the above on the same row

    `target_type` is a plain string, not a Postgres enum. No ForeignKey on `target_id`."""

    __tablename__ = "document_reference_relates_to"
    __table_args__ = (
        Index("ix_document_reference_relates_to_target", "target_type", "target_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )
    code = Column(
        Enum(
            DocumentRelationshipType,
            name="document_relationship_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    target_reference = Column(String, nullable=True)
    target_type = Column(String, nullable=True)
    target_id = Column(BigInteger, nullable=True)
    target_identifier_system = Column(String, nullable=True)
    target_identifier_value = Column(String, nullable=True)

    document_reference = relationship(
        "DocumentReferenceModel", back_populates="relates_to"
    )
