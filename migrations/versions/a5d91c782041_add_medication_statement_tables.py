"""add_medication_statement_tables

Revision ID: a5d91c782041
Revises: 4b2458546921
Create Date: 2026-11-02 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a5d91c782041'
down_revision: Union[str, None] = '4b2458546921'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_statement_status AS ENUM (
                'active', 'completed', 'entered-in-error', 'intended', 'stopped', 'on-hold', 'unknown', 'not-taken'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_statement_subject_reference_type AS ENUM ('Patient', 'Group');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_statement_medication_reference_type AS ENUM ('Medication');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_statement_based_on_reference_type AS ENUM (
                'MedicationRequest', 'CarePlan', 'ServiceRequest'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_statement_part_of_reference_type AS ENUM (
                'MedicationAdministration', 'MedicationDispense', 'MedicationStatement', 'Procedure', 'Observation'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_statement_context_reference_type AS ENUM ('Encounter', 'EpisodeOfCare');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_statement_information_source_reference_type AS ENUM (
                'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Organization'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_statement_reason_reference_type AS ENUM (
                'Condition', 'Observation', 'DiagnosticReport'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_statement_note_author_reference_type AS ENUM (
                'Practitioner', 'Patient', 'RelatedPerson', 'Organization'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("CREATE SEQUENCE IF NOT EXISTS medication_statement_pub_seq START WITH 500000 INCREMENT BY 1")

    # 1. Main table
    op.create_table(
        'medication_statement',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_id', sa.BigInteger(), server_default=sa.text("nextval('medication_statement_pub_seq')"), nullable=False),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'completed', 'entered-in-error', 'intended', 'stopped', 'on-hold', 'unknown', 'not-taken', name='medication_statement_status', create_type=False), nullable=False),
        sa.Column('category_text', sa.String(), nullable=True),
        sa.Column('medication_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('medication_reference', sa.String(), nullable=True),
        sa.Column('medication_type', postgresql.ENUM('Medication', name='medication_statement_medication_reference_type', create_type=False), nullable=True),
        sa.Column('medication_id', sa.BigInteger(), nullable=True),
        sa.Column('medication_display', sa.String(), nullable=True),
        sa.Column('medication_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('medication_identifier_type_system', sa.String(), nullable=True),
        sa.Column('medication_identifier_type_version', sa.String(), nullable=True),
        sa.Column('medication_identifier_type_code', sa.String(), nullable=True),
        sa.Column('medication_identifier_type_display', sa.String(), nullable=True),
        sa.Column('medication_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('medication_identifier_type_text', sa.String(), nullable=True),
        sa.Column('medication_identifier_system', sa.String(), nullable=True),
        sa.Column('medication_identifier_value', sa.String(), nullable=True),
        sa.Column('medication_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('medication_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=False),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='medication_statement_subject_reference_type', create_type=False), nullable=False),
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
        sa.Column('context_reference', sa.String(), nullable=True),
        sa.Column('context_type', postgresql.ENUM('Encounter', 'EpisodeOfCare', name='medication_statement_context_reference_type', create_type=False), nullable=True),
        sa.Column('context_id', sa.BigInteger(), nullable=True),
        sa.Column('context_display', sa.String(), nullable=True),
        sa.Column('context_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('context_identifier_type_system', sa.String(), nullable=True),
        sa.Column('context_identifier_type_version', sa.String(), nullable=True),
        sa.Column('context_identifier_type_code', sa.String(), nullable=True),
        sa.Column('context_identifier_type_display', sa.String(), nullable=True),
        sa.Column('context_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('context_identifier_type_text', sa.String(), nullable=True),
        sa.Column('context_identifier_system', sa.String(), nullable=True),
        sa.Column('context_identifier_value', sa.String(), nullable=True),
        sa.Column('context_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('context_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date_asserted', sa.DateTime(timezone=True), nullable=True),
        sa.Column('information_source_reference', sa.String(), nullable=True),
        sa.Column('information_source_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Organization', name='medication_statement_information_source_reference_type', create_type=False), nullable=True),
        sa.Column('information_source_id', sa.BigInteger(), nullable=True),
        sa.Column('information_source_display', sa.String(), nullable=True),
        sa.Column('information_source_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('information_source_identifier_type_system', sa.String(), nullable=True),
        sa.Column('information_source_identifier_type_version', sa.String(), nullable=True),
        sa.Column('information_source_identifier_type_code', sa.String(), nullable=True),
        sa.Column('information_source_identifier_type_display', sa.String(), nullable=True),
        sa.Column('information_source_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('information_source_identifier_type_text', sa.String(), nullable=True),
        sa.Column('information_source_identifier_system', sa.String(), nullable=True),
        sa.Column('information_source_identifier_value', sa.String(), nullable=True),
        sa.Column('information_source_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('information_source_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_id'), 'medication_statement', ['id'], unique=False)
    op.create_index(op.f('ix_medication_statement_medication_statement_id'), 'medication_statement', ['medication_statement_id'], unique=True)
    op.create_index(op.f('ix_medication_statement_medication_id'), 'medication_statement', ['medication_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_subject_id'), 'medication_statement', ['subject_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_context_id'), 'medication_statement', ['context_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_information_source_id'), 'medication_statement', ['information_source_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_tenant_id'), 'medication_statement', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_created_at'), 'medication_statement', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_statement_updated_at'), 'medication_statement', ['updated_at'], unique=False)

    # 2. identifier
    op.create_table(
        'medication_statement_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_identifier_medication_statement_pk'), 'medication_statement_identifier', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_identifier_assigner_id'), 'medication_statement_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_identifier_tenant_id'), 'medication_statement_identifier', ['tenant_id'], unique=False)

    op.create_table(
        'medication_statement_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_identifier_id'], ['medication_statement_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_identifier_type_coding_medication_statement_identifier_id'), 'medication_statement_identifier_type_coding', ['medication_statement_identifier_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_identifier_type_coding_tenant_id'), 'medication_statement_identifier_type_coding', ['tenant_id'], unique=False)

    # 3. based_on
    op.create_table(
        'medication_statement_based_on',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('MedicationRequest', 'CarePlan', 'ServiceRequest', name='medication_statement_based_on_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_based_on_medication_statement_pk'), 'medication_statement_based_on', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_based_on_reference_id'), 'medication_statement_based_on', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_based_on_tenant_id'), 'medication_statement_based_on', ['tenant_id'], unique=False)

    # 4. part_of
    op.create_table(
        'medication_statement_part_of',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('MedicationAdministration', 'MedicationDispense', 'MedicationStatement', 'Procedure', 'Observation', name='medication_statement_part_of_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_part_of_medication_statement_pk'), 'medication_statement_part_of', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_part_of_reference_id'), 'medication_statement_part_of', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_part_of_tenant_id'), 'medication_statement_part_of', ['tenant_id'], unique=False)

    # 5. status_reason
    op.create_table(
        'medication_statement_status_reason',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_status_reason_medication_statement_pk'), 'medication_statement_status_reason', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_status_reason_tenant_id'), 'medication_statement_status_reason', ['tenant_id'], unique=False)

    op.create_table(
        'medication_statement_status_reason_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_status_reason_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_status_reason_id'], ['medication_statement_status_reason.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_status_reason_coding_medication_statement_status_reason_id'), 'medication_statement_status_reason_coding', ['medication_statement_status_reason_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_status_reason_coding_tenant_id'), 'medication_statement_status_reason_coding', ['tenant_id'], unique=False)

    # 6. category_coding
    op.create_table(
        'medication_statement_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_category_coding_medication_statement_pk'), 'medication_statement_category_coding', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_category_coding_tenant_id'), 'medication_statement_category_coding', ['tenant_id'], unique=False)

    # 7. medication_coding
    op.create_table(
        'medication_statement_medication_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_medication_coding_medication_statement_pk'), 'medication_statement_medication_coding', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_medication_coding_tenant_id'), 'medication_statement_medication_coding', ['tenant_id'], unique=False)

    # 8. derived_from
    op.create_table(
        'medication_statement_derived_from',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_derived_from_medication_statement_pk'), 'medication_statement_derived_from', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_derived_from_reference_id'), 'medication_statement_derived_from', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_derived_from_tenant_id'), 'medication_statement_derived_from', ['tenant_id'], unique=False)

    # 9. reason_code
    op.create_table(
        'medication_statement_reason_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_reason_code_medication_statement_pk'), 'medication_statement_reason_code', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_reason_code_tenant_id'), 'medication_statement_reason_code', ['tenant_id'], unique=False)

    op.create_table(
        'medication_statement_reason_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_reason_code_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_reason_code_id'], ['medication_statement_reason_code.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_reason_code_coding_medication_statement_reason_code_id'), 'medication_statement_reason_code_coding', ['medication_statement_reason_code_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_reason_code_coding_tenant_id'), 'medication_statement_reason_code_coding', ['tenant_id'], unique=False)

    # 10. reason_reference
    op.create_table(
        'medication_statement_reason_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', name='medication_statement_reason_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_reason_reference_medication_statement_pk'), 'medication_statement_reason_reference', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_reason_reference_reference_id'), 'medication_statement_reason_reference', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_reason_reference_tenant_id'), 'medication_statement_reason_reference', ['tenant_id'], unique=False)

    # 11. note
    op.create_table(
        'medication_statement_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', postgresql.ENUM('Practitioner', 'Patient', 'RelatedPerson', 'Organization', name='medication_statement_note_author_reference_type', create_type=False), nullable=True),
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
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_note_medication_statement_pk'), 'medication_statement_note', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_note_author_id'), 'medication_statement_note', ['author_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_note_tenant_id'), 'medication_statement_note', ['tenant_id'], unique=False)

    # 12. dosage
    op.create_table(
        'medication_statement_dosage',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_pk', sa.BigInteger(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('patient_instruction', sa.Text(), nullable=True),
        sa.Column('timing', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('as_needed_boolean', sa.Boolean(), nullable=True),
        sa.Column('as_needed_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('site_text', sa.String(), nullable=True),
        sa.Column('route_text', sa.String(), nullable=True),
        sa.Column('method_text', sa.String(), nullable=True),
        sa.Column('dose_and_rate', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('max_dose_per_period', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('max_dose_per_administration_value', sa.Numeric(), nullable=True),
        sa.Column('max_dose_per_administration_unit', sa.String(), nullable=True),
        sa.Column('max_dose_per_administration_system', sa.String(), nullable=True),
        sa.Column('max_dose_per_administration_code', sa.String(), nullable=True),
        sa.Column('max_dose_per_lifetime_value', sa.Numeric(), nullable=True),
        sa.Column('max_dose_per_lifetime_unit', sa.String(), nullable=True),
        sa.Column('max_dose_per_lifetime_system', sa.String(), nullable=True),
        sa.Column('max_dose_per_lifetime_code', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['medication_statement_pk'], ['medication_statement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_dosage_medication_statement_pk'), 'medication_statement_dosage', ['medication_statement_pk'], unique=False)
    op.create_index(op.f('ix_medication_statement_dosage_tenant_id'), 'medication_statement_dosage', ['tenant_id'], unique=False)

    op.create_table(
        'medication_statement_dosage_site_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_dosage_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_dosage_id'], ['medication_statement_dosage.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_dosage_site_coding_medication_statement_dosage_id'), 'medication_statement_dosage_site_coding', ['medication_statement_dosage_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_dosage_site_coding_tenant_id'), 'medication_statement_dosage_site_coding', ['tenant_id'], unique=False)

    op.create_table(
        'medication_statement_dosage_route_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_dosage_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_dosage_id'], ['medication_statement_dosage.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_dosage_route_coding_medication_statement_dosage_id'), 'medication_statement_dosage_route_coding', ['medication_statement_dosage_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_dosage_route_coding_tenant_id'), 'medication_statement_dosage_route_coding', ['tenant_id'], unique=False)

    op.create_table(
        'medication_statement_dosage_method_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_dosage_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_dosage_id'], ['medication_statement_dosage.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_dosage_method_coding_medication_statement_dosage_id'), 'medication_statement_dosage_method_coding', ['medication_statement_dosage_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_dosage_method_coding_tenant_id'), 'medication_statement_dosage_method_coding', ['tenant_id'], unique=False)

    op.create_table(
        'medication_statement_dosage_as_needed_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_dosage_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_dosage_id'], ['medication_statement_dosage.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_dosage_as_needed_coding_medication_statement_dosage_id'), 'medication_statement_dosage_as_needed_coding', ['medication_statement_dosage_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_dosage_as_needed_coding_tenant_id'), 'medication_statement_dosage_as_needed_coding', ['tenant_id'], unique=False)

    op.create_table(
        'medication_statement_dosage_additional_instruction',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_dosage_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['medication_statement_dosage_id'], ['medication_statement_dosage.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_dosage_additional_instruction_medication_statement_dosage_id'), 'medication_statement_dosage_additional_instruction', ['medication_statement_dosage_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_dosage_additional_instruction_tenant_id'), 'medication_statement_dosage_additional_instruction', ['tenant_id'], unique=False)

    op.create_table(
        'medication_statement_dosage_additional_instruction_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_statement_dosage_additional_instruction_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_statement_dosage_additional_instruction_id'], ['medication_statement_dosage_additional_instruction.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_statement_dosage_addl_inst_coding_id'), 'medication_statement_dosage_additional_instruction_coding', ['medication_statement_dosage_additional_instruction_id'], unique=False)
    op.create_index(op.f('ix_medication_statement_dosage_additional_instruction_coding_tenant_id'), 'medication_statement_dosage_additional_instruction_coding', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_table('medication_statement_dosage_additional_instruction_coding')
    op.drop_table('medication_statement_dosage_additional_instruction')
    op.drop_table('medication_statement_dosage_as_needed_coding')
    op.drop_table('medication_statement_dosage_method_coding')
    op.drop_table('medication_statement_dosage_route_coding')
    op.drop_table('medication_statement_dosage_site_coding')
    op.drop_table('medication_statement_dosage')
    op.drop_table('medication_statement_note')
    op.drop_table('medication_statement_reason_reference')
    op.drop_table('medication_statement_reason_code_coding')
    op.drop_table('medication_statement_reason_code')
    op.drop_table('medication_statement_derived_from')
    op.drop_table('medication_statement_medication_coding')
    op.drop_table('medication_statement_category_coding')
    op.drop_table('medication_statement_status_reason_coding')
    op.drop_table('medication_statement_status_reason')
    op.drop_table('medication_statement_part_of')
    op.drop_table('medication_statement_based_on')
    op.drop_table('medication_statement_identifier_type_coding')
    op.drop_table('medication_statement_identifier')
    op.drop_table('medication_statement')

    op.execute("DROP SEQUENCE IF EXISTS medication_statement_pub_seq")

    op.execute("DROP TYPE IF EXISTS medication_statement_note_author_reference_type")
    op.execute("DROP TYPE IF EXISTS medication_statement_reason_reference_type")
    op.execute("DROP TYPE IF EXISTS medication_statement_information_source_reference_type")
    op.execute("DROP TYPE IF EXISTS medication_statement_context_reference_type")
    op.execute("DROP TYPE IF EXISTS medication_statement_part_of_reference_type")
    op.execute("DROP TYPE IF EXISTS medication_statement_based_on_reference_type")
    op.execute("DROP TYPE IF EXISTS medication_statement_medication_reference_type")
    op.execute("DROP TYPE IF EXISTS medication_statement_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS medication_statement_status")
