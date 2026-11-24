"""medication_knowledge: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: d8e1f4a7c295
Revises: i0a5e8d2f649
Create Date: 2026-12-23 10:00:00.000000

Stores MedicationKnowledge whole in `content` (see MedicationKnowledgeModel's docstring), like the
other resources already moved (MedicationDispense i0a5e8d2f649, MedicationAdministration
h9f4d7c1e538, Medication a4f9b6d2e038, ...). The whole FHIR resource - `code`, `doseForm`,
`amount`, `synonym`, `relatedMedicationKnowledge`, `associatedMedication`, `productType`,
`monograph`, `ingredient`, `preparationInstruction`, `intendedRoute`, `cost`, `monitoringProgram`,
`administrationGuidelines`, `medicineClassification`, `packaging`, `drugCharacteristic`,
`contraindication`, `regulatory`, `kinetics` and `extension` - moves into
`medication_knowledge.content`; every column/table that survives is a search index for one of the
FHIR R4 MedicationKnowledge search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  medication_knowledge: status (the Postgres enum already held the true FHIR codes, so it
      stays), the manufacturer_* columns (`manufacturer_type` becomes a plain string); the public
      id gets its sequence as a server default; new: content.
  medication_knowledge_token: new - code, doseform, ingredient-code, classification,
      classification-type, monograph-type, monitoring-program-type, and (strings held as the
      code) monitoring-program-name and source-cost
  medication_knowledge_reference: new - ingredient and monograph
  dropped: every other child table, every main-table column with no search parameter and the
      per-field `medication_knowledge_*` enums (the status enum stays).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_medication_knowledge() logic (but keeping a reference's raw string, so an
absolute URL is not lost), so this migration never depends on application code that has since
changed; (2) drops the old child tables/columns and creates the index tables; (3) rebuilds the
index from `content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but
rebuilding the old normalized tables from it is not implemented - restore from a backup taken
before upgrading.
"""

import json
import re
import unicodedata
from datetime import date, datetime, time
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d8e1f4a7c295"
down_revision: Union[str, None] = "i0a5e8d2f649"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "medication_knowledge"

_STATUS = ("active", "inactive", "entered-in-error")


# -- shared helpers (frozen - never import application code here) ---------------------------


def _prune(value):
    if isinstance(value, dict):
        out = {k: _prune(v) for k, v in value.items()}
        return {k: v for k, v in out.items() if v is not None and v != [] and v != {}}
    if isinstance(value, list):
        out = [_prune(v) for v in value]
        return [v for v in out if v is not None and v != [] and v != {}]
    return value


def _iso(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


def _period(start, end):
    return {"start": _iso(start), "end": _iso(end)}


def _json(value):
    """A raw text() query can hand JSONB back as a string."""
    return json.loads(value) if isinstance(value, str) else value


def _rows(bind, sql, **params):
    return bind.execute(sa.text(sql), params).mappings().all()


def _norm(text):
    """Frozen copy of app.fhir.search.values.normalize."""
    if text is None:
        return None
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


# -- upgrade: old columns/tables -> content (frozen copy of the old mapper) ------

_COMPARATORS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


def _coding(c):
    return {
        "system": c["system"],
        "version": c["version"],
        "code": c["code"],
        "display": c["display"],
        "userSelected": c["user_selected"],
    }


def _concept(codings, text):
    return {"coding": [_coding(c) for c in codings], "text": text}


def _fallback_identifier(row, prefix):
    """The logical identifier of a Reference (read tolerantly)."""
    g = row.get
    return {
        "use": g(f"{prefix}_use"),
        "type": {
            "coding": [
                {
                    "system": g(f"{prefix}_type_system"),
                    "version": g(f"{prefix}_type_version"),
                    "code": g(f"{prefix}_type_code"),
                    "display": g(f"{prefix}_type_display"),
                    "userSelected": g(f"{prefix}_type_user_selected"),
                }
            ],
            "text": g(f"{prefix}_type_text"),
        },
        "system": g(f"{prefix}_system"),
        "value": g(f"{prefix}_value"),
        "period": _period(g(f"{prefix}_period_start"), g(f"{prefix}_period_end")),
    }


def _ref(row, prefix):
    """A Reference from the old `{prefix}_reference/_type/_id/_display/_identifier_*` columns."""
    g = row.get
    raw = g(f"{prefix}_reference")
    if not raw and g(f"{prefix}_type") and g(f"{prefix}_id"):
        raw = f"{g(f'{prefix}_type')}/{g(f'{prefix}_id')}"
    return {
        "reference": raw,
        "display": g(f"{prefix}_display"),
        "identifier": _fallback_identifier(row, f"{prefix}_identifier"),
    }


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _num(value):
    return float(value) if value is not None else None


def _quantity(row, prefix):
    """A Quantity from `{prefix}_value/_comparator/_unit/_system/_code`; prefix "" means bare."""
    g = row.get
    p = f"{prefix}_" if prefix else ""
    quantity = {
        "value": _num(g(f"{p}value")),
        "unit": g(f"{p}unit"),
        "system": g(f"{p}system"),
        "code": g(f"{p}code"),
    }
    if g(f"{p}comparator"):
        quantity["comparator"] = _COMPARATORS.get(str(g(f"{p}comparator")).lower())
    quantity = {k: v for k, v in quantity.items() if v is not None}
    return quantity or None


def _ratio(row, prefix):
    return {
        "numerator": _quantity(row, f"{prefix}_numerator"),
        "denominator": _quantity(row, f"{prefix}_denominator"),
    }


def _money(row, prefix):
    return {
        "value": _num(row.get(f"{prefix}_value")),
        "currency": row.get(f"{prefix}_currency"),
    }


def _cc(bind, table, fk, fk_value, text):
    """A CodeableConcept from `<table>` coding rows keyed on `fk` plus a text column."""
    return _concept(_rows_of(bind, table, fk, fk_value), text)


def _cc_list(bind, table, pk):
    """A 0..* CodeableConcept held as `<P>_<table>` (text) + `<P>_<table>_coding`."""
    return [
        _concept(
            _rows_of(bind, f"{P}_{table}_coding", f"{P}_{table}_id", row["id"]),
            row["text"],
        )
        for row in _rows_of(bind, f"{P}_{table}", f"{P}_pk", pk)
    ]


def _related(bind, r):
    return {
        "type": _cc(
            bind,
            f"{P}_related_type_coding",
            f"{P}_related_id",
            r["id"],
            r["type_text"],
        ),
        "reference": [
            _ref(x, "reference")
            for x in _rows_of(
                bind, f"{P}_related_reference", f"{P}_related_id", r["id"]
            )
        ],
    }


def _monograph(bind, m):
    return {
        "type": _cc(
            bind,
            f"{P}_monograph_type_coding",
            f"{P}_monograph_id",
            m["id"],
            m["type_text"],
        ),
        "source": _ref(m, "source"),
    }


def _ingredient(bind, i):
    entry = {
        "isActive": i["is_active"],
        "strength": _ratio(i, "strength"),
    }
    concept = _cc(
        bind,
        f"{P}_ingredient_item_coding",
        f"{P}_ingredient_id",
        i["id"],
        i["item_codeable_concept_text"],
    )
    if _prune(concept):
        entry["itemCodeableConcept"] = concept
    reference = _ref(i, "item")
    if _prune(reference):
        entry["itemReference"] = reference
    return entry


def _cost(bind, c):
    return {
        "type": _cc(
            bind, f"{P}_cost_type_coding", f"{P}_cost_id", c["id"], c["type_text"]
        ),
        "source": c["source"],
        "cost": _money(c, "cost"),
    }


def _monitoring_program(bind, m):
    return {
        "type": _cc(
            bind,
            f"{P}_monitoring_program_type_coding",
            f"{P}_monitoring_program_id",
            m["id"],
            m["type_text"],
        ),
        "name": m["name"],
    }


def _admin_guideline(bind, ag):
    aid = ag["id"]
    fk = f"{P}_admin_guideline_id"
    entry = {
        "dosage": [
            {
                "type": _cc(
                    bind,
                    f"{P}_ag_dosage_type_coding",
                    f"{P}_ag_dosage_id",
                    d["id"],
                    d["type_text"],
                ),
                "dosage": _json(d["dosage"]),
            }
            for d in _rows_of(bind, f"{P}_ag_dosage", fk, aid)
        ],
        "patientCharacteristics": [
            {
                "characteristicCodeableConcept": _cc(
                    bind,
                    f"{P}_ag_patient_char_coding",
                    f"{P}_ag_patient_char_id",
                    pc["id"],
                    pc["characteristic_codeable_concept_text"],
                ),
                "characteristicQuantity": _quantity(pc, "characteristic_quantity"),
                "value": list(pc["value"] or []),
            }
            for pc in _rows_of(bind, f"{P}_ag_patient_char", fk, aid)
        ],
    }
    concept = _cc(
        bind,
        f"{P}_ag_indication_coding",
        fk,
        aid,
        ag["indication_codeable_concept_text"],
    )
    if _prune(concept):
        entry["indicationCodeableConcept"] = concept
    reference = _ref(ag, "indication")
    if _prune(reference):
        entry["indicationReference"] = reference
    return entry


def _medicine_classification(bind, mc):
    return {
        "type": _cc(
            bind,
            f"{P}_med_class_type_coding",
            f"{P}_medicine_classification_id",
            mc["id"],
            mc["type_text"],
        ),
        "classification": [
            _concept(
                _rows_of(
                    bind,
                    f"{P}_med_class_item_coding",
                    f"{P}_med_class_item_id",
                    item["id"],
                ),
                item["text"],
            )
            for item in _rows_of(
                bind, f"{P}_med_class_item", f"{P}_medicine_classification_id", mc["id"]
            )
        ],
    }


def _drug_characteristic(bind, dc):
    entry = {
        "type": _cc(
            bind,
            f"{P}_drug_char_type_coding",
            f"{P}_drug_characteristic_id",
            dc["id"],
            dc["type_text"],
        ),
        "valueString": dc["value_string"],
        "valueQuantity": _quantity(dc, "value_quantity"),
        "valueBase64Binary": dc["value_base64_binary"],
    }
    concept = _cc(
        bind,
        f"{P}_drug_char_val_coding",
        f"{P}_drug_characteristic_id",
        dc["id"],
        dc["value_codeable_concept_text"],
    )
    if _prune(concept):
        entry["valueCodeableConcept"] = concept
    return entry


def _regulatory(bind, reg):
    rid = reg["id"]
    fk = f"{P}_regulatory_id"
    return {
        "regulatoryAuthority": _ref(reg, "regulatory_authority"),
        "substitution": [
            {
                "type": _cc(
                    bind,
                    f"{P}_reg_sub_type_coding",
                    f"{P}_reg_sub_id",
                    s["id"],
                    s["type_text"],
                ),
                "allowed": s["allowed"],
            }
            for s in _rows_of(bind, f"{P}_reg_sub", fk, rid)
        ],
        "schedule": [
            {
                "schedule": _cc(
                    bind,
                    f"{P}_reg_sched_coding",
                    f"{P}_reg_sched_id",
                    sc["id"],
                    sc["schedule_text"],
                )
            }
            for sc in _rows_of(bind, f"{P}_reg_sched", fk, rid)
        ],
        "maxDispense": {
            "quantity": _quantity(reg, "max_dispense_quantity"),
            "period": _quantity(reg, "max_dispense_period"),
        },
    }


def _kinetics(bind, k):
    kid = k["id"]
    fk = f"{P}_kinetics_id"
    return {
        "areaUnderCurve": [
            _quantity(a, "") for a in _rows_of(bind, f"{P}_kinetics_auc", fk, kid)
        ],
        "lethalDose50": [
            _quantity(a, "") for a in _rows_of(bind, f"{P}_kinetics_ld50", fk, kid)
        ],
        "halfLifePeriod": _quantity(k, "half_life_period"),
    }


def _build_content(bind, r):
    pk = r["id"]

    def by_pk(table):
        return _rows_of(bind, f"{P}_{table}", f"{P}_pk", pk)

    content = {
        "extension": list(_json(r["extension"]) or []),
        "code": _cc(bind, f"{P}_code_coding", f"{P}_pk", pk, r["code_text"]),
        "status": r["status_text"],
        "manufacturer": _ref(r, "manufacturer"),
        "doseForm": _cc(
            bind, f"{P}_dose_form_coding", f"{P}_pk", pk, r["dose_form_text"]
        ),
        "amount": _quantity(r, "amount"),
        "synonym": list(r["synonym"] or []),
        "relatedMedicationKnowledge": [_related(bind, x) for x in by_pk("related")],
        "associatedMedication": [
            _ref(x, "reference") for x in by_pk("associated_medication")
        ],
        "productType": _cc_list(bind, "product_type", pk),
        "monograph": [_monograph(bind, x) for x in by_pk("monograph")],
        "ingredient": [_ingredient(bind, x) for x in by_pk("ingredient")],
        "preparationInstruction": r["preparation_instruction"],
        "intendedRoute": _cc_list(bind, "intended_route", pk),
        "cost": [_cost(bind, x) for x in by_pk("cost")],
        "monitoringProgram": [
            _monitoring_program(bind, x) for x in by_pk("monitoring_program")
        ],
        "administrationGuidelines": [
            _admin_guideline(bind, x) for x in by_pk("admin_guideline")
        ],
        "medicineClassification": [
            _medicine_classification(bind, x) for x in by_pk("medicine_classification")
        ],
        "packaging": {
            "type": _cc(
                bind,
                f"{P}_packaging_type_coding",
                f"{P}_pk",
                pk,
                r["packaging_type_text"],
            ),
            "quantity": _quantity(r, "packaging_quantity"),
        },
        "drugCharacteristic": [
            _drug_characteristic(bind, x) for x in by_pk("drug_characteristic")
        ],
        "contraindication": [_ref(x, "reference") for x in by_pk("contraindication")],
        "regulatory": [_regulatory(bind, x) for x in by_pk("regulatory")],
        "kinetics": [_kinetics(bind, x) for x in by_pk("kinetics")],
    }
    return _prune(content)


def _backfill_content(bind):
    # `status` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, f"SELECT *, status::text AS status_text FROM {P}"):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {
                "c": json.dumps(_build_content(bind, dict(r)), default=str),
                "id": r["id"],
            },
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) ---------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_MANUFACTURER_TYPES = ("Organization",)
_REFERENCE_TYPES = {
    "ingredient": ("Substance",),
    "monograph": ("DocumentReference", "Media"),
}


def _typed(reference, allowed):
    match = _REF.match(reference or "")
    if match and match["type"] in allowed:
        return match["type"], int(match["id"])
    return None, None


def _ref_params(prefix, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    rtype, rid = _typed(reference, allowed)
    return {
        f"{prefix}_reference": reference,
        f"{prefix}_type": rtype,
        f"{prefix}_id": rid,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def _insert_token(bind, pk, param, concept):
    if not isinstance(concept, dict):
        return
    text = _norm(concept.get("text"))
    codings = [
        c
        for c in concept.get("coding") or []
        if c.get("system") or c.get("code") or c.get("display")
    ]
    for c in codings or ([{}] if text else []):
        bind.execute(
            sa.text(
                f"INSERT INTO {P}_token ({P}_pk, param, system, code, display_norm, text_norm) "
                "VALUES (:pk, :param, :s, :c, :d, :t)"
            ),
            {
                "pk": pk,
                "param": param,
                "s": c.get("system"),
                "c": c.get("code"),
                "d": _norm(c.get("display")),
                "t": text,
            },
        )


def _insert_string_token(bind, pk, param, value):
    if isinstance(value, str) and value:
        bind.execute(
            sa.text(
                f"INSERT INTO {P}_token ({P}_pk, param, code) VALUES (:pk, :param, :c)"
            ),
            {"pk": pk, "param": param, "c": value},
        )


def _insert_reference(bind, pk, param, ref):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, _REFERENCE_TYPES[param])
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_reference ({P}_pk, param, reference_reference, reference_type, "
            "reference_id, reference_identifier_system, reference_identifier_value) "
            "VALUES (:pk, :param, :r, :t, :i, :s, :v)"
        ),
        {
            "pk": pk,
            "param": param,
            "r": reference,
            "t": rtype,
            "i": rid,
            "s": identifier.get("system"),
            "v": identifier.get("value"),
        },
    )


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])
        status = doc.get("status")
        columns = _ref_params(
            "manufacturer", doc.get("manufacturer"), _MANUFACTURER_TYPES
        )
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS medication_knowledge_status), {sets} "
                "WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )
        _insert_token(bind, pk, "code", doc.get("code"))
        _insert_token(bind, pk, "doseform", doc.get("doseForm"))
        for ingredient in doc.get("ingredient") or []:
            ingredient = ingredient or {}
            _insert_token(
                bind, pk, "ingredient-code", ingredient.get("itemCodeableConcept")
            )
            _insert_reference(bind, pk, "ingredient", ingredient.get("itemReference"))
        for classification in doc.get("medicineClassification") or []:
            classification = classification or {}
            _insert_token(bind, pk, "classification-type", classification.get("type"))
            for concept in classification.get("classification") or []:
                _insert_token(bind, pk, "classification", concept)
        for monograph in doc.get("monograph") or []:
            monograph = monograph or {}
            _insert_token(bind, pk, "monograph-type", monograph.get("type"))
            _insert_reference(bind, pk, "monograph", monograph.get("source"))
        for program in doc.get("monitoringProgram") or []:
            program = program or {}
            _insert_token(bind, pk, "monitoring-program-type", program.get("type"))
            _insert_string_token(
                bind, pk, "monitoring-program-name", program.get("name")
            )
        for cost in doc.get("cost") or []:
            _insert_string_token(bind, pk, "source-cost", (cost or {}).get("source"))


# Main-table columns that survive unchanged: the id, the audit/tenant columns, the status (an
# enum that already held the true FHIR codes) and the manufacturer index columns (the
# reference-type enum becomes a plain string).
_KEEP = {
    "id",
    "medication_knowledge_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "status",
    "manufacturer_reference",
    "manufacturer_type",
    "manufacturer_id",
    "manufacturer_identifier_system",
    "manufacturer_identifier_value",
}


def _fk():
    return sa.Column(
        f"{P}_pk", sa.BigInteger(), sa.ForeignKey(f"{P}.id"), nullable=False
    )


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        P, sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    _backfill_content(bind)

    # Every old child table (the prefix is unique to this resource).
    for (table,) in bind.execute(
        sa.text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
            "AND table_name LIKE 'medication\\_knowledge\\_%' AND table_type = 'BASE TABLE'"
        )
    ).all():
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    existing = [
        r[0]
        for r in bind.execute(
            sa.text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{P}' "
                "AND table_schema = current_schema()"
            )
        )
    ]
    for column in existing:
        if column not in _KEEP:
            op.drop_column(P, column)

    # The manufacturer's reference type was an enum; it is a plain string now.
    op.alter_column(
        P,
        "manufacturer_type",
        type_=sa.String(),
        nullable=True,
        postgresql_using="manufacturer_type::text",
    )
    # Every per-field `medication_knowledge_*` enum of the old schema except the status.
    for (name,) in bind.execute(
        sa.text(
            "SELECT typname FROM pg_type WHERE typtype = 'e' AND typname LIKE 'medication\\_knowledge\\_%' "
            "AND typname <> 'medication_knowledge_status'"
        )
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN medication_knowledge_id SET DEFAULT nextval('medication_knowledge_pub_seq')"
    )

    # The audit columns as the shared mixin declares them (the original table was created with
    # looser ones): tenant/actor NOT NULL, timestamps nullable and indexed, and no UNIQUE on the
    # public id (the sequence keeps it unique).
    op.execute(f"UPDATE {P} SET tenant_id = '' WHERE tenant_id IS NULL")
    op.execute(f"UPDATE {P} SET created_by = '' WHERE created_by IS NULL")
    op.alter_column(P, "tenant_id", existing_type=sa.String(), nullable=False)
    op.alter_column(P, "created_by", existing_type=sa.String(), nullable=False)
    op.alter_column(
        P, "created_at", existing_type=sa.DateTime(timezone=True), nullable=True
    )
    op.alter_column(
        P, "updated_at", existing_type=sa.DateTime(timezone=True), nullable=True
    )
    op.execute(
        f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS medication_knowledge_medication_knowledge_id_key"
    )
    for column in ("id", "tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status: the enum stays; the column is nullable (an index, not a requirement).
    op.alter_column(
        P,
        "status",
        existing_type=postgresql.ENUM(
            *_STATUS, name="medication_knowledge_status", create_type=False
        ),
        nullable=True,
    )

    op.create_table(
        f"{P}_token",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("param", sa.String(), nullable=False),
        sa.Column("system", sa.String(), nullable=True),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("display_norm", sa.String(), nullable=True),
        sa.Column("text_norm", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_token", f"{P}_pk")
    op.create_index(
        "ix_medication_knowledge_token_param_code", f"{P}_token", ["param", "code"]
    )

    op.create_table(
        f"{P}_reference",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("param", sa.String(), nullable=False),
        sa.Column("reference_reference", sa.String(), nullable=True),
        sa.Column("reference_type", sa.String(), nullable=True),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.Column("reference_identifier_system", sa.String(), nullable=True),
        sa.Column("reference_identifier_value", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_reference", f"{P}_pk")
    op.create_index(
        "ix_medication_knowledge_reference_param_type_id",
        f"{P}_reference",
        ["param", "reference_type", "reference_id"],
    )

    _rebuild_index(bind)
    op.create_index(
        f"ix_{P}_manufacturer_id", P, ["manufacturer_id"], if_not_exists=True
    )
    op.create_index(
        "ix_medication_knowledge_medication_knowledge_id",
        P,
        ["medication_knowledge_id"],
        unique=True,
        if_not_exists=True,
    )
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "medication_knowledge content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
