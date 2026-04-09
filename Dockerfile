FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY my_env /app/my_env
COPY my_env/pyproject.toml /app/

# Install dependencies using uv (without cache mount for compatibility)
RUN cd my_env && uv sync --no-editable

# Set PATH to use the virtual environment
ENV PATH="/app/my_env/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "my_env.server.app:app", "--host", "0.0.0.0", "--port", "8000"]