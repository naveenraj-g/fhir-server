"""add_flag_tables

Revision ID: dbf7519d8b31
Revises: 888cf5f065fa
Create Date: 2026-10-31 16:01:38.362762

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dbf7519d8b31'
down_revision: Union[str, None] = '888cf5f065fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ───────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE flag_status AS ENUM ('active', 'inactive', 'entered-in-error');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE flag_subject_reference_type AS ENUM ('Patient', 'Location', 'Group', 'Organization', 'Practitioner', 'PlanDefinition', 'Medication', 'Procedure');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE flag_encounter_reference_type AS ENUM ('Encounter');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE flag_author_reference_type AS ENUM ('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ── 2. Create Public ID Sequence ───────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS flag_pub_seq START WITH 450000 INCREMENT BY 1")

    # ── 3. Create Tables and Indexes ───────────────────────────────────────────
    op.create_table('flag',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('flag_id', sa.BigInteger(), nullable=False),
    sa.Column('status', postgresql.ENUM('active', 'inactive', 'entered-in-error', name='flag_status', create_type=False), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('subject_reference', sa.String(), nullable=False),
    sa.Column('subject_type', postgresql.ENUM('Patient', 'Location', 'Group', 'Organization', 'Practitioner', 'PlanDefinition', 'Medication', 'Procedure', name='flag_subject_reference_type', create_type=False), nullable=False),
    sa.Column('subject_id', sa.BigInteger(), nullable=True),
    sa.Column('subject_display', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('encounter_reference', sa.String(), nullable=True),
    sa.Column('encounter_type', postgresql.ENUM('Encounter', name='flag_encounter_reference_type', create_type=False), nullable=True),
    sa.Column('encounter_id', sa.BigInteger(), nullable=True),
    sa.Column('encounter_display', sa.String(), nullable=True),
    sa.Column('author_reference', sa.String(), nullable=True),
    sa.Column('author_type', postgresql.ENUM('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', name='flag_author_reference_type', create_type=False), nullable=True),
    sa.Column('author_id', sa.BigInteger(), nullable=True),
    sa.Column('author_display', sa.String(), nullable=True),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flag_author_id'), 'flag', ['author_id'], unique=False)
    op.create_index(op.f('ix_flag_created_at'), 'flag', ['created_at'], unique=False)
    op.create_index(op.f('ix_flag_encounter_id'), 'flag', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_flag_flag_id'), 'flag', ['flag_id'], unique=True)
    op.create_index(op.f('ix_flag_subject_id'), 'flag', ['subject_id'], unique=False)
    op.create_index(op.f('ix_flag_tenant_id'), 'flag', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_flag_updated_at'), 'flag', ['updated_at'], unique=False)

    op.create_table('flag_category',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('flag_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['flag_pk'], ['flag.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flag_category_created_at'), 'flag_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_flag_category_flag_pk'), 'flag_category', ['flag_pk'], unique=False)
    op.create_index(op.f('ix_flag_category_tenant_id'), 'flag_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_flag_category_updated_at'), 'flag_category', ['updated_at'], unique=False)

    op.create_table('flag_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('flag_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['flag_pk'], ['flag.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flag_code_coding_created_at'), 'flag_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_flag_code_coding_flag_pk'), 'flag_code_coding', ['flag_pk'], unique=False)
    op.create_index(op.f('ix_flag_code_coding_tenant_id'), 'flag_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_flag_code_coding_updated_at'), 'flag_code_coding', ['updated_at'], unique=False)

    op.create_table('flag_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('flag_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_reference', sa.String(), nullable=True),
    sa.Column('assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
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
    sa.ForeignKeyConstraint(['flag_pk'], ['flag.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flag_identifier_assigner_id'), 'flag_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_flag_identifier_created_at'), 'flag_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_flag_identifier_flag_pk'), 'flag_identifier', ['flag_pk'], unique=False)
    op.create_index(op.f('ix_flag_identifier_tenant_id'), 'flag_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_flag_identifier_updated_at'), 'flag_identifier', ['updated_at'], unique=False)

    op.create_table('flag_category_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('flag_category_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['flag_category_id'], ['flag_category.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flag_category_coding_created_at'), 'flag_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_flag_category_coding_flag_category_id'), 'flag_category_coding', ['flag_category_id'], unique=False)
    op.create_index(op.f('ix_flag_category_coding_tenant_id'), 'flag_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_flag_category_coding_updated_at'), 'flag_category_coding', ['updated_at'], unique=False)

    op.create_table('flag_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('flag_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['flag_identifier_id'], ['flag_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flag_identifier_type_coding_created_at'), 'flag_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_flag_identifier_type_coding_flag_identifier_id'), 'flag_identifier_type_coding', ['flag_identifier_id'], unique=False)
    op.create_index(op.f('ix_flag_identifier_type_coding_tenant_id'), 'flag_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_flag_identifier_type_coding_updated_at'), 'flag_identifier_type_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    op.drop_table('flag_identifier_type_coding')
    op.drop_table('flag_category_coding')
    op.drop_table('flag_identifier')
    op.drop_table('flag_code_coding')
    op.drop_table('flag_category')
    op.drop_table('flag')

    op.execute("DROP SEQUENCE IF EXISTS flag_pub_seq")

    op.execute("DROP TYPE IF EXISTS flag_author_reference_type")
    op.execute("DROP TYPE IF EXISTS flag_encounter_reference_type")
    op.execute("DROP TYPE IF EXISTS flag_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS flag_status")
