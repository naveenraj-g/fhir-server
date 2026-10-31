from enum import Enum


class ObservationDefinitionPermittedDataType(str, Enum):
    """ObservationDefinition.permittedDataType required binding codes."""

    Quantity = "Quantity"
    CodeableConcept = "CodeableConcept"
    string = "string"
    boolean = "boolean"
    integer = "integer"
    Range = "Range"
    Ratio = "Ratio"
    SampledData = "SampledData"
    time = "time"
    dateTime = "dateTime"
    Period = "Period"


class ObservationDefinitionQualifiedIntervalCategory(str, Enum):
    """ObservationDefinition.qualifiedInterval.category codes."""

    reference = "reference"
    critical = "critical"
    absolute = "absolute"


class ObservationDefinitionGender(str, Enum):
    """ObservationDefinition.qualifiedInterval.gender codes."""

    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class ObservationDefinitionValueSetReferenceType(str, Enum):
    """Target resource for ObservationDefinition value set references."""

    ValueSet = "ValueSet"


class ObservationDefinitionAssignerReferenceType(str, Enum):
    """Target resource for ObservationDefinition.identifier.assigner."""

    Organization = "Organization"
