"""add_immunization_evaluation_tables

Revision ID: 1dc9a9c35da9
Revises: a95c0593c9e4
Create Date: 2026-11-03 17:38:20.341855

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1dc9a9c35da9'
down_revision: Union[str, None] = 'a95c0593c9e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Types and Sequence
    op.execute("CREATE TYPE immunization_evaluation_authority_reference_type AS ENUM ('ORGANIZATION')")
    op.execute("CREATE TYPE immunization_evaluation_immunization_event_reference_type AS ENUM ('IMMUNIZATION')")
    op.execute("CREATE TYPE immunization_evaluation_patient_reference_type AS ENUM ('PATIENT')")
    op.execute("CREATE TYPE immunization_evaluation_status AS ENUM ('completed', 'entered-in-error')")
    op.execute('CREATE SEQUENCE IF NOT EXISTS immunization_evaluation_pub_seq START 610000 INCREMENT 1')

    # Main table
    op.create_table('immunization_evaluation',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_evaluation_id', sa.BigInteger(), server_default=sa.text("nextval('immunization_evaluation_pub_seq')"), nullable=False),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('status', postgresql.ENUM('completed', 'entered-in-error', name='immunization_evaluation_status', create_type=False), nullable=False),
        sa.Column('patient_reference', sa.String(), nullable=False),
        sa.Column('patient_type', postgresql.ENUM('PATIENT', name='immunization_evaluation_patient_reference_type', create_type=False), nullable=False),
        sa.Column('patient_id', sa.BigInteger(), nullable=True),
        sa.Column('patient_display', sa.String(), nullable=True),
        sa.Column('patient_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('patient_identifier_type_system', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_version', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_code', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_display', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('patient_identifier_type_text', sa.String(), nullable=True),
        sa.Column('patient_identifier_system', sa.String(), nullable=True),
        sa.Column('patient_identifier_value', sa.String(), nullable=True),
        sa.Column('patient_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('patient_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('authority_reference', sa.String(), nullable=True),
        sa.Column('authority_type', postgresql.ENUM('ORGANIZATION', name='immunization_evaluation_authority_reference_type', create_type=False), nullable=True),
        sa.Column('authority_id', sa.BigInteger(), nullable=True),
        sa.Column('authority_display', sa.String(), nullable=True),
        sa.Column('authority_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('authority_identifier_type_system', sa.String(), nullable=True),
        sa.Column('authority_identifier_type_version', sa.String(), nullable=True),
        sa.Column('authority_identifier_type_code', sa.String(), nullable=True),
        sa.Column('authority_identifier_type_display', sa.String(), nullable=True),
        sa.Column('authority_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('authority_identifier_type_text', sa.String(), nullable=True),
        sa.Column('authority_identifier_system', sa.String(), nullable=True),
        sa.Column('authority_identifier_value', sa.String(), nullable=True),
        sa.Column('authority_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('authority_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_disease_text', sa.String(), nullable=True),
        sa.Column('immunization_event_reference', sa.String(), nullable=False),
        sa.Column('immunization_event_type', postgresql.ENUM('IMMUNIZATION', name='immunization_evaluation_immunization_event_reference_type', create_type=False), nullable=False),
        sa.Column('immunization_event_id', sa.BigInteger(), nullable=True),
        sa.Column('immunization_event_display', sa.String(), nullable=True),
        sa.Column('immunization_event_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('immunization_event_identifier_type_system', sa.String(), nullable=True),
        sa.Column('immunization_event_identifier_type_version', sa.String(), nullable=True),
        sa.Column('immunization_event_identifier_type_code', sa.String(), nullable=True),
        sa.Column('immunization_event_identifier_type_display', sa.String(), nullable=True),
        sa.Column('immunization_event_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('immunization_event_identifier_type_text', sa.String(), nullable=True),
        sa.Column('immunization_event_identifier_system', sa.String(), nullable=True),
        sa.Column('immunization_event_identifier_value', sa.String(), nullable=True),
        sa.Column('immunization_event_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('immunization_event_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dose_status_text', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('series', sa.String(), nullable=True),
        sa.Column('dose_number_positive_int', sa.Integer(), nullable=True),
        sa.Column('dose_number_string', sa.String(), nullable=True),
        sa.Column('series_doses_positive_int', sa.Integer(), nullable=True),
        sa.Column('series_doses_string', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('dose_number_positive_int IS NULL OR dose_number_string IS NULL', name='ck_immunization_evaluation_dose_number_choice'),
        sa.CheckConstraint('series_doses_positive_int IS NULL OR series_doses_string IS NULL', name='ck_immunization_evaluation_series_doses_choice'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_evaluation_authority_id'), 'immunization_evaluation', ['authority_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_created_at'), 'immunization_evaluation', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_id'), 'immunization_evaluation', ['id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_immunization_evaluation_id'), 'immunization_evaluation', ['immunization_evaluation_id'], unique=True)
    op.create_index(op.f('ix_immunization_evaluation_immunization_event_id'), 'immunization_evaluation', ['immunization_event_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_patient_id'), 'immunization_evaluation', ['patient_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_tenant_id'), 'immunization_evaluation', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_updated_at'), 'immunization_evaluation', ['updated_at'], unique=False)

    # dose_status_coding
    op.create_table('immunization_evaluation_dose_status_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_evaluation_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_evaluation_pk'], ['immunization_evaluation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_evaluation_dose_status_coding_created_at'), 'immunization_evaluation_dose_status_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_dose_status_coding_immunization_evaluation_pk'), 'immunization_evaluation_dose_status_coding', ['immunization_evaluation_pk'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_dose_status_coding_tenant_id'), 'immunization_evaluation_dose_status_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_dose_status_coding_updated_at'), 'immunization_evaluation_dose_status_coding', ['updated_at'], unique=False)

    # dose_status_reason
    op.create_table('immunization_evaluation_dose_status_reason',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_evaluation_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_evaluation_pk'], ['immunization_evaluation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_evaluation_dose_status_reason_created_at'), 'immunization_evaluation_dose_status_reason', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_dose_status_reason_immunization_evaluation_pk'), 'immunization_evaluation_dose_status_reason', ['immunization_evaluation_pk'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_dose_status_reason_tenant_id'), 'immunization_evaluation_dose_status_reason', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_dose_status_reason_updated_at'), 'immunization_evaluation_dose_status_reason', ['updated_at'], unique=False)

    # dose_status_reason_coding
    op.create_table('immunization_evaluation_dose_status_reason_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('dose_status_reason_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['dose_status_reason_id'], ['immunization_evaluation_dose_status_reason.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_evaluation_dose_status_reason_coding_created_at'), 'immunization_evaluation_dose_status_reason_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_dose_status_reason_coding_dose_status_reason_id'), 'immunization_evaluation_dose_status_reason_coding', ['dose_status_reason_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_dose_status_reason_coding_tenant_id'), 'immunization_evaluation_dose_status_reason_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_dose_status_reason_coding_updated_at'), 'immunization_evaluation_dose_status_reason_coding', ['updated_at'], unique=False)

    # identifier
    op.create_table('immunization_evaluation_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_evaluation_pk', sa.BigInteger(), nullable=False),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_reference', sa.String(), nullable=True),
        sa.Column('assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('assigner_id', sa.BigInteger(), nullable=True),
        sa.Column('assigner_display', sa.String(), nullable=True),
        sa.Column('assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('assigner_identifier_type_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_version', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_code', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_display', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_evaluation_pk'], ['immunization_evaluation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_evaluation_identifier_assigner_id'), 'immunization_evaluation_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_identifier_created_at'), 'immunization_evaluation_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_identifier_immunization_evaluation_pk'), 'immunization_evaluation_identifier', ['immunization_evaluation_pk'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_identifier_tenant_id'), 'immunization_evaluation_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_identifier_updated_at'), 'immunization_evaluation_identifier', ['updated_at'], unique=False)

    # identifier_type_coding
    op.create_table('immunization_evaluation_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('identifier_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['identifier_id'], ['immunization_evaluation_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_evaluation_identifier_type_coding_created_at'), 'immunization_evaluation_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_identifier_type_coding_identifier_id'), 'immunization_evaluation_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_identifier_type_coding_tenant_id'), 'immunization_evaluation_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_identifier_type_coding_updated_at'), 'immunization_evaluation_identifier_type_coding', ['updated_at'], unique=False)

    # target_disease_coding
    op.create_table('immunization_evaluation_target_disease_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_evaluation_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_evaluation_pk'], ['immunization_evaluation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_evaluation_target_disease_coding_created_at'), 'immunization_evaluation_target_disease_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_target_disease_coding_immunization_evaluation_pk'), 'immunization_evaluation_target_disease_coding', ['immunization_evaluation_pk'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_target_disease_coding_tenant_id'), 'immunization_evaluation_target_disease_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_evaluation_target_disease_coding_updated_at'), 'immunization_evaluation_target_disease_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse FK order
    op.drop_index(op.f('ix_immunization_evaluation_identifier_type_coding_updated_at'), table_name='immunization_evaluation_identifier_type_coding')
    op.drop_index(op.f('ix_immunization_evaluation_identifier_type_coding_tenant_id'), table_name='immunization_evaluation_identifier_type_coding')
    op.drop_index(op.f('ix_immunization_evaluation_identifier_type_coding_identifier_id'), table_name='immunization_evaluation_identifier_type_coding')
    op.drop_index(op.f('ix_immunization_evaluation_identifier_type_coding_created_at'), table_name='immunization_evaluation_identifier_type_coding')
    op.drop_table('immunization_evaluation_identifier_type_coding')

    op.drop_index(op.f('ix_immunization_evaluation_identifier_updated_at'), table_name='immunization_evaluation_identifier')
    op.drop_index(op.f('ix_immunization_evaluation_identifier_tenant_id'), table_name='immunization_evaluation_identifier')
    op.drop_index(op.f('ix_immunization_evaluation_identifier_immunization_evaluation_pk'), table_name='immunization_evaluation_identifier')
    op.drop_index(op.f('ix_immunization_evaluation_identifier_created_at'), table_name='immunization_evaluation_identifier')
    op.drop_index(op.f('ix_immunization_evaluation_identifier_assigner_id'), table_name='immunization_evaluation_identifier')
    op.drop_table('immunization_evaluation_identifier')

    op.drop_index(op.f('ix_immunization_evaluation_target_disease_coding_updated_at'), table_name='immunization_evaluation_target_disease_coding')
    op.drop_index(op.f('ix_immunization_evaluation_target_disease_coding_tenant_id'), table_name='immunization_evaluation_target_disease_coding')
    op.drop_index(op.f('ix_immunization_evaluation_target_disease_coding_immunization_evaluation_pk'), table_name='immunization_evaluation_target_disease_coding')
    op.drop_index(op.f('ix_immunization_evaluation_target_disease_coding_created_at'), table_name='immunization_evaluation_target_disease_coding')
    op.drop_table('immunization_evaluation_target_disease_coding')

    op.drop_index(op.f('ix_immunization_evaluation_dose_status_reason_coding_updated_at'), table_name='immunization_evaluation_dose_status_reason_coding')
    op.drop_index(op.f('ix_immunization_evaluation_dose_status_reason_coding_tenant_id'), table_name='immunization_evaluation_dose_status_reason_coding')
    op.drop_index(op.f('ix_immunization_evaluation_dose_status_reason_coding_dose_status_reason_id'), table_name='immunization_evaluation_dose_status_reason_coding')
    op.drop_index(op.f('ix_immunization_evaluation_dose_status_reason_coding_created_at'), table_name='immunization_evaluation_dose_status_reason_coding')
    op.drop_table('immunization_evaluation_dose_status_reason_coding')

    op.drop_index(op.f('ix_immunization_evaluation_dose_status_reason_updated_at'), table_name='immunization_evaluation_dose_status_reason')
    op.drop_index(op.f('ix_immunization_evaluation_dose_status_reason_tenant_id'), table_name='immunization_evaluation_dose_status_reason')
    op.drop_index(op.f('ix_immunization_evaluation_dose_status_reason_immunization_evaluation_pk'), table_name='immunization_evaluation_dose_status_reason')
    op.drop_index(op.f('ix_immunization_evaluation_dose_status_reason_created_at'), table_name='immunization_evaluation_dose_status_reason')
    op.drop_table('immunization_evaluation_dose_status_reason')

    op.drop_index(op.f('ix_immunization_evaluation_dose_status_coding_updated_at'), table_name='immunization_evaluation_dose_status_coding')
    op.drop_index(op.f('ix_immunization_evaluation_dose_status_coding_tenant_id'), table_name='immunization_evaluation_dose_status_coding')
    op.drop_index(op.f('ix_immunization_evaluation_dose_status_coding_immunization_evaluation_pk'), table_name='immunization_evaluation_dose_status_coding')
    op.drop_index(op.f('ix_immunization_evaluation_dose_status_coding_created_at'), table_name='immunization_evaluation_dose_status_coding')
    op.drop_table('immunization_evaluation_dose_status_coding')

    op.drop_index(op.f('ix_immunization_evaluation_updated_at'), table_name='immunization_evaluation')
    op.drop_index(op.f('ix_immunization_evaluation_tenant_id'), table_name='immunization_evaluation')
    op.drop_index(op.f('ix_immunization_evaluation_patient_id'), table_name='immunization_evaluation')
    op.drop_index(op.f('ix_immunization_evaluation_immunization_event_id'), table_name='immunization_evaluation')
    op.drop_index(op.f('ix_immunization_evaluation_immunization_evaluation_id'), table_name='immunization_evaluation')
    op.drop_index(op.f('ix_immunization_evaluation_id'), table_name='immunization_evaluation')
    op.drop_index(op.f('ix_immunization_evaluation_created_at'), table_name='immunization_evaluation')
    op.drop_index(op.f('ix_immunization_evaluation_authority_id'), table_name='immunization_evaluation')
    op.drop_table('immunization_evaluation')

    # Drop sequence
    op.execute('DROP SEQUENCE IF EXISTS immunization_evaluation_pub_seq')

    # Drop types
    op.execute('DROP TYPE IF EXISTS immunization_evaluation_authority_reference_type')
    op.execute('DROP TYPE IF EXISTS immunization_evaluation_immunization_event_reference_type')
    op.execute('DROP TYPE IF EXISTS immunization_evaluation_patient_reference_type')
    op.execute('DROP TYPE IF EXISTS immunization_evaluation_status')
