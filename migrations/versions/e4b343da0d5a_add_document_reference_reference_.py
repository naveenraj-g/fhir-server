"""add document_reference reference identifier fallback columns

Revision ID: e4b343da0d5a
Revises: 10642524491b
Create Date: 2026-11-01 19:12:55.370039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e4b343da0d5a'
down_revision: Union[str, None] = '10642524491b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('document_reference', sa.Column('master_identifier_assigner_identifier_type_system', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('master_identifier_assigner_identifier_type_version', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('master_identifier_assigner_identifier_type_code', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('master_identifier_assigner_identifier_type_display', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('master_identifier_assigner_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('document_reference', sa.Column('master_identifier_assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference', sa.Column('master_identifier_assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_type_system', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_type_version', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_type_code', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_type_display', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_type_text', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_system', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_value', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference', sa.Column('subject_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_type_system', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_type_version', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_type_code', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_type_display', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_type_text', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_system', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_value', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference', sa.Column('authenticator_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_type_system', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_type_version', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_type_code', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_type_display', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_type_text', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_system', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_value', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference', sa.Column('custodian_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_type_system', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_type_version', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_type_code', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_type_display', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_type_text', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_system', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_value', sa.String(), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference', sa.Column('context_source_patient_info_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_type_system', sa.String(), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_type_version', sa.String(), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_type_code', sa.String(), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_type_display', sa.String(), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_type_text', sa.String(), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_system', sa.String(), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_value', sa.String(), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference_author', sa.Column('author_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference_context_encounter', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_type_text', sa.String(), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_system', sa.String(), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_value', sa.String(), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference_context_related', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference_identifier', sa.Column('assigner_identifier_type_system', sa.String(), nullable=True))

    op.add_column('document_reference_identifier', sa.Column('assigner_identifier_type_version', sa.String(), nullable=True))

    op.add_column('document_reference_identifier', sa.Column('assigner_identifier_type_code', sa.String(), nullable=True))

    op.add_column('document_reference_identifier', sa.Column('assigner_identifier_type_display', sa.String(), nullable=True))

    op.add_column('document_reference_identifier', sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('document_reference_identifier', sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference_identifier', sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_type_system', sa.String(), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_type_version', sa.String(), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_type_code', sa.String(), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_type_display', sa.String(), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_type_user_selected', sa.Boolean(), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_type_text', sa.String(), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_system', sa.String(), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_value', sa.String(), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_period_start', sa.DateTime(timezone=True), nullable=True))

    op.add_column('document_reference_relates_to', sa.Column('target_identifier_period_end', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('document_reference_relates_to', 'target_identifier_period_end')

    op.drop_column('document_reference_relates_to', 'target_identifier_period_start')

    op.drop_column('document_reference_relates_to', 'target_identifier_value')

    op.drop_column('document_reference_relates_to', 'target_identifier_system')

    op.drop_column('document_reference_relates_to', 'target_identifier_type_text')

    op.drop_column('document_reference_relates_to', 'target_identifier_type_user_selected')

    op.drop_column('document_reference_relates_to', 'target_identifier_type_display')

    op.drop_column('document_reference_relates_to', 'target_identifier_type_code')

    op.drop_column('document_reference_relates_to', 'target_identifier_type_version')

    op.drop_column('document_reference_relates_to', 'target_identifier_type_system')

    op.drop_column('document_reference_relates_to', 'target_identifier_use')

    op.drop_column('document_reference_identifier', 'assigner_identifier_period_end')

    op.drop_column('document_reference_identifier', 'assigner_identifier_period_start')

    op.drop_column('document_reference_identifier', 'assigner_identifier_type_user_selected')

    op.drop_column('document_reference_identifier', 'assigner_identifier_type_display')

    op.drop_column('document_reference_identifier', 'assigner_identifier_type_code')

    op.drop_column('document_reference_identifier', 'assigner_identifier_type_version')

    op.drop_column('document_reference_identifier', 'assigner_identifier_type_system')

    op.drop_column('document_reference_context_related', 'reference_identifier_period_end')

    op.drop_column('document_reference_context_related', 'reference_identifier_period_start')

    op.drop_column('document_reference_context_related', 'reference_identifier_value')

    op.drop_column('document_reference_context_related', 'reference_identifier_system')

    op.drop_column('document_reference_context_related', 'reference_identifier_type_text')

    op.drop_column('document_reference_context_related', 'reference_identifier_type_user_selected')

    op.drop_column('document_reference_context_related', 'reference_identifier_type_display')

    op.drop_column('document_reference_context_related', 'reference_identifier_type_code')

    op.drop_column('document_reference_context_related', 'reference_identifier_type_version')

    op.drop_column('document_reference_context_related', 'reference_identifier_type_system')

    op.drop_column('document_reference_context_related', 'reference_identifier_use')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_period_end')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_period_start')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_value')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_system')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_type_text')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_type_user_selected')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_type_display')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_type_code')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_type_version')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_type_system')

    op.drop_column('document_reference_context_encounter', 'reference_identifier_use')

    op.drop_column('document_reference_author', 'author_identifier_period_end')

    op.drop_column('document_reference_author', 'author_identifier_period_start')

    op.drop_column('document_reference_author', 'author_identifier_value')

    op.drop_column('document_reference_author', 'author_identifier_system')

    op.drop_column('document_reference_author', 'author_identifier_type_text')

    op.drop_column('document_reference_author', 'author_identifier_type_user_selected')

    op.drop_column('document_reference_author', 'author_identifier_type_display')

    op.drop_column('document_reference_author', 'author_identifier_type_code')

    op.drop_column('document_reference_author', 'author_identifier_type_version')

    op.drop_column('document_reference_author', 'author_identifier_type_system')

    op.drop_column('document_reference_author', 'author_identifier_use')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_period_end')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_period_start')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_value')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_system')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_type_text')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_type_user_selected')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_type_display')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_type_code')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_type_version')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_type_system')

    op.drop_column('document_reference', 'context_source_patient_info_identifier_use')

    op.drop_column('document_reference', 'custodian_identifier_period_end')

    op.drop_column('document_reference', 'custodian_identifier_period_start')

    op.drop_column('document_reference', 'custodian_identifier_value')

    op.drop_column('document_reference', 'custodian_identifier_system')

    op.drop_column('document_reference', 'custodian_identifier_type_text')

    op.drop_column('document_reference', 'custodian_identifier_type_user_selected')

    op.drop_column('document_reference', 'custodian_identifier_type_display')

    op.drop_column('document_reference', 'custodian_identifier_type_code')

    op.drop_column('document_reference', 'custodian_identifier_type_version')

    op.drop_column('document_reference', 'custodian_identifier_type_system')

    op.drop_column('document_reference', 'custodian_identifier_use')

    op.drop_column('document_reference', 'authenticator_identifier_period_end')

    op.drop_column('document_reference', 'authenticator_identifier_period_start')

    op.drop_column('document_reference', 'authenticator_identifier_value')

    op.drop_column('document_reference', 'authenticator_identifier_system')

    op.drop_column('document_reference', 'authenticator_identifier_type_text')

    op.drop_column('document_reference', 'authenticator_identifier_type_user_selected')

    op.drop_column('document_reference', 'authenticator_identifier_type_display')

    op.drop_column('document_reference', 'authenticator_identifier_type_code')

    op.drop_column('document_reference', 'authenticator_identifier_type_version')

    op.drop_column('document_reference', 'authenticator_identifier_type_system')

    op.drop_column('document_reference', 'authenticator_identifier_use')

    op.drop_column('document_reference', 'subject_identifier_period_end')

    op.drop_column('document_reference', 'subject_identifier_period_start')

    op.drop_column('document_reference', 'subject_identifier_value')

    op.drop_column('document_reference', 'subject_identifier_system')

    op.drop_column('document_reference', 'subject_identifier_type_text')

    op.drop_column('document_reference', 'subject_identifier_type_user_selected')

    op.drop_column('document_reference', 'subject_identifier_type_display')

    op.drop_column('document_reference', 'subject_identifier_type_code')

    op.drop_column('document_reference', 'subject_identifier_type_version')

    op.drop_column('document_reference', 'subject_identifier_type_system')

    op.drop_column('document_reference', 'subject_identifier_use')

    op.drop_column('document_reference', 'master_identifier_assigner_identifier_period_end')

    op.drop_column('document_reference', 'master_identifier_assigner_identifier_period_start')

    op.drop_column('document_reference', 'master_identifier_assigner_identifier_type_user_selected')

    op.drop_column('document_reference', 'master_identifier_assigner_identifier_type_display')

    op.drop_column('document_reference', 'master_identifier_assigner_identifier_type_code')

    op.drop_column('document_reference', 'master_identifier_assigner_identifier_type_version')

    op.drop_column('document_reference', 'master_identifier_assigner_identifier_type_system')
