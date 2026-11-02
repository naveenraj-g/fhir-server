"""add_risk_assessment_tables

Revision ID: b027dab8fb83
Revises: 06977c394bf1
Create Date: 2026-11-02 21:57:33.611931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b027dab8fb83'
down_revision: Union[str, None] = '06977c394bf1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_assessment_status AS ENUM (
                'registered', 'preliminary', 'final', 'amended', 'corrected', 'cancelled', 'entered-in-error', 'unknown'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_assessment_condition_reference_type AS ENUM ('Condition');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_assessment_performer_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Device'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_assessment_reason_reference_type AS ENUM (
                'Condition', 'Observation', 'DiagnosticReport', 'DocumentReference'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_assessment_note_author_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS risk_assessment_pub_seq START WITH 520000 INCREMENT BY 1")

    # 3. Tables
    op.create_table('risk_assessment',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_id', sa.BigInteger(), server_default=sa.text("nextval('risk_assessment_pub_seq')"), nullable=False),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('status', postgresql.ENUM('registered', 'preliminary', 'final', 'amended', 'corrected', 'cancelled', 'entered-in-error', 'unknown', name='risk_assessment_status', create_type=False), nullable=False),
    sa.Column('method_text', sa.String(), nullable=True),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('subject_reference', sa.String(), nullable=True),
    sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='subject_reference_type', create_type=False), nullable=True),
    sa.Column('subject_id', sa.BigInteger(), nullable=True),
    sa.Column('subject_display', sa.String(), nullable=True),
    sa.Column('subject_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('subject_identifier_type_system', sa.String(), nullable=True),
    sa.Column('subject_identifier_type_version', sa.String(), nullable=True),
    sa.Column('subject_identifier_type_code', sa.String(), nullable=True),
    sa.Column('subject_identifier_type_display', sa.String(), nullable=True),
    sa.Column('subject_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('subject_identifier_type_text', sa.String(), nullable=True),
    sa.Column('subject_identifier_system', sa.String(), nullable=True),
    sa.Column('subject_identifier_value', sa.String(), nullable=True),
    sa.Column('subject_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('subject_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('based_on_reference', sa.String(), nullable=True),
    sa.Column('based_on_type', sa.String(), nullable=True),
    sa.Column('based_on_id', sa.BigInteger(), nullable=True),
    sa.Column('based_on_display', sa.String(), nullable=True),
    sa.Column('based_on_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('based_on_identifier_type_system', sa.String(), nullable=True),
    sa.Column('based_on_identifier_type_version', sa.String(), nullable=True),
    sa.Column('based_on_identifier_type_code', sa.String(), nullable=True),
    sa.Column('based_on_identifier_type_display', sa.String(), nullable=True),
    sa.Column('based_on_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('based_on_identifier_type_text', sa.String(), nullable=True),
    sa.Column('based_on_identifier_system', sa.String(), nullable=True),
    sa.Column('based_on_identifier_value', sa.String(), nullable=True),
    sa.Column('based_on_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('based_on_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('parent_reference', sa.String(), nullable=True),
    sa.Column('parent_type', sa.String(), nullable=True),
    sa.Column('parent_id', sa.BigInteger(), nullable=True),
    sa.Column('parent_display', sa.String(), nullable=True),
    sa.Column('parent_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('parent_identifier_type_system', sa.String(), nullable=True),
    sa.Column('parent_identifier_type_version', sa.String(), nullable=True),
    sa.Column('parent_identifier_type_code', sa.String(), nullable=True),
    sa.Column('parent_identifier_type_display', sa.String(), nullable=True),
    sa.Column('parent_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('parent_identifier_type_text', sa.String(), nullable=True),
    sa.Column('parent_identifier_system', sa.String(), nullable=True),
    sa.Column('parent_identifier_value', sa.String(), nullable=True),
    sa.Column('parent_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('parent_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('encounter_reference', sa.String(), nullable=True),
    sa.Column('encounter_type', postgresql.ENUM('Encounter', name='encounter_reference_type', create_type=False), nullable=True),
    sa.Column('encounter_id', sa.BigInteger(), nullable=True),
    sa.Column('encounter_display', sa.String(), nullable=True),
    sa.Column('encounter_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('encounter_identifier_type_system', sa.String(), nullable=True),
    sa.Column('encounter_identifier_type_version', sa.String(), nullable=True),
    sa.Column('encounter_identifier_type_code', sa.String(), nullable=True),
    sa.Column('encounter_identifier_type_display', sa.String(), nullable=True),
    sa.Column('encounter_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('encounter_identifier_type_text', sa.String(), nullable=True),
    sa.Column('encounter_identifier_system', sa.String(), nullable=True),
    sa.Column('encounter_identifier_value', sa.String(), nullable=True),
    sa.Column('encounter_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('encounter_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('occurrence_date_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('occurrence_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('occurrence_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('condition_reference', sa.String(), nullable=True),
    sa.Column('condition_type', postgresql.ENUM('Condition', name='risk_assessment_condition_reference_type', create_type=False), nullable=True),
    sa.Column('condition_id', sa.BigInteger(), nullable=True),
    sa.Column('condition_display', sa.String(), nullable=True),
    sa.Column('condition_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('condition_identifier_type_system', sa.String(), nullable=True),
    sa.Column('condition_identifier_type_version', sa.String(), nullable=True),
    sa.Column('condition_identifier_type_code', sa.String(), nullable=True),
    sa.Column('condition_identifier_type_display', sa.String(), nullable=True),
    sa.Column('condition_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('condition_identifier_type_text', sa.String(), nullable=True),
    sa.Column('condition_identifier_system', sa.String(), nullable=True),
    sa.Column('condition_identifier_value', sa.String(), nullable=True),
    sa.Column('condition_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('condition_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('performer_reference', sa.String(), nullable=True),
    sa.Column('performer_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Device', name='risk_assessment_performer_reference_type', create_type=False), nullable=True),
    sa.Column('performer_id', sa.BigInteger(), nullable=True),
    sa.Column('performer_display', sa.String(), nullable=True),
    sa.Column('performer_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('performer_identifier_type_system', sa.String(), nullable=True),
    sa.Column('performer_identifier_type_version', sa.String(), nullable=True),
    sa.Column('performer_identifier_type_code', sa.String(), nullable=True),
    sa.Column('performer_identifier_type_display', sa.String(), nullable=True),
    sa.Column('performer_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('performer_identifier_type_text', sa.String(), nullable=True),
    sa.Column('performer_identifier_system', sa.String(), nullable=True),
    sa.Column('performer_identifier_value', sa.String(), nullable=True),
    sa.Column('performer_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('performer_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('mitigation', sa.Text(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_based_on_id'), 'risk_assessment', ['based_on_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_condition_id'), 'risk_assessment', ['condition_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_created_at'), 'risk_assessment', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_encounter_id'), 'risk_assessment', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_parent_id'), 'risk_assessment', ['parent_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_performer_id'), 'risk_assessment', ['performer_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_risk_assessment_id'), 'risk_assessment', ['risk_assessment_id'], unique=True)
    op.create_index(op.f('ix_risk_assessment_subject_id'), 'risk_assessment', ['subject_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_tenant_id'), 'risk_assessment', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_updated_at'), 'risk_assessment', ['updated_at'], unique=False)
    op.create_table('risk_assessment_basis',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', sa.String(), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reference_identifier_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_value', sa.String(), nullable=True),
    sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['risk_assessment_pk'], ['risk_assessment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_basis_created_at'), 'risk_assessment_basis', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_basis_reference_id'), 'risk_assessment_basis', ['reference_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_basis_risk_assessment_pk'), 'risk_assessment_basis', ['risk_assessment_pk'], unique=False)
    op.create_index(op.f('ix_risk_assessment_basis_tenant_id'), 'risk_assessment_basis', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_basis_updated_at'), 'risk_assessment_basis', ['updated_at'], unique=False)
    op.create_table('risk_assessment_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['risk_assessment_pk'], ['risk_assessment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_code_coding_created_at'), 'risk_assessment_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_code_coding_risk_assessment_pk'), 'risk_assessment_code_coding', ['risk_assessment_pk'], unique=False)
    op.create_index(op.f('ix_risk_assessment_code_coding_tenant_id'), 'risk_assessment_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_code_coding_updated_at'), 'risk_assessment_code_coding', ['updated_at'], unique=False)
    op.create_table('risk_assessment_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['risk_assessment_pk'], ['risk_assessment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_identifier_assigner_id'), 'risk_assessment_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_identifier_created_at'), 'risk_assessment_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_identifier_risk_assessment_pk'), 'risk_assessment_identifier', ['risk_assessment_pk'], unique=False)
    op.create_index(op.f('ix_risk_assessment_identifier_tenant_id'), 'risk_assessment_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_identifier_updated_at'), 'risk_assessment_identifier', ['updated_at'], unique=False)
    op.create_table('risk_assessment_method_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['risk_assessment_pk'], ['risk_assessment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_method_coding_created_at'), 'risk_assessment_method_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_method_coding_risk_assessment_pk'), 'risk_assessment_method_coding', ['risk_assessment_pk'], unique=False)
    op.create_index(op.f('ix_risk_assessment_method_coding_tenant_id'), 'risk_assessment_method_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_method_coding_updated_at'), 'risk_assessment_method_coding', ['updated_at'], unique=False)
    op.create_table('risk_assessment_note',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_pk', sa.BigInteger(), nullable=False),
    sa.Column('author_string', sa.String(), nullable=True),
    sa.Column('author_reference', sa.String(), nullable=True),
    sa.Column('author_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', name='risk_assessment_note_author_reference_type', create_type=False), nullable=True),
    sa.Column('author_id', sa.BigInteger(), nullable=True),
    sa.Column('author_display', sa.String(), nullable=True),
    sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('author_identifier_type_system', sa.String(), nullable=True),
    sa.Column('author_identifier_type_version', sa.String(), nullable=True),
    sa.Column('author_identifier_type_code', sa.String(), nullable=True),
    sa.Column('author_identifier_type_display', sa.String(), nullable=True),
    sa.Column('author_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('author_identifier_type_text', sa.String(), nullable=True),
    sa.Column('author_identifier_system', sa.String(), nullable=True),
    sa.Column('author_identifier_value', sa.String(), nullable=True),
    sa.Column('author_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('author_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['risk_assessment_pk'], ['risk_assessment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_note_author_id'), 'risk_assessment_note', ['author_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_note_created_at'), 'risk_assessment_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_note_risk_assessment_pk'), 'risk_assessment_note', ['risk_assessment_pk'], unique=False)
    op.create_index(op.f('ix_risk_assessment_note_tenant_id'), 'risk_assessment_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_note_updated_at'), 'risk_assessment_note', ['updated_at'], unique=False)
    op.create_table('risk_assessment_prediction',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_pk', sa.BigInteger(), nullable=False),
    sa.Column('outcome_text', sa.String(), nullable=True),
    sa.Column('probability_decimal', sa.Numeric(), nullable=True),
    sa.Column('probability_range_low_value', sa.Numeric(), nullable=True),
    sa.Column('probability_range_low_unit', sa.String(), nullable=True),
    sa.Column('probability_range_low_system', sa.String(), nullable=True),
    sa.Column('probability_range_low_code', sa.String(), nullable=True),
    sa.Column('probability_range_high_value', sa.Numeric(), nullable=True),
    sa.Column('probability_range_high_unit', sa.String(), nullable=True),
    sa.Column('probability_range_high_system', sa.String(), nullable=True),
    sa.Column('probability_range_high_code', sa.String(), nullable=True),
    sa.Column('qualitative_risk_text', sa.String(), nullable=True),
    sa.Column('relative_risk', sa.Numeric(), nullable=True),
    sa.Column('when_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('when_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('when_range_low_value', sa.Numeric(), nullable=True),
    sa.Column('when_range_low_unit', sa.String(), nullable=True),
    sa.Column('when_range_low_system', sa.String(), nullable=True),
    sa.Column('when_range_low_code', sa.String(), nullable=True),
    sa.Column('when_range_high_value', sa.Numeric(), nullable=True),
    sa.Column('when_range_high_unit', sa.String(), nullable=True),
    sa.Column('when_range_high_system', sa.String(), nullable=True),
    sa.Column('when_range_high_code', sa.String(), nullable=True),
    sa.Column('rationale', sa.Text(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['risk_assessment_pk'], ['risk_assessment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_prediction_created_at'), 'risk_assessment_prediction', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_prediction_risk_assessment_pk'), 'risk_assessment_prediction', ['risk_assessment_pk'], unique=False)
    op.create_index(op.f('ix_risk_assessment_prediction_tenant_id'), 'risk_assessment_prediction', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_prediction_updated_at'), 'risk_assessment_prediction', ['updated_at'], unique=False)
    op.create_table('risk_assessment_reason_code',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['risk_assessment_pk'], ['risk_assessment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_reason_code_created_at'), 'risk_assessment_reason_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_reason_code_risk_assessment_pk'), 'risk_assessment_reason_code', ['risk_assessment_pk'], unique=False)
    op.create_index(op.f('ix_risk_assessment_reason_code_tenant_id'), 'risk_assessment_reason_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_reason_code_updated_at'), 'risk_assessment_reason_code', ['updated_at'], unique=False)
    op.create_table('risk_assessment_reason_reference',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', 'DocumentReference', name='risk_assessment_reason_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reference_identifier_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_value', sa.String(), nullable=True),
    sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['risk_assessment_pk'], ['risk_assessment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_reason_reference_created_at'), 'risk_assessment_reason_reference', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_reason_reference_reference_id'), 'risk_assessment_reason_reference', ['reference_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_reason_reference_risk_assessment_pk'), 'risk_assessment_reason_reference', ['risk_assessment_pk'], unique=False)
    op.create_index(op.f('ix_risk_assessment_reason_reference_tenant_id'), 'risk_assessment_reason_reference', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_reason_reference_updated_at'), 'risk_assessment_reason_reference', ['updated_at'], unique=False)
    op.create_table('risk_assessment_identifier_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['risk_assessment_identifier_id'], ['risk_assessment_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_identifier_coding_created_at'), 'risk_assessment_identifier_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_identifier_coding_risk_assessment_identifier_id'), 'risk_assessment_identifier_coding', ['risk_assessment_identifier_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_identifier_coding_tenant_id'), 'risk_assessment_identifier_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_identifier_coding_updated_at'), 'risk_assessment_identifier_coding', ['updated_at'], unique=False)
    op.create_table('risk_assessment_pred_outcome_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_prediction_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['risk_assessment_prediction_id'], ['risk_assessment_prediction.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_pred_outcome_coding_created_at'), 'risk_assessment_pred_outcome_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_pred_outcome_coding_risk_assessment_prediction_id'), 'risk_assessment_pred_outcome_coding', ['risk_assessment_prediction_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_pred_outcome_coding_tenant_id'), 'risk_assessment_pred_outcome_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_pred_outcome_coding_updated_at'), 'risk_assessment_pred_outcome_coding', ['updated_at'], unique=False)
    op.create_table('risk_assessment_pred_qual_risk_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_prediction_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['risk_assessment_prediction_id'], ['risk_assessment_prediction.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_pred_qual_risk_coding_created_at'), 'risk_assessment_pred_qual_risk_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_pred_qual_risk_coding_risk_assessment_prediction_id'), 'risk_assessment_pred_qual_risk_coding', ['risk_assessment_prediction_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_pred_qual_risk_coding_tenant_id'), 'risk_assessment_pred_qual_risk_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_pred_qual_risk_coding_updated_at'), 'risk_assessment_pred_qual_risk_coding', ['updated_at'], unique=False)
    op.create_table('risk_assessment_reason_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('risk_assessment_reason_code_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['risk_assessment_reason_code_id'], ['risk_assessment_reason_code.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_reason_code_coding_created_at'), 'risk_assessment_reason_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_assessment_reason_code_coding_risk_assessment_reason_code_id'), 'risk_assessment_reason_code_coding', ['risk_assessment_reason_code_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_reason_code_coding_tenant_id'), 'risk_assessment_reason_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_reason_code_coding_updated_at'), 'risk_assessment_reason_code_coding', ['updated_at'], unique=False)



def downgrade() -> None:
    # Drop tables in reverse FK dependency order
    op.drop_table('risk_assessment_reason_code_coding')
    op.drop_table('risk_assessment_pred_qual_risk_coding')
    op.drop_table('risk_assessment_pred_outcome_coding')
    op.drop_table('risk_assessment_identifier_coding')
    op.drop_table('risk_assessment_note')
    op.drop_table('risk_assessment_prediction')
    op.drop_table('risk_assessment_reason_reference')
    op.drop_table('risk_assessment_reason_code')
    op.drop_table('risk_assessment_method_coding')
    op.drop_table('risk_assessment_code_coding')
    op.drop_table('risk_assessment_basis')
    op.drop_table('risk_assessment_identifier')
    op.drop_table('risk_assessment')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS risk_assessment_pub_seq")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS risk_assessment_note_author_reference_type")
    op.execute("DROP TYPE IF EXISTS risk_assessment_reason_reference_type")
    op.execute("DROP TYPE IF EXISTS risk_assessment_performer_reference_type")
    op.execute("DROP TYPE IF EXISTS risk_assessment_condition_reference_type")
    op.execute("DROP TYPE IF EXISTS risk_assessment_status")
