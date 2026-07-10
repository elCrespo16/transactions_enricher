from typing import Dict, List, Optional
import copy
import logging
import os

import yaml
from pydantic import BaseModel

from transactions_rules.bank_rules import BankConfiguration, Rule
from transactions_rules.conditions import Condition, OperatorEnum
from transactions_rules.operations import (
    ArithmeticOperationConfig,
    ArithmeticOperatorEnum,
    ColumnValue,
    OperationConfig,
    OperationsEnum,
)

logger = logging.getLogger(__name__)


class BankEnricher:
    def __init__(
        self,
        file: Optional[str] = None,
        bank_config: Optional[BankConfiguration] = None,
    ) -> None:
        self.file = file
        self.bank_config = bank_config or (BankConfiguration.load(file) if file else BankConfiguration())
        logger.info(f"Initialized enricher for '{self.bank_config.bank_name or 'cli_bank'}'")

    def enrich_bank_row(self, row: Dict) -> List[Dict]:
        new_row = copy.deepcopy(row)
        print(row)
        created_rows = self.bank_config.process_row(new_row)
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
        os.makedirs(transactions_dir, exist_ok=True)
        default_config = BankConfiguration(
            bank_name=filename,
            transactions_path=transactions_dir,
            padding_rows=1,
            separator=",",
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
        )
        default_config.save(config_file)
        logger.info(f"Generated default config: {config_file}")


# Backward compatibility alias
BankConfig = BankConfiguration
