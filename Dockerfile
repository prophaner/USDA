# Start from a lightweight Python image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable stdout/stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# Install system dependencies (if any), then your Python deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY curado_usda .

# Expose the port Uvicorn will serve on
EXPOSE 80

# Launch Uvicorn with the package's FastAPI app
CMD ["uvicorn", "curado_usda.server:app", "--host", "0.0.0.0", "--port", "80"]
