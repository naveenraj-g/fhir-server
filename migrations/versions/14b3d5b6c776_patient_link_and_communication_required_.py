"""patient link and communication required fields

Revision ID: 14b3d5b6c776
Revises: c0e027c854e1
Create Date: 2026-07-28 09:56:11.005382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '14b3d5b6c776'
down_revision: Union[str, None] = 'c0e027c854e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('patient_communication', 'language_code',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('patient_link', 'other_type',
               existing_type=postgresql.ENUM('Patient', 'RelatedPerson', name='patient_link_other_type'),
               nullable=False)
    op.alter_column('patient_link', 'other_id',
               existing_type=sa.INTEGER(),
               nullable=False)


def downgrade() -> None:
    op.alter_column('patient_link', 'other_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('patient_link', 'other_type',
               existing_type=postgresql.ENUM('Patient', 'RelatedPerson', name='patient_link_other_type'),
               nullable=True)
    op.alter_column('patient_communication', 'language_code',
               existing_type=sa.VARCHAR(),
               nullable=True)
