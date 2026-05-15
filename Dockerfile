# Multi-stage build for both development and production
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Development stage
FROM base as development

ENV FLASK_APP=app
ENV FLASK_ENV=development

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]

# Production stage
FROM base as production

ENV FLASK_ENV=production

EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "120", "wsgi:app"]
