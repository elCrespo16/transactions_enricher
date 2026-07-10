import unittest

from transactions_rules.bank_rules import BankRules, Rule
from transactions_rules.conditions import Condition, OperatorEnum
from transactions_rules.operations import ColumnValue, OperationConfig, OperationsEnum
from transactions_rules.rule_tagging import (
    add_tags_to_rule,
    available_tags,
    rules_with_tag,
    suggest_tags_for_rule,
)


class RuleTaggingTests(unittest.TestCase):
    def test_suggest_tags_for_transfer_rule(self):
        rule = Rule(
            conditions=[
                Condition(column="Concepto", operator=OperatorEnum.CONTAINS, value="Move to save")
            ],
            operations=[
                OperationConfig(
                    operation_type=OperationsEnum.CHANGE_VALUE,
                    column_values=[ColumnValue(column="destination", value="B100 Health")],
                )
            ],
        )

        tags = suggest_tags_for_rule(rule, source_name="b100_bank_rules.yaml")

        self.assertIn("bank:b100", tags)
        self.assertIn("domain:transfer", tags)
        self.assertIn("action:transform", tags)

    def test_suggested_tags_do_not_mutate_rule_until_applied(self):
        rule = Rule(
            conditions=[],
            operations=[
                OperationConfig(
                    operation_type=OperationsEnum.ADD_COLUMN,
                    column_values=[ColumnValue(column="category", value="unknown")],
                )
            ],
            tags=["manual:review"],
        )

        suggested_tags = suggest_tags_for_rule(rule, source_name="santander_bank_rules.yaml")

        self.assertEqual(rule.tags, ["manual:review"])
        self.assertIn("bank:santander", suggested_tags)
        self.assertIn("rule:catch_all", suggested_tags)

    def test_add_tags_and_filter_rules(self):
        first_rule = Rule(
            conditions=[Condition(column="Concepto", operator=OperatorEnum.CONTAINS, value="save")],
            operations=[],
            tags=["domain:transfer"],
        )
        second_rule = Rule(
            conditions=[Condition(column="Concepto", operator=OperatorEnum.CONTAINS, value="rent")],
            operations=[],
            tags=["domain:expense"],
        )

        updated_rule = add_tags_to_rule(first_rule, ["status:review"])
        bank_rules = BankRules(rules=[updated_rule, second_rule])

        self.assertIn("status:review", updated_rule.tags)
        self.assertEqual(available_tags(bank_rules), ["domain:expense", "domain:transfer", "status:review"])
        self.assertEqual(len(rules_with_tag(bank_rules, "domain:transfer").rules), 1)
        self.assertEqual(len(rules_with_tag(bank_rules, "status:review").rules), 1)


if __name__ == "__main__":
    unittest.main()