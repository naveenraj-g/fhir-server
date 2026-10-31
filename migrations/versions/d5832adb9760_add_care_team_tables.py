"""add_care_team_tables

Revision ID: d5832adb9760
Revises: a1b2c3d4e5f7
Create Date: 2026-10-30 20:43:54.395125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd5832adb9760'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enum types ─────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE care_team_status AS ENUM ('proposed', 'active', 'suspended', 'inactive', 'entered-in-error')")
    op.execute("CREATE TYPE care_team_subject_reference_type AS ENUM ('Patient', 'Group')")
    op.execute("CREATE TYPE care_team_encounter_reference_type AS ENUM ('Encounter')")
    op.execute("CREATE TYPE care_team_participant_member_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'RelatedPerson', 'Patient', 'Organization', 'CareTeam')")
    op.execute("CREATE TYPE care_team_participant_on_behalf_of_reference_type AS ENUM ('Organization')")
    op.execute("CREATE TYPE care_team_reason_reference_type AS ENUM ('Condition')")
    op.execute("CREATE TYPE care_team_managing_organization_reference_type AS ENUM ('Organization')")
    op.execute("CREATE TYPE care_team_note_author_reference_type AS ENUM ('Practitioner', 'Patient', 'RelatedPerson', 'Organization')")

    # ── Public sequence ────────────────────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS care_team_pub_seq START 390000 INCREMENT 1")

    # ── 1. care_team (main table) ──────────────────────────────────────────────
    op.create_table(
        'care_team',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_team_id', sa.BigInteger(), server_default=sa.text("nextval('care_team_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('proposed', 'active', 'suspended', 'inactive', 'entered-in-error', name='care_team_status', create_type=False), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=True),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='care_team_subject_reference_type', create_type=False), nullable=True),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('encounter_reference', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM('Encounter', name='care_team_encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.BigInteger(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('care_team_id'),
    )
    op.create_index(op.f('ix_care_team_care_team_id'), 'care_team', ['care_team_id'], unique=True)
    op.create_index(op.f('ix_care_team_user_id'), 'care_team', ['user_id'], unique=False)
    op.create_index(op.f('ix_care_team_tenant_id'), 'care_team', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_subject_id'), 'care_team', ['subject_id'], unique=False)
    op.create_index(op.f('ix_care_team_encounter_id'), 'care_team', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_care_team_created_at'), 'care_team', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_updated_at'), 'care_team', ['updated_at'], unique=False)

    # ── 2. care_team_identifier ────────────────────────────────────────────────
    op.create_table(
        'care_team_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_team_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['care_team_pk'], ['care_team.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_identifier_care_team_pk'), 'care_team_identifier', ['care_team_pk'], unique=False)
    op.create_index(op.f('ix_care_team_identifier_assigner_id'), 'care_team_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_care_team_identifier_tenant_id'), 'care_team_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_identifier_created_at'), 'care_team_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_identifier_updated_at'), 'care_team_identifier', ['updated_at'], unique=False)

    # ── 3. care_team_identifier_type_coding ────────────────────────────────────
    op.create_table(
        'care_team_identifier_type_coding',
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
        sa.ForeignKeyConstraint(['identifier_id'], ['care_team_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_identifier_type_coding_identifier_id'), 'care_team_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_care_team_identifier_type_coding_tenant_id'), 'care_team_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_identifier_type_coding_created_at'), 'care_team_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_identifier_type_coding_updated_at'), 'care_team_identifier_type_coding', ['updated_at'], unique=False)

    # ── 4. care_team_category ──────────────────────────────────────────────────
    op.create_table(
        'care_team_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_team_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_team_pk'], ['care_team.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_category_care_team_pk'), 'care_team_category', ['care_team_pk'], unique=False)
    op.create_index(op.f('ix_care_team_category_tenant_id'), 'care_team_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_category_created_at'), 'care_team_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_category_updated_at'), 'care_team_category', ['updated_at'], unique=False)

    # ── 5. care_team_category_coding ───────────────────────────────────────────
    op.create_table(
        'care_team_category_coding',
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
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['care_team_category.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_category_coding_category_id'), 'care_team_category_coding', ['category_id'], unique=False)
    op.create_index(op.f('ix_care_team_category_coding_tenant_id'), 'care_team_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_category_coding_created_at'), 'care_team_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_category_coding_updated_at'), 'care_team_category_coding', ['updated_at'], unique=False)

    # ── 6. care_team_participant ───────────────────────────────────────────────
    op.create_table(
        'care_team_participant',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_team_pk', sa.BigInteger(), nullable=False),
        sa.Column('member_reference', sa.String(), nullable=True),
        sa.Column('member_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'RelatedPerson', 'Patient', 'Organization', 'CareTeam', name='care_team_participant_member_reference_type', create_type=False), nullable=True),
        sa.Column('member_id', sa.BigInteger(), nullable=True),
        sa.Column('member_display', sa.String(), nullable=True),
        sa.Column('on_behalf_of_reference', sa.String(), nullable=True),
        sa.Column('on_behalf_of_type', postgresql.ENUM('Organization', name='care_team_participant_on_behalf_of_reference_type', create_type=False), nullable=True),
        sa.Column('on_behalf_of_id', sa.BigInteger(), nullable=True),
        sa.Column('on_behalf_of_display', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_team_pk'], ['care_team.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_participant_care_team_pk'), 'care_team_participant', ['care_team_pk'], unique=False)
    op.create_index(op.f('ix_care_team_participant_member_id'), 'care_team_participant', ['member_id'], unique=False)
    op.create_index(op.f('ix_care_team_participant_on_behalf_of_id'), 'care_team_participant', ['on_behalf_of_id'], unique=False)
    op.create_index(op.f('ix_care_team_participant_tenant_id'), 'care_team_participant', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_participant_created_at'), 'care_team_participant', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_participant_updated_at'), 'care_team_participant', ['updated_at'], unique=False)

    # ── 7. care_team_participant_role ──────────────────────────────────────────
    op.create_table(
        'care_team_participant_role',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('participant_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['participant_id'], ['care_team_participant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_participant_role_participant_id'), 'care_team_participant_role', ['participant_id'], unique=False)
    op.create_index(op.f('ix_care_team_participant_role_tenant_id'), 'care_team_participant_role', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_participant_role_created_at'), 'care_team_participant_role', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_participant_role_updated_at'), 'care_team_participant_role', ['updated_at'], unique=False)

    # ── 8. care_team_participant_role_coding ───────────────────────────────────
    op.create_table(
        'care_team_participant_role_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('role_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['role_id'], ['care_team_participant_role.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_participant_role_coding_role_id'), 'care_team_participant_role_coding', ['role_id'], unique=False)
    op.create_index(op.f('ix_care_team_participant_role_coding_tenant_id'), 'care_team_participant_role_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_participant_role_coding_created_at'), 'care_team_participant_role_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_participant_role_coding_updated_at'), 'care_team_participant_role_coding', ['updated_at'], unique=False)

    # ── 9. care_team_reason_code ───────────────────────────────────────────────
    op.create_table(
        'care_team_reason_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_team_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_team_pk'], ['care_team.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_reason_code_care_team_pk'), 'care_team_reason_code', ['care_team_pk'], unique=False)
    op.create_index(op.f('ix_care_team_reason_code_tenant_id'), 'care_team_reason_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_reason_code_created_at'), 'care_team_reason_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_reason_code_updated_at'), 'care_team_reason_code', ['updated_at'], unique=False)

    # ── 10. care_team_reason_code_coding ───────────────────────────────────────
    op.create_table(
        'care_team_reason_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('reason_code_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['reason_code_id'], ['care_team_reason_code.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_reason_code_coding_reason_code_id'), 'care_team_reason_code_coding', ['reason_code_id'], unique=False)
    op.create_index(op.f('ix_care_team_reason_code_coding_tenant_id'), 'care_team_reason_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_reason_code_coding_created_at'), 'care_team_reason_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_reason_code_coding_updated_at'), 'care_team_reason_code_coding', ['updated_at'], unique=False)

    # ── 11. care_team_reason_reference ─────────────────────────────────────────
    op.create_table(
        'care_team_reason_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_team_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Condition', name='care_team_reason_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_team_pk'], ['care_team.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_reason_reference_care_team_pk'), 'care_team_reason_reference', ['care_team_pk'], unique=False)
    op.create_index(op.f('ix_care_team_reason_reference_reference_id'), 'care_team_reason_reference', ['reference_id'], unique=False)
    op.create_index(op.f('ix_care_team_reason_reference_tenant_id'), 'care_team_reason_reference', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_reason_reference_created_at'), 'care_team_reason_reference', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_reason_reference_updated_at'), 'care_team_reason_reference', ['updated_at'], unique=False)

    # ── 12. care_team_managing_organization ────────────────────────────────────
    op.create_table(
        'care_team_managing_organization',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_team_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Organization', name='care_team_managing_organization_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_team_pk'], ['care_team.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_managing_organization_care_team_pk'), 'care_team_managing_organization', ['care_team_pk'], unique=False)
    op.create_index(op.f('ix_care_team_managing_organization_reference_id'), 'care_team_managing_organization', ['reference_id'], unique=False)
    op.create_index(op.f('ix_care_team_managing_organization_tenant_id'), 'care_team_managing_organization', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_managing_organization_created_at'), 'care_team_managing_organization', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_managing_organization_updated_at'), 'care_team_managing_organization', ['updated_at'], unique=False)

    # ── 13. care_team_telecom ──────────────────────────────────────────────────
    op.create_table(
        'care_team_telecom',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_team_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_team_pk'], ['care_team.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_telecom_care_team_pk'), 'care_team_telecom', ['care_team_pk'], unique=False)
    op.create_index(op.f('ix_care_team_telecom_tenant_id'), 'care_team_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_telecom_created_at'), 'care_team_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_telecom_updated_at'), 'care_team_telecom', ['updated_at'], unique=False)

    # ── 14. care_team_note ─────────────────────────────────────────────────────
    op.create_table(
        'care_team_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('care_team_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_reference', sa.String(), nullable=True),
        sa.Column('author_reference_type', postgresql.ENUM('Practitioner', 'Patient', 'RelatedPerson', 'Organization', name='care_team_note_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['care_team_pk'], ['care_team.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_care_team_note_care_team_pk'), 'care_team_note', ['care_team_pk'], unique=False)
    op.create_index(op.f('ix_care_team_note_author_reference_id'), 'care_team_note', ['author_reference_id'], unique=False)
    op.create_index(op.f('ix_care_team_note_tenant_id'), 'care_team_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_care_team_note_created_at'), 'care_team_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_care_team_note_updated_at'), 'care_team_note', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse FK order
    op.drop_table('care_team_note')
    op.drop_table('care_team_telecom')
    op.drop_table('care_team_managing_organization')
    op.drop_table('care_team_reason_reference')
    op.drop_table('care_team_reason_code_coding')
    op.drop_table('care_team_reason_code')
    op.drop_table('care_team_participant_role_coding')
    op.drop_table('care_team_participant_role')
    op.drop_table('care_team_participant')
    op.drop_table('care_team_category_coding')
    op.drop_table('care_team_category')
    op.drop_table('care_team_identifier_type_coding')
    op.drop_table('care_team_identifier')
    op.drop_table('care_team')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS care_team_pub_seq")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS care_team_note_author_reference_type")
    op.execute("DROP TYPE IF EXISTS care_team_managing_organization_reference_type")
    op.execute("DROP TYPE IF EXISTS care_team_reason_reference_type")
    op.execute("DROP TYPE IF EXISTS care_team_participant_on_behalf_of_reference_type")
    op.execute("DROP TYPE IF EXISTS care_team_participant_member_reference_type")
    op.execute("DROP TYPE IF EXISTS care_team_encounter_reference_type")
    op.execute("DROP TYPE IF EXISTS care_team_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS care_team_status")
