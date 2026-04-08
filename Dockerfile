FROM ghcr.io/meta-pytorch/openenv-base:latest
WORKDIR /app

# Copy project files
COPY my_env /app/my_env
COPY my_env/pyproject.toml /app/

# Install the package with available dependencies
RUN pip install openenv fastapi uvicorn pydantic && pip install -e .

EXPOSE 8000
CMD ["uvicorn", "my_env.server.app:app", "--host", "0.0.0.0", "--port", "8000"]