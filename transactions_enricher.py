from typing import Dict, List
import yaml
import copy
import re
import os
from pydantic import BaseModel
from bank_rules import BankRules, Rule
from operations import OperationDTO, ColumnValue, OperationsEnum
from conditions import Condition, OperatorEnum

class BankConfig(BaseModel):
    bank_name: str
    transactions_path: str
    rules_config_path: str
    padding_rows: int = 0
    separator: str = ","

    @classmethod
    def load(cls, config_file) -> 'BankConfig':
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

class BankEnricher:

    def __init__(self, file: str) -> None:
        self.file = file
        self.bank_config = BankConfig.load(file)
        self.bank_rules = BankRules.load(self.bank_config.rules_config_path)

    def enrich_bank_transactions(self):
        transactions_files = self.load_bank_transactions()
        for file in transactions_files:
            rows = []
            with open(file, "r") as f:
                for _ in range(self.bank_config.padding_rows):
                    f.readline()
                headers = f.readline().strip().split(self.bank_config.separator)
                for line in f.readlines():
                    clean_line = self.remove_commas_inside_quotes(line)
                    row = clean_line.strip().split(self.bank_config.separator)
                    row_dict = self.build_row_dict(row, headers)
                    rows.append(row_dict)

            enriched_rows = []
            for row in rows:
                enriched_rows += self.enrich_bank_row(row)
            self.save_enriched_bank_files(file, enriched_rows)

    def remove_commas_inside_quotes(self, line):
        def replacer(match):
            quoted_text = match.group(0)
            return quoted_text.replace(self.bank_config.separator, '')

        return re.sub(r'"[^"]*"', replacer, line)


    def load_bank_transactions(self) -> List[str]:
        """
        Load all the csv files from the transactions path
        """
        if not os.path.exists(self.bank_config.transactions_path):
            raise FileNotFoundError(f"Transactions path {self.bank_config.transactions_path} does not exist")
        bank_files = []
        for file in os.listdir(self.bank_config.transactions_path):
            if file.endswith(".csv") and not file.endswith("_enriched.csv"):
                bank_files.append(os.path.join(self.bank_config.transactions_path, file))
        return bank_files

    def build_row_dict(self, row, headers) -> Dict:
        row_dict = {}
        for i, header in enumerate(headers):
            row_dict[header] = row[i]
        return row_dict


    def enrich_bank_row(self, row: Dict) -> List[Dict]:
        new_row = copy.deepcopy(row)
        created_rows = self.bank_rules.process_row(new_row)
        if created_rows:
            return created_rows
        else:
            return [new_row]


    def save_enriched_bank_files(self, file, enriched_rows: List[Dict]):
        """
        """
        with open(file.replace(".csv", "_enriched.csv"), "w") as f:
            if len(enriched_rows) == 0:
                return
            headers = enriched_rows[0].keys()
            f.write(self.bank_config.separator.join(headers) + "\n")
            for row in enriched_rows:
                row_values = [str(row[header]) for header in headers]
                f.write(self.bank_config.separator.join(row_values) + "\n")

    def generate_default_config(config_file: str):
        filename, _ = os.path.splitext(config_file)
        dir_name = os.path.dirname(config_file)
        transactions_dir = os.path.join(dir_name, f"{filename}_transactions")
        bank_rules_file =  os.path.join(dir_name, f"./{filename}_bank_rules.yaml")
        os.makedirs(transactions_dir, exist_ok=True)
        default_config = BankConfig(
            bank_name=filename,
            transactions_path=transactions_dir,
            rules_config_path=bank_rules_file,
            padding_rows=1,
            separator=","
        )
        default_config.save(config_file)
        BankRules(
            rules=[Rule(
                    conditions=[Condition(
                        column="description",
                        operator=OperatorEnum.CONTAINS,
                        value="sample"
                    )],
                    operations=[OperationDTO(
                        operation_type=OperationsEnum.ADD_COLUMN,
                        column_values=[ColumnValue(
                            column="category",
                            value="sample_category"
                        )]
                    )])]
        ).save(bank_rules_file)