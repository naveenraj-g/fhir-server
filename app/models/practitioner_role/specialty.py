from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# specialty (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class PractitionerRoleSpecialty(TenantAuditMixin, Base):
    """specialty[] — specific specialty of the practitioner. `text` stays
    flattened (sibling of coding[], not part of it); `coding[]` itself is a
    real 0..* child table (PractitionerRoleSpecialtyCoding, below) rather
    than a single flattened coding — same reasoning as
    HealthcareServiceSpecialty's own coding[] promotion."""

    __tablename__ = "practitioner_role_specialty"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_pk = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    practitioner_role = relationship(
        "PractitionerRoleModel", back_populates="specialties"
    )
    codings = relationship(
        "PractitionerRoleSpecialtyCoding",
        back_populates="specialty",
        cascade="all, delete-orphan",
    )


class PractitionerRoleSpecialtyCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of PractitionerRole.specialty.coding (0..*)."""

    __tablename__ = "practitioner_role_specialty_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_specialty_id = Column(
        BigInteger,
        ForeignKey("practitioner_role_specialty.id"),
        nullable=False,
        index=True,
    )

    specialty = relationship("PractitionerRoleSpecialty", back_populates="codings")
