import csv
from io import StringIO
from flask import request, Blueprint
from flask.views import MethodView


validate_csv_bp = Blueprint('validate_csv', __name__)

class ValidateCSVView(MethodView):
    def post(self):
        print(request.files)
        if not request.files:
            return {"error": "Invalid input: file expected"}, 400
        if len(request.files.keys()) > 1:
            return {"error": "Multiple files uploaded; only one expected"}, 400

        file = list(request.files.values())[0]
        try:
            content = file.read().decode('utf-8')
            reader = csv.DictReader(StringIO(content))
            rows = list(reader)

            if not rows:
                return {"error": "CSV is empty or has no data rows"}, 400

            return {
                "message": f"CSV is valid. Total rows: {len(rows)}",
                "columns": reader.fieldnames
            }, 200
        except UnicodeDecodeError:
            return {"error": "Failed to decode file: invalid encoding"}, 400
        except Exception as exc:
            return {"error": f"CSV validation failed: {str(exc)}"}, 400

validate_csv_bp.add_url_rule('/validate_csv', view_func=ValidateCSVView.as_view('validate_csv'))