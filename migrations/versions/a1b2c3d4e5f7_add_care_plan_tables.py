"""add_care_plan_tables

Revision ID: a1b2c3d4e5f7
Revises: f0a1b2c3d4e5
Create Date: 2026-10-30 18:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'f0a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum types
    op.execute("CREATE TYPE care_plan_status AS ENUM ('draft', 'active', 'on-hold', 'revoked', 'completed', 'entered-in-error', 'unknown')")
    op.execute("CREATE TYPE care_plan_intent AS ENUM ('proposal', 'plan', 'order', 'option')")
    op.execute("CREATE TYPE care_plan_activity_status AS ENUM ('not-started', 'scheduled', 'in-progress', 'on-hold', 'completed', 'cancelled', 'stopped', 'unknown', 'entered-in-error')")
    op.execute("CREATE TYPE care_plan_activity_kind AS ENUM ('Appointment', 'CommunicationRequest', 'DeviceRequest', 'MedicationRequest', 'NutritionOrder', 'Task', 'ServiceRequest', 'VisionPrescription')")
    op.execute("CREATE TYPE care_plan_quantity_comparator AS ENUM ('<', '<=', '>=', '>')")
    op.execute("CREATE TYPE care_plan_subject_reference_type AS ENUM ('Patient', 'Group')")
    op.execute("CREATE TYPE care_plan_encounter_reference_type AS ENUM ('Encounter')")
    op.execute("CREATE TYPE care_plan_author_reference_type AS ENUM ('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Organization', 'CareTeam')")
    op.execute("CREATE TYPE care_plan_contributor_reference_type AS ENUM ('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Organization', 'CareTeam')")
    op.execute("CREATE TYPE care_plan_care_team_reference_type AS ENUM ('CareTeam')")
    op.execute("CREATE TYPE care_plan_addresses_reference_type AS ENUM ('Condition')")
    op.execute("CREATE TYPE care_plan_goal_reference_type AS ENUM ('Goal')")
    op.execute("CREATE TYPE care_plan_based_on_reference_type AS ENUM ('CarePlan', 'ServiceRequest', 'NutritionOrder')")
    op.execute("CREATE TYPE care_plan_replaces_reference_type AS ENUM ('CarePlan')")
    op.execute("CREATE TYPE care_plan_part_of_reference_type AS ENUM ('CarePlan')")
    op.execute("CREATE TYPE care_plan_activity_reference_type AS ENUM ('Appointment', 'CommunicationRequest', 'DeviceRequest', 'MedicationRequest', 'NutritionOrder', 'Task', 'ServiceRequest', 'VisionPrescription', 'RequestGroup')")
    op.execute("CREATE TYPE care_plan_activity_detail_performer_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'Organization', 'RelatedPerson', 'Patient', 'CareTeam', 'HealthcareService', 'Device')")
    op.execute("CREATE TYPE care_plan_activity_detail_reason_reference_type AS ENUM ('Condition', 'Observation', 'DiagnosticReport', 'DocumentReference')")
    op.execute("CREATE TYPE care_plan_location_reference_type AS ENUM ('Location')")
    op.execute("CREATE TYPE care_plan_product_reference_type AS ENUM ('Medication', 'Substance')")

    # Public sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS care_plan_pub_seq START 290000 INCREMENT 1")

    # Main care_plan table
    op.create_table(
        'care_plan',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_id', sa.BigInteger(), server_default=sa.text("nextval('care_plan_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('instantiates_canonical', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('instantiates_uri', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'on-hold', 'revoked', 'completed', 'entered-in-error', 'unknown', name='care_plan_status', create_type=False), nullable=False),
        sa.Column('intent', postgresql.ENUM('proposal', 'plan', 'order', 'option', name='care_plan_intent', create_type=False), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=True),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='care_plan_subject_reference_type', create_type=False), nullable=False),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('encounter_reference', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM('Encounter', name='care_plan_encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.BigInteger(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Organization', 'CareTeam', name='care_plan_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_id', sa.BigInteger(), nullable=True),
        sa.Column('author_display', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('care_plan_id'),
    )
    op.create_index(op.f('ix_care_plan_care_plan_id'), 'care_plan', ['care_plan_id'], unique=True)
    op.create_index(op.f('ix_care_plan_user_id'), 'care_plan', ['user_id'], unique=False)
    op.create_index(op.f('ix_care_plan_tenant_id'), 'care_plan', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_plan_subject_id'), 'care_plan', ['subject_id'], unique=False)
    op.create_index(op.f('ix_care_plan_encounter_id'), 'care_plan', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_care_plan_author_id'), 'care_plan', ['author_id'], unique=False)

    # care_plan_identifier
    op.create_table(
        'care_plan_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_identifier_care_plan_pk'), 'care_plan_identifier', ['care_plan_pk'], unique=False)

    # care_plan_identifier_type_coding
    op.create_table(
        'care_plan_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('identifier_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['identifier_id'], ['care_plan_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_identifier_type_coding_identifier_id'), 'care_plan_identifier_type_coding', ['identifier_id'], unique=False)

    # care_plan_category
    op.create_table(
        'care_plan_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_category_care_plan_pk'), 'care_plan_category', ['care_plan_pk'], unique=False)

    # care_plan_category_coding
    op.create_table(
        'care_plan_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('category_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['care_plan_category.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_category_coding_category_id'), 'care_plan_category_coding', ['category_id'], unique=False)

    # care_plan_based_on
    op.create_table(
        'care_plan_based_on',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('CarePlan', 'ServiceRequest', 'NutritionOrder', name='care_plan_based_on_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_based_on_care_plan_pk'), 'care_plan_based_on', ['care_plan_pk'], unique=False)
    op.create_index(op.f('ix_care_plan_based_on_reference_id'), 'care_plan_based_on', ['reference_id'], unique=False)

    # care_plan_replaces
    op.create_table(
        'care_plan_replaces',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('CarePlan', name='care_plan_replaces_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_replaces_care_plan_pk'), 'care_plan_replaces', ['care_plan_pk'], unique=False)
    op.create_index(op.f('ix_care_plan_replaces_reference_id'), 'care_plan_replaces', ['reference_id'], unique=False)

    # care_plan_part_of
    op.create_table(
        'care_plan_part_of',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('CarePlan', name='care_plan_part_of_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_part_of_care_plan_pk'), 'care_plan_part_of', ['care_plan_pk'], unique=False)
    op.create_index(op.f('ix_care_plan_part_of_reference_id'), 'care_plan_part_of', ['reference_id'], unique=False)

    # care_plan_contributor
    op.create_table(
        'care_plan_contributor',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Organization', 'CareTeam', name='care_plan_contributor_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_contributor_care_plan_pk'), 'care_plan_contributor', ['care_plan_pk'], unique=False)
    op.create_index(op.f('ix_care_plan_contributor_reference_id'), 'care_plan_contributor', ['reference_id'], unique=False)

    # care_plan_care_team
    op.create_table(
        'care_plan_care_team',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('CareTeam', name='care_plan_care_team_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_care_team_care_plan_pk'), 'care_plan_care_team', ['care_plan_pk'], unique=False)
    op.create_index(op.f('ix_care_plan_care_team_reference_id'), 'care_plan_care_team', ['reference_id'], unique=False)

    # care_plan_addresses
    op.create_table(
        'care_plan_addresses',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Condition', name='care_plan_addresses_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_addresses_care_plan_pk'), 'care_plan_addresses', ['care_plan_pk'], unique=False)
    op.create_index(op.f('ix_care_plan_addresses_reference_id'), 'care_plan_addresses', ['reference_id'], unique=False)

    # care_plan_goal
    op.create_table(
        'care_plan_goal',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Goal', name='care_plan_goal_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_goal_care_plan_pk'), 'care_plan_goal', ['care_plan_pk'], unique=False)
    op.create_index(op.f('ix_care_plan_goal_reference_id'), 'care_plan_goal', ['reference_id'], unique=False)

    # care_plan_note
    op.create_table(
        'care_plan_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_reference', sa.String(), nullable=True),
        sa.Column('author_reference_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Organization', 'CareTeam', name='care_plan_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_note_care_plan_pk'), 'care_plan_note', ['care_plan_pk'], unique=False)

    # care_plan_activity
    op.create_table(
        'care_plan_activity',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_plan_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Appointment', 'CommunicationRequest', 'DeviceRequest', 'MedicationRequest', 'NutritionOrder', 'Task', 'ServiceRequest', 'VisionPrescription', 'RequestGroup', name='care_plan_activity_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('detail_kind', postgresql.ENUM('Appointment', 'CommunicationRequest', 'DeviceRequest', 'MedicationRequest', 'NutritionOrder', 'Task', 'ServiceRequest', 'VisionPrescription', name='care_plan_activity_kind', create_type=False), nullable=True),
        sa.Column('detail_instantiates_canonical', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('detail_instantiates_uri', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('detail_code_text', sa.String(), nullable=True),
        sa.Column('detail_status', postgresql.ENUM('not-started', 'scheduled', 'in-progress', 'on-hold', 'completed', 'cancelled', 'stopped', 'unknown', 'entered-in-error', name='care_plan_activity_status', create_type=False), nullable=True),
        sa.Column('detail_status_reason_text', sa.String(), nullable=True),
        sa.Column('detail_do_not_perform', sa.Boolean(), nullable=True),
        sa.Column('detail_scheduled_timing', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('detail_scheduled_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('detail_scheduled_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('detail_scheduled_string', sa.String(), nullable=True),
        sa.Column('detail_location_reference', sa.String(), nullable=True),
        sa.Column('detail_location_type', postgresql.ENUM('Location', name='care_plan_location_reference_type', create_type=False), nullable=True),
        sa.Column('detail_location_id', sa.BigInteger(), nullable=True),
        sa.Column('detail_location_display', sa.String(), nullable=True),
        sa.Column('detail_product_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('detail_product_reference', sa.String(), nullable=True),
        sa.Column('detail_product_type', postgresql.ENUM('Medication', 'Substance', name='care_plan_product_reference_type', create_type=False), nullable=True),
        sa.Column('detail_product_id', sa.BigInteger(), nullable=True),
        sa.Column('detail_product_display', sa.String(), nullable=True),
        sa.Column('detail_daily_amount_value', sa.Numeric(), nullable=True),
        sa.Column('detail_daily_amount_comparator', postgresql.ENUM('<', '<=', '>=', '>', name='care_plan_quantity_comparator', create_type=False), nullable=True),
        sa.Column('detail_daily_amount_unit', sa.String(), nullable=True),
        sa.Column('detail_daily_amount_system', sa.String(), nullable=True),
        sa.Column('detail_daily_amount_code', sa.String(), nullable=True),
        sa.Column('detail_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('detail_quantity_comparator', postgresql.ENUM('<', '<=', '>=', '>', name='care_plan_quantity_comparator', create_type=False), nullable=True),
        sa.Column('detail_quantity_unit', sa.String(), nullable=True),
        sa.Column('detail_quantity_system', sa.String(), nullable=True),
        sa.Column('detail_quantity_code', sa.String(), nullable=True),
        sa.Column('detail_description', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_plan_pk'], ['care_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_care_plan_pk'), 'care_plan_activity', ['care_plan_pk'], unique=False)
    op.create_index(op.f('ix_care_plan_activity_reference_id'), 'care_plan_activity', ['reference_id'], unique=False)
    op.create_index(op.f('ix_care_plan_activity_detail_location_id'), 'care_plan_activity', ['detail_location_id'], unique=False)
    op.create_index(op.f('ix_care_plan_activity_detail_product_id'), 'care_plan_activity', ['detail_product_id'], unique=False)

    # care_plan_activity_outcome_cc
    op.create_table(
        'care_plan_activity_outcome_cc',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_outcome_cc_activity_id'), 'care_plan_activity_outcome_cc', ['activity_id'], unique=False)

    # care_plan_activity_outcome_cc_coding
    op.create_table(
        'care_plan_activity_outcome_cc_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('outcome_cc_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['outcome_cc_id'], ['care_plan_activity_outcome_cc.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_outcome_cc_coding_outcome_cc_id'), 'care_plan_activity_outcome_cc_coding', ['outcome_cc_id'], unique=False)

    # care_plan_activity_outcome_reference
    op.create_table(
        'care_plan_activity_outcome_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_outcome_reference_activity_id'), 'care_plan_activity_outcome_reference', ['activity_id'], unique=False)
    op.create_index(op.f('ix_care_plan_activity_outcome_reference_reference_id'), 'care_plan_activity_outcome_reference', ['reference_id'], unique=False)

    # care_plan_activity_progress
    op.create_table(
        'care_plan_activity_progress',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_reference', sa.String(), nullable=True),
        sa.Column('author_reference_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Organization', 'CareTeam', name='care_plan_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_progress_activity_id'), 'care_plan_activity_progress', ['activity_id'], unique=False)

    # care_plan_activity_detail_code_coding
    op.create_table(
        'care_plan_activity_detail_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_detail_code_coding_activity_id'), 'care_plan_activity_detail_code_coding', ['activity_id'], unique=False)

    # care_plan_activity_detail_reason_code
    op.create_table(
        'care_plan_activity_detail_reason_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_detail_reason_code_activity_id'), 'care_plan_activity_detail_reason_code', ['activity_id'], unique=False)

    # care_plan_activity_detail_reason_code_coding
    op.create_table(
        'care_plan_activity_detail_reason_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('reason_code_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['reason_code_id'], ['care_plan_activity_detail_reason_code.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_detail_reason_code_coding_reason_code_id'), 'care_plan_activity_detail_reason_code_coding', ['reason_code_id'], unique=False)

    # care_plan_activity_detail_reason_reference
    op.create_table(
        'care_plan_activity_detail_reason_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', 'DocumentReference', name='care_plan_activity_detail_reason_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_detail_reason_reference_activity_id'), 'care_plan_activity_detail_reason_reference', ['activity_id'], unique=False)
    op.create_index(op.f('ix_care_plan_activity_detail_reason_reference_reference_id'), 'care_plan_activity_detail_reason_reference', ['reference_id'], unique=False)

    # care_plan_activity_detail_goal
    op.create_table(
        'care_plan_activity_detail_goal',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Goal', name='care_plan_goal_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_detail_goal_activity_id'), 'care_plan_activity_detail_goal', ['activity_id'], unique=False)
    op.create_index(op.f('ix_care_plan_activity_detail_goal_reference_id'), 'care_plan_activity_detail_goal', ['reference_id'], unique=False)

    # care_plan_activity_detail_status_reason_coding
    op.create_table(
        'care_plan_activity_detail_status_reason_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_detail_status_reason_coding_activity_id'), 'care_plan_activity_detail_status_reason_coding', ['activity_id'], unique=False)

    # care_plan_activity_detail_performer
    op.create_table(
        'care_plan_activity_detail_performer',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'RelatedPerson', 'Patient', 'CareTeam', 'HealthcareService', 'Device', name='care_plan_activity_detail_performer_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_detail_performer_activity_id'), 'care_plan_activity_detail_performer', ['activity_id'], unique=False)
    op.create_index(op.f('ix_care_plan_activity_detail_performer_reference_id'), 'care_plan_activity_detail_performer', ['reference_id'], unique=False)

    # care_plan_activity_detail_product_coding
    op.create_table(
        'care_plan_activity_detail_product_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_plan_activity_detail_product_coding_activity_id'), 'care_plan_activity_detail_product_coding', ['activity_id'], unique=False)


def downgrade() -> None:
    op.drop_table('care_plan_activity_detail_product_coding')
    op.drop_table('care_plan_activity_detail_performer')
    op.drop_table('care_plan_activity_detail_status_reason_coding')
    op.drop_table('care_plan_activity_detail_goal')
    op.drop_table('care_plan_activity_detail_reason_reference')
    op.drop_table('care_plan_activity_detail_reason_code_coding')
    op.drop_table('care_plan_activity_detail_reason_code')
    op.drop_table('care_plan_activity_detail_code_coding')
    op.drop_table('care_plan_activity_progress')
    op.drop_table('care_plan_activity_outcome_reference')
    op.drop_table('care_plan_activity_outcome_cc_coding')
    op.drop_table('care_plan_activity_outcome_cc')
    op.drop_table('care_plan_activity')
    op.drop_table('care_plan_note')
    op.drop_table('care_plan_goal')
    op.drop_table('care_plan_addresses')
    op.drop_table('care_plan_care_team')
    op.drop_table('care_plan_contributor')
    op.drop_table('care_plan_part_of')
    op.drop_table('care_plan_replaces')
    op.drop_table('care_plan_based_on')
    op.drop_table('care_plan_category_coding')
    op.drop_table('care_plan_category')
    op.drop_table('care_plan_identifier_type_coding')
    op.drop_table('care_plan_identifier')
    op.drop_table('care_plan')

    op.execute("DROP SEQUENCE IF EXISTS care_plan_pub_seq")
    op.execute("DROP TYPE IF EXISTS care_plan_product_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_location_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_activity_detail_reason_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_activity_detail_performer_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_activity_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_part_of_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_replaces_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_based_on_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_goal_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_addresses_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_care_team_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_contributor_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_author_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_encounter_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS care_plan_quantity_comparator")
    op.execute("DROP TYPE IF EXISTS care_plan_activity_kind")
    op.execute("DROP TYPE IF EXISTS care_plan_activity_status")
    op.execute("DROP TYPE IF EXISTS care_plan_intent")
    op.execute("DROP TYPE IF EXISTS care_plan_status")
