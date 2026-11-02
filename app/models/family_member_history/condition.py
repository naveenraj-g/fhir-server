from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.family_member_history.enums import (
    FamilyMemberHistoryNoteAuthorReferenceType,
    FamilyMemberHistoryQuantityComparator,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class FamilyMemberHistoryCondition(TenantAuditMixin, Base):
    """FamilyMemberHistory.condition (0..* BackboneElement)."""

    __tablename__ = "family_member_history_condition"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_pk = Column(
        BigInteger, ForeignKey("family_member_history.id"), nullable=False, index=True
    )

    code_text = Column(String, nullable=True)
    outcome_text = Column(String, nullable=True)
    contributed_to_death = Column(Boolean, nullable=True)

    # onset[x] (0..1 choice: Age | Range | Period | string)
    onset_age_value = Column(Numeric, nullable=True)
    onset_age_comparator = Column(
        Enum(
            FamilyMemberHistoryQuantityComparator,
            name="family_member_history_quantity_comparator",
        ),
        nullable=True,
    )
    onset_age_unit = Column(String, nullable=True)
    onset_age_system = Column(String, nullable=True)
    onset_age_code = Column(String, nullable=True)

    onset_range_low_value = Column(Numeric, nullable=True)
    onset_range_low_unit = Column(String, nullable=True)
    onset_range_low_system = Column(String, nullable=True)
    onset_range_low_code = Column(String, nullable=True)
    onset_range_high_value = Column(Numeric, nullable=True)
    onset_range_high_unit = Column(String, nullable=True)
    onset_range_high_system = Column(String, nullable=True)
    onset_range_high_code = Column(String, nullable=True)

    onset_period_start = Column(DateTime(timezone=True), nullable=True)
    onset_period_end = Column(DateTime(timezone=True), nullable=True)
    onset_string = Column(String, nullable=True)

    family_member_history = relationship(
        "FamilyMemberHistoryModel", back_populates="conditions"
    )
    code_codings = relationship(
        "FamilyMemberHistoryConditionCodeCoding",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    outcome_codings = relationship(
        "FamilyMemberHistoryConditionOutcomeCoding",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "FamilyMemberHistoryConditionNote",
        back_populates="condition",
        cascade="all, delete-orphan",
    )


class FamilyMemberHistoryConditionCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of FamilyMemberHistory.condition.code.coding (0..*)."""

    __tablename__ = "family_member_history_condition_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_condition_id = Column(
        BigInteger,
        ForeignKey("family_member_history_condition.id"),
        nullable=False,
        index=True,
    )

    condition = relationship("FamilyMemberHistoryCondition", back_populates="code_codings")


class FamilyMemberHistoryConditionOutcomeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of FamilyMemberHistory.condition.outcome.coding (0..*)."""

    __tablename__ = "family_member_history_condition_outcome_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_condition_id = Column(
        BigInteger,
        ForeignKey("family_member_history_condition.id"),
        nullable=False,
        index=True,
    )

    condition = relationship("FamilyMemberHistoryCondition", back_populates="outcome_codings")


class FamilyMemberHistoryConditionNote(TenantAuditMixin, Base):
    """One entry of FamilyMemberHistory.condition.note (0..* Annotation)."""

    __tablename__ = "family_member_history_condition_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_condition_id = Column(
        BigInteger,
        ForeignKey("family_member_history_condition.id"),
        nullable=False,
        index=True,
    )

    author_string = Column(String, nullable=True)
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(
            FamilyMemberHistoryNoteAuthorReferenceType,
            name="family_member_history_note_author_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    # author.identifier fallback (11 columns)
    author_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    author_identifier_type_system = Column(String, nullable=True)
    author_identifier_type_version = Column(String, nullable=True)
    author_identifier_type_code = Column(String, nullable=True)
    author_identifier_type_display = Column(String, nullable=True)
    author_identifier_type_user_selected = Column(Boolean, nullable=True)
    author_identifier_type_text = Column(String, nullable=True)
    author_identifier_system = Column(String, nullable=True)
    author_identifier_value = Column(String, nullable=True)
    author_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    author_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    time = Column(DateTime(timezone=True), nullable=True)
    text = Column(Text, nullable=True)

    condition = relationship("FamilyMemberHistoryCondition", back_populates="notes")
