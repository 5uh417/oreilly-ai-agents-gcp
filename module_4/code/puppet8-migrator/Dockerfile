# Dockerfile for the Puppet 7→8 Migration API Server
#
# Build:
#   docker build -t puppet8-migrator-api .
#
# Run:
#   docker run -p 8090:8090 \
#     -e GOOGLE_API_KEY=your-key \
#     -e GIT_TOKEN=your-github-pat \
#     puppet8-migrator-api
#
# For Concord Docker task:
#   Use this image directly in the Concord task configuration.

FROM python:3.11-slim

# Install git (required for cloning repos)
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy the full project
COPY . .

# Make scripts executable
RUN chmod +x concord_runner.py run_demo.py run_programmatic.py

# Default: run the API server
EXPOSE 8090
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8090"]
