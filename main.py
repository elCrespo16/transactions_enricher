from transactions_rules.csv_processor import BankTransactionsCsvProcessor
from transactions_rules.transactions_enricher import BankConfiguration, BankEnricher
from argparse import ArgumentParser
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def configure_logging(log_file: str = "transactions_enricher.log"):
    log_path = Path(log_file)
    if not log_path.parent.exists() and str(log_path.parent) != ".":
        log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Reset handlers to avoid duplicated logs when executed multiple times.
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logger.info(f"Logging configured. Output file: {log_path.resolve()}")

def main():
    parser = ArgumentParser(description="Enrich bank transactions based on rules")
    parser.add_argument(
        "-f",
        "--config_file",
        type=str,
        required=False,
        default=None,
        help="Path to the bank config file (optional if CLI overrides are provided)",
    )
    parser.add_argument(
        "-d",
        "--generate_default_config",
        action='store_true',
        help="If set, generates a default config file at the specified path",
    )
    parser.add_argument(
        "-l",
        "--log_file",
        type=str,
        default="transactions_enricher.log",
        help="Path to the log file",
    )
    parser.add_argument(
        "--transactions_path",
        type=str,
        default=None,
        help="Override the transactions path from the config file",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="If set, only enrich this single CSV file (overrides transactions_path discovery)",
    )
    args = parser.parse_args()
    configure_logging(args.log_file)

    if args.generate_default_config:
        if not args.config_file:
            parser.error("--config_file is required when using --generate_default_config")
        logger.info(f"Generating default config at {args.config_file}")
        print(f"Generating default config: {args.config_file}")
        BankEnricher.generate_default_config(args.config_file)
        logger.info("Default config generated successfully")
        return

    if not args.config_file and not args.file and not args.transactions_path:
        parser.error("Provide --config_file or --file or --transactions_path")

    logger.info(f"Starting enrichment with config {args.config_file}")
    print("Starting transactions enrichment...")
    bank_config = BankConfiguration.load(args.config_file) if args.config_file else BankConfiguration()
    if args.transactions_path is not None:
        bank_config.transactions_path = args.transactions_path
    enricher = BankEnricher(bank_config=bank_config)
    processor = BankTransactionsCsvProcessor(enricher.bank_config, enricher)
    processor.process_all_files(single_file=args.file)
    logger.info("Enrichment finished successfully")
    print("Finished transactions enrichment")

if __name__ == "__main__":
    main()

