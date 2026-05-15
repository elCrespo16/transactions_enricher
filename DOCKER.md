# Docker Setup for Transactions Enricher

This project now supports Docker with both development and production environments.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

### Development Environment

Run with Flask development server (auto-reloading):

```bash
TARGET_ENV=development docker compose up
```

The application will be available at `http://localhost:5000`

### Production Environment

Run with Gunicorn (production WSGI server):

```bash
TARGET_ENV=production docker compose up
```

The application will be available at `http://localhost:5000`

## Configuration

### Environment Variables

- `TARGET_ENV`: Set to `development` or `production` (default: `development`)
- `PORT`: Port to expose (default: `5000`)

### Building the Image

To build the Docker image for a specific environment:

```bash
# Development image
docker build --target development -t transactions_enricher:dev .

# Production image
docker build --target production -t transactions_enricher:prod .
```

### Running Containers Directly

```bash
# Development
docker run -it -p 5000:5000 -v $(pwd):/app transactions_enricher:dev

# Production
docker run -d -p 5000:5000 transactions_enricher:prod
```

## File Structure

- `Dockerfile`: Multi-stage build configuration supporting both dev and prod environments
- `docker-compose.yml`: Orchestrates the container with configurable environment

## Notes

- **Development**: Uses Flask's built-in development server with auto-reloading. Code changes in the mounted volume will trigger server restart.
- **Production**: Uses Gunicorn with 4 worker processes and 120-second timeout for robust production deployment.
- Non-root user (`appuser`) runs the application for security.
- Volumes are mounted in development mode for live code changes; not included in production recommendations.
