from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Any, Dict
import copy
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, Field, ConfigDict


class OperationsEnum(Enum):
    DUPLICATE_ROW = "duplicate_row"
    ADD_COLUMN = "add_column"
    CHANGE_VALUE = "change_value"
    COPY_COLUMNS = "copy_columns"
    DELETE_COLUMN = "delete_column"
    ARITHMETIC_OPERATION = "arithmetic_operation"


class ArithmeticOperatorEnum(str, Enum):
    ADD = "+"
    SUBTRACT = "-"
    CONCAT = "concat"


class ColumnValue(BaseModel):
    column: str
    value: str | int | float | None = None


class OperationConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    operation_type: OperationsEnum
    column_values: List[ColumnValue] = Field(default_factory=list)

    def dict(self, **kwargs) -> Dict[str, Any]:
        data = {
            "operation_type": self.operation_type.value,
            "column_values": [cv.dict() for cv in self.column_values],
        }
        data.update(getattr(self, "model_extra", None) or {})
        return data

    def __str__(self):
        column_values_str = ", ".join([
            f"{cv.column} {cv.value}" if cv.value is not None else cv.column
            for cv in self.column_values
        ])
        return f"{self.operation_type.value} {column_values_str}"


class ArithmeticOperationConfig(OperationConfig):
    operator: ArithmeticOperatorEnum
    destination: str

    def dict(self, **kwargs) -> Dict[str, Any]:
        data = super().dict(**kwargs)
        data.update(
            {
                "operator": self.operator.value,
                "destination": self.destination,
            }
        )
        return data


class OperationFactory:
    operation_mapping = {
    }

    @classmethod
    def register(cls, operation_enum):
        def wrapper(operation_class):
            cls.operation_mapping[operation_enum] = operation_class
            return operation_class
        return wrapper

    @classmethod
    def create(
        cls,
        operation_config: OperationConfig | ArithmeticOperationConfig,
    ) -> "Operation":
        # OperationFactory now expects validated OperationConfig / ArithmeticOperationConfig
        operation = cls.operation_mapping.get(operation_config.operation_type)
        if operation is None:
            raise ValueError(f"Unsupported operation type: {operation_config.operation_type}")
        return operation(operation_config)


class Operation(ABC):
    operation_type: OperationsEnum

    def __init__(self, config: OperationConfig | ArithmeticOperationConfig | List[ColumnValue]) -> None:
        self.config = config
        self.column_values = getattr(config, "column_values", config if isinstance(config, list) else [])

    @abstractmethod
    def apply(self, row):
        raise NotImplementedError

    def get_mandatory_columns(self) -> List[str]:
        return []

    def __str__(self):
        column_values_str = ", ".join([
            f"{cv.column} {cv.value}" if cv.value is not None else cv.column
            for cv in self.column_values
        ])
        return f"{self.operation_type.value} {column_values_str}"


@OperationFactory.register(OperationsEnum.DELETE_COLUMN)
class DeleteColumnOperation(Operation):
    operation_type = OperationsEnum.DELETE_COLUMN

    def apply(self, row):
        for column_value in self.column_values:
            if column_value.column in row:
                del row[column_value.column]

    def get_mandatory_columns(self) -> List[str]:
        return []


@OperationFactory.register(OperationsEnum.DUPLICATE_ROW)
class DuplicateRowOperation(Operation):
    operation_type = OperationsEnum.DUPLICATE_ROW

    def apply(self, row):
        new_row = self._duplicate_row(row)
        for column_value in self.column_values:
            new_row[column_value.column] = column_value.value
        return [row, new_row]

    def _duplicate_row(self, row):
        return copy.deepcopy(row)

    def get_mandatory_columns(self) -> List[str]:
        return []


@OperationFactory.register(OperationsEnum.ADD_COLUMN)
class AddColumnOperation(Operation):
    operation_type = OperationsEnum.ADD_COLUMN

    def apply(self, row):
        for column_value in self.column_values:
            if column_value.column not in row:
                row[column_value.column] = column_value.value

    def get_mandatory_columns(self) -> List[str]:
        return []


@OperationFactory.register(OperationsEnum.CHANGE_VALUE)
class ChangeValueOperation(Operation):
    operation_type = OperationsEnum.CHANGE_VALUE

    def apply(self, row):
        for column_value in self.column_values:
            row[column_value.column] = column_value.value

    def get_mandatory_columns(self) -> List[str]:
        return []


@OperationFactory.register(OperationsEnum.COPY_COLUMNS)
class CopyColumnsOperation(Operation):
    operation_type = OperationsEnum.COPY_COLUMNS

    def apply(self, row):
        for column_value in self.column_values:
            row[column_value.column] = row.get(column_value.value, "")

    def get_mandatory_columns(self) -> List[str]:
        return list({column_value.value for column_value in self.column_values if column_value.value is not None})


@OperationFactory.register(OperationsEnum.ARITHMETIC_OPERATION)
class ArithmeticOperation(Operation):
    operation_type = OperationsEnum.ARITHMETIC_OPERATION

    def __init__(self, config: ArithmeticOperationConfig | OperationConfig | List[ColumnValue]) -> None:
        super().__init__(config)
        if not isinstance(config, ArithmeticOperationConfig):
            raise TypeError("ArithmeticOperation requires ArithmeticOperationConfig")
        # cache validated config pieces
        self.destination: str = config.destination
        self.operator: ArithmeticOperatorEnum = config.operator
        self.sources: List[str] = [cv.column for cv in config.column_values]

    def _coerce_number(self, value: Any) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"Arithmetic operation requires numeric values, got: {value!r}") from exc

    def _normalize_number(self, value: Decimal) -> int | float:
        if value == value.to_integral_value():
            return int(value)
        return float(value)

    def apply(self, row):
        sources = self.sources
        if len(sources) < 2:
            raise ValueError("Arithmetic operation requires at least two source columns (use column_values)")

        missing_columns = [column for column in sources if column not in row]
        if missing_columns:
            raise ValueError(f"Arithmetic operation cannot run, missing columns: {', '.join(missing_columns)}")

        values = [row[column] for column in sources]

        if self.operator == ArithmeticOperatorEnum.ADD:
            result = self._coerce_number(values[0])
            for value in values[1:]:
                result += self._coerce_number(value)
            row[self.destination] = self._normalize_number(result)
            return

        if self.operator == ArithmeticOperatorEnum.SUBTRACT:
            result = self._coerce_number(values[0])
            for value in values[1:]:
                result -= self._coerce_number(value)
            row[self.destination] = self._normalize_number(result)
            return

        if self.operator == ArithmeticOperatorEnum.CONCAT:
            row[self.destination] = "".join("" if value is None else str(value) for value in values)
            return

        raise ValueError(f"Unsupported arithmetic operator: {self.operator}")

    def get_mandatory_columns(self) -> List[str]:
        return list(self.sources)

    def __str__(self):
        sources = ", ".join(self.sources)
        return f"{self.operation_type.value} {self.destination} {self.operator.value} {sources}"