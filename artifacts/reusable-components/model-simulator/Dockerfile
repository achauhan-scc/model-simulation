FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system --gid 10001 simulator \
    && useradd --system --uid 10001 --gid simulator --home-dir /nonexistent simulator

COPY pyproject.toml README.md ./
COPY src ./src
COPY mappings ./mappings
COPY responses ./responses

RUN python -m pip install --no-cache-dir .

USER 10001:10001

EXPOSE 8000

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
