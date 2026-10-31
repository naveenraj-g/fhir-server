from enum import Enum


class GroupType(str, Enum):
    """Types of resources that are members of group."""

    person = "person"
    animal = "animal"
    practitioner = "practitioner"
    device = "device"
    medication = "medication"
    substance = "substance"


class GroupManagingEntityReferenceType(str, Enum):
    """Allowed target types for Group.managingEntity."""

    Organization = "Organization"
    RelatedPerson = "RelatedPerson"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class GroupMemberEntityReferenceType(str, Enum):
    """Allowed target types for Group.member.entity."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Device = "Device"
    Medication = "Medication"
    Substance = "Substance"
    Group = "Group"
