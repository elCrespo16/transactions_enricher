from transactions_enricher import BankEnricher
from argparse import ArgumentParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ConsoleOutputHandler = logging.StreamHandler()
logger.addHandler(ConsoleOutputHandler)

def main():
    parser = ArgumentParser(description="Enrich bank transactions based on rules")
    parser.add_argument(
        "-f",
        "--config_file",
        type=str,
        required=True,
        help="Path to the bank config file",
    )
    parser.add_argument(
        "-d",
        "--generate_default_config",
        action='store_true',
        help="If set, generates a default config file at the specified path",
    )
    args = parser.parse_args()

    if args.generate_default_config:
        BankEnricher.generate_default_config(args.config_file)
        return
    enricher = BankEnricher(args.config_file)
    enricher.enrich_bank_transactions()

if __name__ == "__main__":
    main()

