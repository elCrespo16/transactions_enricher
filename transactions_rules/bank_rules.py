from typing import List, Set

from transactions_rules.conditions import Condition
from transactions_rules.operations import OperationConfig, ArithmeticOperationConfig, OperationFactory

import yaml
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Rule example idea:
# - conditions:
#    - column: column1
#      operator: contains
#      value: tula
#   operations:
#    - operation_type: duplicate_row
#      values:
#        - column: column1
#          value: tula2
# This is a rule, when a row with column 1 contains "tula", it will return the current row as it is,
# and create a duplicated one with the column1 with value "tula2"

class Rule(BaseModel):
    conditions: List[Condition]
    operations: List[ArithmeticOperationConfig | OperationConfig]

    def check_and_apply(self, row):
        if self._is_rule_applicable(row):
            print(row.items())
            before = set(row.items())
            new_rows = self._apply(row)
            after = set(row.items())
            changes_str = ", ".join([f"{k} -> {v}" for k, v in after - before])
            logger.info(f"Applied {self} | Changes: {changes_str if changes_str else 'none'}")
            return new_rows if new_rows else None

    def _apply(self, row):
        new_rows = []
        for operation in self.operations:
            op = OperationFactory.create(operation_config=operation)
            created_rows = op.apply(row)
            if created_rows is not None:
                new_rows += created_rows
        return new_rows

    def _is_rule_applicable(self, row):
        for condition in self.conditions:
            valid = condition.is_applicable(row)
            if not valid:
                return False
        return True

    def get_mandatory_columns(self) -> Set[str]:
        columns = {condition.column for condition in self.conditions}
        for operation in self.operations:
            columns.update(operation.get_mandatory_columns())
        return columns

    def __str__(self):
        conditions_str = ", ".join([str(cond) for cond in self.conditions])
        operations_str = ", ".join([str(op) for op in self.operations])
        return f"Rule: {conditions_str} -> {operations_str}"



class BankRules(BaseModel):
    rules: List[Rule]

    @classmethod
    def load(cls, config_file) -> 'BankRules':
        """
        Load config from file
        """
        with open(config_file) as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
        new_config = cls.parse_obj(config)
        logger.info(f"Loaded rules config from {config_file}. Rules: {len(new_config.rules)}")
        return new_config

    def save(self, file_name):
        """
        Save config to file
        """
        with open(file_name, "w") as f:
            yaml.dump(self.dict(), f, default_flow_style=False)

    def process_row(self, row):
        """
        """
        new_rows = []
        for rule in self.rules:
            created_rows = rule.check_and_apply(row)
            if created_rows is not None:
                new_rows += created_rows
        return new_rows

