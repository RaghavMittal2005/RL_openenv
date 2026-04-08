FROM ghcr.io/meta-pytorch/openenv-base:latest
WORKDIR /app
COPY my_env /app/my_env
COPY my_env/pyproject.toml /app/
RUN uv pip install -e . && uv pip install -r my_env/server/requirements.txt
EXPOSE 8000
CMD ["uvicorn", "my_env.server.app:app", "--host", "0.0.0.0", "--port", "8000"]