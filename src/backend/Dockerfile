# Base Python image
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye AS base
WORKDIR /app

FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.6.3 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Copy project files for dependency resolution
COPY uv.lock pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv \
   --mount=type=bind,source=uv.lock,target=uv.lock \
   --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
   uv sync --frozen --no-install-project --no-dev

# Copy entire project and install
COPY . /app  
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

FROM base
COPY --from=builder /app /app
COPY --from=builder /bin/uv /bin/uv
ENV PATH="/app/.venv/bin:$PATH"

# Set working directory to backend where app_kernel.py is located
WORKDIR /app/src/backend

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app_kernel:app", "--host", "0.0.0.0", "--port", "8000"]
