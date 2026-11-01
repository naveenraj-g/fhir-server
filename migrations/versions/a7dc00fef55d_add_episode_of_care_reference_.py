"""add episode_of_care reference identifier fallback columns

Revision ID: a7dc00fef55d
Revises: 26c08b471f6d
Create Date: 2026-11-01 18:30:21.077938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a7dc00fef55d'
down_revision: Union[str, None] = '26c08b471f6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── episode_of_care core table ──
    op.alter_column('episode_of_care', 'patient_reference',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.add_column('episode_of_care', sa.Column('patient_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('episode_of_care', sa.Column('patient_identifier_type_system', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('patient_identifier_type_version', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('patient_identifier_type_code', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('patient_identifier_type_display', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('patient_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('episode_of_care', sa.Column('patient_identifier_type_text', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('patient_identifier_system', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('patient_identifier_value', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('patient_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episode_of_care', sa.Column('patient_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_type_system', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_type_version', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_type_code', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_type_display', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_type_text', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_system', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_value', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episode_of_care', sa.Column('managing_organization_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('episode_of_care', sa.Column('care_manager_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('episode_of_care', sa.Column('care_manager_identifier_type_system', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('care_manager_identifier_type_version', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('care_manager_identifier_type_code', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('care_manager_identifier_type_display', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('care_manager_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('episode_of_care', sa.Column('care_manager_identifier_type_text', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('care_manager_identifier_system', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('care_manager_identifier_value', sa.String(), nullable=True))
    op.add_column('episode_of_care', sa.Column('care_manager_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episode_of_care', sa.Column('care_manager_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # ── episode_of_care_identifier table ──
    op.add_column('episode_of_care_identifier', sa.Column('assigner_identifier_type_system', sa.String(), nullable=True))
    op.add_column('episode_of_care_identifier', sa.Column('assigner_identifier_type_version', sa.String(), nullable=True))
    op.add_column('episode_of_care_identifier', sa.Column('assigner_identifier_type_code', sa.String(), nullable=True))
    op.add_column('episode_of_care_identifier', sa.Column('assigner_identifier_type_display', sa.String(), nullable=True))
    op.add_column('episode_of_care_identifier', sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('episode_of_care_identifier', sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episode_of_care_identifier', sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # ── episode_of_care_diagnosis table ──
    op.alter_column('episode_of_care_diagnosis', 'condition_reference',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_type_system', sa.String(), nullable=True))
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_type_version', sa.String(), nullable=True))
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_type_code', sa.String(), nullable=True))
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_type_display', sa.String(), nullable=True))
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_type_text', sa.String(), nullable=True))
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_system', sa.String(), nullable=True))
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_value', sa.String(), nullable=True))
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episode_of_care_diagnosis', sa.Column('condition_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # ── episode_of_care_referral_request table ──
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_system', sa.String(), nullable=True))
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_value', sa.String(), nullable=True))
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episode_of_care_referral_request', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # ── episode_of_care_team table ──
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_system', sa.String(), nullable=True))
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_value', sa.String(), nullable=True))
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episode_of_care_team', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # ── episode_of_care_account table ──
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_system', sa.String(), nullable=True))
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_value', sa.String(), nullable=True))
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episode_of_care_account', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # ── episode_of_care_account table ──
    op.drop_column('episode_of_care_account', 'reference_identifier_period_end')
    op.drop_column('episode_of_care_account', 'reference_identifier_period_start')
    op.drop_column('episode_of_care_account', 'reference_identifier_value')
    op.drop_column('episode_of_care_account', 'reference_identifier_system')
    op.drop_column('episode_of_care_account', 'reference_identifier_type_text')
    op.drop_column('episode_of_care_account', 'reference_identifier_type_user_selected')
    op.drop_column('episode_of_care_account', 'reference_identifier_type_display')
    op.drop_column('episode_of_care_account', 'reference_identifier_type_code')
    op.drop_column('episode_of_care_account', 'reference_identifier_type_version')
    op.drop_column('episode_of_care_account', 'reference_identifier_type_system')
    op.drop_column('episode_of_care_account', 'reference_identifier_use')

    # ── episode_of_care_team table ──
    op.drop_column('episode_of_care_team', 'reference_identifier_period_end')
    op.drop_column('episode_of_care_team', 'reference_identifier_period_start')
    op.drop_column('episode_of_care_team', 'reference_identifier_value')
    op.drop_column('episode_of_care_team', 'reference_identifier_system')
    op.drop_column('episode_of_care_team', 'reference_identifier_type_text')
    op.drop_column('episode_of_care_team', 'reference_identifier_type_user_selected')
    op.drop_column('episode_of_care_team', 'reference_identifier_type_display')
    op.drop_column('episode_of_care_team', 'reference_identifier_type_code')
    op.drop_column('episode_of_care_team', 'reference_identifier_type_version')
    op.drop_column('episode_of_care_team', 'reference_identifier_type_system')
    op.drop_column('episode_of_care_team', 'reference_identifier_use')

    # ── episode_of_care_referral_request table ──
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_period_end')
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_period_start')
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_value')
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_system')
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_type_text')
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_type_user_selected')
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_type_display')
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_type_code')
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_type_version')
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_type_system')
    op.drop_column('episode_of_care_referral_request', 'reference_identifier_use')

    # ── episode_of_care_diagnosis table ──
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_period_end')
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_period_start')
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_value')
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_system')
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_type_text')
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_type_user_selected')
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_type_display')
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_type_code')
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_type_version')
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_type_system')
    op.drop_column('episode_of_care_diagnosis', 'condition_identifier_use')
    op.alter_column('episode_of_care_diagnosis', 'condition_reference',
               existing_type=sa.VARCHAR(),
               nullable=False)

    # ── episode_of_care_identifier table ──
    op.drop_column('episode_of_care_identifier', 'assigner_identifier_period_end')
    op.drop_column('episode_of_care_identifier', 'assigner_identifier_period_start')
    op.drop_column('episode_of_care_identifier', 'assigner_identifier_type_user_selected')
    op.drop_column('episode_of_care_identifier', 'assigner_identifier_type_display')
    op.drop_column('episode_of_care_identifier', 'assigner_identifier_type_code')
    op.drop_column('episode_of_care_identifier', 'assigner_identifier_type_version')
    op.drop_column('episode_of_care_identifier', 'assigner_identifier_type_system')

    # ── episode_of_care core table ──
    op.drop_column('episode_of_care', 'care_manager_identifier_period_end')
    op.drop_column('episode_of_care', 'care_manager_identifier_period_start')
    op.drop_column('episode_of_care', 'care_manager_identifier_value')
    op.drop_column('episode_of_care', 'care_manager_identifier_system')
    op.drop_column('episode_of_care', 'care_manager_identifier_type_text')
    op.drop_column('episode_of_care', 'care_manager_identifier_type_user_selected')
    op.drop_column('episode_of_care', 'care_manager_identifier_type_display')
    op.drop_column('episode_of_care', 'care_manager_identifier_type_code')
    op.drop_column('episode_of_care', 'care_manager_identifier_type_version')
    op.drop_column('episode_of_care', 'care_manager_identifier_type_system')
    op.drop_column('episode_of_care', 'care_manager_identifier_use')

    op.drop_column('episode_of_care', 'managing_organization_identifier_period_end')
    op.drop_column('episode_of_care', 'managing_organization_identifier_period_start')
    op.drop_column('episode_of_care', 'managing_organization_identifier_value')
    op.drop_column('episode_of_care', 'managing_organization_identifier_system')
    op.drop_column('episode_of_care', 'managing_organization_identifier_type_text')
    op.drop_column('episode_of_care', 'managing_organization_identifier_type_user_selected')
    op.drop_column('episode_of_care', 'managing_organization_identifier_type_display')
    op.drop_column('episode_of_care', 'managing_organization_identifier_type_code')
    op.drop_column('episode_of_care', 'managing_organization_identifier_type_version')
    op.drop_column('episode_of_care', 'managing_organization_identifier_type_system')
    op.drop_column('episode_of_care', 'managing_organization_identifier_use')

    op.drop_column('episode_of_care', 'patient_identifier_period_end')
    op.drop_column('episode_of_care', 'patient_identifier_period_start')
    op.drop_column('episode_of_care', 'patient_identifier_value')
    op.drop_column('episode_of_care', 'patient_identifier_system')
    op.drop_column('episode_of_care', 'patient_identifier_type_text')
    op.drop_column('episode_of_care', 'patient_identifier_type_user_selected')
    op.drop_column('episode_of_care', 'patient_identifier_type_display')
    op.drop_column('episode_of_care', 'patient_identifier_type_code')
    op.drop_column('episode_of_care', 'patient_identifier_type_version')
    op.drop_column('episode_of_care', 'patient_identifier_type_system')
    op.drop_column('episode_of_care', 'patient_identifier_use')
    op.alter_column('episode_of_care', 'patient_reference',
               existing_type=sa.VARCHAR(),
               nullable=False)
