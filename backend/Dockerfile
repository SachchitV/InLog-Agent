FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app/backend

# Copy dependency files first (cache layer)
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --frozen --no-dev

# Copy backend source
COPY . .

# Create runtime directories
RUN mkdir -p data/uploads data/schemas outputs

EXPOSE 8000

CMD ["uv", "run", "python", "server.py"]
