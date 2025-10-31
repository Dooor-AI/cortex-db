FROM python:3.11-slim

# Increase pip timeout to handle large dependency downloads during multi-arch builds
ENV PIP_DEFAULT_TIMEOUT=600

# Install system dependencies required for PDF rendering and OpenCV.
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./requirements.txt

# Use cache mount for pip to speed up rebuilds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

COPY . /app/gateway

ENV PYTHONPATH=/app

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
