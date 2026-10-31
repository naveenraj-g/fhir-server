from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.allergy_intolerance.enums import (
    AllergyIntoleranceNoteAuthorReferenceType,
    AllergyIntoleranceSeverity,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class AllergyIntoleranceReaction(TenantAuditMixin, Base):
    """AllergyIntolerance.reaction (0..* BackboneElement) child table."""

    __tablename__ = "allergy_intolerance_reaction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    allergy_intolerance_pk = Column(
        BigInteger,
        ForeignKey("allergy_intolerance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    description = Column(String, nullable=True)
    onset = Column(DateTime(timezone=True), nullable=True)
    severity = Column(
        Enum(
            AllergyIntoleranceSeverity,
            name="allergy_intolerance_severity",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    substance_text = Column(String, nullable=True)
    exposure_route_text = Column(String, nullable=True)

    allergy_intolerance = relationship(
        "AllergyIntoleranceModel",
        back_populates="reactions",
    )
    substance_codings = relationship(
        "AllergyIntoleranceReactionSubstanceCoding",
        back_populates="reaction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    manifestations = relationship(
        "AllergyIntoleranceReactionManifestation",
        back_populates="reaction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    exposure_route_codings = relationship(
        "AllergyIntoleranceReactionExposureRouteCoding",
        back_populates="reaction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notes = relationship(
        "AllergyIntoleranceReactionNote",
        back_populates="reaction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AllergyIntoleranceReactionSubstanceCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """AllergyIntolerance.reaction.substance.coding (0..* Coding) grandchild table."""

    __tablename__ = "allergy_intolerance_reaction_substance_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reaction_id = Column(
        BigInteger,
        ForeignKey("allergy_intolerance_reaction.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reaction = relationship(
        "AllergyIntoleranceReaction",
        back_populates="substance_codings",
    )


class AllergyIntoleranceReactionManifestation(TenantAuditMixin, Base):
    """AllergyIntolerance.reaction.manifestation (1..* CodeableConcept) grandchild table."""

    __tablename__ = "allergy_intolerance_reaction_manifestation"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reaction_id = Column(
        BigInteger,
        ForeignKey("allergy_intolerance_reaction.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    reaction = relationship(
        "AllergyIntoleranceReaction",
        back_populates="manifestations",
    )
    codings = relationship(
        "AllergyIntoleranceReactionManifestationCoding",
        back_populates="manifestation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AllergyIntoleranceReactionManifestationCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """AllergyIntolerance.reaction.manifestation.coding (0..* Coding) great-grandchild table."""

    __tablename__ = "allergy_intolerance_reaction_manifestation_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    manifestation_id = Column(
        BigInteger,
        ForeignKey(
            "allergy_intolerance_reaction_manifestation.id", ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )

    manifestation = relationship(
        "AllergyIntoleranceReactionManifestation",
        back_populates="codings",
    )


class AllergyIntoleranceReactionExposureRouteCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """AllergyIntolerance.reaction.exposureRoute.coding (0..* Coding) grandchild table."""

    __tablename__ = "allergy_intolerance_reaction_exposure_route_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reaction_id = Column(
        BigInteger,
        ForeignKey("allergy_intolerance_reaction.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reaction = relationship(
        "AllergyIntoleranceReaction",
        back_populates="exposure_route_codings",
    )


class AllergyIntoleranceReactionNote(TenantAuditMixin, Base):
    """AllergyIntolerance.reaction.note (0..* Annotation) grandchild table."""

    __tablename__ = "allergy_intolerance_reaction_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reaction_id = Column(
        BigInteger,
        ForeignKey("allergy_intolerance_reaction.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    text = Column(Text, nullable=False)
    time = Column(DateTime(timezone=True), nullable=True)
    author_string = Column(String, nullable=True)
    author_reference_type = Column(
        Enum(
            AllergyIntoleranceNoteAuthorReferenceType,
            name="allergy_intolerance_reaction_note_author_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    author_reference_id = Column(BigInteger, nullable=True)
    author_reference_display = Column(String, nullable=True)

    reaction = relationship(
        "AllergyIntoleranceReaction",
        back_populates="notes",
    )
