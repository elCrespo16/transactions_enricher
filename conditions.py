from abc import ABC
from enum import Enum
from typing import Any, Dict
from pydantic import BaseModel


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

    def apply(self, operand_1: Any, operand_2: Any) -> bool:
        return operand_1 in operand_2

class EqualOperator(Operator):
    name = OperatorEnum.EQUAL

    def apply(self, operand_1: Any, operand_2: Any) -> bool:
        return isinstance(operand_1, type(operand_2)) and operand_1 == operand_2

class LessOperator(Operator):
    name = OperatorEnum.LESS

    def apply(self, operand_1: Any, operand_2: Any) -> bool:
        return operand_1 < operand_2

class GreaterOperator(Operator):
    name = OperatorEnum.GREATER

    def apply(self, operand_1: Any, operand_2: Any) -> bool:
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
    value: str

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