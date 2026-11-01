"""add related_person patient reference identifier columns

Revision ID: 2f5454a971d5
Revises: 326ee2e17826
Create Date: 2026-11-01 14:19:19.338845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2f5454a971d5'
down_revision: Union[str, None] = '326ee2e17826'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('related_person', sa.Column('patient_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('related_person', sa.Column('patient_identifier_type_system', sa.String(), nullable=True))
    op.add_column('related_person', sa.Column('patient_identifier_type_version', sa.String(), nullable=True))
    op.add_column('related_person', sa.Column('patient_identifier_type_code', sa.String(), nullable=True))
    op.add_column('related_person', sa.Column('patient_identifier_type_display', sa.String(), nullable=True))
    op.add_column('related_person', sa.Column('patient_identifier_type_text', sa.String(), nullable=True))
    op.add_column('related_person', sa.Column('patient_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('related_person', sa.Column('patient_identifier_system', sa.String(), nullable=True))
    op.add_column('related_person', sa.Column('patient_identifier_value', sa.String(), nullable=True))
    op.add_column('related_person', sa.Column('patient_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('related_person', sa.Column('patient_identifier_period_end', sa.DateTime(timezone=True), nullable=True))
    op.alter_column('related_person', 'patient_reference',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('related_person', 'patient_type',
               existing_type=postgresql.ENUM('Patient', name='related_person_patient_reference_type', create_type=False),
               nullable=True)


def downgrade() -> None:
    op.alter_column('related_person', 'patient_type',
               existing_type=postgresql.ENUM('Patient', name='related_person_patient_reference_type', create_type=False),
               nullable=False)
    op.alter_column('related_person', 'patient_reference',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_column('related_person', 'patient_identifier_period_end')
    op.drop_column('related_person', 'patient_identifier_period_start')
    op.drop_column('related_person', 'patient_identifier_value')
    op.drop_column('related_person', 'patient_identifier_system')
    op.drop_column('related_person', 'patient_identifier_type_user_selected')
    op.drop_column('related_person', 'patient_identifier_type_text')
    op.drop_column('related_person', 'patient_identifier_type_display')
    op.drop_column('related_person', 'patient_identifier_type_code')
    op.drop_column('related_person', 'patient_identifier_type_version')
    op.drop_column('related_person', 'patient_identifier_type_system')
    op.drop_column('related_person', 'patient_identifier_use')
