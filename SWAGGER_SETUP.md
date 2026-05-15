# Swagger/OpenAPI Integration

This project now includes both a CLI and a Flask API with integrated Swagger UI.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask API:**
   ```bash
   # Using flask CLI
   flask --app wsgi run

   # Or using Python
   python wsgi.py

   # Or using gunicorn (production)
   gunicorn wsgi:app --bind 0.0.0.0:5000
   ```

3. **Access Swagger UI:**
   - Open your browser to: `http://localhost:5000/apidocs/`
   - The interactive Swagger UI allows you to test all endpoints
   - Alternative Swagger UI endpoint: `http://localhost:5000/apidocs`
   - ReDoc endpoint: `http://localhost:5000/redoc/`

## API Endpoints

### CSV Validation
- **POST /validate_csv** - Validate CSV file structure and data
  - Upload a CSV file to check if it's properly formatted

### Rules Validation
- **POST /validate_rules** - Validate enrichment rules
  - Upload YAML/YML rules file or send rules as JSON

### CSV Enrichment
- **POST /enrich_csv** - Enrich CSV with rules
  - Upload CSV file and rules file to get enriched data
  - Optional: provide bank configuration

## Documentation Files

- **swagger.json** - Complete OpenAPI 3.0 specification in JSON format
- **swagger.yaml** - Complete OpenAPI 3.0 specification in YAML format

## Example Usage with curl

### Validate CSV
```bash
curl -X POST -F "file=@transactions.csv" http://localhost:5000/validate_csv
```

### Validate Rules
```bash
# With YAML file
curl -X POST -F "file=@rules.yaml" http://localhost:5000/validate_rules

# With JSON
curl -X POST -H "Content-Type: application/json" \
  -d '{"rules": [...]}' http://localhost:5000/validate_rules
```

### Enrich CSV
```bash
curl -X POST \
  -F "file=@transactions.csv" \
  -F "rules=@rules.yaml" \
  http://localhost:5000/enrich_csv
```

## CLI Usage

The original CLI is still available:
```bash
python main.py -f bank_config.yaml
```

For more CLI options:
```bash
python main.py --help
```
