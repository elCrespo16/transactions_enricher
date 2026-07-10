
"""
duplicate_transactions_detector.py

Refactored CLI tool to detect duplicated transfer transactions across multiple CSVs.

Lightweight class-based design:
- `ConfigManager` handles config load/save and interactive mapping creation
- `CSVParser` reads CSV files and normalizes amounts/dates
- `DuplicateDetector` groups transactions and finds transfer duplicates
- `ReportWriter` emits CSV reports and optional filtered files
- `CLI` wires everything together

The behavior is intentionally simple and focused; avoid over-engineering.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

try:
	from pydantic import BaseModel
except Exception:
	print("pydantic is required. Install with: pip install pydantic")
	raise


class ColumnMapping(BaseModel):
	date: str
	amount: str
	destination: str
	category: str
	delimiter: Optional[str] = ";"
	date_format: Optional[str] = None


class BanksConfig(BaseModel):
	banks: Dict[str, ColumnMapping] = {}


class ConfigManager:
	def __init__(self, path: str = "banks_config.json"):
		self.path = path
		self.config = self.load()

	def load(self) -> BanksConfig:
		if os.path.exists(self.path):
			with open(self.path, "r", encoding="utf-8") as f:
				data = json.load(f)
			return BanksConfig(**data)
		return BanksConfig()

	def save(self):
		with open(self.path, "w", encoding="utf-8") as f:
			f.write(self.config.json(indent=2, ensure_ascii=False))

	def prompt_mapping(self, bank_name: str) -> ColumnMapping:
		print(f"Creating mapping for bank: {bank_name}")
		date = input("Column name for date (e.g. Fecha operación): ").strip()
		amount = input("Column name for amount (e.g. Importe): ").strip()
		destination = input("Column name for destination (e.g. destination): ").strip()
		category = input("Column name for category (e.g. category): ").strip()
		delim = input("CSV delimiter (default ';'): ").strip() or ";"
		date_fmt = input("Optional date format (e.g. %d/%m/%Y) or leave blank: ").strip() or None
		mapping = ColumnMapping(date=date, amount=amount, destination=destination, category=category, delimiter=delim, date_format=date_fmt)
		self.config.banks[bank_name] = mapping
		return mapping


@dataclass
class Transaction:
	bank: str
	file: str
	rownum: int
	date: Optional[datetime]
	amount: Optional[float]
	destination: str
	category: str
	raw: Dict[str, str]


class CSVParser:
	def __init__(self):
		pass

	@staticmethod
	def parse_amount(s: str) -> Optional[float]:
		if s is None:
			return None
		s = s.strip().lstrip()
		if s == "":
			return None
		s = s.replace("€", "").replace("$", "").replace("\xa0", "").strip()
		if "." in s and "," in s:
			s = s.replace(".", "")
			s = s.replace(",", ".")
		else:
			if "," in s and "." not in s:
				s = s.replace(",", ".")
		s = s.replace(" ", "")
		try:
			return float(Decimal(s))
		except Exception:
			cleaned = "".join(ch for ch in s if ch.isdigit() or ch in "-.")
			if cleaned == "":
				return None
			try:
				return float(cleaned)
			except Exception:
				return None

	@staticmethod
	def parse_date(s: str, fmt: Optional[str] = None) -> Optional[datetime]:
		if not s:
			return None
		s = s.strip().lstrip()
		if fmt:
			try:
				return datetime.strptime(s, fmt)
			except Exception:
				pass
		for f in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
			try:
				return datetime.strptime(s, f)
			except Exception:
				continue
		parts = [p for p in s.replace("/", "-").replace(".", "-").split("-") if p]
		if len(parts) >= 3:
			d, m, y = parts[0:3]
			try:
				y = int(y) if len(y) > 2 else (2000 + int(y))
				return datetime(int(y), int(m), int(d))
			except Exception:
				return None
		return None

	def read(self, path: str, bank: str, mapping: ColumnMapping, only_transfers: bool = False) -> List[Transaction]:
		rows: List[Transaction] = []
		delim = mapping.delimiter or ";"
		with open(path, newline="", encoding="utf-8") as f:
			f.read(0)
			f.seek(0)
			reader = csv.DictReader(f, delimiter=delim)
			for i, r in enumerate(reader, start=1):
				date = self.parse_date(r.get(mapping.date, ""), mapping.date_format)
				amount = self.parse_amount(r.get(mapping.amount, ""))
				dest = (r.get(mapping.destination, "") or "")
				cat = (r.get(mapping.category, "") or "").strip().lstrip()
				# if only_transfers, skip rows not matching Traspasos
				if only_transfers:
					if not (cat and "traspas" in cat.lower()):
						continue
				tx = Transaction(bank=bank, file=path, rownum=i, date=date, amount=amount, destination=dest, category=cat, raw=r)
				rows.append(tx)

		return rows


class DuplicateDetector:
	def __init__(self, days_window: int = 31):
		self.days_window = days_window

	@staticmethod
	def is_traspasos(cat: str) -> bool:
		if not cat:
			return False
		return "traspas" in cat.lower()

	def _norm(self, s: str) -> str:
		return (s or "").strip().lower()

	def _destinations_match(self, a: Transaction, b: Transaction) -> bool:
		# exact match preferred, then fall back to substring/bank-name heuristics
		d1 = self._norm(a.destination)
		d2 = self._norm(b.destination)
		b1 = self._norm(a.bank)
		b2 = self._norm(b.bank)
		if d1 and d2 and d1 == d2:
			return True
		if d1 and b2 and b2 in d1:
			return True
		if d2 and b1 and b1 in d2:
			return True
		if d1 and d2 and (d1 in d2 or d2 in d1):
			return True
		return False

	def _opposite_signs(self, a: Transaction, b: Transaction) -> bool:
		# Use multiplication to test for opposite signs, robust to small rounding
		try:
			return (a.amount is not None and b.amount is not None) and (a.amount * b.amount < 0)
		except Exception:
			return False

	def _dates_within(self, a: Transaction, b: Transaction, max_days: int) -> bool:
		if not a.date or not b.date:
			# If one or both dates missing, don't disqualify — allow match
			return True
		return abs((a.date - b.date).days) <= max_days

	def _find_matches_for_amount(self, items: List[Transaction], max_days: int) -> List[Transaction]:
		n = len(items)
		matched = []
		seen = set()
		for i in range(n):
			a = items[i]
			if not self.is_traspasos(a.category):
				continue
			for j in range(i + 1, n):
				b = items[j]
				if not self.is_traspasos(b.category):
					continue
				if a.bank == b.bank:
					continue
				if not self._opposite_signs(a, b):
					continue
				if not self._dates_within(a, b, max_days):
					continue
				if not (self._destinations_match(a, b) or self._destinations_match(b, a)):
					continue
				# record both transactions
				for tx in (a, b):
					ident = (tx.file, tx.rownum)
					if ident in seen:
						continue
					seen.add(ident)
					matched.append(tx)
		return matched

	def detect(self, transactions: List[Transaction]) -> List[Tuple[float, List[Transaction]]]:
		buckets: Dict[float, List[Transaction]] = defaultdict(list)
		for t in transactions:
			if t.amount is None:
				continue
			buckets[round(abs(t.amount), 2)].append(t)
		duplicates: List[Tuple[float, List[Transaction]]] = []
		max_days = min(self.days_window, 5)
		for amt, items in buckets.items():
			matched = self._find_matches_for_amount(items, max_days)
			if len(matched) >= 2:
				duplicates.append((amt, matched))
		return duplicates


class ReportWriter:
	@staticmethod
	def write_report(duplicates: List[Tuple[float, List[Transaction]]], outpath: str):
		with open(outpath, "w", encoding="utf-8", newline="") as f:
			w = csv.writer(f)
			w.writerow(["amount", "bank", "file", "rownum", "date", "destination", "category"])
			for amt, items in duplicates:
				for it in items:
					w.writerow([amt, it.bank, os.path.basename(it.file), it.rownum, it.date.isoformat() if it.date else "", it.destination, it.category])



class CLI:
	def __init__(self):
		self.parser = argparse.ArgumentParser(description="Detect duplicated transfer transactions across CSVs.")
		self.parser.add_argument("files", nargs="+", help="CSV files to scan")
		self.parser.add_argument("--config", "-c", default="banks_config.json", help="Path to banks config JSON")
		self.parser.add_argument("--report", "-r", default="duplicates_report.csv", help="Output duplicates report CSV")
		self.parser.add_argument("--keep-bank", "-k", default=None, help="Bank to prefer keeping when removing duplicates")


	def run(self, argv=None):
		args = self.parser.parse_args(argv)
		cfgm = ConfigManager(args.config)
		csvp = CSVParser()
		detector = DuplicateDetector()

		file_bank_map: Dict[str, str] = {}
		for f in args.files:
			print(f"\nFile: {f}")
			banks = list(cfgm.config.banks.keys())
			if banks:
				print("Known banks:")
				for i, b in enumerate(banks, start=1):
					print(f"  {i}. {b}")
			choice = input("Enter bank name to use (or number), or new to create mapping: ").strip()
			if choice.lower() == "new":
				name = input("New bank name: ").strip()
				cfgm.prompt_mapping(name)
				file_bank_map[f] = name
			elif choice.isdigit() and 1 <= int(choice) <= len(banks):
				file_bank_map[f] = banks[int(choice) - 1]
			elif choice in cfgm.config.banks:
				file_bank_map[f] = choice
			else:
				cfgm.prompt_mapping(choice)
				file_bank_map[f] = choice

		cfgm.save()

		all_transactions: List[Transaction] = []
		transactions_by_file: Dict[str, List[Transaction]] = {}
		for f, bank in file_bank_map.items():
			mapping = cfgm.config.banks[bank]
			txs = csvp.read(f, bank, mapping, only_transfers=True)
			transactions_by_file[f] = txs
			all_transactions.extend(txs)

		duplicates = detector.detect(all_transactions)

		if not duplicates:
			print("No duplicates detected.")
			return

		print(f"Detected {len(duplicates)} potential duplicate groups. Writing report to {args.report}")
		ReportWriter.write_report(duplicates, args.report)

		print("Summary of duplicate groups (amount -> banks involved):")
		for amt, items in duplicates:
			banks = sorted(set(it.bank for it in items))
			print(f"  {amt} -> {', '.join(banks)}")



def main(argv=None):
	CLI().run(argv)


if __name__ == "__main__":
	main()
