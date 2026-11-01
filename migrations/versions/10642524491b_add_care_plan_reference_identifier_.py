"""add care_plan reference identifier fallback columns

Revision ID: 10642524491b
Revises: a7dc00fef55d
Create Date: 2026-11-01 18:52:06.266483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '10642524491b'
down_revision: Union[str, None] = 'a7dc00fef55d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('care_plan', sa.Column('subject_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan', sa.Column('subject_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('subject_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('subject_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('subject_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('subject_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan', sa.Column('subject_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('subject_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('subject_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('subject_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan', sa.Column('subject_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan', sa.Column('encounter_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan', sa.Column('author_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.alter_column('care_plan', 'subject_type',
               existing_type=postgresql.ENUM('Patient', 'Group', name='care_plan_subject_reference_type', create_type=False),
               nullable=True)

    op.add_column('care_plan_activity', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_activity', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_location_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity', sa.Column('detail_product_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity_detail_goal', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity_detail_performer', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity_detail_reason_reference', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity_outcome_reference', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_activity_progress', sa.Column('author_reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_addresses', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_based_on', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_care_team', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_contributor', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_goal', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_identifier', sa.Column('assigner_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_identifier', sa.Column('assigner_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_identifier', sa.Column('assigner_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_identifier', sa.Column('assigner_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_identifier', sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_identifier', sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_identifier', sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_note', sa.Column('author_reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_part_of', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('care_plan_replaces', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('care_plan_replaces', 'reference_identifier_period_end')

    op.drop_column('care_plan_replaces', 'reference_identifier_period_start')

    op.drop_column('care_plan_replaces', 'reference_identifier_value')

    op.drop_column('care_plan_replaces', 'reference_identifier_system')

    op.drop_column('care_plan_replaces', 'reference_identifier_type_text')

    op.drop_column('care_plan_replaces', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_replaces', 'reference_identifier_type_display')

    op.drop_column('care_plan_replaces', 'reference_identifier_type_code')

    op.drop_column('care_plan_replaces', 'reference_identifier_type_version')

    op.drop_column('care_plan_replaces', 'reference_identifier_type_system')

    op.drop_column('care_plan_replaces', 'reference_identifier_use')

    op.drop_column('care_plan_part_of', 'reference_identifier_period_end')

    op.drop_column('care_plan_part_of', 'reference_identifier_period_start')

    op.drop_column('care_plan_part_of', 'reference_identifier_value')

    op.drop_column('care_plan_part_of', 'reference_identifier_system')

    op.drop_column('care_plan_part_of', 'reference_identifier_type_text')

    op.drop_column('care_plan_part_of', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_part_of', 'reference_identifier_type_display')

    op.drop_column('care_plan_part_of', 'reference_identifier_type_code')

    op.drop_column('care_plan_part_of', 'reference_identifier_type_version')

    op.drop_column('care_plan_part_of', 'reference_identifier_type_system')

    op.drop_column('care_plan_part_of', 'reference_identifier_use')

    op.drop_column('care_plan_note', 'author_reference_identifier_period_end')

    op.drop_column('care_plan_note', 'author_reference_identifier_period_start')

    op.drop_column('care_plan_note', 'author_reference_identifier_value')

    op.drop_column('care_plan_note', 'author_reference_identifier_system')

    op.drop_column('care_plan_note', 'author_reference_identifier_type_text')

    op.drop_column('care_plan_note', 'author_reference_identifier_type_user_selected')

    op.drop_column('care_plan_note', 'author_reference_identifier_type_display')

    op.drop_column('care_plan_note', 'author_reference_identifier_type_code')

    op.drop_column('care_plan_note', 'author_reference_identifier_type_version')

    op.drop_column('care_plan_note', 'author_reference_identifier_type_system')

    op.drop_column('care_plan_note', 'author_reference_identifier_use')

    op.drop_column('care_plan_identifier', 'assigner_identifier_period_end')

    op.drop_column('care_plan_identifier', 'assigner_identifier_period_start')

    op.drop_column('care_plan_identifier', 'assigner_identifier_type_user_selected')

    op.drop_column('care_plan_identifier', 'assigner_identifier_type_display')

    op.drop_column('care_plan_identifier', 'assigner_identifier_type_code')

    op.drop_column('care_plan_identifier', 'assigner_identifier_type_version')

    op.drop_column('care_plan_identifier', 'assigner_identifier_type_system')

    op.drop_column('care_plan_goal', 'reference_identifier_period_end')

    op.drop_column('care_plan_goal', 'reference_identifier_period_start')

    op.drop_column('care_plan_goal', 'reference_identifier_value')

    op.drop_column('care_plan_goal', 'reference_identifier_system')

    op.drop_column('care_plan_goal', 'reference_identifier_type_text')

    op.drop_column('care_plan_goal', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_goal', 'reference_identifier_type_display')

    op.drop_column('care_plan_goal', 'reference_identifier_type_code')

    op.drop_column('care_plan_goal', 'reference_identifier_type_version')

    op.drop_column('care_plan_goal', 'reference_identifier_type_system')

    op.drop_column('care_plan_goal', 'reference_identifier_use')

    op.drop_column('care_plan_contributor', 'reference_identifier_period_end')

    op.drop_column('care_plan_contributor', 'reference_identifier_period_start')

    op.drop_column('care_plan_contributor', 'reference_identifier_value')

    op.drop_column('care_plan_contributor', 'reference_identifier_system')

    op.drop_column('care_plan_contributor', 'reference_identifier_type_text')

    op.drop_column('care_plan_contributor', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_contributor', 'reference_identifier_type_display')

    op.drop_column('care_plan_contributor', 'reference_identifier_type_code')

    op.drop_column('care_plan_contributor', 'reference_identifier_type_version')

    op.drop_column('care_plan_contributor', 'reference_identifier_type_system')

    op.drop_column('care_plan_contributor', 'reference_identifier_use')

    op.drop_column('care_plan_care_team', 'reference_identifier_period_end')

    op.drop_column('care_plan_care_team', 'reference_identifier_period_start')

    op.drop_column('care_plan_care_team', 'reference_identifier_value')

    op.drop_column('care_plan_care_team', 'reference_identifier_system')

    op.drop_column('care_plan_care_team', 'reference_identifier_type_text')

    op.drop_column('care_plan_care_team', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_care_team', 'reference_identifier_type_display')

    op.drop_column('care_plan_care_team', 'reference_identifier_type_code')

    op.drop_column('care_plan_care_team', 'reference_identifier_type_version')

    op.drop_column('care_plan_care_team', 'reference_identifier_type_system')

    op.drop_column('care_plan_care_team', 'reference_identifier_use')

    op.drop_column('care_plan_based_on', 'reference_identifier_period_end')

    op.drop_column('care_plan_based_on', 'reference_identifier_period_start')

    op.drop_column('care_plan_based_on', 'reference_identifier_value')

    op.drop_column('care_plan_based_on', 'reference_identifier_system')

    op.drop_column('care_plan_based_on', 'reference_identifier_type_text')

    op.drop_column('care_plan_based_on', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_based_on', 'reference_identifier_type_display')

    op.drop_column('care_plan_based_on', 'reference_identifier_type_code')

    op.drop_column('care_plan_based_on', 'reference_identifier_type_version')

    op.drop_column('care_plan_based_on', 'reference_identifier_type_system')

    op.drop_column('care_plan_based_on', 'reference_identifier_use')

    op.drop_column('care_plan_addresses', 'reference_identifier_period_end')

    op.drop_column('care_plan_addresses', 'reference_identifier_period_start')

    op.drop_column('care_plan_addresses', 'reference_identifier_value')

    op.drop_column('care_plan_addresses', 'reference_identifier_system')

    op.drop_column('care_plan_addresses', 'reference_identifier_type_text')

    op.drop_column('care_plan_addresses', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_addresses', 'reference_identifier_type_display')

    op.drop_column('care_plan_addresses', 'reference_identifier_type_code')

    op.drop_column('care_plan_addresses', 'reference_identifier_type_version')

    op.drop_column('care_plan_addresses', 'reference_identifier_type_system')

    op.drop_column('care_plan_addresses', 'reference_identifier_use')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_period_end')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_period_start')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_value')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_system')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_type_text')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_type_user_selected')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_type_display')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_type_code')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_type_version')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_type_system')

    op.drop_column('care_plan_activity_progress', 'author_reference_identifier_use')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_period_end')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_period_start')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_value')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_system')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_type_text')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_type_display')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_type_code')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_type_version')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_type_system')

    op.drop_column('care_plan_activity_outcome_reference', 'reference_identifier_use')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_period_end')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_period_start')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_value')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_system')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_type_text')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_type_display')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_type_code')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_type_version')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_type_system')

    op.drop_column('care_plan_activity_detail_reason_reference', 'reference_identifier_use')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_period_end')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_period_start')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_value')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_system')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_type_text')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_type_display')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_type_code')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_type_version')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_type_system')

    op.drop_column('care_plan_activity_detail_performer', 'reference_identifier_use')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_period_end')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_period_start')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_value')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_system')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_type_text')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_type_display')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_type_code')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_type_version')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_type_system')

    op.drop_column('care_plan_activity_detail_goal', 'reference_identifier_use')

    op.drop_column('care_plan_activity', 'detail_product_identifier_period_end')

    op.drop_column('care_plan_activity', 'detail_product_identifier_period_start')

    op.drop_column('care_plan_activity', 'detail_product_identifier_value')

    op.drop_column('care_plan_activity', 'detail_product_identifier_system')

    op.drop_column('care_plan_activity', 'detail_product_identifier_type_text')

    op.drop_column('care_plan_activity', 'detail_product_identifier_type_user_selected')

    op.drop_column('care_plan_activity', 'detail_product_identifier_type_display')

    op.drop_column('care_plan_activity', 'detail_product_identifier_type_code')

    op.drop_column('care_plan_activity', 'detail_product_identifier_type_version')

    op.drop_column('care_plan_activity', 'detail_product_identifier_type_system')

    op.drop_column('care_plan_activity', 'detail_product_identifier_use')

    op.drop_column('care_plan_activity', 'detail_location_identifier_period_end')

    op.drop_column('care_plan_activity', 'detail_location_identifier_period_start')

    op.drop_column('care_plan_activity', 'detail_location_identifier_value')

    op.drop_column('care_plan_activity', 'detail_location_identifier_system')

    op.drop_column('care_plan_activity', 'detail_location_identifier_type_text')

    op.drop_column('care_plan_activity', 'detail_location_identifier_type_user_selected')

    op.drop_column('care_plan_activity', 'detail_location_identifier_type_display')

    op.drop_column('care_plan_activity', 'detail_location_identifier_type_code')

    op.drop_column('care_plan_activity', 'detail_location_identifier_type_version')

    op.drop_column('care_plan_activity', 'detail_location_identifier_type_system')

    op.drop_column('care_plan_activity', 'detail_location_identifier_use')

    op.drop_column('care_plan_activity', 'reference_identifier_period_end')

    op.drop_column('care_plan_activity', 'reference_identifier_period_start')

    op.drop_column('care_plan_activity', 'reference_identifier_value')

    op.drop_column('care_plan_activity', 'reference_identifier_system')

    op.drop_column('care_plan_activity', 'reference_identifier_type_text')

    op.drop_column('care_plan_activity', 'reference_identifier_type_user_selected')

    op.drop_column('care_plan_activity', 'reference_identifier_type_display')

    op.drop_column('care_plan_activity', 'reference_identifier_type_code')

    op.drop_column('care_plan_activity', 'reference_identifier_type_version')

    op.drop_column('care_plan_activity', 'reference_identifier_type_system')

    op.drop_column('care_plan_activity', 'reference_identifier_use')

    op.alter_column('care_plan', 'subject_type',
               existing_type=postgresql.ENUM('Patient', 'Group', name='care_plan_subject_reference_type', create_type=False),
               nullable=False)

    op.drop_column('care_plan', 'author_identifier_period_end')

    op.drop_column('care_plan', 'author_identifier_period_start')

    op.drop_column('care_plan', 'author_identifier_value')

    op.drop_column('care_plan', 'author_identifier_system')

    op.drop_column('care_plan', 'author_identifier_type_text')

    op.drop_column('care_plan', 'author_identifier_type_user_selected')

    op.drop_column('care_plan', 'author_identifier_type_display')

    op.drop_column('care_plan', 'author_identifier_type_code')

    op.drop_column('care_plan', 'author_identifier_type_version')

    op.drop_column('care_plan', 'author_identifier_type_system')

    op.drop_column('care_plan', 'author_identifier_use')

    op.drop_column('care_plan', 'encounter_identifier_period_end')

    op.drop_column('care_plan', 'encounter_identifier_period_start')

    op.drop_column('care_plan', 'encounter_identifier_value')

    op.drop_column('care_plan', 'encounter_identifier_system')

    op.drop_column('care_plan', 'encounter_identifier_type_text')

    op.drop_column('care_plan', 'encounter_identifier_type_user_selected')

    op.drop_column('care_plan', 'encounter_identifier_type_display')

    op.drop_column('care_plan', 'encounter_identifier_type_code')

    op.drop_column('care_plan', 'encounter_identifier_type_version')

    op.drop_column('care_plan', 'encounter_identifier_type_system')

    op.drop_column('care_plan', 'encounter_identifier_use')

    op.drop_column('care_plan', 'subject_identifier_period_end')

    op.drop_column('care_plan', 'subject_identifier_period_start')

    op.drop_column('care_plan', 'subject_identifier_value')

    op.drop_column('care_plan', 'subject_identifier_system')

    op.drop_column('care_plan', 'subject_identifier_type_text')

    op.drop_column('care_plan', 'subject_identifier_type_user_selected')

    op.drop_column('care_plan', 'subject_identifier_type_display')

    op.drop_column('care_plan', 'subject_identifier_type_code')

    op.drop_column('care_plan', 'subject_identifier_type_version')

    op.drop_column('care_plan', 'subject_identifier_type_system')

    op.drop_column('care_plan', 'subject_identifier_use')
