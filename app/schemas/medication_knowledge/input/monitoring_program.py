from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)


class MedicationKnowledgeMonitoringProgramInput(BaseModel):
    """MedicationKnowledge.monitoringProgram (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    type: MedicationKnowledgeCodeableConceptInput | None = Field(
        None, description="Type of program under which the medication is monitored."
    )
    name: str | None = Field(None, description="Name of the monitoring program.")
