"""add_activity_definition_tables

Revision ID: 281676cba0e6
Revises: 21e305b60db9
Create Date: 2026-10-30 22:58:14.162471

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '281676cba0e6'
down_revision: Union[str, None] = '21e305b60db9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ──────────────────────────────────────────────────
    op.execute("CREATE TYPE activity_definition_assigner_reference_type AS ENUM ('Organization')")
    op.execute("CREATE TYPE activity_definition_contact_role AS ENUM ('contact', 'author', 'editor', 'reviewer', 'endorser')")
    op.execute("CREATE TYPE activity_definition_identifier_use AS ENUM ('usual', 'official', 'temp', 'secondary', 'old')")
    op.execute("CREATE TYPE activity_definition_intent AS ENUM ('proposal', 'plan', 'directive', 'order', 'original_order', 'reflex_order', 'filler_order', 'instance_order', 'option')")
    op.execute("CREATE TYPE activity_definition_kind AS ENUM ('Appointment', 'AppointmentResponse', 'CarePlan', 'Claim', 'CommunicationRequest', 'Contract', 'DeviceRequest', 'EnrollmentRequest', 'ImmunizationRecommendation', 'MedicationRequest', 'NutritionOrder', 'ServiceRequest', 'SupplyRequest', 'Task', 'VisionPrescription')")
    op.execute("CREATE TYPE activity_definition_location_reference_type AS ENUM ('Location')")
    op.execute("CREATE TYPE activity_definition_observation_req_reference_type AS ENUM ('ObservationDefinition')")
    op.execute("CREATE TYPE activity_definition_observation_result_req_ref_type AS ENUM ('ObservationDefinition')")
    op.execute("CREATE TYPE activity_definition_participant_type AS ENUM ('patient', 'practitioner', 'related_person', 'device')")
    op.execute("CREATE TYPE activity_definition_priority AS ENUM ('routine', 'urgent', 'asap', 'stat')")
    op.execute("CREATE TYPE activity_definition_product_reference_type AS ENUM ('Medication', 'Substance')")
    op.execute("CREATE TYPE activity_definition_quantity_comparator AS ENUM ('lt', 'le', 'ge', 'gt')")
    op.execute("CREATE TYPE activity_definition_related_artifact_type AS ENUM ('documentation', 'justification', 'citation', 'predecessor', 'successor', 'derived_from', 'depends_on', 'composed_of')")
    op.execute("CREATE TYPE activity_definition_specimen_req_reference_type AS ENUM ('SpecimenDefinition')")
    op.execute("CREATE TYPE activity_definition_status AS ENUM ('draft', 'active', 'retired', 'unknown')")
    op.execute("CREATE TYPE activity_definition_subject_reference_type AS ENUM ('Group')")
    op.execute("CREATE TYPE activity_definition_use_context_value_reference_type AS ENUM ('PlanDefinition', 'ResearchStudy', 'InsurancePlan', 'HealthcareService', 'Group', 'Location', 'Organization')")

    # ── 2. Create Sequence ────────────────────────────────────────────────────
    op.execute('CREATE SEQUENCE IF NOT EXISTS activity_definition_pub_seq START 410000 INCREMENT 1')

    # ── 3. Main Table ─────────────────────────────────────────────────────────
    op.create_table(
        'activity_definition',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_id', sa.BigInteger(), server_default=sa.text("nextval('activity_definition_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('subtitle', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'retired', 'unknown', name='activity_definition_status', create_type=False), nullable=False),
        sa.Column('experimental', sa.Boolean(), nullable=True),
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
        sa.Column('subject_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=True),
        sa.Column('subject_type', postgresql.ENUM('Group', name='activity_definition_subject_reference_type', create_type=False), nullable=True),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('library', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('kind', postgresql.ENUM('Appointment', 'AppointmentResponse', 'CarePlan', 'Claim', 'CommunicationRequest', 'Contract', 'DeviceRequest', 'EnrollmentRequest', 'ImmunizationRecommendation', 'MedicationRequest', 'NutritionOrder', 'ServiceRequest', 'SupplyRequest', 'Task', 'VisionPrescription', name='activity_definition_kind', create_type=False), nullable=True),
        sa.Column('profile', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('intent', postgresql.ENUM('proposal', 'plan', 'directive', 'order', 'original_order', 'reflex_order', 'filler_order', 'instance_order', 'option', name='activity_definition_intent', create_type=False), nullable=True),
        sa.Column('priority', postgresql.ENUM('routine', 'urgent', 'asap', 'stat', name='activity_definition_priority', create_type=False), nullable=True),
        sa.Column('do_not_perform', sa.Boolean(), nullable=True),
        sa.Column('timing_timing', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timing_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timing_age_value', sa.Numeric(), nullable=True),
        sa.Column('timing_age_unit', sa.String(), nullable=True),
        sa.Column('timing_age_system', sa.String(), nullable=True),
        sa.Column('timing_age_code', sa.String(), nullable=True),
        sa.Column('timing_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timing_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timing_range_low_value', sa.Numeric(), nullable=True),
        sa.Column('timing_range_low_unit', sa.String(), nullable=True),
        sa.Column('timing_range_high_value', sa.Numeric(), nullable=True),
        sa.Column('timing_range_high_unit', sa.String(), nullable=True),
        sa.Column('timing_duration_value', sa.Numeric(), nullable=True),
        sa.Column('timing_duration_unit', sa.String(), nullable=True),
        sa.Column('timing_duration_system', sa.String(), nullable=True),
        sa.Column('timing_duration_code', sa.String(), nullable=True),
        sa.Column('location_reference', sa.String(), nullable=True),
        sa.Column('location_type', postgresql.ENUM('Location', name='activity_definition_location_reference_type', create_type=False), nullable=True),
        sa.Column('location_id', sa.BigInteger(), nullable=True),
        sa.Column('location_display', sa.String(), nullable=True),
        sa.Column('product_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('product_reference', sa.String(), nullable=True),
        sa.Column('product_type', postgresql.ENUM('Medication', 'Substance', name='activity_definition_product_reference_type', create_type=False), nullable=True),
        sa.Column('product_id', sa.BigInteger(), nullable=True),
        sa.Column('product_display', sa.String(), nullable=True),
        sa.Column('quantity_value', sa.Numeric(), nullable=True),
        sa.Column('quantity_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='activity_definition_quantity_comparator', create_type=False), nullable=True),
        sa.Column('quantity_unit', sa.String(), nullable=True),
        sa.Column('quantity_system', sa.String(), nullable=True),
        sa.Column('quantity_code', sa.String(), nullable=True),
        sa.Column('transform', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_activity_definition_id'), 'activity_definition', ['activity_definition_id'], unique=True)
    op.create_index(op.f('ix_activity_definition_created_at'), 'activity_definition', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_location_id'), 'activity_definition', ['location_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_name'), 'activity_definition', ['name'], unique=False)
    op.create_index(op.f('ix_activity_definition_product_id'), 'activity_definition', ['product_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_status'), 'activity_definition', ['status'], unique=False)
    op.create_index(op.f('ix_activity_definition_subject_id'), 'activity_definition', ['subject_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_tenant_id'), 'activity_definition', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_updated_at'), 'activity_definition', ['updated_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_url'), 'activity_definition', ['url'], unique=False)
    op.create_index(op.f('ix_activity_definition_user_id'), 'activity_definition', ['user_id'], unique=False)

    # ── 4. Direct Child Tables ────────────────────────────────────────────────
    op.create_table('activity_definition_body_site',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_body_site_activity_definition_pk'), 'activity_definition_body_site', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_body_site_created_at'), 'activity_definition_body_site', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_body_site_tenant_id'), 'activity_definition_body_site', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_body_site_updated_at'), 'activity_definition_body_site', ['updated_at'], unique=False)

    op.create_table('activity_definition_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_code_coding_activity_definition_pk'), 'activity_definition_code_coding', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_code_coding_created_at'), 'activity_definition_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_code_coding_tenant_id'), 'activity_definition_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_code_coding_updated_at'), 'activity_definition_code_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_contact',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('role', postgresql.ENUM('contact', 'author', 'editor', 'reviewer', 'endorser', name='activity_definition_contact_role', create_type=False), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_contact_activity_definition_pk'), 'activity_definition_contact', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_contact_created_at'), 'activity_definition_contact', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_contact_role'), 'activity_definition_contact', ['role'], unique=False)
    op.create_index(op.f('ix_activity_definition_contact_tenant_id'), 'activity_definition_contact', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_contact_updated_at'), 'activity_definition_contact', ['updated_at'], unique=False)

    op.create_table('activity_definition_dosage',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_dosage_activity_definition_pk'), 'activity_definition_dosage', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_created_at'), 'activity_definition_dosage', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_tenant_id'), 'activity_definition_dosage', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_updated_at'), 'activity_definition_dosage', ['updated_at'], unique=False)

    op.create_table('activity_definition_dynamic_value',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('expression_description', sa.String(), nullable=True),
        sa.Column('expression_name', sa.String(), nullable=True),
        sa.Column('expression_language', sa.String(), nullable=True),
        sa.Column('expression_expression', sa.Text(), nullable=True),
        sa.Column('expression_reference', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_dynamic_value_activity_definition_pk'), 'activity_definition_dynamic_value', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_dynamic_value_created_at'), 'activity_definition_dynamic_value', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_dynamic_value_tenant_id'), 'activity_definition_dynamic_value', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_dynamic_value_updated_at'), 'activity_definition_dynamic_value', ['updated_at'], unique=False)

    op.create_table('activity_definition_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='activity_definition_identifier_use', create_type=False), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_reference', sa.String(), nullable=True),
        sa.Column('assigner_type', postgresql.ENUM('Organization', name='activity_definition_assigner_reference_type', create_type=False), nullable=True),
        sa.Column('assigner_id', sa.BigInteger(), nullable=True),
        sa.Column('assigner_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_identifier_activity_definition_pk'), 'activity_definition_identifier', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_identifier_assigner_id'), 'activity_definition_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_identifier_created_at'), 'activity_definition_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_identifier_tenant_id'), 'activity_definition_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_identifier_updated_at'), 'activity_definition_identifier', ['updated_at'], unique=False)

    op.create_table('activity_definition_jurisdiction',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_jurisdiction_activity_definition_pk'), 'activity_definition_jurisdiction', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_jurisdiction_created_at'), 'activity_definition_jurisdiction', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_jurisdiction_tenant_id'), 'activity_definition_jurisdiction', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_jurisdiction_updated_at'), 'activity_definition_jurisdiction', ['updated_at'], unique=False)

    op.create_table('activity_definition_observation_requirement',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('ObservationDefinition', name='activity_definition_observation_req_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_observation_requirement_activity_definition_pk'), 'activity_definition_observation_requirement', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_observation_requirement_created_at'), 'activity_definition_observation_requirement', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_observation_requirement_reference_id'), 'activity_definition_observation_requirement', ['reference_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_observation_requirement_tenant_id'), 'activity_definition_observation_requirement', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_observation_requirement_updated_at'), 'activity_definition_observation_requirement', ['updated_at'], unique=False)

    op.create_table('activity_definition_observation_result_requirement',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('ObservationDefinition', name='activity_definition_observation_result_req_ref_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_observation_result_requirement_activity_definition_pk'), 'activity_definition_observation_result_requirement', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_observation_result_requirement_created_at'), 'activity_definition_observation_result_requirement', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_observation_result_requirement_reference_id'), 'activity_definition_observation_result_requirement', ['reference_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_observation_result_requirement_tenant_id'), 'activity_definition_observation_result_requirement', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_observation_result_requirement_updated_at'), 'activity_definition_observation_result_requirement', ['updated_at'], unique=False)

    op.create_table('activity_definition_participant',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('type', postgresql.ENUM('patient', 'practitioner', 'related_person', 'device', name='activity_definition_participant_type', create_type=False), nullable=False),
        sa.Column('role_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_participant_activity_definition_pk'), 'activity_definition_participant', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_participant_created_at'), 'activity_definition_participant', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_participant_tenant_id'), 'activity_definition_participant', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_participant_updated_at'), 'activity_definition_participant', ['updated_at'], unique=False)

    op.create_table('activity_definition_product_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_product_coding_activity_definition_pk'), 'activity_definition_product_coding', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_product_coding_created_at'), 'activity_definition_product_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_product_coding_tenant_id'), 'activity_definition_product_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_product_coding_updated_at'), 'activity_definition_product_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_related_artifact',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('type', postgresql.ENUM('documentation', 'justification', 'citation', 'predecessor', 'successor', 'derived_from', 'depends_on', 'composed_of', name='activity_definition_related_artifact_type', create_type=False), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_related_artifact_activity_definition_pk'), 'activity_definition_related_artifact', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_related_artifact_created_at'), 'activity_definition_related_artifact', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_related_artifact_tenant_id'), 'activity_definition_related_artifact', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_related_artifact_updated_at'), 'activity_definition_related_artifact', ['updated_at'], unique=False)

    op.create_table('activity_definition_specimen_requirement',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('SpecimenDefinition', name='activity_definition_specimen_req_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_specimen_requirement_activity_definition_pk'), 'activity_definition_specimen_requirement', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_specimen_requirement_created_at'), 'activity_definition_specimen_requirement', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_specimen_requirement_reference_id'), 'activity_definition_specimen_requirement', ['reference_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_specimen_requirement_tenant_id'), 'activity_definition_specimen_requirement', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_specimen_requirement_updated_at'), 'activity_definition_specimen_requirement', ['updated_at'], unique=False)

    op.create_table('activity_definition_subject_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_subject_coding_activity_definition_pk'), 'activity_definition_subject_coding', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_subject_coding_created_at'), 'activity_definition_subject_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_subject_coding_tenant_id'), 'activity_definition_subject_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_subject_coding_updated_at'), 'activity_definition_subject_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_topic',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_topic_activity_definition_pk'), 'activity_definition_topic', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_topic_created_at'), 'activity_definition_topic', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_topic_tenant_id'), 'activity_definition_topic', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_topic_updated_at'), 'activity_definition_topic', ['updated_at'], unique=False)

    op.create_table('activity_definition_use_context',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('value_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('value_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('value_quantity_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='activity_definition_quantity_comparator', create_type=False), nullable=True),
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
        sa.Column('value_reference_type', postgresql.ENUM('PlanDefinition', 'ResearchStudy', 'InsurancePlan', 'HealthcareService', 'Group', 'Location', 'Organization', name='activity_definition_use_context_value_reference_type', create_type=False), nullable=True),
        sa.Column('value_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('value_reference_display', sa.String(), nullable=True),
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
        sa.ForeignKeyConstraint(['activity_definition_pk'], ['activity_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_use_context_activity_definition_pk'), 'activity_definition_use_context', ['activity_definition_pk'], unique=False)
    op.create_index(op.f('ix_activity_definition_use_context_created_at'), 'activity_definition_use_context', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_use_context_tenant_id'), 'activity_definition_use_context', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_use_context_updated_at'), 'activity_definition_use_context', ['updated_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_use_context_value_reference_id'), 'activity_definition_use_context', ['value_reference_id'], unique=False)

    # ── 5. Grandchild Tables ──────────────────────────────────────────────────
    op.create_table('activity_definition_body_site_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_body_site_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_body_site_id'], ['activity_definition_body_site.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_body_site_coding_activity_definition_body_site_id'), 'activity_definition_body_site_coding', ['activity_definition_body_site_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_body_site_coding_created_at'), 'activity_definition_body_site_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_body_site_coding_tenant_id'), 'activity_definition_body_site_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_body_site_coding_updated_at'), 'activity_definition_body_site_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_contact_telecom',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_contact_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_contact_id'], ['activity_definition_contact.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_contact_telecom_activity_definition_contact_id'), 'activity_definition_contact_telecom', ['activity_definition_contact_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_contact_telecom_created_at'), 'activity_definition_contact_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_contact_telecom_tenant_id'), 'activity_definition_contact_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_contact_telecom_updated_at'), 'activity_definition_contact_telecom', ['updated_at'], unique=False)

    op.create_table('activity_definition_dosage_as_needed_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_dosage_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_dosage_id'], ['activity_definition_dosage.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_dosage_as_needed_coding_activity_definition_dosage_id'), 'activity_definition_dosage_as_needed_coding', ['activity_definition_dosage_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_as_needed_coding_created_at'), 'activity_definition_dosage_as_needed_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_as_needed_coding_tenant_id'), 'activity_definition_dosage_as_needed_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_as_needed_coding_updated_at'), 'activity_definition_dosage_as_needed_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_dosage_method_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_dosage_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_dosage_id'], ['activity_definition_dosage.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_dosage_method_coding_activity_definition_dosage_id'), 'activity_definition_dosage_method_coding', ['activity_definition_dosage_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_method_coding_created_at'), 'activity_definition_dosage_method_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_method_coding_tenant_id'), 'activity_definition_dosage_method_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_method_coding_updated_at'), 'activity_definition_dosage_method_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_dosage_route_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_dosage_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_dosage_id'], ['activity_definition_dosage.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_dosage_route_coding_activity_definition_dosage_id'), 'activity_definition_dosage_route_coding', ['activity_definition_dosage_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_route_coding_created_at'), 'activity_definition_dosage_route_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_route_coding_tenant_id'), 'activity_definition_dosage_route_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_route_coding_updated_at'), 'activity_definition_dosage_route_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_dosage_site_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_dosage_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_dosage_id'], ['activity_definition_dosage.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_dosage_site_coding_activity_definition_dosage_id'), 'activity_definition_dosage_site_coding', ['activity_definition_dosage_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_site_coding_created_at'), 'activity_definition_dosage_site_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_site_coding_tenant_id'), 'activity_definition_dosage_site_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_dosage_site_coding_updated_at'), 'activity_definition_dosage_site_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_identifier_type_coding',
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
        sa.ForeignKeyConstraint(['identifier_id'], ['activity_definition_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_identifier_type_coding_created_at'), 'activity_definition_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_identifier_type_coding_identifier_id'), 'activity_definition_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_identifier_type_coding_tenant_id'), 'activity_definition_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_identifier_type_coding_updated_at'), 'activity_definition_identifier_type_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_jurisdiction_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_jurisdiction_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_jurisdiction_id'], ['activity_definition_jurisdiction.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_jurisdiction_coding_activity_definition_jurisdiction_id'), 'activity_definition_jurisdiction_coding', ['activity_definition_jurisdiction_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_jurisdiction_coding_created_at'), 'activity_definition_jurisdiction_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_jurisdiction_coding_tenant_id'), 'activity_definition_jurisdiction_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_jurisdiction_coding_updated_at'), 'activity_definition_jurisdiction_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_participant_role_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_participant_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_participant_id'], ['activity_definition_participant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_participant_role_coding_activity_definition_participant_id'), 'activity_definition_participant_role_coding', ['activity_definition_participant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_participant_role_coding_created_at'), 'activity_definition_participant_role_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_participant_role_coding_tenant_id'), 'activity_definition_participant_role_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_participant_role_coding_updated_at'), 'activity_definition_participant_role_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_topic_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_topic_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_topic_id'], ['activity_definition_topic.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_topic_coding_activity_definition_topic_id'), 'activity_definition_topic_coding', ['activity_definition_topic_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_topic_coding_created_at'), 'activity_definition_topic_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_topic_coding_tenant_id'), 'activity_definition_topic_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_topic_coding_updated_at'), 'activity_definition_topic_coding', ['updated_at'], unique=False)

    op.create_table('activity_definition_use_context_value_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_definition_use_context_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['activity_definition_use_context_id'], ['activity_definition_use_context.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_use_context_value_coding_activity_definition_use_context_id'), 'activity_definition_use_context_value_coding', ['activity_definition_use_context_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_use_context_value_coding_created_at'), 'activity_definition_use_context_value_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_definition_use_context_value_coding_tenant_id'), 'activity_definition_use_context_value_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_use_context_value_coding_updated_at'), 'activity_definition_use_context_value_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop grandchild tables
    op.drop_table('activity_definition_use_context_value_coding')
    op.drop_table('activity_definition_topic_coding')
    op.drop_table('activity_definition_participant_role_coding')
    op.drop_table('activity_definition_jurisdiction_coding')
    op.drop_table('activity_definition_identifier_type_coding')
    op.drop_table('activity_definition_dosage_site_coding')
    op.drop_table('activity_definition_dosage_route_coding')
    op.drop_table('activity_definition_dosage_method_coding')
    op.drop_table('activity_definition_dosage_as_needed_coding')
    op.drop_table('activity_definition_contact_telecom')
    op.drop_table('activity_definition_body_site_coding')

    # Drop child tables
    op.drop_table('activity_definition_use_context')
    op.drop_table('activity_definition_topic')
    op.drop_table('activity_definition_subject_coding')
    op.drop_table('activity_definition_specimen_requirement')
    op.drop_table('activity_definition_related_artifact')
    op.drop_table('activity_definition_product_coding')
    op.drop_table('activity_definition_participant')
    op.drop_table('activity_definition_observation_result_requirement')
    op.drop_table('activity_definition_observation_requirement')
    op.drop_table('activity_definition_jurisdiction')
    op.drop_table('activity_definition_identifier')
    op.drop_table('activity_definition_dynamic_value')
    op.drop_table('activity_definition_dosage')
    op.drop_table('activity_definition_contact')
    op.drop_table('activity_definition_code_coding')
    op.drop_table('activity_definition_body_site')

    # Drop main table
    op.drop_table('activity_definition')

    # Drop sequence
    op.execute('DROP SEQUENCE IF EXISTS activity_definition_pub_seq')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS activity_definition_use_context_value_reference_type')
    op.execute('DROP TYPE IF EXISTS activity_definition_subject_reference_type')
    op.execute('DROP TYPE IF EXISTS activity_definition_status')
    op.execute('DROP TYPE IF EXISTS activity_definition_specimen_req_reference_type')
    op.execute('DROP TYPE IF EXISTS activity_definition_related_artifact_type')
    op.execute('DROP TYPE IF EXISTS activity_definition_quantity_comparator')
    op.execute('DROP TYPE IF EXISTS activity_definition_product_reference_type')
    op.execute('DROP TYPE IF EXISTS activity_definition_priority')
    op.execute('DROP TYPE IF EXISTS activity_definition_participant_type')
    op.execute('DROP TYPE IF EXISTS activity_definition_observation_result_req_ref_type')
    op.execute('DROP TYPE IF EXISTS activity_definition_observation_req_reference_type')
    op.execute('DROP TYPE IF EXISTS activity_definition_location_reference_type')
    op.execute('DROP TYPE IF EXISTS activity_definition_kind')
    op.execute('DROP TYPE IF EXISTS activity_definition_intent')
    op.execute('DROP TYPE IF EXISTS activity_definition_identifier_use')
    op.execute('DROP TYPE IF EXISTS activity_definition_contact_role')
    op.execute('DROP TYPE IF EXISTS activity_definition_assigner_reference_type')
