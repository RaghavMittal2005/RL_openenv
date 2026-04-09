FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY my_env /app/my_env
COPY my_env/pyproject.toml /app/

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Install dependencies using uv
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f my_env/uv.lock ]; then \
        cd my_env && uv sync --frozen --no-editable; \
    else \
        cd my_env && uv sync --no-editable; \
    fi

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "my_env.server.app:app", "--host", "0.0.0.0", "--port", "8000"]