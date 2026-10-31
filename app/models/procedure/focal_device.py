from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.procedure.enums import ProcedureFocalDeviceManipulatedReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ProcedureFocalDevice(TenantAuditMixin, Base):
    """Procedure.focalDevice (0..* BackboneElement) child table."""

    __tablename__ = "procedure_focal_device"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    action_text = Column(String, nullable=True)

    manipulated_reference = Column(String, nullable=True)
    manipulated_type = Column(
        Enum(
            ProcedureFocalDeviceManipulatedReferenceType,
            name="procedure_focal_device_manipulated_reference_type",
        ),
        nullable=False,
    )
    manipulated_id = Column(BigInteger, nullable=True, index=True)
    manipulated_display = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="focal_devices")
    action_codings = relationship(
        "ProcedureFocalDeviceActionCoding",
        back_populates="focal_device",
        cascade="all, delete-orphan",
    )


class ProcedureFocalDeviceActionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.focalDevice.action.coding (0..* Coding) grandchild table."""

    __tablename__ = "procedure_focal_device_action_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    focal_device_id = Column(
        BigInteger,
        ForeignKey("procedure_focal_device.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    focal_device = relationship("ProcedureFocalDevice", back_populates="action_codings")
