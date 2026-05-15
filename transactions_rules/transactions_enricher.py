from typing import Dict, List, Optional
import copy
import logging
import os

import yaml
from pydantic import BaseModel

from transactions_rules.bank_rules import BankRules, Rule
from transactions_rules.conditions import Condition, OperatorEnum
from transactions_rules.operations import (
    ArithmeticOperationConfig,
    ArithmeticOperatorEnum,
    ColumnValue,
    OperationConfig,
    OperationsEnum,
)

logger = logging.getLogger(__name__)


class BankConfig(BaseModel):
    bank_name: Optional[str] = None
    transactions_path: Optional[str] = None
    rules_config_path: Optional[str] = None
    padding_rows: int = 0
    separator: str = ","

    @classmethod
    def load(cls, config_file) -> "BankConfig":
        """Load config from file."""
        with open(config_file) as file_handle:
            config = yaml.load(file_handle.read(), Loader=yaml.FullLoader)
        new_config = cls.parse_obj(config)
        logger.info(f"Loaded bank config from {config_file} for bank '{new_config.bank_name}'")
        return new_config

    def save(self, file_name):
        """Save config to file."""
        with open(file_name, "w") as file_handle:
            yaml.dump(self.dict(), file_handle, default_flow_style=False)


class BankEnricher:
    def __init__(
        self,
        file: Optional[str] = None,
        bank_config: Optional[BankConfig] = None,
        bank_rules: Optional[BankRules] = None,
        rules_config_path: Optional[str] = None,
    ) -> None:
        self.file = file
        self.bank_config = bank_config or (BankConfig.load(file) if file else BankConfig())

        if rules_config_path is not None:
            self.bank_config.rules_config_path = rules_config_path
            logger.info(f"Overriding rules_config_path with CLI value: {rules_config_path}")

        if bank_rules is not None:
            self.bank_rules = bank_rules
        else:
            if not self.bank_config.rules_config_path:
                raise ValueError("rules_config_path is required (config file or --rules_config_path)")
            self.bank_rules = BankRules.load(self.bank_config.rules_config_path)

        logger.info(f"Initialized enricher for '{self.bank_config.bank_name or 'cli_bank'}'")

    def enrich_bank_row(self, row: Dict) -> List[Dict]:
        new_row = copy.deepcopy(row)
        print(row)
        created_rows = self.bank_rules.process_row(new_row)
        if created_rows:
            return created_rows
        return [new_row]

    def enrich_rows(self, rows: List[Dict]) -> List[Dict]:
        print(rows)
        enriched_rows = []
        for row in rows:
            enriched_rows += self.enrich_bank_row(row)
        return enriched_rows

    @staticmethod
    def generate_default_config(config_file: str):
        filename, _ = os.path.splitext(config_file)
        dir_name = os.path.dirname(config_file)
        transactions_dir = os.path.join(dir_name, f"{filename}_transactions")
        bank_rules_file = os.path.join(dir_name, f"./{filename}_bank_rules.yaml")
        os.makedirs(transactions_dir, exist_ok=True)
        default_config = BankConfig(
            bank_name=filename,
            transactions_path=transactions_dir,
            rules_config_path=bank_rules_file,
            padding_rows=1,
            separator=",",
        )
        default_config.save(config_file)
        BankRules(
            rules=[
                Rule(
                    conditions=[
                        Condition(
                            column="description",
                            operator=OperatorEnum.CONTAINS,
                            value="sample",
                        )
                    ],
                    operations=[
                        OperationConfig(
                            operation_type=OperationsEnum.ADD_COLUMN,
                            column_values=[
                                ColumnValue(
                                    column="category",
                                    value="sample_category",
                                )
                            ],
                        ),
                        ArithmeticOperationConfig(
                            operation_type=OperationsEnum.ARITHMETIC_OPERATION,
                            operator=ArithmeticOperatorEnum.CONCAT,
                            destination="description_copy",
                            column_values=[
                                ColumnValue(column="description"),
                                ColumnValue(column="category"),
                            ],
                        ),
                    ],
                )
            ]
        ).save(bank_rules_file)
        logger.info(f"Generated default config: {config_file}")