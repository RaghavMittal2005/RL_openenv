FROM ghcr.io/meta-pytorch/openenv-base:latest
WORKDIR /app

# Upgrade pip and install latest openenv first
RUN pip install --upgrade pip && pip install 'openenv>=0.2.0' fastapi uvicorn

# Copy project files
COPY my_env /app/my_env
COPY my_env/pyproject.toml /app/

# Install the package in editable mode
RUN pip install -e .

EXPOSE 8000
CMD ["uvicorn", "my_env.server.app:app", "--host", "0.0.0.0", "--port", "8000"]