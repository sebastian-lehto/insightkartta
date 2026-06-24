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

# backend/data/raw/ is committed to the repo, so this never needs network
# access to StatFin or vaalit.fi at build time — it only transforms/analyzes
# data that's already on disk.
RUN make pipeline-all PYTHON=python3

EXPOSE 8000

CMD ["make", "serve", "PYTHON=python3"]
