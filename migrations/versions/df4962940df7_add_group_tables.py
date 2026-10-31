"""add_group_tables

Revision ID: df4962940df7
Revises: edbf00d68352
Create Date: 2026-10-31 01:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'df4962940df7'
down_revision: Union[str, None] = 'edbf00d68352'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ───────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE group_type AS ENUM (
                'person', 'animal', 'practitioner', 'device', 'medication', 'substance'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE group_managing_entity_reference_type AS ENUM (
                'Organization', 'RelatedPerson', 'Practitioner', 'PractitionerRole'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE group_member_entity_reference_type AS ENUM (
                'Patient', 'Practitioner', 'PractitionerRole', 'Device', 'Medication', 'Substance', 'Group'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE group_identifier_use AS ENUM (
                'usual', 'official', 'temp', 'secondary', 'old'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ── 2. Create Sequence ─────────────────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS group_pub_seq START WITH 430000 INCREMENT BY 1")

    # ── 3. Create Main Table: group ───────────────────────────────────────────
    op.create_table(
        'group',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('group_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('type', postgresql.ENUM('person', 'animal', 'practitioner', 'device', 'medication', 'substance', name='group_type', create_type=False), nullable=False),
        sa.Column('actual', sa.Boolean(), nullable=False),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('managing_entity_reference', sa.String(), nullable=True),
        sa.Column('managing_entity_type', postgresql.ENUM('Organization', 'RelatedPerson', 'Practitioner', 'PractitionerRole', name='group_managing_entity_reference_type', create_type=False), nullable=True),
        sa.Column('managing_entity_id', sa.BigInteger(), nullable=True),
        sa.Column('managing_entity_display', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id')
    )
    op.create_index(op.f('ix_group_group_id'), 'group', ['group_id'], unique=True)
    op.create_index(op.f('ix_group_user_id'), 'group', ['user_id'], unique=False)
    op.create_index(op.f('ix_group_managing_entity_id'), 'group', ['managing_entity_id'], unique=False)
    op.create_index(op.f('ix_group_tenant_id'), 'group', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_group_created_at'), 'group', ['created_at'], unique=False)
    op.create_index(op.f('ix_group_updated_at'), 'group', ['updated_at'], unique=False)

    # ── 4. Create Child Table: group_code_coding ──────────────────────────────
    op.create_table(
        'group_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('group_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['group_pk'], ['group.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_code_coding_group_pk'), 'group_code_coding', ['group_pk'], unique=False)
    op.create_index(op.f('ix_group_code_coding_tenant_id'), 'group_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_group_code_coding_created_at'), 'group_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_group_code_coding_updated_at'), 'group_code_coding', ['updated_at'], unique=False)

    # ── 5. Create Child Table: group_identifier ───────────────────────────────
    op.create_table(
        'group_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('group_pk', sa.BigInteger(), nullable=False),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='group_identifier_use', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['group_pk'], ['group.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_identifier_group_pk'), 'group_identifier', ['group_pk'], unique=False)
    op.create_index(op.f('ix_group_identifier_tenant_id'), 'group_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_group_identifier_created_at'), 'group_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_group_identifier_updated_at'), 'group_identifier', ['updated_at'], unique=False)

    # ── 6. Create Grandchild Table: group_identifier_type_coding ──────────────
    op.create_table(
        'group_identifier_type_coding',
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
        sa.ForeignKeyConstraint(['identifier_id'], ['group_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_identifier_type_coding_identifier_id'), 'group_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_group_identifier_type_coding_tenant_id'), 'group_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_group_identifier_type_coding_created_at'), 'group_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_group_identifier_type_coding_updated_at'), 'group_identifier_type_coding', ['updated_at'], unique=False)

    # ── 7. Create Child Table: group_characteristic ───────────────────────────
    op.create_table(
        'group_characteristic',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('group_pk', sa.BigInteger(), nullable=False),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('exclude', sa.Boolean(), nullable=False, default=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('value_quantity', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('value_range', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('value_reference_reference', sa.String(), nullable=True),
        sa.Column('value_reference_type', sa.String(), nullable=True),
        sa.Column('value_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('value_reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['group_pk'], ['group.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_characteristic_group_pk'), 'group_characteristic', ['group_pk'], unique=False)
    op.create_index(op.f('ix_group_characteristic_tenant_id'), 'group_characteristic', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_group_characteristic_created_at'), 'group_characteristic', ['created_at'], unique=False)
    op.create_index(op.f('ix_group_characteristic_updated_at'), 'group_characteristic', ['updated_at'], unique=False)

    # ── 8. Create Grandchild Table: group_characteristic_code_coding ──────────
    op.create_table(
        'group_characteristic_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('characteristic_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['characteristic_id'], ['group_characteristic.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_characteristic_code_coding_characteristic_id'), 'group_characteristic_code_coding', ['characteristic_id'], unique=False)
    op.create_index(op.f('ix_group_characteristic_code_coding_tenant_id'), 'group_characteristic_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_group_characteristic_code_coding_created_at'), 'group_characteristic_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_group_characteristic_code_coding_updated_at'), 'group_characteristic_code_coding', ['updated_at'], unique=False)

    # ── 9. Create Grandchild Table: group_characteristic_value_coding ─────────
    op.create_table(
        'group_characteristic_value_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('characteristic_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['characteristic_id'], ['group_characteristic.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_characteristic_value_coding_characteristic_id'), 'group_characteristic_value_coding', ['characteristic_id'], unique=False)
    op.create_index(op.f('ix_group_characteristic_value_coding_tenant_id'), 'group_characteristic_value_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_group_characteristic_value_coding_created_at'), 'group_characteristic_value_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_group_characteristic_value_coding_updated_at'), 'group_characteristic_value_coding', ['updated_at'], unique=False)

    # ── 10. Create Child Table: group_member ──────────────────────────────────
    op.create_table(
        'group_member',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('group_pk', sa.BigInteger(), nullable=False),
        sa.Column('entity_reference', sa.String(), nullable=False),
        sa.Column('entity_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'Device', 'Medication', 'Substance', 'Group', name='group_member_entity_reference_type', create_type=False), nullable=True),
        sa.Column('entity_id', sa.BigInteger(), nullable=True),
        sa.Column('entity_display', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inactive', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['group_pk'], ['group.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_member_group_pk'), 'group_member', ['group_pk'], unique=False)
    op.create_index(op.f('ix_group_member_entity_id'), 'group_member', ['entity_id'], unique=False)
    op.create_index(op.f('ix_group_member_tenant_id'), 'group_member', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_group_member_created_at'), 'group_member', ['created_at'], unique=False)
    op.create_index(op.f('ix_group_member_updated_at'), 'group_member', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse FK order
    op.drop_table('group_member')
    op.drop_table('group_characteristic_value_coding')
    op.drop_table('group_characteristic_code_coding')
    op.drop_table('group_characteristic')
    op.drop_table('group_identifier_type_coding')
    op.drop_table('group_identifier')
    op.drop_table('group_code_coding')
    op.drop_table('group')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS group_pub_seq")

    # Drop enum types
    enums_to_drop = [
        'group_member_entity_reference_type',
        'group_managing_entity_reference_type',
        'group_identifier_use',
        'group_type',
    ]
    for enum_name in enums_to_drop:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
