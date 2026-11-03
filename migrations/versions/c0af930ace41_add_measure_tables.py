"""add_measure_tables

Revision ID: c0af930ace41
Revises: 286d55bd92c4
Create Date: 2026-11-03 09:09:13.102006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c0af930ace41'
down_revision: Union[str, None] = '286d55bd92c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_contact_role AS ENUM (
                'contact', 'author', 'editor', 'reviewer', 'endorser'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_quantity_comparator AS ENUM (
                'lt', 'le', 'ge', 'gt'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_related_artifact_type AS ENUM (
                'documentation', 'justification', 'citation', 'predecessor', 'successor', 'derived_from', 'depends_on', 'composed_of'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_status AS ENUM (
                'draft', 'active', 'retired', 'unknown'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_subject_reference_type AS ENUM (
                'Group'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_use_context_value_reference_type AS ENUM (
                'PlanDefinition', 'ResearchStudy', 'InsurancePlan', 'HealthcareService', 'Group', 'Location', 'Organization', 'Measure'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS measure_pub_seq START WITH 560000 INCREMENT BY 1;")

    # 3. Tables
    op.create_table('measure',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_id', sa.BigInteger(), server_default=sa.text("nextval('measure_pub_seq')"), nullable=False),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('subtitle', sa.String(), nullable=True),
    sa.Column('status', postgresql.ENUM('draft', 'active', 'retired', 'unknown', name='measure_status', create_type=False), nullable=False),
    sa.Column('experimental', sa.Boolean(), nullable=True),
    sa.Column('subject_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('subject_reference', sa.String(), nullable=True),
    sa.Column('subject_type', postgresql.ENUM('Group', name='measure_subject_reference_type', create_type=False), nullable=True),
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
    sa.Column('date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('publisher', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('purpose', sa.Text(), nullable=True),
    sa.Column('usage', sa.Text(), nullable=True),
    sa.Column('copyright', sa.Text(), nullable=True),
    sa.Column('approval_date', sa.Date(), nullable=True),
    sa.Column('last_review_date', sa.Date(), nullable=True),
    sa.Column('effective_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('effective_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('library', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('disclaimer', sa.Text(), nullable=True),
    sa.Column('scoring_text', sa.String(), nullable=True),
    sa.Column('composite_scoring_text', sa.String(), nullable=True),
    sa.Column('risk_adjustment', sa.String(), nullable=True),
    sa.Column('rate_aggregation', sa.String(), nullable=True),
    sa.Column('rationale', sa.Text(), nullable=True),
    sa.Column('clinical_recommendation_statement', sa.Text(), nullable=True),
    sa.Column('improvement_notation_text', sa.String(), nullable=True),
    sa.Column('definition', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('guidance', sa.Text(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_created_at'), 'measure', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_id'), 'measure', ['id'], unique=False)
    op.create_index(op.f('ix_measure_measure_id'), 'measure', ['measure_id'], unique=True)
    op.create_index(op.f('ix_measure_subject_id'), 'measure', ['subject_id'], unique=False)
    op.create_index(op.f('ix_measure_tenant_id'), 'measure', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_updated_at'), 'measure', ['updated_at'], unique=False)
    op.create_table('measure_composite_scoring_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_composite_scoring_coding_created_at'), 'measure_composite_scoring_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_composite_scoring_coding_measure_pk'), 'measure_composite_scoring_coding', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_composite_scoring_coding_tenant_id'), 'measure_composite_scoring_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_composite_scoring_coding_updated_at'), 'measure_composite_scoring_coding', ['updated_at'], unique=False)
    op.create_table('measure_contact',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
    sa.Column('role', postgresql.ENUM('contact', 'author', 'editor', 'reviewer', 'endorser', name='measure_contact_role', create_type=False), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_contact_created_at'), 'measure_contact', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_contact_measure_pk'), 'measure_contact', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_contact_role'), 'measure_contact', ['role'], unique=False)
    op.create_index(op.f('ix_measure_contact_tenant_id'), 'measure_contact', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_contact_updated_at'), 'measure_contact', ['updated_at'], unique=False)
    op.create_table('measure_group',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_group_created_at'), 'measure_group', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_group_measure_pk'), 'measure_group', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_group_tenant_id'), 'measure_group', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_group_updated_at'), 'measure_group', ['updated_at'], unique=False)
    op.create_table('measure_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_identifier_assigner_id'), 'measure_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_measure_identifier_created_at'), 'measure_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_identifier_measure_pk'), 'measure_identifier', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_identifier_tenant_id'), 'measure_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_identifier_updated_at'), 'measure_identifier', ['updated_at'], unique=False)
    op.create_table('measure_improvement_notation_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_improvement_notation_coding_created_at'), 'measure_improvement_notation_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_improvement_notation_coding_measure_pk'), 'measure_improvement_notation_coding', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_improvement_notation_coding_tenant_id'), 'measure_improvement_notation_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_improvement_notation_coding_updated_at'), 'measure_improvement_notation_coding', ['updated_at'], unique=False)
    op.create_table('measure_jurisdiction',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_jurisdiction_created_at'), 'measure_jurisdiction', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_jurisdiction_measure_pk'), 'measure_jurisdiction', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_jurisdiction_tenant_id'), 'measure_jurisdiction', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_jurisdiction_updated_at'), 'measure_jurisdiction', ['updated_at'], unique=False)
    op.create_table('measure_related_artifact',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
    sa.Column('type', postgresql.ENUM('documentation', 'justification', 'citation', 'predecessor', 'successor', 'derived_from', 'depends_on', 'composed_of', name='measure_related_artifact_type', create_type=False), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('citation', sa.Text(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('document', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('resource', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_related_artifact_created_at'), 'measure_related_artifact', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_related_artifact_measure_pk'), 'measure_related_artifact', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_related_artifact_tenant_id'), 'measure_related_artifact', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_related_artifact_updated_at'), 'measure_related_artifact', ['updated_at'], unique=False)
    op.create_table('measure_scoring_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_scoring_coding_created_at'), 'measure_scoring_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_scoring_coding_measure_pk'), 'measure_scoring_coding', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_scoring_coding_tenant_id'), 'measure_scoring_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_scoring_coding_updated_at'), 'measure_scoring_coding', ['updated_at'], unique=False)
    op.create_table('measure_subject_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_subject_coding_created_at'), 'measure_subject_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_subject_coding_measure_pk'), 'measure_subject_coding', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_subject_coding_tenant_id'), 'measure_subject_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_subject_coding_updated_at'), 'measure_subject_coding', ['updated_at'], unique=False)
    op.create_table('measure_supplemental_data',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('criteria_description', sa.String(), nullable=True),
    sa.Column('criteria_name', sa.String(), nullable=True),
    sa.Column('criteria_language', sa.String(), nullable=True),
    sa.Column('criteria_expression', sa.Text(), nullable=True),
    sa.Column('criteria_reference', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_supplemental_data_created_at'), 'measure_supplemental_data', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_measure_pk'), 'measure_supplemental_data', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_tenant_id'), 'measure_supplemental_data', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_updated_at'), 'measure_supplemental_data', ['updated_at'], unique=False)
    op.create_table('measure_topic',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_topic_created_at'), 'measure_topic', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_topic_measure_pk'), 'measure_topic', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_topic_tenant_id'), 'measure_topic', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_topic_updated_at'), 'measure_topic', ['updated_at'], unique=False)
    op.create_table('measure_type',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_type_created_at'), 'measure_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_type_measure_pk'), 'measure_type', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_type_tenant_id'), 'measure_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_type_updated_at'), 'measure_type', ['updated_at'], unique=False)
    op.create_table('measure_use_context',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_pk', sa.BigInteger(), nullable=False),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.Column('value_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('value_quantity_value', sa.Numeric(), nullable=True),
    sa.Column('value_quantity_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='measure_quantity_comparator', create_type=False), nullable=True),
    sa.Column('value_quantity_unit', sa.String(), nullable=True),
    sa.Column('value_quantity_system', sa.String(), nullable=True),
    sa.Column('value_quantity_code', sa.String(), nullable=True),
    sa.Column('value_range_low_value', sa.Numeric(), nullable=True),
    sa.Column('value_range_low_unit', sa.String(), nullable=True),
    sa.Column('value_range_low_system', sa.String(), nullable=True),
    sa.Column('value_range_low_code', sa.String(), nullable=True),
    sa.Column('value_range_high_value', sa.Numeric(), nullable=True),
    sa.Column('value_range_high_unit', sa.String(), nullable=True),
    sa.Column('value_range_high_system', sa.String(), nullable=True),
    sa.Column('value_range_high_code', sa.String(), nullable=True),
    sa.Column('value_reference_reference', sa.String(), nullable=True),
    sa.Column('value_reference_type', postgresql.ENUM('PlanDefinition', 'ResearchStudy', 'InsurancePlan', 'HealthcareService', 'Group', 'Location', 'Organization', 'Measure', name='measure_use_context_value_reference_type', create_type=False), nullable=True),
    sa.Column('value_reference_id', sa.BigInteger(), nullable=True),
    sa.Column('value_reference_display', sa.String(), nullable=True),
    sa.Column('value_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('value_reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('value_reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('value_reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('value_reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('value_reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('value_reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('value_reference_identifier_system', sa.String(), nullable=True),
    sa.Column('value_reference_identifier_value', sa.String(), nullable=True),
    sa.Column('value_reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('value_reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_pk'], ['measure.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_use_context_created_at'), 'measure_use_context', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_use_context_measure_pk'), 'measure_use_context', ['measure_pk'], unique=False)
    op.create_index(op.f('ix_measure_use_context_tenant_id'), 'measure_use_context', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_use_context_updated_at'), 'measure_use_context', ['updated_at'], unique=False)
    op.create_index(op.f('ix_measure_use_context_value_reference_id'), 'measure_use_context', ['value_reference_id'], unique=False)
    op.create_table('measure_contact_telecom',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_contact_id', sa.BigInteger(), nullable=False),
    sa.Column('system', postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False), nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_contact_id'], ['measure_contact.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_contact_telecom_created_at'), 'measure_contact_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_contact_telecom_measure_contact_id'), 'measure_contact_telecom', ['measure_contact_id'], unique=False)
    op.create_index(op.f('ix_measure_contact_telecom_tenant_id'), 'measure_contact_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_contact_telecom_updated_at'), 'measure_contact_telecom', ['updated_at'], unique=False)
    op.create_table('measure_group_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_group_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_group_id'], ['measure_group.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_group_code_coding_created_at'), 'measure_group_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_group_code_coding_measure_group_id'), 'measure_group_code_coding', ['measure_group_id'], unique=False)
    op.create_index(op.f('ix_measure_group_code_coding_tenant_id'), 'measure_group_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_group_code_coding_updated_at'), 'measure_group_code_coding', ['updated_at'], unique=False)
    op.create_table('measure_group_population',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_group_id', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('criteria_description', sa.String(), nullable=True),
    sa.Column('criteria_name', sa.String(), nullable=True),
    sa.Column('criteria_language', sa.String(), nullable=True),
    sa.Column('criteria_expression', sa.Text(), nullable=True),
    sa.Column('criteria_reference', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_group_id'], ['measure_group.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_group_population_created_at'), 'measure_group_population', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_group_population_measure_group_id'), 'measure_group_population', ['measure_group_id'], unique=False)
    op.create_index(op.f('ix_measure_group_population_tenant_id'), 'measure_group_population', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_group_population_updated_at'), 'measure_group_population', ['updated_at'], unique=False)
    op.create_table('measure_group_stratifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_group_id', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('criteria_description', sa.String(), nullable=True),
    sa.Column('criteria_name', sa.String(), nullable=True),
    sa.Column('criteria_language', sa.String(), nullable=True),
    sa.Column('criteria_expression', sa.Text(), nullable=True),
    sa.Column('criteria_reference', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_group_id'], ['measure_group.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_group_stratifier_created_at'), 'measure_group_stratifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_measure_group_id'), 'measure_group_stratifier', ['measure_group_id'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_tenant_id'), 'measure_group_stratifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_updated_at'), 'measure_group_stratifier', ['updated_at'], unique=False)
    op.create_table('measure_identifier_type_coding',
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
    sa.ForeignKeyConstraint(['identifier_id'], ['measure_identifier.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_identifier_type_coding_created_at'), 'measure_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_identifier_type_coding_identifier_id'), 'measure_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_measure_identifier_type_coding_tenant_id'), 'measure_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_identifier_type_coding_updated_at'), 'measure_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('measure_jurisdiction_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_jurisdiction_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_jurisdiction_id'], ['measure_jurisdiction.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_jurisdiction_coding_created_at'), 'measure_jurisdiction_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_jurisdiction_coding_measure_jurisdiction_id'), 'measure_jurisdiction_coding', ['measure_jurisdiction_id'], unique=False)
    op.create_index(op.f('ix_measure_jurisdiction_coding_tenant_id'), 'measure_jurisdiction_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_jurisdiction_coding_updated_at'), 'measure_jurisdiction_coding', ['updated_at'], unique=False)
    op.create_table('measure_supplemental_data_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_supplemental_data_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_supplemental_data_id'], ['measure_supplemental_data.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_supplemental_data_code_coding_created_at'), 'measure_supplemental_data_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_code_coding_measure_supplemental_data_id'), 'measure_supplemental_data_code_coding', ['measure_supplemental_data_id'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_code_coding_tenant_id'), 'measure_supplemental_data_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_code_coding_updated_at'), 'measure_supplemental_data_code_coding', ['updated_at'], unique=False)
    op.create_table('measure_supplemental_data_usage',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_supplemental_data_id', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_supplemental_data_id'], ['measure_supplemental_data.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_supplemental_data_usage_created_at'), 'measure_supplemental_data_usage', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_usage_measure_supplemental_data_id'), 'measure_supplemental_data_usage', ['measure_supplemental_data_id'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_usage_tenant_id'), 'measure_supplemental_data_usage', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_usage_updated_at'), 'measure_supplemental_data_usage', ['updated_at'], unique=False)
    op.create_table('measure_topic_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_topic_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_topic_id'], ['measure_topic.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_topic_coding_created_at'), 'measure_topic_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_topic_coding_measure_topic_id'), 'measure_topic_coding', ['measure_topic_id'], unique=False)
    op.create_index(op.f('ix_measure_topic_coding_tenant_id'), 'measure_topic_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_topic_coding_updated_at'), 'measure_topic_coding', ['updated_at'], unique=False)
    op.create_table('measure_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_type_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_type_id'], ['measure_type.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_type_coding_created_at'), 'measure_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_type_coding_measure_type_id'), 'measure_type_coding', ['measure_type_id'], unique=False)
    op.create_index(op.f('ix_measure_type_coding_tenant_id'), 'measure_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_type_coding_updated_at'), 'measure_type_coding', ['updated_at'], unique=False)
    op.create_table('measure_use_context_value_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_use_context_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_use_context_id'], ['measure_use_context.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_use_context_value_coding_created_at'), 'measure_use_context_value_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_use_context_value_coding_measure_use_context_id'), 'measure_use_context_value_coding', ['measure_use_context_id'], unique=False)
    op.create_index(op.f('ix_measure_use_context_value_coding_tenant_id'), 'measure_use_context_value_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_use_context_value_coding_updated_at'), 'measure_use_context_value_coding', ['updated_at'], unique=False)
    op.create_table('measure_group_population_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_group_population_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_group_population_id'], ['measure_group_population.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_group_population_code_coding_created_at'), 'measure_group_population_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_group_population_code_coding_measure_group_population_id'), 'measure_group_population_code_coding', ['measure_group_population_id'], unique=False)
    op.create_index(op.f('ix_measure_group_population_code_coding_tenant_id'), 'measure_group_population_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_group_population_code_coding_updated_at'), 'measure_group_population_code_coding', ['updated_at'], unique=False)
    op.create_table('measure_group_stratifier_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_group_stratifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_group_stratifier_id'], ['measure_group_stratifier.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_group_stratifier_code_coding_created_at'), 'measure_group_stratifier_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_code_coding_measure_group_stratifier_id'), 'measure_group_stratifier_code_coding', ['measure_group_stratifier_id'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_code_coding_tenant_id'), 'measure_group_stratifier_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_code_coding_updated_at'), 'measure_group_stratifier_code_coding', ['updated_at'], unique=False)
    op.create_table('measure_group_stratifier_component',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_group_stratifier_id', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('criteria_description', sa.String(), nullable=True),
    sa.Column('criteria_name', sa.String(), nullable=True),
    sa.Column('criteria_language', sa.String(), nullable=True),
    sa.Column('criteria_expression', sa.Text(), nullable=True),
    sa.Column('criteria_reference', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_group_stratifier_id'], ['measure_group_stratifier.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_group_stratifier_component_created_at'), 'measure_group_stratifier_component', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_component_measure_group_stratifier_id'), 'measure_group_stratifier_component', ['measure_group_stratifier_id'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_component_tenant_id'), 'measure_group_stratifier_component', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_component_updated_at'), 'measure_group_stratifier_component', ['updated_at'], unique=False)
    op.create_table('measure_supplemental_data_usage_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_supplemental_data_usage_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_supplemental_data_usage_id'], ['measure_supplemental_data_usage.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_supplemental_data_usage_coding_created_at'), 'measure_supplemental_data_usage_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_usage_coding_measure_supplemental_data_usage_id'), 'measure_supplemental_data_usage_coding', ['measure_supplemental_data_usage_id'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_usage_coding_tenant_id'), 'measure_supplemental_data_usage_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_supplemental_data_usage_coding_updated_at'), 'measure_supplemental_data_usage_coding', ['updated_at'], unique=False)
    op.create_table('measure_group_stratifier_component_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_group_stratifier_component_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_group_stratifier_component_id'], ['measure_group_stratifier_component.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_group_stratifier_component_code_coding_created_at'), 'measure_group_stratifier_component_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_component_code_coding_measure_group_stratifier_component_id'), 'measure_group_stratifier_component_code_coding', ['measure_group_stratifier_component_id'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_component_code_coding_tenant_id'), 'measure_group_stratifier_component_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_group_stratifier_component_code_coding_updated_at'), 'measure_group_stratifier_component_code_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    op.drop_table('measure_group_stratifier_component_code_coding')
    op.drop_table('measure_supplemental_data_usage_coding')
    op.drop_table('measure_group_stratifier_component')
    op.drop_table('measure_group_stratifier_code_coding')
    op.drop_table('measure_group_population_code_coding')
    op.drop_table('measure_use_context_value_coding')
    op.drop_table('measure_type_coding')
    op.drop_table('measure_topic_coding')
    op.drop_table('measure_supplemental_data_usage')
    op.drop_table('measure_supplemental_data_code_coding')
    op.drop_table('measure_jurisdiction_coding')
    op.drop_table('measure_identifier_type_coding')
    op.drop_table('measure_group_stratifier')
    op.drop_table('measure_group_population')
    op.drop_table('measure_group_code_coding')
    op.drop_table('measure_contact_telecom')
    op.drop_table('measure_use_context')
    op.drop_table('measure_type')
    op.drop_table('measure_topic')
    op.drop_table('measure_supplemental_data')
    op.drop_table('measure_subject_coding')
    op.drop_table('measure_scoring_coding')
    op.drop_table('measure_related_artifact')
    op.drop_table('measure_jurisdiction')
    op.drop_table('measure_improvement_notation_coding')
    op.drop_table('measure_identifier')
    op.drop_table('measure_group')
    op.drop_table('measure_contact')
    op.drop_table('measure_composite_scoring_coding')
    op.drop_table('measure')
    op.execute("DROP SEQUENCE IF EXISTS measure_pub_seq")
    op.execute("DROP TYPE IF EXISTS measure_use_context_value_reference_type")
    op.execute("DROP TYPE IF EXISTS measure_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS measure_status")
    op.execute("DROP TYPE IF EXISTS measure_related_artifact_type")
    op.execute("DROP TYPE IF EXISTS measure_quantity_comparator")
    op.execute("DROP TYPE IF EXISTS measure_contact_role")
