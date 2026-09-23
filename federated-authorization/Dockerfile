FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Runtime directories (overridden by volume mounts in compose)
RUN mkdir -p /data/documents

ENV DB_PATH=/data/app.db
ENV DOCUMENTS_DIR=/data/documents
# Stream print() output straight to the container logs (no stdout buffering)
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
