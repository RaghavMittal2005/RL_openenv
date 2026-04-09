FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project files (pyproject.toml at root, package in my_env/)
COPY my_env/pyproject.toml /app/
COPY my_env/*.py /app/my_env/
COPY my_env/server/ /app/my_env/server/
ENV ENABLE_WEB_INTERFACE=true
# Install dependencies using uv
RUN uv sync --no-editable

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "my_env.server.app:app", "--host", "0.0.0.0", "--port", "8000"]