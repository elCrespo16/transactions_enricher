from abc import ABC
from enum import Enum
from typing import List, Any, Dict
import copy
from pydantic import BaseModel


class OperationsEnum(Enum):
    DUPLICATE_ROW = "duplicate_row"
    ADD_COLUMN = "add_column"
    CHANGE_VALUE = "change_value"
    COPY_COLUMNS = "copy_columns"
    DELETE_COLUMN = "delete_column"


class ColumnValue(BaseModel):
    column: str
    value: str

# TODO: refactor to check if column_value needs a value or not (e.g., delete_column doesn't need a value)
class OperationDTO(BaseModel):
    operation_type: OperationsEnum
    column_values: List[ColumnValue]

    def dict(self, **kwargs) -> Dict[str, Any]:
        return {"operation_type": self.operation_type.value,
                "column_values": [cv.dict() for cv in self.column_values]}

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
    def create(cls, operation_dto: OperationDTO) -> 'Operation':
        operation = cls.operation_mapping.get(operation_dto.operation_type)
        if operation is None:
            raise ValueError
        return operation(operation_dto.column_values)


class Operation(ABC):
    def __init__(self, column_values: List[ColumnValue]) -> None:
        self.column_values = column_values

    def apply(self, row):
        raise NotImplementedError

    def get_mandatory_columns(self) -> List[str]:
        return [column_value.column for column_value in self.column_values]

@OperationFactory.register(OperationsEnum.DELETE_COLUMN)
class DeleteColumnOperation(Operation):
    operation_type = OperationsEnum.DELETE_COLUMN

    def apply(self, row):
        for column_value in self.column_values:
            if column_value.column in row:
                del row[column_value.column]

@OperationFactory.register(OperationsEnum.DUPLICATE_ROW)
class DuplicateOperation(Operation):
    operation_type = OperationsEnum.DUPLICATE_ROW

    def apply(self, row):
        new_row = self._duplicate_row(row)
        for column_value in self.column_values:
            new_row[column_value.column] = column_value.value
        return [row, new_row]

    def _duplicate_row(self, row):
        return copy.deepcopy(row)

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

@OperationFactory.register(OperationsEnum.COPY_COLUMNS)
class CopyColumns(Operation):
    operation_type = OperationsEnum.COPY_COLUMNS

    def apply(self, row):
        for column_value in self.column_values:
            row[column_value.column] = row.get(column_value.value, "")

    def get_mandatory_columns(self) -> List[str]:
        columns = []
        for column_value in self.column_values:
            columns.append(column_value.value)
            columns.append(column_value.column)
        return columns


