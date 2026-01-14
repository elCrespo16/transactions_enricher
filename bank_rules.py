from typing import List, Set

from conditions import Condition
from operations import OperationDTO, OperationFactory

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
    operations: List[OperationDTO]

    def check_and_apply(self, row):
        if self._is_rule_applicable(row):
            new_rows = self._apply(row)
            logger.info(f"Rule applied: {self.dict()}: Row before: {row} after: {new_rows}")
            return new_rows if new_rows else None

    def _apply(self, row):
        new_rows = []
        for operation in self.operations:
            op = OperationFactory.create(operation_dto=operation)
            created_rows = op.apply(row)
            if created_rows is not None:
                new_rows += op.apply(row)
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



class BankRules(BaseModel):
    rules: List[Rule]

    @classmethod
    def load(cls, config_file) -> 'BankRules':
        """
        Load config from file
        """
        with open(config_file) as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
        new_config =  cls.parse_obj(config)
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
                new_rows += rule.check_and_apply(row)
        return new_rows

