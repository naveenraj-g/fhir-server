"""add_schedule_tables

Revision ID: fa6ec326bb00
Revises: dc95264fa0a9
Create Date: 2026-10-23 00:00:00.000000

Schedule was deleted from the codebase in the mass resource cleanup (see
CLAUDE.md / configs/config.yaml's `routes.enabled` comment), but unlike
PractitionerRole, its six DB tables were never actually dropped — they were
left behind in the pre-rework legacy shape (hand-declared `org_id`, a
flattened single `coding_*`/`type_*` per row instead of a real 0..* coding
child table, `assigner` as a bare string, `schedule_id` as the containment
FK column name). All six tables are empty (confirmed: 0 rows each) and the
`schedule_pub_seq` sequence has never advanced past its start value, so
rather than writing a long ALTER chain, this migration drops the stale
legacy tables/enum outright and recreates them against the current
TenantAuditMixin/coding-grandchild-table/`<resource>_pk` conventions —
functionally a fresh build, same as every other reworked resource.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fa6ec326bb00'
down_revision: Union[str, None] = 'dc95264fa0a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Drop the stale pre-cleanup legacy tables (all confirmed empty) ──────
    op.drop_table('schedule_actor')
    op.drop_table('schedule_identifier')
    op.drop_table('schedule_service_category')
    op.drop_table('schedule_service_type')
    op.drop_table('schedule_specialty')
    op.drop_table('schedule')
    op.execute('DROP TYPE IF EXISTS schedule_actor_reference_type')
    # schedule_pub_seq is left alone — IF NOT EXISTS below is a no-op; it has
    # never advanced past 200000 so there's no gap to worry about.

    # ── New PG enum type this resource introduces ───────────────────────────
    op.execute(
        "CREATE TYPE schedule_actor_reference_type AS ENUM "
        "('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', "
        "'Device', 'HealthcareService', 'Location')"
    )
    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS schedule_pub_seq START 200000 INCREMENT 1"
    )

    op.create_table(
        'schedule',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.BigInteger(), server_default=sa.text("nextval('schedule_pub_seq')"), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('planning_horizon_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planning_horizon_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_created_at'), 'schedule', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_id'), 'schedule', ['id'], unique=False)
    op.create_index(op.f('ix_schedule_schedule_id'), 'schedule', ['schedule_id'], unique=True)
    op.create_index(op.f('ix_schedule_tenant_id'), 'schedule', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_updated_at'), 'schedule', ['updated_at'], unique=False)

    op.create_table(
        'schedule_actor',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Device', 'HealthcareService', 'Location', name='schedule_actor_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['schedule_pk'], ['schedule.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('schedule_pk', 'reference_type', 'reference_id', name='uq_schedule_actor_reference'),
    )
    op.create_index(op.f('ix_schedule_actor_created_at'), 'schedule_actor', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_actor_reference_id'), 'schedule_actor', ['reference_id'], unique=False)
    op.create_index(op.f('ix_schedule_actor_schedule_pk'), 'schedule_actor', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_actor_tenant_id'), 'schedule_actor', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_actor_updated_at'), 'schedule_actor', ['updated_at'], unique=False)

    op.create_table(
        'schedule_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_pk', sa.BigInteger(), nullable=False),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('assigner_id', sa.BigInteger(), nullable=True),
        sa.Column('assigner_display', sa.String(), nullable=True),
        sa.Column('assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('assigner_identifier_type_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_version', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_code', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_display', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['schedule_pk'], ['schedule.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('system', 'value', name='uq_schedule_identifier_system_value'),
    )
    op.create_index(op.f('ix_schedule_identifier_assigner_id'), 'schedule_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_created_at'), 'schedule_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_schedule_pk'), 'schedule_identifier', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_tenant_id'), 'schedule_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_updated_at'), 'schedule_identifier', ['updated_at'], unique=False)

    op.create_table(
        'schedule_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['schedule_identifier_id'], ['schedule_identifier.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_identifier_type_coding_created_at'), 'schedule_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_type_coding_schedule_identifier_id'), 'schedule_identifier_type_coding', ['schedule_identifier_id'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_type_coding_tenant_id'), 'schedule_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_type_coding_updated_at'), 'schedule_identifier_type_coding', ['updated_at'], unique=False)

    op.create_table(
        'schedule_service_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['schedule_pk'], ['schedule.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_service_category_created_at'), 'schedule_service_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_schedule_pk'), 'schedule_service_category', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_tenant_id'), 'schedule_service_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_updated_at'), 'schedule_service_category', ['updated_at'], unique=False)

    op.create_table(
        'schedule_service_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_service_category_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['schedule_service_category_id'], ['schedule_service_category.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_service_category_coding_created_at'), 'schedule_service_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_coding_schedule_service_category_id'), 'schedule_service_category_coding', ['schedule_service_category_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_coding_tenant_id'), 'schedule_service_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_coding_updated_at'), 'schedule_service_category_coding', ['updated_at'], unique=False)

    op.create_table(
        'schedule_service_type',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['schedule_pk'], ['schedule.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_service_type_created_at'), 'schedule_service_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_schedule_pk'), 'schedule_service_type', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_tenant_id'), 'schedule_service_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_updated_at'), 'schedule_service_type', ['updated_at'], unique=False)

    op.create_table(
        'schedule_service_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_service_type_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['schedule_service_type_id'], ['schedule_service_type.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_service_type_coding_created_at'), 'schedule_service_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_coding_schedule_service_type_id'), 'schedule_service_type_coding', ['schedule_service_type_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_coding_tenant_id'), 'schedule_service_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_coding_updated_at'), 'schedule_service_type_coding', ['updated_at'], unique=False)

    op.create_table(
        'schedule_specialty',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['schedule_pk'], ['schedule.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_specialty_created_at'), 'schedule_specialty', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_schedule_pk'), 'schedule_specialty', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_tenant_id'), 'schedule_specialty', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_updated_at'), 'schedule_specialty', ['updated_at'], unique=False)

    op.create_table(
        'schedule_specialty_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_specialty_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['schedule_specialty_id'], ['schedule_specialty.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_specialty_coding_created_at'), 'schedule_specialty_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_coding_schedule_specialty_id'), 'schedule_specialty_coding', ['schedule_specialty_id'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_coding_tenant_id'), 'schedule_specialty_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_coding_updated_at'), 'schedule_specialty_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_schedule_specialty_coding_updated_at'), table_name='schedule_specialty_coding')
    op.drop_index(op.f('ix_schedule_specialty_coding_tenant_id'), table_name='schedule_specialty_coding')
    op.drop_index(op.f('ix_schedule_specialty_coding_schedule_specialty_id'), table_name='schedule_specialty_coding')
    op.drop_index(op.f('ix_schedule_specialty_coding_created_at'), table_name='schedule_specialty_coding')
    op.drop_table('schedule_specialty_coding')

    op.drop_index(op.f('ix_schedule_specialty_updated_at'), table_name='schedule_specialty')
    op.drop_index(op.f('ix_schedule_specialty_tenant_id'), table_name='schedule_specialty')
    op.drop_index(op.f('ix_schedule_specialty_schedule_pk'), table_name='schedule_specialty')
    op.drop_index(op.f('ix_schedule_specialty_created_at'), table_name='schedule_specialty')
    op.drop_table('schedule_specialty')

    op.drop_index(op.f('ix_schedule_service_type_coding_updated_at'), table_name='schedule_service_type_coding')
    op.drop_index(op.f('ix_schedule_service_type_coding_tenant_id'), table_name='schedule_service_type_coding')
    op.drop_index(op.f('ix_schedule_service_type_coding_schedule_service_type_id'), table_name='schedule_service_type_coding')
    op.drop_index(op.f('ix_schedule_service_type_coding_created_at'), table_name='schedule_service_type_coding')
    op.drop_table('schedule_service_type_coding')

    op.drop_index(op.f('ix_schedule_service_type_updated_at'), table_name='schedule_service_type')
    op.drop_index(op.f('ix_schedule_service_type_tenant_id'), table_name='schedule_service_type')
    op.drop_index(op.f('ix_schedule_service_type_schedule_pk'), table_name='schedule_service_type')
    op.drop_index(op.f('ix_schedule_service_type_created_at'), table_name='schedule_service_type')
    op.drop_table('schedule_service_type')

    op.drop_index(op.f('ix_schedule_service_category_coding_updated_at'), table_name='schedule_service_category_coding')
    op.drop_index(op.f('ix_schedule_service_category_coding_tenant_id'), table_name='schedule_service_category_coding')
    op.drop_index(op.f('ix_schedule_service_category_coding_schedule_service_category_id'), table_name='schedule_service_category_coding')
    op.drop_index(op.f('ix_schedule_service_category_coding_created_at'), table_name='schedule_service_category_coding')
    op.drop_table('schedule_service_category_coding')

    op.drop_index(op.f('ix_schedule_service_category_updated_at'), table_name='schedule_service_category')
    op.drop_index(op.f('ix_schedule_service_category_tenant_id'), table_name='schedule_service_category')
    op.drop_index(op.f('ix_schedule_service_category_schedule_pk'), table_name='schedule_service_category')
    op.drop_index(op.f('ix_schedule_service_category_created_at'), table_name='schedule_service_category')
    op.drop_table('schedule_service_category')

    op.drop_index(op.f('ix_schedule_identifier_type_coding_updated_at'), table_name='schedule_identifier_type_coding')
    op.drop_index(op.f('ix_schedule_identifier_type_coding_tenant_id'), table_name='schedule_identifier_type_coding')
    op.drop_index(op.f('ix_schedule_identifier_type_coding_schedule_identifier_id'), table_name='schedule_identifier_type_coding')
    op.drop_index(op.f('ix_schedule_identifier_type_coding_created_at'), table_name='schedule_identifier_type_coding')
    op.drop_table('schedule_identifier_type_coding')

    op.drop_index(op.f('ix_schedule_identifier_updated_at'), table_name='schedule_identifier')
    op.drop_index(op.f('ix_schedule_identifier_tenant_id'), table_name='schedule_identifier')
    op.drop_index(op.f('ix_schedule_identifier_schedule_pk'), table_name='schedule_identifier')
    op.drop_index(op.f('ix_schedule_identifier_created_at'), table_name='schedule_identifier')
    op.drop_index(op.f('ix_schedule_identifier_assigner_id'), table_name='schedule_identifier')
    op.drop_table('schedule_identifier')

    op.drop_index(op.f('ix_schedule_actor_updated_at'), table_name='schedule_actor')
    op.drop_index(op.f('ix_schedule_actor_tenant_id'), table_name='schedule_actor')
    op.drop_index(op.f('ix_schedule_actor_schedule_pk'), table_name='schedule_actor')
    op.drop_index(op.f('ix_schedule_actor_reference_id'), table_name='schedule_actor')
    op.drop_index(op.f('ix_schedule_actor_created_at'), table_name='schedule_actor')
    op.drop_table('schedule_actor')

    op.drop_index(op.f('ix_schedule_updated_at'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_tenant_id'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_schedule_id'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_id'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_created_at'), table_name='schedule')
    op.drop_table('schedule')

    op.execute('DROP TYPE IF EXISTS schedule_actor_reference_type')

    # Recreate the stale legacy shape this migration's upgrade() dropped,
    # so a downgrade leaves the DB exactly as it found it.
    op.execute(
        "CREATE TYPE schedule_actor_reference_type AS ENUM "
        "('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', "
        "'Device', 'HealthcareService', 'Location')"
    )
    op.create_table(
        'schedule',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.BigInteger(), server_default=sa.text("nextval('schedule_pub_seq')"), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('planning_horizon_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planning_horizon_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'schedule_actor',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.BigInteger(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('reference_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Device', 'HealthcareService', 'Location', name='schedule_actor_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('schedule_id', 'reference_type', 'reference_id', name='uq_schedule_actor_reference'),
    )
    op.create_table(
        'schedule_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.BigInteger(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('system', 'value', name='uq_schedule_identifier_system_value'),
    )
    op.create_table(
        'schedule_service_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.BigInteger(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('coding_version', sa.String(), nullable=True),
        sa.Column('coding_user_selected', sa.Boolean(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'schedule_service_type',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.BigInteger(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('coding_version', sa.String(), nullable=True),
        sa.Column('coding_user_selected', sa.Boolean(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'schedule_specialty',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.BigInteger(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('coding_version', sa.String(), nullable=True),
        sa.Column('coding_user_selected', sa.Boolean(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
