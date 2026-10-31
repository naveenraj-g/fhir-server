"""add_episode_of_care_tables

Revision ID: ee2a42a23151
Revises: d5832adb9760
Create Date: 2026-10-30 21:28:33.358704

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ee2a42a23151'
down_revision: Union[str, None] = 'd5832adb9760'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enum types ─────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE episode_of_care_status AS ENUM ('planned', 'waitlist', 'active', 'onhold', 'finished', 'cancelled', 'entered-in-error')")
    op.execute("CREATE TYPE episode_of_care_patient_reference_type AS ENUM ('Patient')")
    op.execute("CREATE TYPE episode_of_care_managing_org_reference_type AS ENUM ('Organization')")
    op.execute("CREATE TYPE episode_of_care_care_manager_reference_type AS ENUM ('Practitioner', 'PractitionerRole')")
    op.execute("CREATE TYPE episode_of_care_diag_condition_reference_type AS ENUM ('Condition')")
    op.execute("CREATE TYPE episode_of_care_referral_request_reference_type AS ENUM ('ServiceRequest')")
    op.execute("CREATE TYPE episode_of_care_team_reference_type AS ENUM ('CareTeam')")
    op.execute("CREATE TYPE episode_of_care_account_reference_type AS ENUM ('Account')")

    # ── Public sequence ────────────────────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS episode_of_care_pub_seq START 350000 INCREMENT 1")

    # ── 1. episode_of_care (main table) ────────────────────────────────────────
    op.create_table(
        'episode_of_care',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_id', sa.BigInteger(), server_default=sa.text("nextval('episode_of_care_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('planned', 'waitlist', 'active', 'onhold', 'finished', 'cancelled', 'entered-in-error', name='episode_of_care_status', create_type=False), nullable=False),
        sa.Column('patient_reference', sa.String(), nullable=False),
        sa.Column('patient_type', postgresql.ENUM('Patient', name='episode_of_care_patient_reference_type', create_type=False), nullable=True),
        sa.Column('patient_id', sa.BigInteger(), nullable=True),
        sa.Column('patient_display', sa.String(), nullable=True),
        sa.Column('managing_organization_reference', sa.String(), nullable=True),
        sa.Column('managing_organization_type', postgresql.ENUM('Organization', name='episode_of_care_managing_org_reference_type', create_type=False), nullable=True),
        sa.Column('managing_organization_id', sa.BigInteger(), nullable=True),
        sa.Column('managing_organization_display', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('care_manager_reference', sa.String(), nullable=True),
        sa.Column('care_manager_type', postgresql.ENUM('Practitioner', 'PractitionerRole', name='episode_of_care_care_manager_reference_type', create_type=False), nullable=True),
        sa.Column('care_manager_id', sa.BigInteger(), nullable=True),
        sa.Column('care_manager_display', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('episode_of_care_id'),
    )
    op.create_index(op.f('ix_episode_of_care_episode_of_care_id'), 'episode_of_care', ['episode_of_care_id'], unique=True)
    op.create_index(op.f('ix_episode_of_care_user_id'), 'episode_of_care', ['user_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_status'), 'episode_of_care', ['status'], unique=False)
    op.create_index(op.f('ix_episode_of_care_tenant_id'), 'episode_of_care', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_patient_id'), 'episode_of_care', ['patient_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_managing_organization_id'), 'episode_of_care', ['managing_organization_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_care_manager_id'), 'episode_of_care', ['care_manager_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_created_at'), 'episode_of_care', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_updated_at'), 'episode_of_care', ['updated_at'], unique=False)

    # ── 2. episode_of_care_identifier ──────────────────────────────────────────
    op.create_table(
        'episode_of_care_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['episode_of_care_pk'], ['episode_of_care.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_identifier_episode_of_care_pk'), 'episode_of_care_identifier', ['episode_of_care_pk'], unique=False)
    op.create_index(op.f('ix_episode_of_care_identifier_assigner_id'), 'episode_of_care_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_identifier_tenant_id'), 'episode_of_care_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_identifier_created_at'), 'episode_of_care_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_identifier_updated_at'), 'episode_of_care_identifier', ['updated_at'], unique=False)

    # ── 3. episode_of_care_identifier_type_coding ──────────────────────────────
    op.create_table(
        'episode_of_care_identifier_type_coding',
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
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['identifier_id'], ['episode_of_care_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_identifier_type_coding_identifier_id'), 'episode_of_care_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_identifier_type_coding_tenant_id'), 'episode_of_care_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_identifier_type_coding_created_at'), 'episode_of_care_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_identifier_type_coding_updated_at'), 'episode_of_care_identifier_type_coding', ['updated_at'], unique=False)

    # ── 4. episode_of_care_status_history ──────────────────────────────────────
    op.create_table(
        'episode_of_care_status_history',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_pk', sa.BigInteger(), nullable=False),
        sa.Column('status', postgresql.ENUM('planned', 'waitlist', 'active', 'onhold', 'finished', 'cancelled', 'entered-in-error', name='episode_of_care_status', create_type=False), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['episode_of_care_pk'], ['episode_of_care.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_status_history_episode_of_care_pk'), 'episode_of_care_status_history', ['episode_of_care_pk'], unique=False)
    op.create_index(op.f('ix_episode_of_care_status_history_tenant_id'), 'episode_of_care_status_history', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_status_history_created_at'), 'episode_of_care_status_history', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_status_history_updated_at'), 'episode_of_care_status_history', ['updated_at'], unique=False)

    # ── 5. episode_of_care_type ────────────────────────────────────────────────
    op.create_table(
        'episode_of_care_type',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['episode_of_care_pk'], ['episode_of_care.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_type_episode_of_care_pk'), 'episode_of_care_type', ['episode_of_care_pk'], unique=False)
    op.create_index(op.f('ix_episode_of_care_type_tenant_id'), 'episode_of_care_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_type_created_at'), 'episode_of_care_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_type_updated_at'), 'episode_of_care_type', ['updated_at'], unique=False)

    # ── 6. episode_of_care_type_coding ─────────────────────────────────────────
    op.create_table(
        'episode_of_care_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('type_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['type_id'], ['episode_of_care_type.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_type_coding_type_id'), 'episode_of_care_type_coding', ['type_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_type_coding_tenant_id'), 'episode_of_care_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_type_coding_created_at'), 'episode_of_care_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_type_coding_updated_at'), 'episode_of_care_type_coding', ['updated_at'], unique=False)

    # ── 7. episode_of_care_diagnosis ───────────────────────────────────────────
    op.create_table(
        'episode_of_care_diagnosis',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_pk', sa.BigInteger(), nullable=False),
        sa.Column('condition_reference', sa.String(), nullable=False),
        sa.Column('condition_type', postgresql.ENUM('Condition', name='episode_of_care_diag_condition_reference_type', create_type=False), nullable=True),
        sa.Column('condition_id', sa.BigInteger(), nullable=True),
        sa.Column('condition_display', sa.String(), nullable=True),
        sa.Column('role_text', sa.String(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['episode_of_care_pk'], ['episode_of_care.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_diagnosis_episode_of_care_pk'), 'episode_of_care_diagnosis', ['episode_of_care_pk'], unique=False)
    op.create_index(op.f('ix_episode_of_care_diagnosis_condition_id'), 'episode_of_care_diagnosis', ['condition_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_diagnosis_tenant_id'), 'episode_of_care_diagnosis', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_diagnosis_created_at'), 'episode_of_care_diagnosis', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_diagnosis_updated_at'), 'episode_of_care_diagnosis', ['updated_at'], unique=False)

    # ── 8. episode_of_care_diagnosis_role_coding ───────────────────────────────
    op.create_table(
        'episode_of_care_diagnosis_role_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('diagnosis_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['diagnosis_id'], ['episode_of_care_diagnosis.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_diagnosis_role_coding_diagnosis_id'), 'episode_of_care_diagnosis_role_coding', ['diagnosis_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_diagnosis_role_coding_tenant_id'), 'episode_of_care_diagnosis_role_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_diagnosis_role_coding_created_at'), 'episode_of_care_diagnosis_role_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_diagnosis_role_coding_updated_at'), 'episode_of_care_diagnosis_role_coding', ['updated_at'], unique=False)

    # ── 9. episode_of_care_referral_request ────────────────────────────────────
    op.create_table(
        'episode_of_care_referral_request',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('ServiceRequest', name='episode_of_care_referral_request_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['episode_of_care_pk'], ['episode_of_care.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_referral_request_episode_of_care_pk'), 'episode_of_care_referral_request', ['episode_of_care_pk'], unique=False)
    op.create_index(op.f('ix_episode_of_care_referral_request_reference_id'), 'episode_of_care_referral_request', ['reference_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_referral_request_tenant_id'), 'episode_of_care_referral_request', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_referral_request_created_at'), 'episode_of_care_referral_request', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_referral_request_updated_at'), 'episode_of_care_referral_request', ['updated_at'], unique=False)

    # ── 10. episode_of_care_team ───────────────────────────────────────────────
    op.create_table(
        'episode_of_care_team',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('CareTeam', name='episode_of_care_team_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['episode_of_care_pk'], ['episode_of_care.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_team_episode_of_care_pk'), 'episode_of_care_team', ['episode_of_care_pk'], unique=False)
    op.create_index(op.f('ix_episode_of_care_team_reference_id'), 'episode_of_care_team', ['reference_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_team_tenant_id'), 'episode_of_care_team', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_team_created_at'), 'episode_of_care_team', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_team_updated_at'), 'episode_of_care_team', ['updated_at'], unique=False)

    # ── 11. episode_of_care_account ────────────────────────────────────────────
    op.create_table(
        'episode_of_care_account',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Account', name='episode_of_care_account_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['episode_of_care_pk'], ['episode_of_care.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_account_episode_of_care_pk'), 'episode_of_care_account', ['episode_of_care_pk'], unique=False)
    op.create_index(op.f('ix_episode_of_care_account_reference_id'), 'episode_of_care_account', ['reference_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_account_tenant_id'), 'episode_of_care_account', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_account_created_at'), 'episode_of_care_account', ['created_at'], unique=False)
    op.create_index(op.f('ix_episode_of_care_account_updated_at'), 'episode_of_care_account', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse FK order
    op.drop_table('episode_of_care_account')
    op.drop_table('episode_of_care_team')
    op.drop_table('episode_of_care_referral_request')
    op.drop_table('episode_of_care_diagnosis_role_coding')
    op.drop_table('episode_of_care_diagnosis')
    op.drop_table('episode_of_care_type_coding')
    op.drop_table('episode_of_care_type')
    op.drop_table('episode_of_care_status_history')
    op.drop_table('episode_of_care_identifier_type_coding')
    op.drop_table('episode_of_care_identifier')
    op.drop_table('episode_of_care')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS episode_of_care_pub_seq")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS episode_of_care_account_reference_type")
    op.execute("DROP TYPE IF EXISTS episode_of_care_team_reference_type")
    op.execute("DROP TYPE IF EXISTS episode_of_care_referral_request_reference_type")
    op.execute("DROP TYPE IF EXISTS episode_of_care_diag_condition_reference_type")
    op.execute("DROP TYPE IF EXISTS episode_of_care_care_manager_reference_type")
    op.execute("DROP TYPE IF EXISTS episode_of_care_managing_org_reference_type")
    op.execute("DROP TYPE IF EXISTS episode_of_care_patient_reference_type")
    op.execute("DROP TYPE IF EXISTS episode_of_care_status")
