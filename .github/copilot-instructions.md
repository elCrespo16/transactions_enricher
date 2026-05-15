# Copilot / AI assistant instructions for Transactions Enricher

This repository is a small, rule-driven CSV transaction enricher written in Python.
Follow these focused, actionable notes to be productive immediately.

1) Big picture
- Core orchestrator: `transactions_enricher.BankEnricher` (constructed from `main.py`).
- Config-driven: Each bank has a YAML `BankConfig` (see `transactions_enricher.BankConfig`)
- Rule engine: `bank_rules.BankRules` loads `Rule` objects (conditions -> operations). Rules are YAML lists under `rules:`.

2) Quick dev / run commands
- Install minimal deps: `pip install pydantic PyYAML` (or use `requirements.txt` if updated).
- Generate a scaffold config: `python main.py -f <bank_config.yaml> --generate_default_config`.
- Run enrichment: `python main.py -f <bank_config.yaml>` (writes files with suffix `_enriched.csv`).

3) Data flow & file conventions
- Input: CSV files under the `transactions_path` defined in the bank config. Files ending with `_enriched.csv` are ignored.
- Parsing: `BankEnricher.enrich_bank_transactions` reads CSV using `csv.DictReader` and honors `padding_rows` and `separator` from config.
- Output: Each input file produces `<input>_enriched.csv` with header columns derived from the first enriched row.

4) Rules YAML shape (concrete example)
```
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
```
- Condition fields: `column`, `operator` (see `conditions.OperatorEnum`), `value`.
- Operation DTO: `operation_type` (see `operations.OperationsEnum`) and `column_values` list.

5) Extension points and concrete patterns
- For any new code, follow existing patterns in the repo for consistency and apply SOLID principles, without over-engineering.
- Add an operation: implement a subclass of `Operation` in `operations.py` and register via `@OperationFactory.register(OperationsEnum.YOUR_OP)`.
- Add an operator/condition: add an `Operator` implementation in `conditions.py` and map it in `OperatorFactory.operator_mapping`.
- Rules may duplicate rows via `duplicate_row` operation — code expects operations to return either `None` or a list of rows.

6) Project-specific conventions / gotchas
- `OperationConfig.dict()` serializes `operation_type` as the enum value string; rules YAML must use string enums (e.g., `add_column`).
- `Condition.is_applicable` uses `OperatorFactory.create(self.operator)` — the code passes Enum values not raw strings; keep operator values consistent with `OperatorEnum`.
- CSV parsing currently relies on `csv.DictReader` and `trade_republic_preprocessor.py` implements a specialized batch parser for a bank with 3-row batches — use it as an example for non-standard CSVs.
- Logging: `main.configure_logging` configures file and console logging; prefer using the logger for traceability.

7) Files to inspect for implementation examples
- Orchestrator & CLI: `main.py` and `transactions_enricher.py`
- Rule models: `bank_rules.py`
- Operations & factory: `operations.py`
- Conditions/operators: `conditions.py`
- Bank-specific preprocessor example: `trade_republic_preprocessor.py`

8) Tests & safety
- There are currently no unit tests in the repo. When modifying behavior of the rule engine, add targeted tests around `Rule.check_and_apply`, `Operation` implementations, and `Condition` operators.

If anything in this file is unclear or you'd like me to include concrete sample config/rules files or a small test harness, tell me which bank folder (for example `b100_transactions`) to base examples on and I'll add them.
