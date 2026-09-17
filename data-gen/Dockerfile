FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY generator ./generator

# No long-running server: this image is invoked per cohort setup, e.g.
#   docker compose run --rm data-gen python -m generator <scenario-instance-id>
CMD ["python", "-m", "generator", "--help"]
