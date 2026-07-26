from abc import ABC
from enum import Enum
from typing import Any, Dict
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class OperatorEnum(Enum):
    CONTAINS = "contains"
    EQUAL = "="
    LESS = ">"
    GREATER = "<"

class Operator(ABC):
    def apply(self, operand_1: Any, operand_2: Any) -> bool:
        raise NotImplementedError

class ContainsOperator(Operator):
    name = OperatorEnum.CONTAINS

    def apply(self, operand_1: Any, operand_2: str) -> bool:
        try:
            operand_1 = str(operand_1).lower()
        except Exception:
            logger.warning(f"Error occurred while converting {operand_1} to string")
            return False
        return operand_1 in operand_2.lower()

class EqualOperator(Operator):
    name = OperatorEnum.EQUAL

    def apply(self, operand_1: Any, operand_2: Any) -> bool:
        return isinstance(operand_1, type(operand_2)) and operand_1 == operand_2

class LessOperator(Operator):
    name = OperatorEnum.LESS

    def apply(self, operand_1: Any, operand_2: Any) -> bool:
        try:
            operand_1 = type(operand_2)(operand_1)
        except Exception:
            logger.warning(f"Error occurred while converting {operand_1} to type {type(operand_2)}")
            return False
        return operand_1 < operand_2

class GreaterOperator(Operator):
    name = OperatorEnum.GREATER

    def apply(self, operand_1: Any, operand_2: Any) -> bool:
        try:
            operand_1 = type(operand_2)(operand_1)
        except Exception:
            logger.warning(f"Error occurred while converting {operand_1} to type {type(operand_2)}")
            return False
        return operand_1 > operand_2


class OperatorFactory:
    operator_mapping = {
        OperatorEnum.GREATER: GreaterOperator,
        OperatorEnum.LESS: LessOperator,
        OperatorEnum.EQUAL: EqualOperator,
        OperatorEnum.CONTAINS: ContainsOperator
    }

    @classmethod
    def create(cls, operator: str) -> Operator:
        operator = cls.operator_mapping.get(operator)
        if operator is None:
            raise ValueError
        return operator()

class Condition(BaseModel):
    column: str
    operator: OperatorEnum
    value: str | int | float

    def is_applicable(self, row):
        if self.column not in row:
            return False
        op = OperatorFactory.create(self.operator)
        return op.apply(self.value, row[self.column])

    def dict(self, **kwargs) -> Dict[str, Any]:
        return {
            "column": self.column,
            "operator": self.operator.value,
            "value": self.value
        }

    def __str__(self):
        return f"{self.column} {self.operator.value} {self.value}"