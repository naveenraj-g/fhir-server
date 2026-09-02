"""healthcare_service_telecom_not_null

Revision ID: 765485b919b1
Revises: cb20e4c5af59
Create Date: 2026-09-02 17:22:25.686816

Fixes an inconsistency introduced in cb20e4c5af59: HealthcareServiceTelecom's
`system`/`value` were left nullable, unlike every other resource's telecom
table (Patient, Practitioner, Organization, Location, PractitionerRole all
require both). Table is empty in every environment this has been applied to,
so this is a straight NOT NULL tightening with no backfill needed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '765485b919b1'
down_revision: Union[str, None] = 'cb20e4c5af59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'healthcare_service_telecom', 'system',
        existing_type=postgresql.ENUM(
            'phone', 'fax', 'email', 'pager', 'url', 'sms', 'other',
            name='contact_point_system', create_type=False,
        ),
        nullable=False,
    )
    op.alter_column(
        'healthcare_service_telecom', 'value',
        existing_type=sa.VARCHAR(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'healthcare_service_telecom', 'value',
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.alter_column(
        'healthcare_service_telecom', 'system',
        existing_type=postgresql.ENUM(
            'phone', 'fax', 'email', 'pager', 'url', 'sms', 'other',
            name='contact_point_system', create_type=False,
        ),
        nullable=True,
    )
