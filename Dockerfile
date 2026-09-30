FROM python:3.12-slim

# `make` drives the pipeline/server commands so this stays a thin wrapper
# around the same Makefile used locally, rather than duplicating its logic.
RUN apt-get update \
    && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml Makefile ./
RUN pip install --no-cache-dir .

COPY backend/ backend/

# StatFin and election raw inputs are committed. Paavo postal data is not, so
# the postal-only target fetches it during the image build and generates
# processed CSVs and analysis. Raw responses are removed from the image only.
RUN make pipeline-all postal-pipeline PYTHON=python3 \
    && rm -rf backend/data/raw/postal_code_*

EXPOSE 8000

CMD ["make", "serve", "PYTHON=python3"]
