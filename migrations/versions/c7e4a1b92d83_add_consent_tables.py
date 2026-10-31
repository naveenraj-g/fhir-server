"""add_consent_tables

Revision ID: c7e4a1b92d83
Revises: df4962940df7
Create Date: 2026-10-31 09:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c7e4a1b92d83'
down_revision: Union[str, None] = 'df4962940df7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ───────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_status AS ENUM (
                'draft', 'proposed', 'active', 'rejected', 'inactive', 'entered-in-error'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_patient_reference_type AS ENUM ('Patient');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_performer_reference_type AS ENUM (
                'Organization', 'Patient', 'Practitioner', 'RelatedPerson', 'PractitionerRole'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_source_reference_type AS ENUM (
                'Consent', 'DocumentReference', 'Contract', 'QuestionnaireResponse'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_verified_with_reference_type AS ENUM ('Patient', 'RelatedPerson');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_provision_type AS ENUM ('deny', 'permit');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_provision_actor_reference_type AS ENUM (
                'Device', 'Group', 'CareTeam', 'Organization', 'Patient', 'Practitioner', 'RelatedPerson', 'PractitionerRole'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_data_meaning AS ENUM (
                'instance', 'related', 'dependents', 'authoredby'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_identifier_use AS ENUM (
                'usual', 'official', 'temp', 'secondary', 'old'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ── 2. Create Sequence ─────────────────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS consent_pub_seq START WITH 440000 INCREMENT BY 1")

    # ── 3. Main Table: consent ────────────────────────────────────────────────
    op.create_table(
        'consent',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('consent_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'proposed', 'active', 'rejected', 'inactive', 'entered-in-error', name='consent_status', create_type=False), nullable=False),
        sa.Column('scope_text', sa.String(), nullable=True),
        sa.Column('patient_reference', sa.String(), nullable=True),
        sa.Column('patient_type', postgresql.ENUM('Patient', name='consent_patient_reference_type', create_type=False), nullable=True),
        sa.Column('patient_id', sa.BigInteger(), nullable=True),
        sa.Column('patient_display', sa.String(), nullable=True),
        sa.Column('date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_reference_reference', sa.String(), nullable=True),
        sa.Column('source_reference_type', postgresql.ENUM('Consent', 'DocumentReference', 'Contract', 'QuestionnaireResponse', name='consent_source_reference_type', create_type=False), nullable=True),
        sa.Column('source_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('source_reference_display', sa.String(), nullable=True),
        sa.Column('source_attachment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('policy_rule_text', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('consent_id')
    )
    op.create_index(op.f('ix_consent_consent_id'), 'consent', ['consent_id'], unique=True)
    op.create_index(op.f('ix_consent_user_id'), 'consent', ['user_id'], unique=False)
    op.create_index(op.f('ix_consent_patient_id'), 'consent', ['patient_id'], unique=False)
    op.create_index(op.f('ix_consent_tenant_id'), 'consent', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_created_at'), 'consent', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_updated_at'), 'consent', ['updated_at'], unique=False)

    # ── 4. consent_identifier ─────────────────────────────────────────────────
    op.create_table(
        'consent_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('consent_pk', sa.BigInteger(), nullable=False),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='consent_identifier_use', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['consent_pk'], ['consent.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_identifier_consent_pk'), 'consent_identifier', ['consent_pk'], unique=False)
    op.create_index(op.f('ix_consent_identifier_tenant_id'), 'consent_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_identifier_created_at'), 'consent_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_identifier_updated_at'), 'consent_identifier', ['updated_at'], unique=False)

    # ── 5. consent_identifier_type_coding ─────────────────────────────────────
    op.create_table(
        'consent_identifier_type_coding',
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
        sa.ForeignKeyConstraint(['identifier_id'], ['consent_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_identifier_type_coding_identifier_id'), 'consent_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_consent_identifier_type_coding_tenant_id'), 'consent_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_identifier_type_coding_created_at'), 'consent_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_identifier_type_coding_updated_at'), 'consent_identifier_type_coding', ['updated_at'], unique=False)

    # ── 6. consent_scope_coding ───────────────────────────────────────────────
    op.create_table(
        'consent_scope_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('consent_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['consent_pk'], ['consent.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_scope_coding_consent_pk'), 'consent_scope_coding', ['consent_pk'], unique=False)
    op.create_index(op.f('ix_consent_scope_coding_tenant_id'), 'consent_scope_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_scope_coding_created_at'), 'consent_scope_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_scope_coding_updated_at'), 'consent_scope_coding', ['updated_at'], unique=False)

    # ── 7. consent_category ───────────────────────────────────────────────────
    op.create_table(
        'consent_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('consent_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['consent_pk'], ['consent.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_category_consent_pk'), 'consent_category', ['consent_pk'], unique=False)
    op.create_index(op.f('ix_consent_category_tenant_id'), 'consent_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_category_created_at'), 'consent_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_category_updated_at'), 'consent_category', ['updated_at'], unique=False)

    # ── 8. consent_category_coding ───────────────────────────────────────────
    op.create_table(
        'consent_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('category_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['category_id'], ['consent_category.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_category_coding_category_id'), 'consent_category_coding', ['category_id'], unique=False)
    op.create_index(op.f('ix_consent_category_coding_tenant_id'), 'consent_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_category_coding_created_at'), 'consent_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_category_coding_updated_at'), 'consent_category_coding', ['updated_at'], unique=False)

    # ── 9. consent_performer ─────────────────────────────────────────────────
    op.create_table(
        'consent_performer',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('consent_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=False),
        sa.Column('reference_type', postgresql.ENUM('Organization', 'Patient', 'Practitioner', 'RelatedPerson', 'PractitionerRole', name='consent_performer_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['consent_pk'], ['consent.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_performer_consent_pk'), 'consent_performer', ['consent_pk'], unique=False)
    op.create_index(op.f('ix_consent_performer_tenant_id'), 'consent_performer', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_performer_created_at'), 'consent_performer', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_performer_updated_at'), 'consent_performer', ['updated_at'], unique=False)

    # ── 10. consent_organization ─────────────────────────────────────────────
    op.create_table(
        'consent_organization',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('consent_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=False),
        sa.Column('reference_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['consent_pk'], ['consent.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_organization_consent_pk'), 'consent_organization', ['consent_pk'], unique=False)
    op.create_index(op.f('ix_consent_organization_tenant_id'), 'consent_organization', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_organization_created_at'), 'consent_organization', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_organization_updated_at'), 'consent_organization', ['updated_at'], unique=False)

    # ── 11. consent_policy ───────────────────────────────────────────────────
    op.create_table(
        'consent_policy',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('consent_pk', sa.BigInteger(), nullable=False),
        sa.Column('authority', sa.String(), nullable=True),
        sa.Column('uri', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['consent_pk'], ['consent.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_policy_consent_pk'), 'consent_policy', ['consent_pk'], unique=False)
    op.create_index(op.f('ix_consent_policy_tenant_id'), 'consent_policy', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_policy_created_at'), 'consent_policy', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_policy_updated_at'), 'consent_policy', ['updated_at'], unique=False)

    # ── 12. consent_policy_rule_coding ───────────────────────────────────────
    op.create_table(
        'consent_policy_rule_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('consent_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['consent_pk'], ['consent.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_policy_rule_coding_consent_pk'), 'consent_policy_rule_coding', ['consent_pk'], unique=False)
    op.create_index(op.f('ix_consent_policy_rule_coding_tenant_id'), 'consent_policy_rule_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_policy_rule_coding_created_at'), 'consent_policy_rule_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_policy_rule_coding_updated_at'), 'consent_policy_rule_coding', ['updated_at'], unique=False)

    # ── 13. consent_verification ─────────────────────────────────────────────
    op.create_table(
        'consent_verification',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('consent_pk', sa.BigInteger(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False),
        sa.Column('verified_with_reference', sa.String(), nullable=True),
        sa.Column('verified_with_type', postgresql.ENUM('Patient', 'RelatedPerson', name='consent_verified_with_reference_type', create_type=False), nullable=True),
        sa.Column('verified_with_id', sa.BigInteger(), nullable=True),
        sa.Column('verified_with_display', sa.String(), nullable=True),
        sa.Column('verification_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['consent_pk'], ['consent.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_verification_consent_pk'), 'consent_verification', ['consent_pk'], unique=False)
    op.create_index(op.f('ix_consent_verification_tenant_id'), 'consent_verification', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_verification_created_at'), 'consent_verification', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_verification_updated_at'), 'consent_verification', ['updated_at'], unique=False)

    # ── 14. consent_provision ────────────────────────────────────────────────
    op.create_table(
        'consent_provision',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('consent_pk', sa.BigInteger(), nullable=False),
        sa.Column('parent_provision_id', sa.BigInteger(), nullable=True),
        sa.Column('type', postgresql.ENUM('deny', 'permit', name='consent_provision_type', create_type=False), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['consent_pk'], ['consent.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_provision_id'], ['consent_provision.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_consent_pk'), 'consent_provision', ['consent_pk'], unique=False)
    op.create_index(op.f('ix_consent_provision_parent_provision_id'), 'consent_provision', ['parent_provision_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_tenant_id'), 'consent_provision', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_created_at'), 'consent_provision', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_updated_at'), 'consent_provision', ['updated_at'], unique=False)

    # ── 15. consent_provision_actor ──────────────────────────────────────────
    op.create_table(
        'consent_provision_actor',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('provision_id', sa.BigInteger(), nullable=False),
        sa.Column('role_text', sa.String(), nullable=True),
        sa.Column('reference_reference', sa.String(), nullable=False),
        sa.Column('reference_type', postgresql.ENUM('Device', 'Group', 'CareTeam', 'Organization', 'Patient', 'Practitioner', 'RelatedPerson', 'PractitionerRole', name='consent_provision_actor_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['provision_id'], ['consent_provision.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_actor_provision_id'), 'consent_provision_actor', ['provision_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_actor_tenant_id'), 'consent_provision_actor', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_actor_created_at'), 'consent_provision_actor', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_actor_updated_at'), 'consent_provision_actor', ['updated_at'], unique=False)

    # ── 16. consent_provision_actor_role_coding ──────────────────────────────
    op.create_table(
        'consent_provision_actor_role_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('provision_actor_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['provision_actor_id'], ['consent_provision_actor.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_actor_role_coding_actor_id'), 'consent_provision_actor_role_coding', ['provision_actor_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_actor_role_coding_tenant_id'), 'consent_provision_actor_role_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_actor_role_coding_created_at'), 'consent_provision_actor_role_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_actor_role_coding_updated_at'), 'consent_provision_actor_role_coding', ['updated_at'], unique=False)

    # ── 17. consent_provision_action ─────────────────────────────────────────
    op.create_table(
        'consent_provision_action',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('provision_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['provision_id'], ['consent_provision.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_action_provision_id'), 'consent_provision_action', ['provision_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_action_tenant_id'), 'consent_provision_action', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_action_created_at'), 'consent_provision_action', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_action_updated_at'), 'consent_provision_action', ['updated_at'], unique=False)

    # ── 18. consent_provision_action_coding ──────────────────────────────────
    op.create_table(
        'consent_provision_action_coding',
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
        sa.ForeignKeyConstraint(['action_id'], ['consent_provision_action.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_action_coding_action_id'), 'consent_provision_action_coding', ['action_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_action_coding_tenant_id'), 'consent_provision_action_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_action_coding_created_at'), 'consent_provision_action_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_action_coding_updated_at'), 'consent_provision_action_coding', ['updated_at'], unique=False)

    # ── 19. consent_provision_security_label ─────────────────────────────────
    op.create_table(
        'consent_provision_security_label',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('provision_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['provision_id'], ['consent_provision.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_security_label_provision_id'), 'consent_provision_security_label', ['provision_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_security_label_tenant_id'), 'consent_provision_security_label', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_security_label_created_at'), 'consent_provision_security_label', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_security_label_updated_at'), 'consent_provision_security_label', ['updated_at'], unique=False)

    # ── 20. consent_provision_purpose ────────────────────────────────────────
    op.create_table(
        'consent_provision_purpose',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('provision_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['provision_id'], ['consent_provision.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_purpose_provision_id'), 'consent_provision_purpose', ['provision_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_purpose_tenant_id'), 'consent_provision_purpose', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_purpose_created_at'), 'consent_provision_purpose', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_purpose_updated_at'), 'consent_provision_purpose', ['updated_at'], unique=False)

    # ── 21. consent_provision_class ──────────────────────────────────────────
    op.create_table(
        'consent_provision_class',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('provision_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['provision_id'], ['consent_provision.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_class_provision_id'), 'consent_provision_class', ['provision_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_class_tenant_id'), 'consent_provision_class', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_class_created_at'), 'consent_provision_class', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_class_updated_at'), 'consent_provision_class', ['updated_at'], unique=False)

    # ── 22. consent_provision_code ───────────────────────────────────────────
    op.create_table(
        'consent_provision_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('provision_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['provision_id'], ['consent_provision.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_code_provision_id'), 'consent_provision_code', ['provision_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_code_tenant_id'), 'consent_provision_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_code_created_at'), 'consent_provision_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_code_updated_at'), 'consent_provision_code', ['updated_at'], unique=False)

    # ── 23. consent_provision_code_coding ────────────────────────────────────
    op.create_table(
        'consent_provision_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('code_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['code_id'], ['consent_provision_code.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_code_coding_code_id'), 'consent_provision_code_coding', ['code_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_code_coding_tenant_id'), 'consent_provision_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_code_coding_created_at'), 'consent_provision_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_code_coding_updated_at'), 'consent_provision_code_coding', ['updated_at'], unique=False)

    # ── 24. consent_provision_data ───────────────────────────────────────────
    op.create_table(
        'consent_provision_data',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('provision_id', sa.BigInteger(), nullable=False),
        sa.Column('meaning', postgresql.ENUM('instance', 'related', 'dependents', 'authoredby', name='consent_data_meaning', create_type=False), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=False),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['provision_id'], ['consent_provision.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_provision_data_provision_id'), 'consent_provision_data', ['provision_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_data_tenant_id'), 'consent_provision_data', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_consent_provision_data_created_at'), 'consent_provision_data', ['created_at'], unique=False)
    op.create_index(op.f('ix_consent_provision_data_updated_at'), 'consent_provision_data', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse FK order
    op.drop_table('consent_provision_data')
    op.drop_table('consent_provision_code_coding')
    op.drop_table('consent_provision_code')
    op.drop_table('consent_provision_class')
    op.drop_table('consent_provision_purpose')
    op.drop_table('consent_provision_security_label')
    op.drop_table('consent_provision_action_coding')
    op.drop_table('consent_provision_action')
    op.drop_table('consent_provision_actor_role_coding')
    op.drop_table('consent_provision_actor')
    op.drop_table('consent_provision')
    op.drop_table('consent_verification')
    op.drop_table('consent_policy_rule_coding')
    op.drop_table('consent_policy')
    op.drop_table('consent_organization')
    op.drop_table('consent_performer')
    op.drop_table('consent_category_coding')
    op.drop_table('consent_category')
    op.drop_table('consent_scope_coding')
    op.drop_table('consent_identifier_type_coding')
    op.drop_table('consent_identifier')
    op.drop_table('consent')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS consent_pub_seq")

    # Drop enum types
    enums_to_drop = [
        'consent_identifier_use',
        'consent_data_meaning',
        'consent_provision_actor_reference_type',
        'consent_provision_type',
        'consent_verified_with_reference_type',
        'consent_source_reference_type',
        'consent_performer_reference_type',
        'consent_patient_reference_type',
        'consent_status',
    ]
    for enum_name in enums_to_drop:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
