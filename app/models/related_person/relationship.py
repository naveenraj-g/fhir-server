from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class RelatedPersonRelationship(TenantAuditMixin, Base):
    """RelatedPerson.relationship (0..* CodeableConcept) child table."""

    __tablename__ = "related_person_relationship"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    related_person_pk = Column(
        BigInteger, ForeignKey("related_person.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    related_person = relationship("RelatedPersonModel", back_populates="relationships")
    codings = relationship(
        "RelatedPersonRelationshipCoding",
        back_populates="relationship",
        cascade="all, delete-orphan",
    )


class RelatedPersonRelationshipCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of RelatedPerson.relationship.coding (0..*)."""

    __tablename__ = "related_person_relationship_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    related_person_relationship_id = Column(
        BigInteger,
        ForeignKey("related_person_relationship.id"),
        nullable=False,
        index=True,
    )

    relationship = relationship("RelatedPersonRelationship", back_populates="codings")
