FROM python:3.13-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl jq wget git net-tools \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set environment variables
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (main only)
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root --only main

# Final stage
FROM base AS final

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Copy installed dependencies from base
COPY --from=base ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy the rest of the application code
COPY . ./

# Run the FastAPI application with Uvicorn
CMD ["uvicorn", "lmd_state.main:app", "--host", "0.0.0.0", "--port", "8000"]
