# Use a slim Python base image for smaller size
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.29 /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy the uv configuration files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy the application code
COPY src/app/ app/

# Expose the port that FastAPI will run on
EXPOSE 8000

# Use Uvicorn as the ASGI server.
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
