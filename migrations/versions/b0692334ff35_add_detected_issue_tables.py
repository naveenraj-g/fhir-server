"""add_detected_issue_tables

Revision ID: b0692334ff35
Revises: 3444e96ed997
Create Date: 2026-11-02 23:28:47.706780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b0692334ff35'
down_revision: Union[str, None] = '3444e96ed997'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE detected_issue_status AS ENUM (
                'registered', 'preliminary', 'final', 'amended',
                'corrected', 'cancelled', 'entered-in-error', 'unknown'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE detected_issue_severity AS ENUM (
                'high', 'moderate', 'low'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE detected_issue_patient_reference_type AS ENUM (
                'Patient'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE detected_issue_author_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Device'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE detected_issue_mitigation_author_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS detected_issue_pub_seq START WITH 540000 INCREMENT BY 1")

    # 3. Main table
    op.create_table(
        'detected_issue',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_id', sa.BigInteger(), server_default=sa.text("nextval('detected_issue_pub_seq')"), nullable=False),
        sa.Column('status', postgresql.ENUM('registered', 'preliminary', 'final', 'amended', 'corrected', 'cancelled', 'entered-in-error', 'unknown', name='detected_issue_status', create_type=False), nullable=False),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('severity', postgresql.ENUM('high', 'moderate', 'low', name='detected_issue_severity', create_type=False), nullable=True),
        sa.Column('patient_reference', sa.String(), nullable=True),
        sa.Column('patient_type', postgresql.ENUM('Patient', name='detected_issue_patient_reference_type', create_type=False), nullable=True),
        sa.Column('patient_id', sa.BigInteger(), nullable=True),
        sa.Column('patient_display', sa.String(), nullable=True),
        sa.Column('patient_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('patient_identifier_type_system', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_version', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_code', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_display', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('patient_identifier_type_text', sa.String(), nullable=True),
        sa.Column('patient_identifier_system', sa.String(), nullable=True),
        sa.Column('patient_identifier_value', sa.String(), nullable=True),
        sa.Column('patient_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('patient_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('identified_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('identified_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('identified_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Device', name='detected_issue_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_id', sa.BigInteger(), nullable=True),
        sa.Column('author_display', sa.String(), nullable=True),
        sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('author_identifier_type_system', sa.String(), nullable=True),
        sa.Column('author_identifier_type_version', sa.String(), nullable=True),
        sa.Column('author_identifier_type_code', sa.String(), nullable=True),
        sa.Column('author_identifier_type_display', sa.String(), nullable=True),
        sa.Column('author_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('author_identifier_type_text', sa.String(), nullable=True),
        sa.Column('author_identifier_system', sa.String(), nullable=True),
        sa.Column('author_identifier_value', sa.String(), nullable=True),
        sa.Column('author_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('detail', sa.String(), nullable=True),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_author_id'), 'detected_issue', ['author_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_created_at'), 'detected_issue', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_detected_issue_id'), 'detected_issue', ['detected_issue_id'], unique=True)
    op.create_index(op.f('ix_detected_issue_id'), 'detected_issue', ['id'], unique=False)
    op.create_index(op.f('ix_detected_issue_patient_id'), 'detected_issue', ['patient_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_tenant_id'), 'detected_issue', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_updated_at'), 'detected_issue', ['updated_at'], unique=False)

    # 4. detected_issue_code_coding
    op.create_table(
        'detected_issue_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['detected_issue_pk'], ['detected_issue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_code_coding_created_at'), 'detected_issue_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_code_coding_detected_issue_pk'), 'detected_issue_code_coding', ['detected_issue_pk'], unique=False)
    op.create_index(op.f('ix_detected_issue_code_coding_tenant_id'), 'detected_issue_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_code_coding_updated_at'), 'detected_issue_code_coding', ['updated_at'], unique=False)

    # 5. detected_issue_evidence
    op.create_table(
        'detected_issue_evidence',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_pk', sa.BigInteger(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['detected_issue_pk'], ['detected_issue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_evidence_created_at'), 'detected_issue_evidence', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_detected_issue_pk'), 'detected_issue_evidence', ['detected_issue_pk'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_tenant_id'), 'detected_issue_evidence', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_updated_at'), 'detected_issue_evidence', ['updated_at'], unique=False)

    # 6. detected_issue_identifier
    op.create_table(
        'detected_issue_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('assigner_identifier_type_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_version', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_code', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_display', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['detected_issue_pk'], ['detected_issue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_identifier_assigner_id'), 'detected_issue_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_identifier_created_at'), 'detected_issue_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_identifier_detected_issue_pk'), 'detected_issue_identifier', ['detected_issue_pk'], unique=False)
    op.create_index(op.f('ix_detected_issue_identifier_tenant_id'), 'detected_issue_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_identifier_updated_at'), 'detected_issue_identifier', ['updated_at'], unique=False)

    # 7. detected_issue_implicated
    op.create_table(
        'detected_issue_implicated',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_pk', sa.BigInteger(), nullable=False),
        sa.Column('implicated_reference', sa.String(), nullable=True),
        sa.Column('implicated_type', sa.String(), nullable=True),
        sa.Column('implicated_id', sa.BigInteger(), nullable=True),
        sa.Column('implicated_display', sa.String(), nullable=True),
        sa.Column('implicated_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('implicated_identifier_type_system', sa.String(), nullable=True),
        sa.Column('implicated_identifier_type_version', sa.String(), nullable=True),
        sa.Column('implicated_identifier_type_code', sa.String(), nullable=True),
        sa.Column('implicated_identifier_type_display', sa.String(), nullable=True),
        sa.Column('implicated_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('implicated_identifier_type_text', sa.String(), nullable=True),
        sa.Column('implicated_identifier_system', sa.String(), nullable=True),
        sa.Column('implicated_identifier_value', sa.String(), nullable=True),
        sa.Column('implicated_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('implicated_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['detected_issue_pk'], ['detected_issue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_implicated_created_at'), 'detected_issue_implicated', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_implicated_detected_issue_pk'), 'detected_issue_implicated', ['detected_issue_pk'], unique=False)
    op.create_index(op.f('ix_detected_issue_implicated_implicated_id'), 'detected_issue_implicated', ['implicated_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_implicated_tenant_id'), 'detected_issue_implicated', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_implicated_updated_at'), 'detected_issue_implicated', ['updated_at'], unique=False)

    # 8. detected_issue_mitigation
    op.create_table(
        'detected_issue_mitigation',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_pk', sa.BigInteger(), nullable=False),
        sa.Column('action_text', sa.String(), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', postgresql.ENUM('Practitioner', 'PractitionerRole', name='detected_issue_mitigation_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_id', sa.BigInteger(), nullable=True),
        sa.Column('author_display', sa.String(), nullable=True),
        sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('author_identifier_type_system', sa.String(), nullable=True),
        sa.Column('author_identifier_type_version', sa.String(), nullable=True),
        sa.Column('author_identifier_type_code', sa.String(), nullable=True),
        sa.Column('author_identifier_type_display', sa.String(), nullable=True),
        sa.Column('author_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('author_identifier_type_text', sa.String(), nullable=True),
        sa.Column('author_identifier_system', sa.String(), nullable=True),
        sa.Column('author_identifier_value', sa.String(), nullable=True),
        sa.Column('author_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['detected_issue_pk'], ['detected_issue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_mitigation_author_id'), 'detected_issue_mitigation', ['author_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_mitigation_created_at'), 'detected_issue_mitigation', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_mitigation_detected_issue_pk'), 'detected_issue_mitigation', ['detected_issue_pk'], unique=False)
    op.create_index(op.f('ix_detected_issue_mitigation_tenant_id'), 'detected_issue_mitigation', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_mitigation_updated_at'), 'detected_issue_mitigation', ['updated_at'], unique=False)

    # 9. detected_issue_evidence_code
    op.create_table(
        'detected_issue_evidence_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_evidence_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['detected_issue_evidence_id'], ['detected_issue_evidence.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_evidence_code_created_at'), 'detected_issue_evidence_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_code_detected_issue_evidence_id'), 'detected_issue_evidence_code', ['detected_issue_evidence_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_code_tenant_id'), 'detected_issue_evidence_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_code_updated_at'), 'detected_issue_evidence_code', ['updated_at'], unique=False)

    # 10. detected_issue_evidence_detail
    op.create_table(
        'detected_issue_evidence_detail',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_evidence_id', sa.BigInteger(), nullable=False),
        sa.Column('detail_reference', sa.String(), nullable=True),
        sa.Column('detail_type', sa.String(), nullable=True),
        sa.Column('detail_id', sa.BigInteger(), nullable=True),
        sa.Column('detail_display', sa.String(), nullable=True),
        sa.Column('detail_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('detail_identifier_type_system', sa.String(), nullable=True),
        sa.Column('detail_identifier_type_version', sa.String(), nullable=True),
        sa.Column('detail_identifier_type_code', sa.String(), nullable=True),
        sa.Column('detail_identifier_type_display', sa.String(), nullable=True),
        sa.Column('detail_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('detail_identifier_type_text', sa.String(), nullable=True),
        sa.Column('detail_identifier_system', sa.String(), nullable=True),
        sa.Column('detail_identifier_value', sa.String(), nullable=True),
        sa.Column('detail_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('detail_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['detected_issue_evidence_id'], ['detected_issue_evidence.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_evidence_detail_created_at'), 'detected_issue_evidence_detail', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_detail_detail_id'), 'detected_issue_evidence_detail', ['detail_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_detail_detected_issue_evidence_id'), 'detected_issue_evidence_detail', ['detected_issue_evidence_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_detail_tenant_id'), 'detected_issue_evidence_detail', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_detail_updated_at'), 'detected_issue_evidence_detail', ['updated_at'], unique=False)

    # 11. detected_issue_identifier_coding
    op.create_table(
        'detected_issue_identifier_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['detected_issue_identifier_id'], ['detected_issue_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_identifier_coding_created_at'), 'detected_issue_identifier_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_identifier_coding_detected_issue_identifier_id'), 'detected_issue_identifier_coding', ['detected_issue_identifier_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_identifier_coding_tenant_id'), 'detected_issue_identifier_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_identifier_coding_updated_at'), 'detected_issue_identifier_coding', ['updated_at'], unique=False)

    # 12. detected_issue_mitigation_action_coding
    op.create_table(
        'detected_issue_mitigation_action_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_mitigation_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['detected_issue_mitigation_id'], ['detected_issue_mitigation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_mitigation_action_coding_created_at'), 'detected_issue_mitigation_action_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_mitigation_action_coding_detected_issue_mitigation_id'), 'detected_issue_mitigation_action_coding', ['detected_issue_mitigation_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_mitigation_action_coding_tenant_id'), 'detected_issue_mitigation_action_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_mitigation_action_coding_updated_at'), 'detected_issue_mitigation_action_coding', ['updated_at'], unique=False)

    # 13. detected_issue_evidence_code_coding
    op.create_table(
        'detected_issue_evidence_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('detected_issue_evidence_code_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['detected_issue_evidence_code_id'], ['detected_issue_evidence_code.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detected_issue_evidence_code_coding_created_at'), 'detected_issue_evidence_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_code_coding_detected_issue_evidence_code_id'), 'detected_issue_evidence_code_coding', ['detected_issue_evidence_code_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_code_coding_tenant_id'), 'detected_issue_evidence_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_detected_issue_evidence_code_coding_updated_at'), 'detected_issue_evidence_code_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    # 1. Drop tables in reverse FK order
    op.drop_table('detected_issue_evidence_code_coding')
    op.drop_table('detected_issue_mitigation_action_coding')
    op.drop_table('detected_issue_identifier_coding')
    op.drop_table('detected_issue_evidence_detail')
    op.drop_table('detected_issue_evidence_code')
    op.drop_table('detected_issue_mitigation')
    op.drop_table('detected_issue_implicated')
    op.drop_table('detected_issue_identifier')
    op.drop_table('detected_issue_evidence')
    op.drop_table('detected_issue_code_coding')
    op.drop_table('detected_issue')

    # 2. Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS detected_issue_pub_seq")

    # 3. Drop enums
    op.execute("DROP TYPE IF EXISTS detected_issue_mitigation_author_reference_type")
    op.execute("DROP TYPE IF EXISTS detected_issue_author_reference_type")
    op.execute("DROP TYPE IF EXISTS detected_issue_patient_reference_type")
    op.execute("DROP TYPE IF EXISTS detected_issue_severity")
    op.execute("DROP TYPE IF EXISTS detected_issue_status")
