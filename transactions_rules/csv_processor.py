from __future__ import annotations

import csv
import logging
import os
from io import StringIO
from typing import Dict, List, Optional, TextIO

from transactions_rules.transactions_enricher import BankConfiguration, BankEnricher

logger = logging.getLogger(__name__)


class BankTransactionsCsvProcessor:
    def __init__(
        self,
        bank_config: BankConfiguration,
        enricher: Optional[BankEnricher] = None,
    ) -> None:
        self.bank_config = bank_config
        self.enricher = enricher

    def load_transaction_files(self, single_file: Optional[str] = None) -> List[str]:
        if single_file:
            if not os.path.exists(single_file):
                raise FileNotFoundError(f"Specified file {single_file} does not exist")
            logger.info(f"Processing only single file: {single_file}")
            return [single_file]

        if not self.bank_config.transactions_path:
            raise ValueError("transactions_path is required to discover CSV files")
        if not os.path.exists(self.bank_config.transactions_path):
            raise FileNotFoundError(
                f"Transactions path {self.bank_config.transactions_path} does not exist"
            )

        bank_files = []
        for file_name in os.listdir(self.bank_config.transactions_path):
            if file_name.endswith(".csv") and not file_name.endswith("_enriched.csv"):
                bank_files.append(os.path.join(self.bank_config.transactions_path, file_name))

        logger.info(f"Transaction files discovered: {bank_files}")
        return bank_files

    def read_rows_from_path(self, file_path: str) -> List[Dict]:
        with open(file_path, "r", encoding="utf-8", newline="") as file_handle:
            return self.read_rows_from_stream(file_handle)

    def read_rows_from_content(self, content: str) -> List[Dict]:
        return self.read_rows_from_stream(StringIO(content))

    def read_rows_from_stream(self, stream: TextIO) -> List[Dict]:
        for _ in range(self.bank_config.padding_rows):
            stream.readline()
        reader = csv.DictReader(stream, delimiter=self.bank_config.separator)
        return list(reader)

    def enrich_rows(self, rows: List[Dict]) -> List[Dict]:
        if self.enricher is None:
            raise ValueError("An enricher instance is required to enrich rows")
        return self.enricher.enrich_rows(rows)

    def process_file(self, file_path: str) -> List[Dict]:
        rows = self.read_rows_from_path(file_path)
        return self.enrich_rows(rows)

    def process_all_files(self, single_file: Optional[str] = None) -> None:
        for file_path in self.load_transaction_files(single_file=single_file):
            logger.info(f"Starting processing for file: {file_path}")
            enriched_rows = self.process_file(file_path)
            self.save_enriched_rows(file_path, enriched_rows)
            logger.info(f"Finished processing file: {file_path}")

    def save_enriched_rows(self, file_path: str, enriched_rows: List[Dict]) -> None:
        output_file = file_path.replace(".csv", "_enriched.csv")
        with open(output_file, "w", encoding="utf-8", newline="") as file_handle:
            if len(enriched_rows) == 0:
                logger.warning(
                    f"No rows to save for file: {file_path}. Created empty output at {output_file}"
                )
                return

            fieldnames = list(enriched_rows[0].keys())
            writer = csv.DictWriter(
                file_handle,
                fieldnames=fieldnames,
                delimiter=self.bank_config.separator,
            )
            writer.writeheader()
            writer.writerows(enriched_rows)

        logger.info(f"Saved enriched file: {output_file} ({len(enriched_rows)} row(s))")
