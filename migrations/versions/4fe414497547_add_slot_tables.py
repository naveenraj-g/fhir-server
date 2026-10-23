"""add_slot_tables

Revision ID: 4fe414497547
Revises: fa6ec326bb00
Create Date: 2026-10-23 00:00:00.000000

Slot was deleted from the codebase in the mass resource cleanup, but like
Schedule, its five DB tables were never actually dropped — left behind in
the pre-rework legacy shape (hand-declared `org_id`, a flattened single
`coding_*` per row instead of a real 0..* coding child table, `assigner`
as a bare string, `slot_id` as the containment FK column name,
`appointmentType` flattened to a single coding with no child table at
all). All five tables are confirmed empty (0 rows each), so rather than
writing a long ALTER chain, this migration drops the stale legacy tables
outright and recreates them against the current TenantAuditMixin/
coding-grandchild-table/`<resource>_pk` conventions — functionally a fresh
build, same as Schedule's own migration.

`slot_status`'s enum labels (busy/free/busy_unavailable/busy_tentative/
entered_in_error) already match this resource's own SlotStatus model enum
exactly, so that type is reused as-is (create_type=False, never
dropped/recreated). `slot_pub_seq` is untouched for the same reason as
Schedule's own pub_seq — it has never advanced past its start value.

`slot_schedule_reference_type` (the old, Slot-specific name for "a
Reference whose only allowed target is Schedule") is dropped and replaced
by the new shared `schedule_reference_type` — same global-reference-enum
convention as `organization_reference_type`/`practitioner_reference_type`,
so any future resource that also references Schedule can reuse it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4fe414497547'
down_revision: Union[str, None] = 'fa6ec326bb00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Drop the stale pre-cleanup legacy tables (all confirmed empty) ──────
    op.drop_table('slot_identifier')
    op.drop_table('slot_service_category')
    op.drop_table('slot_service_type')
    op.drop_table('slot_specialty')
    op.drop_table('slot')
    op.execute('DROP TYPE IF EXISTS slot_schedule_reference_type')
    # slot_status and slot_pub_seq are left alone — labels/start value
    # already match what this resource's model needs, see module docstring.

    # ── New shared PG enum type this resource introduces ────────────────────
    op.execute("CREATE TYPE schedule_reference_type AS ENUM ('Schedule')")

    op.create_table(
        'slot',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.BigInteger(), server_default=sa.text("nextval('slot_pub_seq')"), nullable=False),
        sa.Column('schedule_type', postgresql.ENUM('Schedule', name='schedule_reference_type', create_type=False), nullable=False),
        sa.Column('schedule_id', sa.BigInteger(), nullable=False),
        sa.Column('schedule_display', sa.String(), nullable=True),
        sa.Column('schedule_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('schedule_identifier_type_system', sa.String(), nullable=True),
        sa.Column('schedule_identifier_type_version', sa.String(), nullable=True),
        sa.Column('schedule_identifier_type_code', sa.String(), nullable=True),
        sa.Column('schedule_identifier_type_display', sa.String(), nullable=True),
        sa.Column('schedule_identifier_type_text', sa.String(), nullable=True),
        sa.Column('schedule_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('schedule_identifier_system', sa.String(), nullable=True),
        sa.Column('schedule_identifier_value', sa.String(), nullable=True),
        sa.Column('schedule_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('schedule_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', postgresql.ENUM('busy', 'free', 'busy_unavailable', 'busy_tentative', 'entered_in_error', name='slot_status', create_type=False), nullable=False),
        sa.Column('start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('appointment_type_text', sa.String(), nullable=True),
        sa.Column('overbooked', sa.Boolean(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_created_at'), 'slot', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_id'), 'slot', ['id'], unique=False)
    op.create_index(op.f('ix_slot_schedule_id'), 'slot', ['schedule_id'], unique=False)
    op.create_index(op.f('ix_slot_slot_id'), 'slot', ['slot_id'], unique=True)
    op.create_index(op.f('ix_slot_tenant_id'), 'slot', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_updated_at'), 'slot', ['updated_at'], unique=False)

    op.create_table(
        'slot_appointment_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['slot_pk'], ['slot.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_appointment_type_coding_created_at'), 'slot_appointment_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_appointment_type_coding_slot_pk'), 'slot_appointment_type_coding', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_appointment_type_coding_tenant_id'), 'slot_appointment_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_appointment_type_coding_updated_at'), 'slot_appointment_type_coding', ['updated_at'], unique=False)

    op.create_table(
        'slot_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['slot_pk'], ['slot.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('system', 'value', name='uq_slot_identifier_system_value'),
    )
    op.create_index(op.f('ix_slot_identifier_assigner_id'), 'slot_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_slot_identifier_created_at'), 'slot_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_identifier_slot_pk'), 'slot_identifier', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_identifier_tenant_id'), 'slot_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_identifier_updated_at'), 'slot_identifier', ['updated_at'], unique=False)

    op.create_table(
        'slot_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['slot_identifier_id'], ['slot_identifier.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_identifier_type_coding_created_at'), 'slot_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_identifier_type_coding_slot_identifier_id'), 'slot_identifier_type_coding', ['slot_identifier_id'], unique=False)
    op.create_index(op.f('ix_slot_identifier_type_coding_tenant_id'), 'slot_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_identifier_type_coding_updated_at'), 'slot_identifier_type_coding', ['updated_at'], unique=False)

    op.create_table(
        'slot_service_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['slot_pk'], ['slot.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_service_category_created_at'), 'slot_service_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_service_category_slot_pk'), 'slot_service_category', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_service_category_tenant_id'), 'slot_service_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_service_category_updated_at'), 'slot_service_category', ['updated_at'], unique=False)

    op.create_table(
        'slot_service_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_service_category_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['slot_service_category_id'], ['slot_service_category.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_service_category_coding_created_at'), 'slot_service_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_service_category_coding_slot_service_category_id'), 'slot_service_category_coding', ['slot_service_category_id'], unique=False)
    op.create_index(op.f('ix_slot_service_category_coding_tenant_id'), 'slot_service_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_service_category_coding_updated_at'), 'slot_service_category_coding', ['updated_at'], unique=False)

    op.create_table(
        'slot_service_type',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['slot_pk'], ['slot.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_service_type_created_at'), 'slot_service_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_service_type_slot_pk'), 'slot_service_type', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_service_type_tenant_id'), 'slot_service_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_service_type_updated_at'), 'slot_service_type', ['updated_at'], unique=False)

    op.create_table(
        'slot_service_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_service_type_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['slot_service_type_id'], ['slot_service_type.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_service_type_coding_created_at'), 'slot_service_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_service_type_coding_slot_service_type_id'), 'slot_service_type_coding', ['slot_service_type_id'], unique=False)
    op.create_index(op.f('ix_slot_service_type_coding_tenant_id'), 'slot_service_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_service_type_coding_updated_at'), 'slot_service_type_coding', ['updated_at'], unique=False)

    op.create_table(
        'slot_specialty',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['slot_pk'], ['slot.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_specialty_created_at'), 'slot_specialty', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_specialty_slot_pk'), 'slot_specialty', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_specialty_tenant_id'), 'slot_specialty', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_specialty_updated_at'), 'slot_specialty', ['updated_at'], unique=False)

    op.create_table(
        'slot_specialty_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_specialty_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['slot_specialty_id'], ['slot_specialty.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_specialty_coding_created_at'), 'slot_specialty_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_specialty_coding_slot_specialty_id'), 'slot_specialty_coding', ['slot_specialty_id'], unique=False)
    op.create_index(op.f('ix_slot_specialty_coding_tenant_id'), 'slot_specialty_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_specialty_coding_updated_at'), 'slot_specialty_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_slot_specialty_coding_updated_at'), table_name='slot_specialty_coding')
    op.drop_index(op.f('ix_slot_specialty_coding_tenant_id'), table_name='slot_specialty_coding')
    op.drop_index(op.f('ix_slot_specialty_coding_slot_specialty_id'), table_name='slot_specialty_coding')
    op.drop_index(op.f('ix_slot_specialty_coding_created_at'), table_name='slot_specialty_coding')
    op.drop_table('slot_specialty_coding')

    op.drop_index(op.f('ix_slot_specialty_updated_at'), table_name='slot_specialty')
    op.drop_index(op.f('ix_slot_specialty_tenant_id'), table_name='slot_specialty')
    op.drop_index(op.f('ix_slot_specialty_slot_pk'), table_name='slot_specialty')
    op.drop_index(op.f('ix_slot_specialty_created_at'), table_name='slot_specialty')
    op.drop_table('slot_specialty')

    op.drop_index(op.f('ix_slot_service_type_coding_updated_at'), table_name='slot_service_type_coding')
    op.drop_index(op.f('ix_slot_service_type_coding_tenant_id'), table_name='slot_service_type_coding')
    op.drop_index(op.f('ix_slot_service_type_coding_slot_service_type_id'), table_name='slot_service_type_coding')
    op.drop_index(op.f('ix_slot_service_type_coding_created_at'), table_name='slot_service_type_coding')
    op.drop_table('slot_service_type_coding')

    op.drop_index(op.f('ix_slot_service_type_updated_at'), table_name='slot_service_type')
    op.drop_index(op.f('ix_slot_service_type_tenant_id'), table_name='slot_service_type')
    op.drop_index(op.f('ix_slot_service_type_slot_pk'), table_name='slot_service_type')
    op.drop_index(op.f('ix_slot_service_type_created_at'), table_name='slot_service_type')
    op.drop_table('slot_service_type')

    op.drop_index(op.f('ix_slot_service_category_coding_updated_at'), table_name='slot_service_category_coding')
    op.drop_index(op.f('ix_slot_service_category_coding_tenant_id'), table_name='slot_service_category_coding')
    op.drop_index(op.f('ix_slot_service_category_coding_slot_service_category_id'), table_name='slot_service_category_coding')
    op.drop_index(op.f('ix_slot_service_category_coding_created_at'), table_name='slot_service_category_coding')
    op.drop_table('slot_service_category_coding')

    op.drop_index(op.f('ix_slot_service_category_updated_at'), table_name='slot_service_category')
    op.drop_index(op.f('ix_slot_service_category_tenant_id'), table_name='slot_service_category')
    op.drop_index(op.f('ix_slot_service_category_slot_pk'), table_name='slot_service_category')
    op.drop_index(op.f('ix_slot_service_category_created_at'), table_name='slot_service_category')
    op.drop_table('slot_service_category')

    op.drop_index(op.f('ix_slot_identifier_type_coding_updated_at'), table_name='slot_identifier_type_coding')
    op.drop_index(op.f('ix_slot_identifier_type_coding_tenant_id'), table_name='slot_identifier_type_coding')
    op.drop_index(op.f('ix_slot_identifier_type_coding_slot_identifier_id'), table_name='slot_identifier_type_coding')
    op.drop_index(op.f('ix_slot_identifier_type_coding_created_at'), table_name='slot_identifier_type_coding')
    op.drop_table('slot_identifier_type_coding')

    op.drop_index(op.f('ix_slot_identifier_updated_at'), table_name='slot_identifier')
    op.drop_index(op.f('ix_slot_identifier_tenant_id'), table_name='slot_identifier')
    op.drop_index(op.f('ix_slot_identifier_slot_pk'), table_name='slot_identifier')
    op.drop_index(op.f('ix_slot_identifier_created_at'), table_name='slot_identifier')
    op.drop_index(op.f('ix_slot_identifier_assigner_id'), table_name='slot_identifier')
    op.drop_table('slot_identifier')

    op.drop_index(op.f('ix_slot_appointment_type_coding_updated_at'), table_name='slot_appointment_type_coding')
    op.drop_index(op.f('ix_slot_appointment_type_coding_tenant_id'), table_name='slot_appointment_type_coding')
    op.drop_index(op.f('ix_slot_appointment_type_coding_slot_pk'), table_name='slot_appointment_type_coding')
    op.drop_index(op.f('ix_slot_appointment_type_coding_created_at'), table_name='slot_appointment_type_coding')
    op.drop_table('slot_appointment_type_coding')

    op.drop_index(op.f('ix_slot_updated_at'), table_name='slot')
    op.drop_index(op.f('ix_slot_tenant_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_slot_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_schedule_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_created_at'), table_name='slot')
    op.drop_table('slot')

    op.execute('DROP TYPE IF EXISTS schedule_reference_type')

    # Recreate the stale legacy shape this migration's upgrade() dropped,
    # so a downgrade leaves the DB exactly as it found it.
    op.execute("CREATE TYPE slot_schedule_reference_type AS ENUM ('Schedule')")
    op.create_table(
        'slot',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.BigInteger(), server_default=sa.text("nextval('slot_pub_seq')"), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('schedule_type', postgresql.ENUM('Schedule', name='slot_schedule_reference_type', create_type=False), nullable=False),
        sa.Column('schedule_display', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('busy', 'free', 'busy_unavailable', 'busy_tentative', 'entered_in_error', name='slot_status', create_type=False), nullable=False),
        sa.Column('start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('appointment_type_system', sa.String(), nullable=True),
        sa.Column('appointment_type_code', sa.String(), nullable=True),
        sa.Column('appointment_type_display', sa.String(), nullable=True),
        sa.Column('appointment_type_text', sa.String(), nullable=True),
        sa.Column('appointment_type_version', sa.String(), nullable=True),
        sa.Column('appointment_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('overbooked', sa.Boolean(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('schedule_id', sa.BigInteger(), nullable=False),
        sa.Column('schedule_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('schedule_identifier_type_system', sa.String(), nullable=True),
        sa.Column('schedule_identifier_type_version', sa.String(), nullable=True),
        sa.Column('schedule_identifier_type_code', sa.String(), nullable=True),
        sa.Column('schedule_identifier_type_display', sa.String(), nullable=True),
        sa.Column('schedule_identifier_type_text', sa.String(), nullable=True),
        sa.Column('schedule_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('schedule_identifier_system', sa.String(), nullable=True),
        sa.Column('schedule_identifier_value', sa.String(), nullable=True),
        sa.Column('schedule_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('schedule_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'slot_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.BigInteger(), nullable=False),
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
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['slot_id'], ['slot.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('system', 'value', name='uq_slot_identifier_system_value'),
    )
    op.create_table(
        'slot_service_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['slot_id'], ['slot.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'slot_service_type',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['slot_id'], ['slot.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'slot_specialty',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['slot_id'], ['slot.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
