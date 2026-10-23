from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# code (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class PractitionerRoleCode(TenantAuditMixin, Base):
    """code[] — roles which this practitioner may perform. `text` stays
    flattened (sibling of coding[], not part of it); `coding[]` itself is a
    real 0..* child table (PractitionerRoleCodeCoding, below) rather than a
    single flattened coding — same reasoning as HealthcareServiceCategory's
    own coding[] promotion."""

    __tablename__ = "practitioner_role_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_pk = Column(
        BigInteger, ForeignKey("practitioner_role.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    practitioner_role = relationship("PractitionerRoleModel", back_populates="codes")
    codings = relationship(
        "PractitionerRoleCodeCoding",
        back_populates="code_concept",
        cascade="all, delete-orphan",
    )


class PractitionerRoleCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of PractitionerRole.code.coding (0..*)."""

    __tablename__ = "practitioner_role_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_role_code_id = Column(
        BigInteger, ForeignKey("practitioner_role_code.id"), nullable=False, index=True
    )

    # Named `code_concept`, not `code` — `code` is already FhirCodingMixin's
    # own column name on this very class, and a same-named relationship in
    # the class body would shadow it, silently dropping the `code` column.
    code_concept = relationship("PractitionerRoleCode", back_populates="codings")
