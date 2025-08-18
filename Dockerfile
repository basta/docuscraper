# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install uv, the project manager
RUN pip install uv

# Copy dependency definitions
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using the lockfile for a reproducible environment
RUN uv pip install --system .

# Copy the application source code into the container
# This includes the 'api', 'doc_scraper_engine', and 'frontend' directories
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the FastAPI app with uvicorn
# It will listen on all interfaces (0.0.0.0) inside the container on port 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]