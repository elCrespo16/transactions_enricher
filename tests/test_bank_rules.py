import unittest

from transactions_rules.bank_rules import Rule
from transactions_rules.conditions import Condition, OperatorEnum
from transactions_rules.operations import ColumnValue, OperationConfig, OperationsEnum


class RuleTests(unittest.TestCase):
    def test_rule_tags_are_preserved(self):
        rule = Rule(
            conditions=[
                Condition(column="description", operator=OperatorEnum.CONTAINS, value="sample")
            ],
            operations=[
                OperationConfig(
                    operation_type=OperationsEnum.ADD_COLUMN,
                    column_values=[ColumnValue(column="category", value="sample_category")],
                )
            ],
            tags=["expenses", "groceries"],
        )

        self.assertEqual(rule.tags, ["expenses", "groceries"])
        self.assertIn("tags: expenses, groceries", str(rule))

    def test_in_place_operation_mutates_row(self):
        rule = Rule(
            conditions=[
                Condition(column="description", operator=OperatorEnum.CONTAINS, value="sample")
            ],
            operations=[
                OperationConfig(
                    operation_type=OperationsEnum.ADD_COLUMN,
                    column_values=[ColumnValue(column="category", value="sample_category")],
                )
            ],
        )

        row = {"description": "sample payment"}
        result = rule.check_and_apply(row)

        self.assertIsNone(result)
        self.assertEqual(row["category"], "sample_category")

    def test_duplicate_operation_returns_rows(self):
        rule = Rule(
            conditions=[
                Condition(column="description", operator=OperatorEnum.CONTAINS, value="sample")
            ],
            operations=[
                OperationConfig(
                    operation_type=OperationsEnum.DUPLICATE_ROW,
                    column_values=[ColumnValue(column="category", value="duplicate")],
                )
            ],
        )

        row = {"description": "sample payment"}
        result = rule.check_and_apply(row)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["category"], "duplicate")


if __name__ == "__main__":
    unittest.main()