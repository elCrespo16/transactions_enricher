import json
from flask import request, Blueprint
from flask_cors import CORS
from yaml import safe_load
from flask.views import MethodView
from transactions_rules.csv_processor import BankTransactionsCsvProcessor
from transactions_rules.bank_rules import BankConfiguration
from transactions_rules.transactions_enricher import BankEnricher


enrich_csv_bp = Blueprint('enrich_csv', __name__)
CORS(enrich_csv_bp, resources={r"/enrich_csv": {"origins": "*"}})

class EnrichCSVView(MethodView):
    def post(self):
        if not request.files:
            return {"error": "Invalid input: file expected"}, 400

        csv_file = None
        rules_file = None
        for key in request.files.keys():
            if key.endswith('.csv'):
                csv_file = request.files[key]
            elif key.endswith(('.yaml', '.yml')):
                rules_file = request.files[key]

        if not csv_file:
            return {"error": "CSV file is required"}, 400

        if not rules_file:
            if not request.form.get('rules'):
                return {"error": "Rules are required either as YAML/YML file or in JSON body"}, 400
            rules = json.loads(request.form.get('rules'))  # Expecting rules in JSON body if not uploaded as file
        else:
            try:
                rules = safe_load(rules_file.read())
            except Exception as exc:
                return {"error": f"Failed to parse rules YAML: {str(exc)}"}, 400

        bank_config = BankConfiguration()  # Default config
        if rules:
            try:
                config = json.loads(config)
                bank_config = BankConfiguration.parse_obj(rules)  # Validate config structure
            except json.JSONDecodeError:
                return {"error": "Failed to parse config JSON"}, 400


        try:
            content = csv_file.read().decode('utf-8')


            processor = BankTransactionsCsvProcessor(bank_config)
            rows = processor.read_rows_from_content(content)

            if not rows:
                return {"error": "CSV is empty or has no data rows"}, 400

            enricher = BankEnricher(bank_config=bank_config)
            enriched_rows = enricher.enrich_rows(rows)

            return {
                "message": f"CSV is valid and enriched. Total rows: {len(enriched_rows)}",
                "columns": list(enriched_rows[0].keys()) if enriched_rows else [],
                "enriched_data": enriched_rows  # In real implementation, consider pagination or limits
            }, 200
        except UnicodeDecodeError:
            return {"error": "Failed to decode file: invalid encoding"}, 400
        except Exception as exc:
            return {"error": f"CSV enrichment failed: {str(exc)}"}, 400

enrich_csv_bp.add_url_rule('/enrich_csv', view_func=EnrichCSVView.as_view('enrich_csv'))