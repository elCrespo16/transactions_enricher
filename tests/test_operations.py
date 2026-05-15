import unittest

from transactions_rules.operations import (
    AddColumnOperation,
    ColumnValue,
    DuplicateRowOperation,
    OperationConfig,
    OperationFactory,
    OperationsEnum,
)


class OperationFactoryTests(unittest.TestCase):
    def test_create_from_dict(self):
        operation = OperationFactory.create(
            {
                "operation_type": "add_column",
                "column_values": [
                    {"column": "category", "value": "sample_category"}
                ],
            }
        )

        self.assertIsInstance(operation, AddColumnOperation)
        row = {"description": "sample transaction"}
        operation.apply(row)
        self.assertEqual(row["category"], "sample_category")

    def test_duplicate_row_operation(self):
        operation = OperationFactory.create(
            OperationConfig(
                operation_type=OperationsEnum.DUPLICATE_ROW,
                column_values=[ColumnValue(column="category", value="duplicate")],
            )
        )

        self.assertIsInstance(operation, DuplicateRowOperation)
        original_row = {"description": "sample transaction"}
        duplicated_rows = operation.apply(original_row)

        self.assertEqual(len(duplicated_rows), 2)
        self.assertEqual(duplicated_rows[0]["description"], "sample transaction")
        self.assertEqual(duplicated_rows[1]["category"], "duplicate")


if __name__ == "__main__":
    unittest.main()