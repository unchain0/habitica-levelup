FROM python:3.14-slim AS deps

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml .
RUN uv pip install --system -e . && rm -rf /root/.cache

FROM python:3.14-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser appuser

WORKDIR /app

COPY --from=deps /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages

COPY --chown=appuser:appuser pyproject.toml .
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser main.py .

RUN mkdir -p /home/appuser/.local/share/habitica-levelup && \
    chown -R appuser:appuser /home/appuser/.local

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "python main.py" > /dev/null 2>&1 || exit 1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    LOG_LEVEL=INFO

CMD ["python", "main.py"]

FROM runtime AS development

USER root

COPY --from=deps /root/.local/bin/uv /usr/local/bin/uv
RUN uv pip install --system --group dev && rm -rf /root/.cache

USER appuser

COPY --chown=appuser:appuser tests/ ./tests/
COPY --chown=appuser:appuser .pre-commit-config.yaml .

CMD ["python", "main.py"]
