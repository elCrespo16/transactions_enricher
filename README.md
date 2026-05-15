# Transactions Enricher

Small utility to enrich bank transaction CSVs using configurable rules.

Supports loading a bank configuration and a set of rules (YAML) to transform
or duplicate rows based on arbitrary conditions. Designed to be lightweight
and easily extended with new operations or condition types.

**Features**
- **Config-driven**: Bank-level config describes input folder, separator
	and rules file.
- **Rule engine**: Apply conditions to rows and run operations (add/change
	columns, duplicate or delete rows, copy values).
- **CSV-friendly**: Handles padding rows and commas inside quoted fields.
- **Extensible**: Add new operations through `operations.py` and conditions
	through `conditions.py`.

**Quick Start**

Requirements
- Python 3.8+
- Dependencies: `pydantic`, `PyYAML`

Install dependencies (example):

```
pip install pydantic pyyaml
```

Generate a default bank config and rules:

```
python main.py -f mybank.yaml --generate_default_config
```

Run the enricher with an existing config:

```
python main.py -f mybank.yaml
```

This will read CSV files from the `transactions_path` defined in the
bank config and write enriched files next to each input file with the
suffix `_enriched.csv`.

**Files of interest**
- `main.py` — CLI entry point.
- `transactions_enricher.py` — Core orchestration (loads config, parses
	CSVs, applies rules, writes outputs).
- `bank_rules.py` — Rule and `BankRules` models that load YAML rules.
- `conditions.py` — Condition/Operator implementations used by rules.
- `operations.py` — Supported operations and factory registration.
- `trade_republic_preprocessor.py` — Example preprocessor for a specific
	bank CSV layout (batch-based parser + normalizer).

**Bank config (example)**

A bank config YAML is loaded into `BankConfig` and contains:

- `bank_name`: logical name
- `transactions_path`: folder with input CSV files
- `rules_config_path`: path to rules YAML
- `padding_rows`: number of header/padding rows to skip
- `separator`: CSV field separator (default `,`)

Use `BankEnricher.generate_default_config` to scaffold these automatically.

**Rules YAML (example)**

Rules are expressed as a list. Each rule has `conditions` and `operations`.

Example rule snippet:

```yaml
rules:
  - conditions:
      - column: description
        operator: contains
        value: sample
    operations:
      - operation_type: add_column
        column_values:
          - column: category
            value: sample_category
      - operation_type: arithmetic_operation
        operator: concat
        destination: description_copy
        column_values:
          - column: description
          - column: category
```

Condition fields:
- `column`: column name to evaluate
- `operator`: one of `contains`, `=`, `>`, `<` (see `conditions.py`)
- `value`: comparison value

Operations
- `duplicate_row`: returns original and a modified duplicate
- `add_column`: adds a new column if missing
- `change_value`: sets a column value
- `copy_columns`: copies value from one column to another
- `delete_column`: removes a column from the row
- `arithmetic_operation`: writes `destination` from `sources`

Arithmetic operation fields
- `destination`: target column to write
- `column_values`: ordered list of source columns (each entry uses `column` to name the source)
- `operator`: validated enum values: `+`, `-`, `concat`

Extending
- To add an operation: implement an `Operation` subclass in
	`operations.py` and register it with `OperationFactory.register(...)`.
- To add a condition/operator: add a new `Operator` in `conditions.py`
	and ensure `OperatorFactory` can create it.

Notes & Caveats
- CSV parsing in `transactions_enricher.py` currently uses simple
	split-based parsing with a regexp helper to remove separators inside
	quoted strings. For complex CSVs consider using Python's `csv` module.
- No automated tests are included in the repository; adding unit tests
	for the rule engine is recommended before further changes.

License & Contributing
- This repository currently has no license file. Add one if you plan to
	share the code.
- Contributions: open an issue or PR with a focused change (new
	operation, operator, bugfix or tests).

If you want, I can also add a minimal `requirements.txt` and a simple
example config + rules file to help get started. Would you like that?
