from flask import request, Blueprint
from flask.views import MethodView
from yaml import safe_load
from flask_cors import CORS

from transactions_rules.bank_rules import BankConfiguration


validate_rules_bp = Blueprint('validate_rules', __name__)
CORS(validate_rules_bp, resources={r"/validate_rules": {"origins": "*"}})

class ValidateRulesView(MethodView):
    def post(self):
        if not request.is_json and not request.files:
            return {"error": "Invalid input: JSON or file expected"}, 400
        if len(request.files.keys()) > 1:
            return {"error": "Multiple files uploaded; only one expected"}, 400
        if request.is_json:
            rules_data = request.get_json()
        else:
            file = list(request.files.values())[0]
            try:
                rules_data = safe_load(file.read())
            except Exception as exc:
                return {"error": f"Failed to parse YAML: {str(exc)}"}, 400

        try:
            rules_config = BankConfiguration.parse_obj(rules_data)
            return {"message": f"Rules are valid. Total rules: {len(rules_config.rules)}"}, 200
        except Exception as exc:
            exception_msg = str(exc).replace("\n", " ")
            return {"error": f"Rules validation failed: {exception_msg}"}, 400

validate_rules_bp.add_url_rule('/validate_rules', view_func=ValidateRulesView.as_view('validate_rules'))





