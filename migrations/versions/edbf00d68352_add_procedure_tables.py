"""add_procedure_tables

Revision ID: edbf00d68352
Revises: af2c005d746a
Create Date: 2026-10-31 01:02:34.033740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'edbf00d68352'
down_revision: Union[str, None] = 'af2c005d746a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ───────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_status AS ENUM (
                'preparation', 'in-progress', 'not-done', 'on-hold',
                'stopped', 'completed', 'entered-in-error', 'unknown'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_subject_reference_type AS ENUM ('Patient', 'Group');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_based_on_reference_type AS ENUM ('CarePlan', 'ServiceRequest');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_part_of_reference_type AS ENUM ('Procedure', 'Observation', 'MedicationAdministration');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_recorder_reference_type AS ENUM ('Patient', 'RelatedPerson', 'Practitioner', 'PractitionerRole');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_asserter_reference_type AS ENUM ('Patient', 'RelatedPerson', 'Practitioner', 'PractitionerRole');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_performer_actor_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'Organization', 'Patient', 'RelatedPerson', 'Device');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_reason_reference_reference_type AS ENUM ('Condition', 'Observation', 'Procedure', 'DiagnosticReport', 'DocumentReference');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_report_reference_type AS ENUM ('DiagnosticReport', 'DocumentReference', 'Composition');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_complication_detail_reference_type AS ENUM ('Condition');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_focal_device_manipulated_reference_type AS ENUM ('Device');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_used_reference_reference_type AS ENUM ('Device', 'Medication', 'Substance');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE procedure_author_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Organization');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ── 2. Create Sequence ────────────────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS procedure_pub_seq START WITH 100000 INCREMENT BY 1")

    # ── 3. Main Procedure Table ───────────────────────────────────────────────
    op.create_table(
        'procedure',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('procedure_id', sa.BigInteger(), server_default=sa.text("nextval('procedure_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('instantiates_canonical', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('instantiates_uri', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', postgresql.ENUM('preparation', 'in-progress', 'not-done', 'on-hold', 'stopped', 'completed', 'entered-in-error', 'unknown', name='procedure_status', create_type=False), nullable=False),
        sa.Column('status_reason_text', sa.String(), nullable=True),
        sa.Column('category_text', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=False),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='procedure_subject_reference_type', create_type=False), nullable=False),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('encounter_reference', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM('Encounter', name='encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.BigInteger(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('performed_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('performed_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('performed_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('performed_string', sa.String(), nullable=True),
        sa.Column('performed_age', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('performed_range', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recorder_reference', sa.String(), nullable=True),
        sa.Column('recorder_type', postgresql.ENUM('Patient', 'RelatedPerson', 'Practitioner', 'PractitionerRole', name='procedure_recorder_reference_type', create_type=False), nullable=True),
        sa.Column('recorder_id', sa.BigInteger(), nullable=True),
        sa.Column('recorder_display', sa.String(), nullable=True),
        sa.Column('asserter_reference', sa.String(), nullable=True),
        sa.Column('asserter_type', postgresql.ENUM('Patient', 'RelatedPerson', 'Practitioner', 'PractitionerRole', name='procedure_asserter_reference_type', create_type=False), nullable=True),
        sa.Column('asserter_id', sa.BigInteger(), nullable=True),
        sa.Column('asserter_display', sa.String(), nullable=True),
        sa.Column('location_reference', sa.String(), nullable=True),
        sa.Column('location_type', postgresql.ENUM('Location', name='location_reference_type', create_type=False), nullable=True),
        sa.Column('location_id', sa.BigInteger(), nullable=True),
        sa.Column('location_display', sa.String(), nullable=True),
        sa.Column('outcome_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_id'), 'procedure', ['id'], unique=False)
    op.create_index(op.f('ix_procedure_procedure_id'), 'procedure', ['procedure_id'], unique=True)
    op.create_index(op.f('ix_procedure_user_id'), 'procedure', ['user_id'], unique=False)
    op.create_index(op.f('ix_procedure_subject_id'), 'procedure', ['subject_id'], unique=False)
    op.create_index(op.f('ix_procedure_encounter_id'), 'procedure', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_procedure_recorder_id'), 'procedure', ['recorder_id'], unique=False)
    op.create_index(op.f('ix_procedure_asserter_id'), 'procedure', ['asserter_id'], unique=False)
    op.create_index(op.f('ix_procedure_location_id'), 'procedure', ['location_id'], unique=False)
    op.create_index(op.f('ix_procedure_tenant_id'), 'procedure', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_procedure_created_at'), 'procedure', ['created_at'], unique=False)
    op.create_index(op.f('ix_procedure_updated_at'), 'procedure', ['updated_at'], unique=False)

    # ── 4. Coding Tables on Main Model ────────────────────────────────────────
    for prefix in ('status_reason', 'category', 'code', 'outcome'):
        tbl_name = f'procedure_{prefix}_coding'
        op.create_table(
            tbl_name,
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('procedure_pk', sa.BigInteger(), nullable=False),
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
            sa.ForeignKeyConstraint(['procedure_pk'], ['procedure.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f(f'ix_{tbl_name}_procedure_pk'), tbl_name, ['procedure_pk'], unique=False)
        op.create_index(op.f(f'ix_{tbl_name}_tenant_id'), tbl_name, ['tenant_id'], unique=False)
        op.create_index(op.f(f'ix_{tbl_name}_created_at'), tbl_name, ['created_at'], unique=False)
        op.create_index(op.f(f'ix_{tbl_name}_updated_at'), tbl_name, ['updated_at'], unique=False)

    # ── 5. Identifier Tables ──────────────────────────────────────────────────
    op.create_table(
        'procedure_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('procedure_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['procedure_pk'], ['procedure.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_identifier_procedure_pk'), 'procedure_identifier', ['procedure_pk'], unique=False)
    op.create_index(op.f('ix_procedure_identifier_assigner_id'), 'procedure_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_procedure_identifier_tenant_id'), 'procedure_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_procedure_identifier_created_at'), 'procedure_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_procedure_identifier_updated_at'), 'procedure_identifier', ['updated_at'], unique=False)

    op.create_table(
        'procedure_identifier_type_coding',
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
        sa.ForeignKeyConstraint(['identifier_id'], ['procedure_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_identifier_type_coding_identifier_id'), 'procedure_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_procedure_identifier_type_coding_tenant_id'), 'procedure_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_procedure_identifier_type_coding_created_at'), 'procedure_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_procedure_identifier_type_coding_updated_at'), 'procedure_identifier_type_coding', ['updated_at'], unique=False)

    # ── 6. Reference Tables ───────────────────────────────────────────────────
    ref_tables = [
        ('procedure_based_on', 'procedure_based_on_reference_type', ['CarePlan', 'ServiceRequest']),
        ('procedure_part_of', 'procedure_part_of_reference_type', ['Procedure', 'Observation', 'MedicationAdministration']),
        ('procedure_reason_reference', 'procedure_reason_reference_reference_type', ['Condition', 'Observation', 'Procedure', 'DiagnosticReport', 'DocumentReference']),
        ('procedure_report', 'procedure_report_reference_type', ['DiagnosticReport', 'DocumentReference', 'Composition']),
        ('procedure_complication_detail', 'procedure_complication_detail_reference_type', ['Condition']),
        ('procedure_used_reference', 'procedure_used_reference_reference_type', ['Device', 'Medication', 'Substance']),
    ]
    for tbl_name, enum_type_name, enum_values in ref_tables:
        op.create_table(
            tbl_name,
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('procedure_pk', sa.BigInteger(), nullable=False),
            sa.Column('reference_reference', sa.String(), nullable=True),
            sa.Column('reference_type', postgresql.ENUM(*enum_values, name=enum_type_name, create_type=False), nullable=False),
            sa.Column('reference_id', sa.BigInteger(), nullable=True),
            sa.Column('reference_display', sa.String(), nullable=True),
            sa.Column('tenant_id', sa.String(), nullable=False),
            sa.Column('created_by', sa.String(), nullable=False),
            sa.Column('updated_by', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['procedure_pk'], ['procedure.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f(f'ix_{tbl_name}_procedure_pk'), tbl_name, ['procedure_pk'], unique=False)
        op.create_index(op.f(f'ix_{tbl_name}_reference_id'), tbl_name, ['reference_id'], unique=False)
        op.create_index(op.f(f'ix_{tbl_name}_tenant_id'), tbl_name, ['tenant_id'], unique=False)
        op.create_index(op.f(f'ix_{tbl_name}_created_at'), tbl_name, ['created_at'], unique=False)
        op.create_index(op.f(f'ix_{tbl_name}_updated_at'), tbl_name, ['updated_at'], unique=False)

    # ── 7. Concept (0..* CodeableConcept) Tables ──────────────────────────────
    concepts = [
        ('procedure_reason_code', 'reason_code_id'),
        ('procedure_body_site', 'body_site_id'),
        ('procedure_complication', 'complication_id'),
        ('procedure_follow_up', 'follow_up_id'),
        ('procedure_used_code', 'used_code_id'),
    ]
    for parent_tbl, fk_col in concepts:
        coding_tbl = f"{parent_tbl}_coding"
        op.create_table(
            parent_tbl,
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('procedure_pk', sa.BigInteger(), nullable=False),
            sa.Column('text', sa.String(), nullable=True),
            sa.Column('tenant_id', sa.String(), nullable=False),
            sa.Column('created_by', sa.String(), nullable=False),
            sa.Column('updated_by', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['procedure_pk'], ['procedure.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f(f'ix_{parent_tbl}_procedure_pk'), parent_tbl, ['procedure_pk'], unique=False)
        op.create_index(op.f(f'ix_{parent_tbl}_tenant_id'), parent_tbl, ['tenant_id'], unique=False)
        op.create_index(op.f(f'ix_{parent_tbl}_created_at'), parent_tbl, ['created_at'], unique=False)
        op.create_index(op.f(f'ix_{parent_tbl}_updated_at'), parent_tbl, ['updated_at'], unique=False)

        op.create_table(
            coding_tbl,
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column(fk_col, sa.BigInteger(), nullable=False),
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
            sa.ForeignKeyConstraint([fk_col], [f'{parent_tbl}.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f(f'ix_{coding_tbl}_{fk_col}'), coding_tbl, [fk_col], unique=False)
        op.create_index(op.f(f'ix_{coding_tbl}_tenant_id'), coding_tbl, ['tenant_id'], unique=False)
        op.create_index(op.f(f'ix_{coding_tbl}_created_at'), coding_tbl, ['created_at'], unique=False)
        op.create_index(op.f(f'ix_{coding_tbl}_updated_at'), coding_tbl, ['updated_at'], unique=False)

    # ── 8. Performer Tables ───────────────────────────────────────────────────
    op.create_table(
        'procedure_performer',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('procedure_pk', sa.BigInteger(), nullable=False),
        sa.Column('function_text', sa.String(), nullable=True),
        sa.Column('actor_reference', sa.String(), nullable=True),
        sa.Column('actor_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'Patient', 'RelatedPerson', 'Device', name='procedure_performer_actor_reference_type', create_type=False), nullable=False),
        sa.Column('actor_id', sa.BigInteger(), nullable=True),
        sa.Column('actor_display', sa.String(), nullable=True),
        sa.Column('on_behalf_of_reference', sa.String(), nullable=True),
        sa.Column('on_behalf_of_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('on_behalf_of_id', sa.BigInteger(), nullable=True),
        sa.Column('on_behalf_of_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['procedure_pk'], ['procedure.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_performer_procedure_pk'), 'procedure_performer', ['procedure_pk'], unique=False)
    op.create_index(op.f('ix_procedure_performer_actor_id'), 'procedure_performer', ['actor_id'], unique=False)
    op.create_index(op.f('ix_procedure_performer_on_behalf_of_id'), 'procedure_performer', ['on_behalf_of_id'], unique=False)
    op.create_index(op.f('ix_procedure_performer_tenant_id'), 'procedure_performer', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_procedure_performer_created_at'), 'procedure_performer', ['created_at'], unique=False)
    op.create_index(op.f('ix_procedure_performer_updated_at'), 'procedure_performer', ['updated_at'], unique=False)

    op.create_table(
        'procedure_performer_function_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('performer_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['performer_id'], ['procedure_performer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_performer_function_coding_performer_id'), 'procedure_performer_function_coding', ['performer_id'], unique=False)
    op.create_index(op.f('ix_procedure_performer_function_coding_tenant_id'), 'procedure_performer_function_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_procedure_performer_function_coding_created_at'), 'procedure_performer_function_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_procedure_performer_function_coding_updated_at'), 'procedure_performer_function_coding', ['updated_at'], unique=False)

    # ── 9. FocalDevice Tables ─────────────────────────────────────────────────
    op.create_table(
        'procedure_focal_device',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('procedure_pk', sa.BigInteger(), nullable=False),
        sa.Column('action_text', sa.String(), nullable=True),
        sa.Column('manipulated_reference', sa.String(), nullable=True),
        sa.Column('manipulated_type', postgresql.ENUM('Device', name='procedure_focal_device_manipulated_reference_type', create_type=False), nullable=False),
        sa.Column('manipulated_id', sa.BigInteger(), nullable=True),
        sa.Column('manipulated_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['procedure_pk'], ['procedure.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_focal_device_procedure_pk'), 'procedure_focal_device', ['procedure_pk'], unique=False)
    op.create_index(op.f('ix_procedure_focal_device_manipulated_id'), 'procedure_focal_device', ['manipulated_id'], unique=False)
    op.create_index(op.f('ix_procedure_focal_device_tenant_id'), 'procedure_focal_device', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_procedure_focal_device_created_at'), 'procedure_focal_device', ['created_at'], unique=False)
    op.create_index(op.f('ix_procedure_focal_device_updated_at'), 'procedure_focal_device', ['updated_at'], unique=False)

    op.create_table(
        'procedure_focal_device_action_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('focal_device_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['focal_device_id'], ['procedure_focal_device.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_focal_device_action_coding_focal_device_id'), 'procedure_focal_device_action_coding', ['focal_device_id'], unique=False)
    op.create_index(op.f('ix_procedure_focal_device_action_coding_tenant_id'), 'procedure_focal_device_action_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_procedure_focal_device_action_coding_created_at'), 'procedure_focal_device_action_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_procedure_focal_device_action_coding_updated_at'), 'procedure_focal_device_action_coding', ['updated_at'], unique=False)

    # ── 10. Note Table ────────────────────────────────────────────────────────
    op.create_table(
        'procedure_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('procedure_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_reference', sa.String(), nullable=True),
        sa.Column('author_reference_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Organization', name='procedure_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['procedure_pk'], ['procedure.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_note_procedure_pk'), 'procedure_note', ['procedure_pk'], unique=False)
    op.create_index(op.f('ix_procedure_note_author_reference_id'), 'procedure_note', ['author_reference_id'], unique=False)
    op.create_index(op.f('ix_procedure_note_tenant_id'), 'procedure_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_procedure_note_created_at'), 'procedure_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_procedure_note_updated_at'), 'procedure_note', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse FK order
    op.drop_table('procedure_note')

    op.drop_table('procedure_focal_device_action_coding')
    op.drop_table('procedure_focal_device')

    op.drop_table('procedure_performer_function_coding')
    op.drop_table('procedure_performer')

    for parent_tbl in ('procedure_used_code', 'procedure_follow_up', 'procedure_complication', 'procedure_body_site', 'procedure_reason_code'):
        op.drop_table(f"{parent_tbl}_coding")
        op.drop_table(parent_tbl)

    for tbl_name in ('procedure_used_reference', 'procedure_complication_detail', 'procedure_report', 'procedure_reason_reference', 'procedure_part_of', 'procedure_based_on'):
        op.drop_table(tbl_name)

    op.drop_table('procedure_identifier_type_coding')
    op.drop_table('procedure_identifier')

    for prefix in ('outcome', 'code', 'category', 'status_reason'):
        op.drop_table(f'procedure_{prefix}_coding')

    op.drop_table('procedure')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS procedure_pub_seq")

    # Drop enum types
    enums_to_drop = [
        'procedure_author_reference_type',
        'procedure_used_reference_reference_type',
        'procedure_focal_device_manipulated_reference_type',
        'procedure_complication_detail_reference_type',
        'procedure_report_reference_type',
        'procedure_reason_reference_reference_type',
        'procedure_performer_actor_reference_type',
        'procedure_asserter_reference_type',
        'procedure_recorder_reference_type',
        'procedure_part_of_reference_type',
        'procedure_based_on_reference_type',
        'procedure_subject_reference_type',
        'procedure_status',
    ]
    for enum_name in enums_to_drop:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
