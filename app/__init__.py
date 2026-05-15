from flask import Flask
from flasgger import Flasgger
from app.validate_rules import validate_rules_bp
from app.validate_csv import validate_csv_bp
from app.enrich_csv import enrich_csv_bp
import os
import json

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_pyfile('config.py', silent=True)

    app.register_blueprint(validate_rules_bp)
    app.register_blueprint(validate_csv_bp)
    app.register_blueprint(enrich_csv_bp)

    # Initialize Flasgger for Swagger UI
    swagger_path = os.path.join(os.path.dirname(__file__), '..', 'swagger.json')
    if os.path.exists(swagger_path):
        with open(swagger_path, 'r') as f:
            swagger_spec = json.load(f)
        Flasgger(app, specs=[{'spec': swagger_spec}])
    else:
        # Fallback to auto-generation if swagger.json not found
        Flasgger(app)

    return app