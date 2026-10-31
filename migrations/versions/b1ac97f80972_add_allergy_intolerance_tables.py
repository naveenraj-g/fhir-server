"""add_allergy_intolerance_tables

Revision ID: b1ac97f80972
Revises: c7e4a1b92d83
Create Date: 2026-10-31 11:09:48.088667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1ac97f80972'
down_revision: Union[str, None] = 'c7e4a1b92d83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ───────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allergy_intolerance_type AS ENUM ('allergy', 'intolerance');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allergy_intolerance_category AS ENUM ('food', 'medication', 'environment', 'biologic');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allergy_intolerance_criticality AS ENUM ('low', 'high', 'unable-to-assess');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allergy_intolerance_severity AS ENUM ('mild', 'moderate', 'severe');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allergy_intolerance_patient_reference_type AS ENUM ('Patient');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allergy_intolerance_encounter_reference_type AS ENUM ('Encounter');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allergy_intolerance_recorder_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allergy_intolerance_asserter_reference_type AS ENUM (
                'Patient', 'RelatedPerson', 'Practitioner', 'PractitionerRole'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allergy_intolerance_note_author_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allergy_intolerance_reaction_note_author_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ── 2. Sequence ────────────────────────────────────────────────────────────
    op.execute('CREATE SEQUENCE IF NOT EXISTS allergy_intolerance_pub_seq START 260000 INCREMENT 1')

    # ── 3. Main Table ──────────────────────────────────────────────────────────
    op.create_table(
        'allergy_intolerance',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('clinical_status_text', sa.String(), nullable=True),
        sa.Column('verification_status_text', sa.String(), nullable=True),
        sa.Column('type', postgresql.ENUM('allergy', 'intolerance', name='allergy_intolerance_type', create_type=False), nullable=True),
        sa.Column('category', sa.ARRAY(postgresql.ENUM('food', 'medication', 'environment', 'biologic', name='allergy_intolerance_category', create_type=False)), nullable=True),
        sa.Column('criticality', postgresql.ENUM('low', 'high', 'unable-to-assess', name='allergy_intolerance_criticality', create_type=False), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('patient_reference', sa.String(), nullable=False),
        sa.Column('patient_type', postgresql.ENUM('Patient', name='allergy_intolerance_patient_reference_type', create_type=False), nullable=False),
        sa.Column('patient_id', sa.BigInteger(), nullable=True),
        sa.Column('patient_display', sa.String(), nullable=True),
        sa.Column('encounter_reference', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM('Encounter', name='allergy_intolerance_encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.BigInteger(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('onset_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onset_age', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('onset_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onset_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onset_range', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('onset_string', sa.String(), nullable=True),
        sa.Column('recorded_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recorder_reference', sa.String(), nullable=True),
        sa.Column('recorder_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', name='allergy_intolerance_recorder_reference_type', create_type=False), nullable=True),
        sa.Column('recorder_id', sa.BigInteger(), nullable=True),
        sa.Column('recorder_display', sa.String(), nullable=True),
        sa.Column('asserter_reference', sa.String(), nullable=True),
        sa.Column('asserter_type', postgresql.ENUM('Patient', 'RelatedPerson', 'Practitioner', 'PractitionerRole', name='allergy_intolerance_asserter_reference_type', create_type=False), nullable=True),
        sa.Column('asserter_id', sa.BigInteger(), nullable=True),
        sa.Column('asserter_display', sa.String(), nullable=True),
        sa.Column('last_occurrence', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_allergy_intolerance_id'), 'allergy_intolerance', ['allergy_intolerance_id'], unique=True)
    op.create_index(op.f('ix_allergy_intolerance_created_at'), 'allergy_intolerance', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_tenant_id'), 'allergy_intolerance', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_updated_at'), 'allergy_intolerance', ['updated_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_user_id'), 'allergy_intolerance', ['user_id'], unique=False)

    # ── 4. Clinical Status Coding ──────────────────────────────────────────────
    op.create_table(
        'allergy_intolerance_clinical_status_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['allergy_intolerance_pk'], ['allergy_intolerance.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_clinical_status_coding_allergy_intolerance_pk'), 'allergy_intolerance_clinical_status_coding', ['allergy_intolerance_pk'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_clinical_status_coding_created_at'), 'allergy_intolerance_clinical_status_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_clinical_status_coding_tenant_id'), 'allergy_intolerance_clinical_status_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_clinical_status_coding_updated_at'), 'allergy_intolerance_clinical_status_coding', ['updated_at'], unique=False)

    # ── 5. Verification Status Coding ──────────────────────────────────────────
    op.create_table(
        'allergy_intolerance_verification_status_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['allergy_intolerance_pk'], ['allergy_intolerance.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_verification_status_coding_allergy_intolerance_pk'), 'allergy_intolerance_verification_status_coding', ['allergy_intolerance_pk'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_verification_status_coding_created_at'), 'allergy_intolerance_verification_status_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_verification_status_coding_tenant_id'), 'allergy_intolerance_verification_status_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_verification_status_coding_updated_at'), 'allergy_intolerance_verification_status_coding', ['updated_at'], unique=False)

    # ── 6. Code Coding ─────────────────────────────────────────────────────────
    op.create_table(
        'allergy_intolerance_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['allergy_intolerance_pk'], ['allergy_intolerance.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_code_coding_allergy_intolerance_pk'), 'allergy_intolerance_code_coding', ['allergy_intolerance_pk'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_code_coding_created_at'), 'allergy_intolerance_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_code_coding_tenant_id'), 'allergy_intolerance_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_code_coding_updated_at'), 'allergy_intolerance_code_coding', ['updated_at'], unique=False)

    # ── 7. Identifier ──────────────────────────────────────────────────────────
    op.create_table(
        'allergy_intolerance_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['allergy_intolerance_pk'], ['allergy_intolerance.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_identifier_allergy_intolerance_pk'), 'allergy_intolerance_identifier', ['allergy_intolerance_pk'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_identifier_created_at'), 'allergy_intolerance_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_identifier_tenant_id'), 'allergy_intolerance_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_identifier_updated_at'), 'allergy_intolerance_identifier', ['updated_at'], unique=False)

    # ── 8. Identifier Type Coding ──────────────────────────────────────────────
    op.create_table(
        'allergy_intolerance_identifier_type_coding',
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
        sa.ForeignKeyConstraint(['identifier_id'], ['allergy_intolerance_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_identifier_type_coding_created_at'), 'allergy_intolerance_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_identifier_type_coding_identifier_id'), 'allergy_intolerance_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_identifier_type_coding_tenant_id'), 'allergy_intolerance_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_identifier_type_coding_updated_at'), 'allergy_intolerance_identifier_type_coding', ['updated_at'], unique=False)

    # ── 9. Note ────────────────────────────────────────────────────────────────
    op.create_table(
        'allergy_intolerance_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', name='allergy_intolerance_note_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['allergy_intolerance_pk'], ['allergy_intolerance.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_note_allergy_intolerance_pk'), 'allergy_intolerance_note', ['allergy_intolerance_pk'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_note_created_at'), 'allergy_intolerance_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_note_tenant_id'), 'allergy_intolerance_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_note_updated_at'), 'allergy_intolerance_note', ['updated_at'], unique=False)

    # ── 10. Reaction ───────────────────────────────────────────────────────────
    op.create_table(
        'allergy_intolerance_reaction',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_pk', sa.BigInteger(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('onset', sa.DateTime(timezone=True), nullable=True),
        sa.Column('severity', postgresql.ENUM('mild', 'moderate', 'severe', name='allergy_intolerance_severity', create_type=False), nullable=True),
        sa.Column('substance_text', sa.String(), nullable=True),
        sa.Column('exposure_route_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['allergy_intolerance_pk'], ['allergy_intolerance.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_reaction_allergy_intolerance_pk'), 'allergy_intolerance_reaction', ['allergy_intolerance_pk'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_created_at'), 'allergy_intolerance_reaction', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_tenant_id'), 'allergy_intolerance_reaction', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_updated_at'), 'allergy_intolerance_reaction', ['updated_at'], unique=False)

    # ── 11. Reaction Substance Coding ──────────────────────────────────────────
    op.create_table(
        'allergy_intolerance_reaction_substance_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('reaction_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['reaction_id'], ['allergy_intolerance_reaction.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_reaction_substance_coding_created_at'), 'allergy_intolerance_reaction_substance_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_substance_coding_reaction_id'), 'allergy_intolerance_reaction_substance_coding', ['reaction_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_substance_coding_tenant_id'), 'allergy_intolerance_reaction_substance_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_substance_coding_updated_at'), 'allergy_intolerance_reaction_substance_coding', ['updated_at'], unique=False)

    # ── 12. Reaction Manifestation ─────────────────────────────────────────────
    op.create_table(
        'allergy_intolerance_reaction_manifestation',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('reaction_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['reaction_id'], ['allergy_intolerance_reaction.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_reaction_manifestation_created_at'), 'allergy_intolerance_reaction_manifestation', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_manifestation_reaction_id'), 'allergy_intolerance_reaction_manifestation', ['reaction_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_manifestation_tenant_id'), 'allergy_intolerance_reaction_manifestation', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_manifestation_updated_at'), 'allergy_intolerance_reaction_manifestation', ['updated_at'], unique=False)

    # ── 13. Reaction Manifestation Coding ──────────────────────────────────────
    op.create_table(
        'allergy_intolerance_reaction_manifestation_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('manifestation_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['manifestation_id'], ['allergy_intolerance_reaction_manifestation.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_reaction_manifestation_coding_created_at'), 'allergy_intolerance_reaction_manifestation_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_manifestation_coding_manifestation_id'), 'allergy_intolerance_reaction_manifestation_coding', ['manifestation_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_manifestation_coding_tenant_id'), 'allergy_intolerance_reaction_manifestation_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_manifestation_coding_updated_at'), 'allergy_intolerance_reaction_manifestation_coding', ['updated_at'], unique=False)

    # ── 14. Reaction Exposure Route Coding ─────────────────────────────────────
    op.create_table(
        'allergy_intolerance_reaction_exposure_route_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('reaction_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['reaction_id'], ['allergy_intolerance_reaction.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_reaction_exposure_route_coding_created_at'), 'allergy_intolerance_reaction_exposure_route_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_exposure_route_coding_reaction_id'), 'allergy_intolerance_reaction_exposure_route_coding', ['reaction_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_exposure_route_coding_tenant_id'), 'allergy_intolerance_reaction_exposure_route_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_exposure_route_coding_updated_at'), 'allergy_intolerance_reaction_exposure_route_coding', ['updated_at'], unique=False)

    # ── 15. Reaction Note ──────────────────────────────────────────────────────
    op.create_table(
        'allergy_intolerance_reaction_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('reaction_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', name='allergy_intolerance_reaction_note_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['reaction_id'], ['allergy_intolerance_reaction.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergy_intolerance_reaction_note_created_at'), 'allergy_intolerance_reaction_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_note_reaction_id'), 'allergy_intolerance_reaction_note', ['reaction_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_note_tenant_id'), 'allergy_intolerance_reaction_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_reaction_note_updated_at'), 'allergy_intolerance_reaction_note', ['updated_at'], unique=False)


def downgrade() -> None:
    # ── Drop Tables in Reverse Dependency Order ────────────────────────────────
    op.drop_table('allergy_intolerance_reaction_note')
    op.drop_table('allergy_intolerance_reaction_exposure_route_coding')
    op.drop_table('allergy_intolerance_reaction_manifestation_coding')
    op.drop_table('allergy_intolerance_reaction_manifestation')
    op.drop_table('allergy_intolerance_reaction_substance_coding')
    op.drop_table('allergy_intolerance_reaction')
    op.drop_table('allergy_intolerance_note')
    op.drop_table('allergy_intolerance_identifier_type_coding')
    op.drop_table('allergy_intolerance_identifier')
    op.drop_table('allergy_intolerance_code_coding')
    op.drop_table('allergy_intolerance_verification_status_coding')
    op.drop_table('allergy_intolerance_clinical_status_coding')
    op.drop_table('allergy_intolerance')

    # ── Drop Sequence ──────────────────────────────────────────────────────────
    op.execute('DROP SEQUENCE IF EXISTS allergy_intolerance_pub_seq')

    # ── Drop Enum Types ────────────────────────────────────────────────────────
    op.execute('DROP TYPE IF EXISTS allergy_intolerance_reaction_note_author_reference_type')
    op.execute('DROP TYPE IF EXISTS allergy_intolerance_note_author_reference_type')
    op.execute('DROP TYPE IF EXISTS allergy_intolerance_asserter_reference_type')
    op.execute('DROP TYPE IF EXISTS allergy_intolerance_recorder_reference_type')
    op.execute('DROP TYPE IF EXISTS allergy_intolerance_encounter_reference_type')
    op.execute('DROP TYPE IF EXISTS allergy_intolerance_patient_reference_type')
    op.execute('DROP TYPE IF EXISTS allergy_intolerance_severity')
    op.execute('DROP TYPE IF EXISTS allergy_intolerance_criticality')
    op.execute('DROP TYPE IF EXISTS allergy_intolerance_category')
    op.execute('DROP TYPE IF EXISTS allergy_intolerance_type')
