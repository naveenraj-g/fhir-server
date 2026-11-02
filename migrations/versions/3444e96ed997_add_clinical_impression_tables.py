"""add_clinical_impression_tables

Revision ID: 3444e96ed997
Revises: b027dab8fb83
Create Date: 2026-11-02 22:41:34.597742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3444e96ed997'
down_revision: Union[str, None] = 'b027dab8fb83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE clinical_impression_status AS ENUM (
                'in-progress', 'completed', 'entered-in-error'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE clinical_impression_assessor_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE clinical_impression_previous_reference_type AS ENUM (
                'ClinicalImpression'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE clinical_impression_problem_reference_type AS ENUM (
                'Condition', 'AllergyIntolerance'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE clinical_impression_finding_reference_type AS ENUM (
                'Condition', 'Observation', 'Media'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE clinical_impression_prognosis_reference_type AS ENUM (
                'RiskAssessment'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE clinical_impression_note_author_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS clinical_impression_pub_seq START WITH 530000 INCREMENT BY 1")

    # 3. Tables and Indexes
    op.create_table('clinical_impression',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_id', sa.BigInteger(), nullable=False),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', postgresql.ENUM('in-progress', 'completed', 'entered-in-error', name='clinical_impression_status', create_type=False), nullable=False),
        sa.Column('status_reason_text', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=False),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='subject_reference_type', create_type=False), nullable=False),
        sa.Column('subject_id', sa.BigInteger(), nullable=False),
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
        sa.Column('effective_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assessor_reference', sa.String(), nullable=True),
        sa.Column('assessor_type', postgresql.ENUM('Practitioner', 'PractitionerRole', name='clinical_impression_assessor_reference_type', create_type=False), nullable=True),
        sa.Column('assessor_id', sa.BigInteger(), nullable=True),
        sa.Column('assessor_display', sa.String(), nullable=True),
        sa.Column('assessor_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('assessor_identifier_type_system', sa.String(), nullable=True),
        sa.Column('assessor_identifier_type_version', sa.String(), nullable=True),
        sa.Column('assessor_identifier_type_code', sa.String(), nullable=True),
        sa.Column('assessor_identifier_type_display', sa.String(), nullable=True),
        sa.Column('assessor_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('assessor_identifier_type_text', sa.String(), nullable=True),
        sa.Column('assessor_identifier_system', sa.String(), nullable=True),
        sa.Column('assessor_identifier_value', sa.String(), nullable=True),
        sa.Column('assessor_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assessor_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('previous_reference', sa.String(), nullable=True),
        sa.Column('previous_type', postgresql.ENUM('ClinicalImpression', name='clinical_impression_previous_reference_type', create_type=False), nullable=True),
        sa.Column('previous_id', sa.BigInteger(), nullable=True),
        sa.Column('previous_display', sa.String(), nullable=True),
        sa.Column('previous_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('previous_identifier_type_system', sa.String(), nullable=True),
        sa.Column('previous_identifier_type_version', sa.String(), nullable=True),
        sa.Column('previous_identifier_type_code', sa.String(), nullable=True),
        sa.Column('previous_identifier_type_display', sa.String(), nullable=True),
        sa.Column('previous_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('previous_identifier_type_text', sa.String(), nullable=True),
        sa.Column('previous_identifier_system', sa.String(), nullable=True),
        sa.Column('previous_identifier_value', sa.String(), nullable=True),
        sa.Column('previous_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('previous_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_assessor_id'), 'clinical_impression', ['assessor_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_clinical_impression_id'), 'clinical_impression', ['clinical_impression_id'], unique=True)

    op.create_index(op.f('ix_clinical_impression_created_at'), 'clinical_impression', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_encounter_id'), 'clinical_impression', ['encounter_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_previous_id'), 'clinical_impression', ['previous_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_status'), 'clinical_impression', ['status'], unique=False)

    op.create_index(op.f('ix_clinical_impression_subject_id'), 'clinical_impression', ['subject_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_tenant_id'), 'clinical_impression', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_updated_at'), 'clinical_impression', ['updated_at'], unique=False)

    op.create_table('clinical_impression_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_code_coding_clinical_impression_pk'), 'clinical_impression_code_coding', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_code_coding_created_at'), 'clinical_impression_code_coding', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_code_coding_tenant_id'), 'clinical_impression_code_coding', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_code_coding_updated_at'), 'clinical_impression_code_coding', ['updated_at'], unique=False)

    op.create_table('clinical_impression_finding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
        sa.Column('item_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('item_reference', sa.String(), nullable=True),
        sa.Column('item_reference_type', postgresql.ENUM('Condition', 'Observation', 'Media', name='clinical_impression_finding_reference_type', create_type=False), nullable=True),
        sa.Column('item_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('item_reference_display', sa.String(), nullable=True),
        sa.Column('item_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('item_reference_identifier_type_system', sa.String(), nullable=True),
        sa.Column('item_reference_identifier_type_version', sa.String(), nullable=True),
        sa.Column('item_reference_identifier_type_code', sa.String(), nullable=True),
        sa.Column('item_reference_identifier_type_display', sa.String(), nullable=True),
        sa.Column('item_reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('item_reference_identifier_type_text', sa.String(), nullable=True),
        sa.Column('item_reference_identifier_system', sa.String(), nullable=True),
        sa.Column('item_reference_identifier_value', sa.String(), nullable=True),
        sa.Column('item_reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('item_reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('basis', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_finding_clinical_impression_pk'), 'clinical_impression_finding', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_finding_created_at'), 'clinical_impression_finding', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_finding_item_reference_id'), 'clinical_impression_finding', ['item_reference_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_finding_tenant_id'), 'clinical_impression_finding', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_finding_updated_at'), 'clinical_impression_finding', ['updated_at'], unique=False)

    op.create_table('clinical_impression_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_identifier_assigner_id'), 'clinical_impression_identifier', ['assigner_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_identifier_clinical_impression_pk'), 'clinical_impression_identifier', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_identifier_created_at'), 'clinical_impression_identifier', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_identifier_tenant_id'), 'clinical_impression_identifier', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_identifier_updated_at'), 'clinical_impression_identifier', ['updated_at'], unique=False)

    op.create_table('clinical_impression_investigation',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_investigation_clinical_impression_pk'), 'clinical_impression_investigation', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_investigation_created_at'), 'clinical_impression_investigation', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_investigation_tenant_id'), 'clinical_impression_investigation', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_investigation_updated_at'), 'clinical_impression_investigation', ['updated_at'], unique=False)

    op.create_table('clinical_impression_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', name='clinical_impression_note_author_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_note_author_id'), 'clinical_impression_note', ['author_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_note_clinical_impression_pk'), 'clinical_impression_note', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_note_created_at'), 'clinical_impression_note', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_note_tenant_id'), 'clinical_impression_note', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_note_updated_at'), 'clinical_impression_note', ['updated_at'], unique=False)

    op.create_table('clinical_impression_problem',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
        sa.Column('problem_reference', sa.String(), nullable=True),
        sa.Column('problem_type', postgresql.ENUM('Condition', 'AllergyIntolerance', name='clinical_impression_problem_reference_type', create_type=False), nullable=True),
        sa.Column('problem_id', sa.BigInteger(), nullable=True),
        sa.Column('problem_display', sa.String(), nullable=True),
        sa.Column('problem_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('problem_identifier_type_system', sa.String(), nullable=True),
        sa.Column('problem_identifier_type_version', sa.String(), nullable=True),
        sa.Column('problem_identifier_type_code', sa.String(), nullable=True),
        sa.Column('problem_identifier_type_display', sa.String(), nullable=True),
        sa.Column('problem_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('problem_identifier_type_text', sa.String(), nullable=True),
        sa.Column('problem_identifier_system', sa.String(), nullable=True),
        sa.Column('problem_identifier_value', sa.String(), nullable=True),
        sa.Column('problem_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('problem_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_problem_clinical_impression_pk'), 'clinical_impression_problem', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_problem_created_at'), 'clinical_impression_problem', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_problem_problem_id'), 'clinical_impression_problem', ['problem_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_problem_tenant_id'), 'clinical_impression_problem', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_problem_updated_at'), 'clinical_impression_problem', ['updated_at'], unique=False)

    op.create_table('clinical_impression_prognosis_codeable_concept',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_prognosis_codeable_concept_clinical_impression_pk'), 'clinical_impression_prognosis_codeable_concept', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_prognosis_codeable_concept_created_at'), 'clinical_impression_prognosis_codeable_concept', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_prognosis_codeable_concept_tenant_id'), 'clinical_impression_prognosis_codeable_concept', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_prognosis_codeable_concept_updated_at'), 'clinical_impression_prognosis_codeable_concept', ['updated_at'], unique=False)

    op.create_table('clinical_impression_prognosis_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('RiskAssessment', name='clinical_impression_prognosis_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('identifier_type_system', sa.String(), nullable=True),
        sa.Column('identifier_type_version', sa.String(), nullable=True),
        sa.Column('identifier_type_code', sa.String(), nullable=True),
        sa.Column('identifier_type_display', sa.String(), nullable=True),
        sa.Column('identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('identifier_type_text', sa.String(), nullable=True),
        sa.Column('identifier_system', sa.String(), nullable=True),
        sa.Column('identifier_value', sa.String(), nullable=True),
        sa.Column('identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_prognosis_reference_clinical_impression_pk'), 'clinical_impression_prognosis_reference', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_prognosis_reference_created_at'), 'clinical_impression_prognosis_reference', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_prognosis_reference_reference_id'), 'clinical_impression_prognosis_reference', ['reference_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_prognosis_reference_tenant_id'), 'clinical_impression_prognosis_reference', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_prognosis_reference_updated_at'), 'clinical_impression_prognosis_reference', ['updated_at'], unique=False)

    op.create_table('clinical_impression_protocol',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
        sa.Column('uri', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_protocol_clinical_impression_pk'), 'clinical_impression_protocol', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_protocol_created_at'), 'clinical_impression_protocol', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_protocol_tenant_id'), 'clinical_impression_protocol', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_protocol_updated_at'), 'clinical_impression_protocol', ['updated_at'], unique=False)

    op.create_table('clinical_impression_status_reason_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_status_reason_coding_clinical_impression_pk'), 'clinical_impression_status_reason_coding', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_status_reason_coding_created_at'), 'clinical_impression_status_reason_coding', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_status_reason_coding_tenant_id'), 'clinical_impression_status_reason_coding', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_status_reason_coding_updated_at'), 'clinical_impression_status_reason_coding', ['updated_at'], unique=False)

    op.create_table('clinical_impression_supporting_info',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('identifier_type_system', sa.String(), nullable=True),
        sa.Column('identifier_type_version', sa.String(), nullable=True),
        sa.Column('identifier_type_code', sa.String(), nullable=True),
        sa.Column('identifier_type_display', sa.String(), nullable=True),
        sa.Column('identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('identifier_type_text', sa.String(), nullable=True),
        sa.Column('identifier_system', sa.String(), nullable=True),
        sa.Column('identifier_value', sa.String(), nullable=True),
        sa.Column('identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['clinical_impression_pk'], ['clinical_impression.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_supporting_info_clinical_impression_pk'), 'clinical_impression_supporting_info', ['clinical_impression_pk'], unique=False)

    op.create_index(op.f('ix_clinical_impression_supporting_info_created_at'), 'clinical_impression_supporting_info', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_supporting_info_reference_id'), 'clinical_impression_supporting_info', ['reference_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_supporting_info_tenant_id'), 'clinical_impression_supporting_info', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_supporting_info_updated_at'), 'clinical_impression_supporting_info', ['updated_at'], unique=False)

    op.create_table('clinical_impression_finding_item_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_finding_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['clinical_impression_finding_id'], ['clinical_impression_finding.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_finding_item_coding_clinical_impression_finding_id'), 'clinical_impression_finding_item_coding', ['clinical_impression_finding_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_finding_item_coding_created_at'), 'clinical_impression_finding_item_coding', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_finding_item_coding_tenant_id'), 'clinical_impression_finding_item_coding', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_finding_item_coding_updated_at'), 'clinical_impression_finding_item_coding', ['updated_at'], unique=False)

    op.create_table('clinical_impression_identifier_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['clinical_impression_identifier_id'], ['clinical_impression_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_identifier_coding_clinical_impression_identifier_id'), 'clinical_impression_identifier_coding', ['clinical_impression_identifier_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_identifier_coding_created_at'), 'clinical_impression_identifier_coding', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_identifier_coding_tenant_id'), 'clinical_impression_identifier_coding', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_identifier_coding_updated_at'), 'clinical_impression_identifier_coding', ['updated_at'], unique=False)

    op.create_table('clinical_impression_investigation_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_investigation_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['clinical_impression_investigation_id'], ['clinical_impression_investigation.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_investigation_code_coding_clinical_impression_investigation_id'), 'clinical_impression_investigation_code_coding', ['clinical_impression_investigation_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_investigation_code_coding_created_at'), 'clinical_impression_investigation_code_coding', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_investigation_code_coding_tenant_id'), 'clinical_impression_investigation_code_coding', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_investigation_code_coding_updated_at'), 'clinical_impression_investigation_code_coding', ['updated_at'], unique=False)

    op.create_table('clinical_impression_investigation_item',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_investigation_id', sa.BigInteger(), nullable=False),
        sa.Column('item_reference', sa.String(), nullable=True),
        sa.Column('item_type', sa.String(), nullable=True),
        sa.Column('item_id', sa.BigInteger(), nullable=True),
        sa.Column('item_display', sa.String(), nullable=True),
        sa.Column('item_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('item_identifier_type_system', sa.String(), nullable=True),
        sa.Column('item_identifier_type_version', sa.String(), nullable=True),
        sa.Column('item_identifier_type_code', sa.String(), nullable=True),
        sa.Column('item_identifier_type_display', sa.String(), nullable=True),
        sa.Column('item_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('item_identifier_type_text', sa.String(), nullable=True),
        sa.Column('item_identifier_system', sa.String(), nullable=True),
        sa.Column('item_identifier_value', sa.String(), nullable=True),
        sa.Column('item_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('item_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['clinical_impression_investigation_id'], ['clinical_impression_investigation.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_investigation_item_clinical_impression_investigation_id'), 'clinical_impression_investigation_item', ['clinical_impression_investigation_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_investigation_item_created_at'), 'clinical_impression_investigation_item', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_investigation_item_item_id'), 'clinical_impression_investigation_item', ['item_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_investigation_item_tenant_id'), 'clinical_impression_investigation_item', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_investigation_item_updated_at'), 'clinical_impression_investigation_item', ['updated_at'], unique=False)

    op.create_table('clinical_impression_prognosis_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('clinical_impression_prognosis_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['clinical_impression_prognosis_id'], ['clinical_impression_prognosis_codeable_concept.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    op.create_index(op.f('ix_clinical_impression_prognosis_coding_clinical_impression_prognosis_id'), 'clinical_impression_prognosis_coding', ['clinical_impression_prognosis_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_prognosis_coding_created_at'), 'clinical_impression_prognosis_coding', ['created_at'], unique=False)

    op.create_index(op.f('ix_clinical_impression_prognosis_coding_tenant_id'), 'clinical_impression_prognosis_coding', ['tenant_id'], unique=False)

    op.create_index(op.f('ix_clinical_impression_prognosis_coding_updated_at'), 'clinical_impression_prognosis_coding', ['updated_at'], unique=False)

def downgrade() -> None:
    # 1. Drop tables in reverse FK dependency order
    op.drop_table('clinical_impression_prognosis_coding')
    op.drop_table('clinical_impression_investigation_item')
    op.drop_table('clinical_impression_investigation_code_coding')
    op.drop_table('clinical_impression_identifier_coding')
    op.drop_table('clinical_impression_finding_item_coding')

    op.drop_table('clinical_impression_supporting_info')
    op.drop_table('clinical_impression_status_reason_coding')
    op.drop_table('clinical_impression_protocol')
    op.drop_table('clinical_impression_prognosis_reference')
    op.drop_table('clinical_impression_prognosis_codeable_concept')
    op.drop_table('clinical_impression_problem')
    op.drop_table('clinical_impression_note')
    op.drop_table('clinical_impression_investigation')
    op.drop_table('clinical_impression_identifier')
    op.drop_table('clinical_impression_finding')
    op.drop_table('clinical_impression_code_coding')

    op.drop_table('clinical_impression')

    # 2. Drop Sequence
    op.execute("DROP SEQUENCE IF EXISTS clinical_impression_pub_seq")

    # 3. Drop Enums
    op.execute("DROP TYPE IF EXISTS clinical_impression_note_author_reference_type")
    op.execute("DROP TYPE IF EXISTS clinical_impression_prognosis_reference_type")
    op.execute("DROP TYPE IF EXISTS clinical_impression_finding_reference_type")
    op.execute("DROP TYPE IF EXISTS clinical_impression_problem_reference_type")
    op.execute("DROP TYPE IF EXISTS clinical_impression_previous_reference_type")
    op.execute("DROP TYPE IF EXISTS clinical_impression_assessor_reference_type")
    op.execute("DROP TYPE IF EXISTS clinical_impression_status")
