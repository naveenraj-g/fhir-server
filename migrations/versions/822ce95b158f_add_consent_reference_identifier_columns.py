"""add consent reference identifier columns

Revision ID: 822ce95b158f
Revises: ffd7c94
Create Date: 2026-11-01 15:33:42.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '822ce95b158f'
down_revision: Union[str, None] = '2f5454a971d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # consent
    op.add_column('consent', sa.Column('patient_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('consent', sa.Column('patient_identifier_type_system', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('patient_identifier_type_version', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('patient_identifier_type_code', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('patient_identifier_type_display', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('patient_identifier_type_text', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('patient_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('consent', sa.Column('patient_identifier_system', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('patient_identifier_value', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('patient_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consent', sa.Column('patient_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('consent', sa.Column('source_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('consent', sa.Column('source_reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('source_reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('source_reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('source_reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('source_reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('source_reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('consent', sa.Column('source_reference_identifier_system', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('source_reference_identifier_value', sa.String(), nullable=True))
    op.add_column('consent', sa.Column('source_reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consent', sa.Column('source_reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # consent_identifier
    op.add_column('consent_identifier', sa.Column('assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('consent_identifier', sa.Column('assigner_identifier_type_system', sa.String(), nullable=True))
    op.add_column('consent_identifier', sa.Column('assigner_identifier_type_version', sa.String(), nullable=True))
    op.add_column('consent_identifier', sa.Column('assigner_identifier_type_code', sa.String(), nullable=True))
    op.add_column('consent_identifier', sa.Column('assigner_identifier_type_display', sa.String(), nullable=True))
    op.add_column('consent_identifier', sa.Column('assigner_identifier_type_text', sa.String(), nullable=True))
    op.add_column('consent_identifier', sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('consent_identifier', sa.Column('assigner_identifier_system', sa.String(), nullable=True))
    op.add_column('consent_identifier', sa.Column('assigner_identifier_value', sa.String(), nullable=True))
    op.add_column('consent_identifier', sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consent_identifier', sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # consent_organization
    op.alter_column('consent_organization', 'reference_reference', existing_type=sa.VARCHAR(), nullable=True)
    op.add_column('consent_organization', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('consent_organization', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('consent_organization', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('consent_organization', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('consent_organization', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('consent_organization', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('consent_organization', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('consent_organization', sa.Column('reference_identifier_system', sa.String(), nullable=True))
    op.add_column('consent_organization', sa.Column('reference_identifier_value', sa.String(), nullable=True))
    op.add_column('consent_organization', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consent_organization', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # consent_performer
    op.alter_column('consent_performer', 'reference_reference', existing_type=sa.VARCHAR(), nullable=True)
    op.add_column('consent_performer', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('consent_performer', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('consent_performer', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('consent_performer', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('consent_performer', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('consent_performer', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('consent_performer', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('consent_performer', sa.Column('reference_identifier_system', sa.String(), nullable=True))
    op.add_column('consent_performer', sa.Column('reference_identifier_value', sa.String(), nullable=True))
    op.add_column('consent_performer', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consent_performer', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # consent_provision_actor
    op.alter_column('consent_provision_actor', 'reference_reference', existing_type=sa.VARCHAR(), nullable=True)
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_system', sa.String(), nullable=True))
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_value', sa.String(), nullable=True))
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consent_provision_actor', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # consent_provision_data
    op.alter_column('consent_provision_data', 'reference_reference', existing_type=sa.VARCHAR(), nullable=True)
    op.add_column('consent_provision_data', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('consent_provision_data', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('consent_provision_data', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('consent_provision_data', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('consent_provision_data', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('consent_provision_data', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('consent_provision_data', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('consent_provision_data', sa.Column('reference_identifier_system', sa.String(), nullable=True))
    op.add_column('consent_provision_data', sa.Column('reference_identifier_value', sa.String(), nullable=True))
    op.add_column('consent_provision_data', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consent_provision_data', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # consent_verification
    op.add_column('consent_verification', sa.Column('verified_with_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('consent_verification', sa.Column('verified_with_identifier_type_system', sa.String(), nullable=True))
    op.add_column('consent_verification', sa.Column('verified_with_identifier_type_version', sa.String(), nullable=True))
    op.add_column('consent_verification', sa.Column('verified_with_identifier_type_code', sa.String(), nullable=True))
    op.add_column('consent_verification', sa.Column('verified_with_identifier_type_display', sa.String(), nullable=True))
    op.add_column('consent_verification', sa.Column('verified_with_identifier_type_text', sa.String(), nullable=True))
    op.add_column('consent_verification', sa.Column('verified_with_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('consent_verification', sa.Column('verified_with_identifier_system', sa.String(), nullable=True))
    op.add_column('consent_verification', sa.Column('verified_with_identifier_value', sa.String(), nullable=True))
    op.add_column('consent_verification', sa.Column('verified_with_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('consent_verification', sa.Column('verified_with_identifier_period_end', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # consent_verification
    op.drop_column('consent_verification', 'verified_with_identifier_period_end')
    op.drop_column('consent_verification', 'verified_with_identifier_period_start')
    op.drop_column('consent_verification', 'verified_with_identifier_value')
    op.drop_column('consent_verification', 'verified_with_identifier_system')
    op.drop_column('consent_verification', 'verified_with_identifier_type_user_selected')
    op.drop_column('consent_verification', 'verified_with_identifier_type_text')
    op.drop_column('consent_verification', 'verified_with_identifier_type_display')
    op.drop_column('consent_verification', 'verified_with_identifier_type_code')
    op.drop_column('consent_verification', 'verified_with_identifier_type_version')
    op.drop_column('consent_verification', 'verified_with_identifier_type_system')
    op.drop_column('consent_verification', 'verified_with_identifier_use')

    # consent_provision_data
    op.drop_column('consent_provision_data', 'reference_identifier_period_end')
    op.drop_column('consent_provision_data', 'reference_identifier_period_start')
    op.drop_column('consent_provision_data', 'reference_identifier_value')
    op.drop_column('consent_provision_data', 'reference_identifier_system')
    op.drop_column('consent_provision_data', 'reference_identifier_type_user_selected')
    op.drop_column('consent_provision_data', 'reference_identifier_type_text')
    op.drop_column('consent_provision_data', 'reference_identifier_type_display')
    op.drop_column('consent_provision_data', 'reference_identifier_type_code')
    op.drop_column('consent_provision_data', 'reference_identifier_type_version')
    op.drop_column('consent_provision_data', 'reference_identifier_type_system')
    op.drop_column('consent_provision_data', 'reference_identifier_use')
    op.alter_column('consent_provision_data', 'reference_reference', existing_type=sa.VARCHAR(), nullable=False)

    # consent_provision_actor
    op.drop_column('consent_provision_actor', 'reference_identifier_period_end')
    op.drop_column('consent_provision_actor', 'reference_identifier_period_start')
    op.drop_column('consent_provision_actor', 'reference_identifier_value')
    op.drop_column('consent_provision_actor', 'reference_identifier_system')
    op.drop_column('consent_provision_actor', 'reference_identifier_type_user_selected')
    op.drop_column('consent_provision_actor', 'reference_identifier_type_text')
    op.drop_column('consent_provision_actor', 'reference_identifier_type_display')
    op.drop_column('consent_provision_actor', 'reference_identifier_type_code')
    op.drop_column('consent_provision_actor', 'reference_identifier_type_version')
    op.drop_column('consent_provision_actor', 'reference_identifier_type_system')
    op.drop_column('consent_provision_actor', 'reference_identifier_use')
    op.alter_column('consent_provision_actor', 'reference_reference', existing_type=sa.VARCHAR(), nullable=False)

    # consent_performer
    op.drop_column('consent_performer', 'reference_identifier_period_end')
    op.drop_column('consent_performer', 'reference_identifier_period_start')
    op.drop_column('consent_performer', 'reference_identifier_value')
    op.drop_column('consent_performer', 'reference_identifier_system')
    op.drop_column('consent_performer', 'reference_identifier_type_user_selected')
    op.drop_column('consent_performer', 'reference_identifier_type_text')
    op.drop_column('consent_performer', 'reference_identifier_type_display')
    op.drop_column('consent_performer', 'reference_identifier_type_code')
    op.drop_column('consent_performer', 'reference_identifier_type_version')
    op.drop_column('consent_performer', 'reference_identifier_type_system')
    op.drop_column('consent_performer', 'reference_identifier_use')
    op.alter_column('consent_performer', 'reference_reference', existing_type=sa.VARCHAR(), nullable=False)

    # consent_organization
    op.drop_column('consent_organization', 'reference_identifier_period_end')
    op.drop_column('consent_organization', 'reference_identifier_period_start')
    op.drop_column('consent_organization', 'reference_identifier_value')
    op.drop_column('consent_organization', 'reference_identifier_system')
    op.drop_column('consent_organization', 'reference_identifier_type_user_selected')
    op.drop_column('consent_organization', 'reference_identifier_type_text')
    op.drop_column('consent_organization', 'reference_identifier_type_display')
    op.drop_column('consent_organization', 'reference_identifier_type_code')
    op.drop_column('consent_organization', 'reference_identifier_type_version')
    op.drop_column('consent_organization', 'reference_identifier_type_system')
    op.drop_column('consent_organization', 'reference_identifier_use')
    op.alter_column('consent_organization', 'reference_reference', existing_type=sa.VARCHAR(), nullable=False)

    # consent_identifier
    op.drop_column('consent_identifier', 'assigner_identifier_period_end')
    op.drop_column('consent_identifier', 'assigner_identifier_period_start')
    op.drop_column('consent_identifier', 'assigner_identifier_value')
    op.drop_column('consent_identifier', 'assigner_identifier_system')
    op.drop_column('consent_identifier', 'assigner_identifier_type_user_selected')
    op.drop_column('consent_identifier', 'assigner_identifier_type_text')
    op.drop_column('consent_identifier', 'assigner_identifier_type_display')
    op.drop_column('consent_identifier', 'assigner_identifier_type_code')
    op.drop_column('consent_identifier', 'assigner_identifier_type_version')
    op.drop_column('consent_identifier', 'assigner_identifier_type_system')
    op.drop_column('consent_identifier', 'assigner_identifier_use')

    # consent
    op.drop_column('consent', 'source_reference_identifier_period_end')
    op.drop_column('consent', 'source_reference_identifier_period_start')
    op.drop_column('consent', 'source_reference_identifier_value')
    op.drop_column('consent', 'source_reference_identifier_system')
    op.drop_column('consent', 'source_reference_identifier_type_user_selected')
    op.drop_column('consent', 'source_reference_identifier_type_text')
    op.drop_column('consent', 'source_reference_identifier_type_display')
    op.drop_column('consent', 'source_reference_identifier_type_code')
    op.drop_column('consent', 'source_reference_identifier_type_version')
    op.drop_column('consent', 'source_reference_identifier_type_system')
    op.drop_column('consent', 'source_reference_identifier_use')

    op.drop_column('consent', 'patient_identifier_period_end')
    op.drop_column('consent', 'patient_identifier_period_start')
    op.drop_column('consent', 'patient_identifier_value')
    op.drop_column('consent', 'patient_identifier_system')
    op.drop_column('consent', 'patient_identifier_type_user_selected')
    op.drop_column('consent', 'patient_identifier_type_text')
    op.drop_column('consent', 'patient_identifier_type_display')
    op.drop_column('consent', 'patient_identifier_type_code')
    op.drop_column('consent', 'patient_identifier_type_version')
    op.drop_column('consent', 'patient_identifier_type_system')
    op.drop_column('consent', 'patient_identifier_use')
