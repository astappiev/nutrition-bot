FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS base

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install deps first so this layer is cached unless pyproject/uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Then bring in the source and install the project itself.
COPY src ./src
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Written by the app at startup; keep it out of the image, mount a volume instead.
VOLUME ["/data"]
ENV DATABASE_PATH=/data/nutrition.db

CMD ["python", "-m", "assistant"]
