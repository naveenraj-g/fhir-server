from enum import Enum


class GroupType(str, Enum):
    """Group.type (group-type, required) - stored by value."""

    person = "person"
    animal = "animal"
    practitioner = "practitioner"
    device = "device"
    medication = "medication"
    substance = "substance"
