"""
Trade Republic CSV Preprocessor
==============================
This script cleans and normalizes malformed CSV files exported from Trade Republic.
It handles the specific 3-row batch format where each transaction is spread across three rows.
The output is a new CSV file with standardized columns: date, type, description, entrada, salida, and balance.
"""


import csv
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# =========================
# Date normalization
# =========================

class DateNormalizer:
    MONTHS = {
        "ene": "01", "feb": "02", "mar": "03", "abr": "04",
        "may": "05", "jun": "06", "jul": "07", "ago": "08",
        "sept": "09", "sep": "09", "oct": "10",
        "nov": "11", "dic": "12"
    }

    def normalize(self, date: str) -> str:
        day, month, year = date.split()
        return f"{day.zfill(2)}/{self.MONTHS[month.lower()]}/{year}"


# =========================
# CSV IO
# =========================

class CsvReader:
    def read(self, path: Path) -> List[List[str]]:
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.reader(f))


class CsvWriter:
    FIELDNAMES = ["date", "type", "description", "entrada", "salida", "balance"]

    def write(self, path: Path, rows: List[Dict[str, str]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)


# =========================
# Core parser (batch-based)
# =========================

class BankCsvParser:
    HEADER_START = "FECHA"

    def __init__(self):
        self.date_normalizer = DateNormalizer()

    def parse(self, rows: List[List[str]]) -> List[Dict[str, str]]:
        transactions = []
        i = 0

        # Parse data in batches of 3 rows
        while i + 2 < len(rows) and rows[i][0].strip():
            r1, r2, r3 = rows[i], rows[i + 1], rows[i + 2]

            transactions.append(self._parse_batch([r1, r2, r3]))
            i += 3

        return transactions

    def _parse_batch(
        self,
        rows: List[List[str]],
    ) -> Dict[str, str]:
        new_row = []
        for i in range(len(rows[0])):
            combined_cell = " ".join(
                rows[j][i].strip() for j in range(len(rows)) if rows[j][i].strip()
            )
            new_row.append(combined_cell)

        return {
            "date": self.date_normalizer.normalize(new_row[0]),
            "type": new_row[1],
            "description": new_row[2],
            "entrada": new_row[3],
            "salida": new_row[4],
            "balance": new_row[5],
        }


# =========================
# Orchestration
# =========================

class OutputPathResolver:
    def resolve(self, input_path: Path) -> Path:
        return input_path.with_name(f"{input_path.stem}_preprocessed{input_path.suffix}")


class CliArguments:
    def parse(self) -> Path:
        parser = argparse.ArgumentParser(
            description="Clean malformed bank CSV (3-row batch format)"
        )
        parser.add_argument("file", type=Path, help="Input CSV file")
        return parser.parse_args().file


# =========================
# Entry point
# =========================

def main():
    input_path = CliArguments().parse()

    reader = CsvReader()
    parser = BankCsvParser()
    writer = CsvWriter()

    rows = reader.read(input_path)
    transactions = parser.parse(rows)

    output_path = OutputPathResolver().resolve(input_path)
    writer.write(output_path, transactions)

    print(f"✔ Enriched CSV created: {output_path}")


if __name__ == "__main__":
    main()
