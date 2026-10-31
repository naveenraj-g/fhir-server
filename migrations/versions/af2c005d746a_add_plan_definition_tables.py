"""add_plan_definition_tables

Revision ID: af2c005d746a
Revises: 281676cba0e6
Create Date: 2026-10-31 00:10:16.407389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'af2c005d746a'
down_revision: Union[str, None] = '281676cba0e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ──────────────────────────────────────────────────
    op.execute("CREATE TYPE plan_definition_status AS ENUM ('draft', 'active', 'retired', 'unknown')")
    op.execute("CREATE TYPE plan_definition_subject_reference_type AS ENUM ('Group')")
    op.execute("CREATE TYPE plan_definition_contact_role AS ENUM ('contact', 'author', 'editor', 'reviewer', 'endorser')")
    op.execute("CREATE TYPE plan_definition_quantity_comparator AS ENUM ('lt', 'le', 'ge', 'gt')")
    op.execute("CREATE TYPE plan_definition_related_artifact_type AS ENUM ('documentation', 'justification', 'citation', 'predecessor', 'successor', 'derived_from', 'depends_on', 'composed_of')")
    op.execute("CREATE TYPE plan_definition_use_context_value_reference_type AS ENUM ('PlanDefinition', 'ResearchStudy', 'InsurancePlan', 'HealthcareService', 'Group', 'Location', 'Organization')")
    op.execute("CREATE TYPE plan_definition_action_priority AS ENUM ('routine', 'urgent', 'asap', 'stat')")
    op.execute("CREATE TYPE plan_definition_action_grouping_behavior AS ENUM ('visual_group', 'logical_group', 'sentence_group')")
    op.execute("CREATE TYPE plan_definition_action_selection_behavior AS ENUM ('any', 'all', 'all_or_none', 'exactly_one', 'at_most_one', 'one_or_more')")
    op.execute("CREATE TYPE plan_definition_action_required_behavior AS ENUM ('must', 'could', 'must_unless_documented')")
    op.execute("CREATE TYPE plan_definition_action_precheck_behavior AS ENUM ('yes', 'no')")
    op.execute("CREATE TYPE plan_definition_action_cardinality_behavior AS ENUM ('single', 'multiple')")
    op.execute("CREATE TYPE plan_definition_action_subject_reference_type AS ENUM ('Group')")

    # ── 2. Create Sequence ────────────────────────────────────────────────────
    op.execute('CREATE SEQUENCE IF NOT EXISTS plan_definition_pub_seq START 420000 INCREMENT 1')

    # ── 3. Main Table ─────────────────────────────────────────────────────────
    op.create_table(
        'plan_definition',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_id', sa.BigInteger(), server_default=sa.text("nextval('plan_definition_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('subtitle', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'retired', 'unknown', name='plan_definition_status', create_type=False), nullable=False),
        sa.Column('experimental', sa.Boolean(), nullable=True),
        sa.Column('subject_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=True),
        sa.Column('subject_type', postgresql.ENUM('Group', name='plan_definition_subject_reference_type', create_type=False), nullable=True),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
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
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_created_at'), 'plan_definition', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_id'), 'plan_definition', ['id'], unique=False)
    op.create_index(op.f('ix_plan_definition_plan_definition_id'), 'plan_definition', ['plan_definition_id'], unique=True)
    op.create_index(op.f('ix_plan_definition_subject_id'), 'plan_definition', ['subject_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_tenant_id'), 'plan_definition', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_updated_at'), 'plan_definition', ['updated_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_user_id'), 'plan_definition', ['user_id'], unique=False)

    # ── 4. Type & Subject Coding Tables ───────────────────────────────────────
    op.create_table(
        'plan_definition_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['plan_definition_pk'], ['plan_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_type_coding_plan_definition_pk'), 'plan_definition_type_coding', ['plan_definition_pk'], unique=False)
    op.create_index(op.f('ix_plan_definition_type_coding_tenant_id'), 'plan_definition_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_type_coding_created_at'), 'plan_definition_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_type_coding_updated_at'), 'plan_definition_type_coding', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_subject_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['plan_definition_pk'], ['plan_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_subject_coding_plan_definition_pk'), 'plan_definition_subject_coding', ['plan_definition_pk'], unique=False)
    op.create_index(op.f('ix_plan_definition_subject_coding_tenant_id'), 'plan_definition_subject_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_subject_coding_created_at'), 'plan_definition_subject_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_subject_coding_updated_at'), 'plan_definition_subject_coding', ['updated_at'], unique=False)

    # ── 5. Identifier Tables ──────────────────────────────────────────────────
    op.create_table(
        'plan_definition_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plan_definition_pk'], ['plan_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_identifier_plan_definition_pk'), 'plan_definition_identifier', ['plan_definition_pk'], unique=False)
    op.create_index(op.f('ix_plan_definition_identifier_assigner_id'), 'plan_definition_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_identifier_tenant_id'), 'plan_definition_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_identifier_created_at'), 'plan_definition_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_identifier_updated_at'), 'plan_definition_identifier', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_identifier_type_coding',
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
        sa.ForeignKeyConstraint(['identifier_id'], ['plan_definition_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_identifier_type_coding_identifier_id'), 'plan_definition_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_identifier_type_coding_tenant_id'), 'plan_definition_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_identifier_type_coding_created_at'), 'plan_definition_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_identifier_type_coding_updated_at'), 'plan_definition_identifier_type_coding', ['updated_at'], unique=False)

    # ── 6. Contact Tables ─────────────────────────────────────────────────────
    op.create_table(
        'plan_definition_contact',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('role', postgresql.ENUM('contact', 'author', 'editor', 'reviewer', 'endorser', name='plan_definition_contact_role', create_type=False), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plan_definition_pk'], ['plan_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_contact_plan_definition_pk'), 'plan_definition_contact', ['plan_definition_pk'], unique=False)
    op.create_index(op.f('ix_plan_definition_contact_role'), 'plan_definition_contact', ['role'], unique=False)
    op.create_index(op.f('ix_plan_definition_contact_tenant_id'), 'plan_definition_contact', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_contact_created_at'), 'plan_definition_contact', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_contact_updated_at'), 'plan_definition_contact', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_contact_telecom',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_contact_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['plan_definition_contact_id'], ['plan_definition_contact.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_contact_telecom_plan_definition_contact_id'), 'plan_definition_contact_telecom', ['plan_definition_contact_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_contact_telecom_tenant_id'), 'plan_definition_contact_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_contact_telecom_created_at'), 'plan_definition_contact_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_contact_telecom_updated_at'), 'plan_definition_contact_telecom', ['updated_at'], unique=False)

    # ── 7. Use Context Tables ─────────────────────────────────────────────────
    op.create_table(
        'plan_definition_use_context',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('value_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('value_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('value_quantity_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='plan_definition_quantity_comparator', create_type=False), nullable=True),
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
        sa.Column('value_reference_type', postgresql.ENUM('PlanDefinition', 'ResearchStudy', 'InsurancePlan', 'HealthcareService', 'Group', 'Location', 'Organization', name='plan_definition_use_context_value_reference_type', create_type=False), nullable=True),
        sa.Column('value_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('value_reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plan_definition_pk'], ['plan_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_use_context_plan_definition_pk'), 'plan_definition_use_context', ['plan_definition_pk'], unique=False)
    op.create_index(op.f('ix_plan_definition_use_context_value_reference_id'), 'plan_definition_use_context', ['value_reference_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_use_context_tenant_id'), 'plan_definition_use_context', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_use_context_created_at'), 'plan_definition_use_context', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_use_context_updated_at'), 'plan_definition_use_context', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_use_context_value_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_use_context_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['plan_definition_use_context_id'], ['plan_definition_use_context.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_use_context_value_coding_plan_definition_use_context_id'), 'plan_definition_use_context_value_coding', ['plan_definition_use_context_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_use_context_value_coding_tenant_id'), 'plan_definition_use_context_value_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_use_context_value_coding_created_at'), 'plan_definition_use_context_value_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_use_context_value_coding_updated_at'), 'plan_definition_use_context_value_coding', ['updated_at'], unique=False)

    # ── 8. Jurisdiction Tables ────────────────────────────────────────────────
    op.create_table(
        'plan_definition_jurisdiction',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plan_definition_pk'], ['plan_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_jurisdiction_plan_definition_pk'), 'plan_definition_jurisdiction', ['plan_definition_pk'], unique=False)
    op.create_index(op.f('ix_plan_definition_jurisdiction_tenant_id'), 'plan_definition_jurisdiction', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_jurisdiction_created_at'), 'plan_definition_jurisdiction', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_jurisdiction_updated_at'), 'plan_definition_jurisdiction', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_jurisdiction_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_jurisdiction_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['plan_definition_jurisdiction_id'], ['plan_definition_jurisdiction.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_jurisdiction_coding_plan_definition_jurisdiction_id'), 'plan_definition_jurisdiction_coding', ['plan_definition_jurisdiction_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_jurisdiction_coding_tenant_id'), 'plan_definition_jurisdiction_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_jurisdiction_coding_created_at'), 'plan_definition_jurisdiction_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_jurisdiction_coding_updated_at'), 'plan_definition_jurisdiction_coding', ['updated_at'], unique=False)

    # ── 9. Topic Tables ───────────────────────────────────────────────────────
    op.create_table(
        'plan_definition_topic',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plan_definition_pk'], ['plan_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_topic_plan_definition_pk'), 'plan_definition_topic', ['plan_definition_pk'], unique=False)
    op.create_index(op.f('ix_plan_definition_topic_tenant_id'), 'plan_definition_topic', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_topic_created_at'), 'plan_definition_topic', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_topic_updated_at'), 'plan_definition_topic', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_topic_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_topic_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['plan_definition_topic_id'], ['plan_definition_topic.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_topic_coding_plan_definition_topic_id'), 'plan_definition_topic_coding', ['plan_definition_topic_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_topic_coding_tenant_id'), 'plan_definition_topic_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_topic_coding_created_at'), 'plan_definition_topic_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_topic_coding_updated_at'), 'plan_definition_topic_coding', ['updated_at'], unique=False)

    # ── 10. Related Artifact Table ────────────────────────────────────────────
    op.create_table(
        'plan_definition_related_artifact',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('type', postgresql.ENUM('documentation', 'justification', 'citation', 'predecessor', 'successor', 'derived_from', 'depends_on', 'composed_of', name='plan_definition_related_artifact_type', create_type=False), nullable=False),
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
        sa.ForeignKeyConstraint(['plan_definition_pk'], ['plan_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_related_artifact_plan_definition_pk'), 'plan_definition_related_artifact', ['plan_definition_pk'], unique=False)
    op.create_index(op.f('ix_plan_definition_related_artifact_tenant_id'), 'plan_definition_related_artifact', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_related_artifact_created_at'), 'plan_definition_related_artifact', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_related_artifact_updated_at'), 'plan_definition_related_artifact', ['updated_at'], unique=False)

    # ── 11. Goal Tables ───────────────────────────────────────────────────────
    op.create_table(
        'plan_definition_goal',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('goal_id', sa.String(), nullable=True),
        sa.Column('category_text', sa.String(), nullable=True),
        sa.Column('description_text', sa.String(), nullable=True),
        sa.Column('priority_text', sa.String(), nullable=True),
        sa.Column('start_text', sa.String(), nullable=True),
        sa.Column('addresses', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('documentation', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('target', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plan_definition_pk'], ['plan_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_goal_plan_definition_pk'), 'plan_definition_goal', ['plan_definition_pk'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_tenant_id'), 'plan_definition_goal', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_created_at'), 'plan_definition_goal', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_updated_at'), 'plan_definition_goal', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_goal_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['goal_id'], ['plan_definition_goal.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_goal_category_coding_goal_id'), 'plan_definition_goal_category_coding', ['goal_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_category_coding_tenant_id'), 'plan_definition_goal_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_category_coding_created_at'), 'plan_definition_goal_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_category_coding_updated_at'), 'plan_definition_goal_category_coding', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_goal_description_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['goal_id'], ['plan_definition_goal.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_goal_description_coding_goal_id'), 'plan_definition_goal_description_coding', ['goal_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_description_coding_tenant_id'), 'plan_definition_goal_description_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_description_coding_created_at'), 'plan_definition_goal_description_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_description_coding_updated_at'), 'plan_definition_goal_description_coding', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_goal_priority_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['goal_id'], ['plan_definition_goal.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_goal_priority_coding_goal_id'), 'plan_definition_goal_priority_coding', ['goal_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_priority_coding_tenant_id'), 'plan_definition_goal_priority_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_priority_coding_created_at'), 'plan_definition_goal_priority_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_priority_coding_updated_at'), 'plan_definition_goal_priority_coding', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_goal_start_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['goal_id'], ['plan_definition_goal.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_goal_start_coding_goal_id'), 'plan_definition_goal_start_coding', ['goal_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_start_coding_tenant_id'), 'plan_definition_goal_start_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_start_coding_created_at'), 'plan_definition_goal_start_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_start_coding_updated_at'), 'plan_definition_goal_start_coding', ['updated_at'], unique=False)

    # ── 12. Action Tables ─────────────────────────────────────────────────────
    op.create_table(
        'plan_definition_action',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('plan_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('parent_action_id', sa.BigInteger(), nullable=True),
        sa.Column('action_id_str', sa.String(), nullable=True),
        sa.Column('prefix', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('text_equivalent', sa.Text(), nullable=True),
        sa.Column('priority', postgresql.ENUM('routine', 'urgent', 'asap', 'stat', name='plan_definition_action_priority', create_type=False), nullable=True),
        sa.Column('code', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reason', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('documentation', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('goal_id', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('subject_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=True),
        sa.Column('subject_type', postgresql.ENUM('Group', name='plan_definition_action_subject_reference_type', create_type=False), nullable=True),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('trigger', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('condition', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('input', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('related_action', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timing_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timing_age', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timing_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timing_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timing_duration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timing_range', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timing_timing', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('participant', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('grouping_behavior', postgresql.ENUM('visual_group', 'logical_group', 'sentence_group', name='plan_definition_action_grouping_behavior', create_type=False), nullable=True),
        sa.Column('selection_behavior', postgresql.ENUM('any', 'all', 'all_or_none', 'exactly_one', 'at_most_one', 'one_or_more', name='plan_definition_action_selection_behavior', create_type=False), nullable=True),
        sa.Column('required_behavior', postgresql.ENUM('must', 'could', 'must_unless_documented', name='plan_definition_action_required_behavior', create_type=False), nullable=True),
        sa.Column('precheck_behavior', postgresql.ENUM('yes', 'no', name='plan_definition_action_precheck_behavior', create_type=False), nullable=True),
        sa.Column('cardinality_behavior', postgresql.ENUM('single', 'multiple', name='plan_definition_action_cardinality_behavior', create_type=False), nullable=True),
        sa.Column('definition_canonical', sa.String(), nullable=True),
        sa.Column('definition_uri', sa.String(), nullable=True),
        sa.Column('transform', sa.String(), nullable=True),
        sa.Column('dynamic_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plan_definition_pk'], ['plan_definition.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_action_id'], ['plan_definition_action.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_action_plan_definition_pk'), 'plan_definition_action', ['plan_definition_pk'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_parent_action_id'), 'plan_definition_action', ['parent_action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_subject_id'), 'plan_definition_action', ['subject_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_tenant_id'), 'plan_definition_action', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_created_at'), 'plan_definition_action', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_updated_at'), 'plan_definition_action', ['updated_at'], unique=False)

    op.create_table(
        'plan_definition_action_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('action_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['action_id'], ['plan_definition_action.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_action_type_coding_action_id'), 'plan_definition_action_type_coding', ['action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_type_coding_tenant_id'), 'plan_definition_action_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_type_coding_created_at'), 'plan_definition_action_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_type_coding_updated_at'), 'plan_definition_action_type_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table('plan_definition_action_type_coding')
    op.drop_table('plan_definition_action')
    op.drop_table('plan_definition_goal_start_coding')
    op.drop_table('plan_definition_goal_priority_coding')
    op.drop_table('plan_definition_goal_description_coding')
    op.drop_table('plan_definition_goal_category_coding')
    op.drop_table('plan_definition_goal')
    op.drop_table('plan_definition_related_artifact')
    op.drop_table('plan_definition_topic_coding')
    op.drop_table('plan_definition_topic')
    op.drop_table('plan_definition_jurisdiction_coding')
    op.drop_table('plan_definition_jurisdiction')
    op.drop_table('plan_definition_use_context_value_coding')
    op.drop_table('plan_definition_use_context')
    op.drop_table('plan_definition_contact_telecom')
    op.drop_table('plan_definition_contact')
    op.drop_table('plan_definition_identifier_type_coding')
    op.drop_table('plan_definition_identifier')
    op.drop_table('plan_definition_subject_coding')
    op.drop_table('plan_definition_type_coding')
    op.drop_table('plan_definition')

    # Drop sequence
    op.execute('DROP SEQUENCE IF EXISTS plan_definition_pub_seq')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS plan_definition_action_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS plan_definition_action_cardinality_behavior")
    op.execute("DROP TYPE IF EXISTS plan_definition_action_precheck_behavior")
    op.execute("DROP TYPE IF EXISTS plan_definition_action_required_behavior")
    op.execute("DROP TYPE IF EXISTS plan_definition_action_selection_behavior")
    op.execute("DROP TYPE IF EXISTS plan_definition_action_grouping_behavior")
    op.execute("DROP TYPE IF EXISTS plan_definition_action_priority")
    op.execute("DROP TYPE IF EXISTS plan_definition_use_context_value_reference_type")
    op.execute("DROP TYPE IF EXISTS plan_definition_related_artifact_type")
    op.execute("DROP TYPE IF EXISTS plan_definition_quantity_comparator")
    op.execute("DROP TYPE IF EXISTS plan_definition_contact_role")
    op.execute("DROP TYPE IF EXISTS plan_definition_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS plan_definition_status")
