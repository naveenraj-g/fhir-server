from sqlalchemy import BigInteger, Column, Enum, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import MedicationKnowledgeStatus

medication_knowledge_id_seq = Sequence(
    "medication_knowledge_pub_seq", start=600000, increment=1, metadata=Base.metadata
)

# R4 target of MedicationKnowledge.manufacturer.
MANUFACTURER_TYPES = ("Organization",)


class MedicationKnowledgeModel(TenantAuditMixin, Base):
    """FHIR R4 MedicationKnowledge - content-based storage, same as Medication, Patient,
    Encounter and the other rebuilt resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at
    read time from this row's own columns - see app.fhir.mappers.medication_knowledge).
    Every other column exists only because a FHIR R4 MedicationKnowledge search parameter
    filters on it (https://www.hl7.org/fhir/R4/medicationknowledge.html#search) and is derived
    from `content` on every write by app.repository.medication_knowledge._indexer.

    Search parameter -> storage:
      status           -> status (0..1 code, Enum column, stored by value so
                          `entered-in-error` is the real FHIR code)
      manufacturer     -> manufacturer_reference/_type/_id + manufacturer_identifier_*
                          (0..1 Reference(Organization), columns)
      code, doseform, ingredient-code, classification, classification-type,
      monograph-type, monitoring-program-type
                       -> MedicationKnowledgeToken (one shared table, one row per coding;
                          `ingredient-code` reads ingredient.itemCodeableConcept,
                          `classification` / `classification-type` read
                          medicineClassification.classification / .type of every entry)
      monitoring-program-name, source-cost
                       -> MedicationKnowledgeToken too: a token search over a plain string
                          (monitoringProgram.name, cost.source), the string held as `code`
                          with no system
      ingredient       -> MedicationKnowledgeReference (ingredient.itemReference, a
                          Reference(Substance))
      monograph        -> MedicationKnowledgeReference (monograph.source, a
                          Reference(DocumentReference | Media))
      _id              -> medication_knowledge_id;  _lastUpdated -> updated_at/created_at

    Everything else (`doseForm`, `amount`, `synonym`, `relatedMedicationKnowledge`,
    `associatedMedication`, `productType`, `ingredient.isActive`/`.strength`,
    `preparationInstruction`, `intendedRoute`, `contraindication`, `regulatory`, `kinetics`,
    `packaging`, `drugCharacteristic`, `administrationGuidelines`, `extension`) has no search
    parameter and lives only in `content`.

    `monograph` points at two resource types, so `reference_type` records which one a
    relative `Type/<id>` names (a plain string, not a Postgres enum): a search by bare id is
    ambiguous (`monograph=Type/id` or `monograph:Type=id`). `ingredient` (Substance) and
    `manufacturer` (Organization) have one target, so a bare id works.

    All index columns are nullable (every MedicationKnowledge element is optional in R4). No
    `user_id`: a MedicationKnowledge is a shared tenant-level entity. No DB-level CHECK
    constraints."""

    __tablename__ = "medication_knowledge"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    medication_knowledge_id = Column(
        BigInteger,
        medication_knowledge_id_seq,
        server_default=medication_knowledge_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        Enum(
            MedicationKnowledgeStatus,
            name="medication_knowledge_status",
            # Store `entered-in-error`, not the Python member name.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # manufacturer (0..1 Reference(Organization))
    manufacturer_reference = Column(String, nullable=True)
    manufacturer_type = Column(String, nullable=True)
    manufacturer_id = Column(BigInteger, nullable=True, index=True)
    manufacturer_identifier_system = Column(String, nullable=True)
    manufacturer_identifier_value = Column(String, nullable=True)

    tokens = relationship(
        "MedicationKnowledgeToken",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "MedicationKnowledgeReference",
        back_populates="medication_knowledge",
        cascade="all, delete-orphan",
    )
