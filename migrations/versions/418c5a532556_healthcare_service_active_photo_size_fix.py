"""healthcare_service_active_photo_size_fix

Revision ID: 418c5a532556
Revises: 765485b919b1
Create Date: 2026-09-02 18:05:00.000000

Fixes two more inconsistencies from cb20e4c5af59, found by comparing against
Patient/Practitioner/Organization/PractitionerRole:
- `active` was left nullable; every other resource with an `active` column
  is `nullable=False, default=False`.
- `photo_size` was BigInteger; FHIR R4's Attachment.size is `unsignedInt`
  (32-bit), and Patient/Practitioner's photo.size columns are Integer.
Table is empty in every environment this has been applied to, so both are
straight tightenings with no backfill needed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '418c5a532556'
down_revision: Union[str, None] = '765485b919b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'healthcare_service', 'active',
        existing_type=sa.BOOLEAN(),
        nullable=False,
    )
    op.alter_column(
        'healthcare_service', 'photo_size',
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'healthcare_service', 'photo_size',
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )
    op.alter_column(
        'healthcare_service', 'active',
        existing_type=sa.BOOLEAN(),
        nullable=True,
    )
