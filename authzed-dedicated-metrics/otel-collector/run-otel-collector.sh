#!/bin/bash

# Load environment variables from file
source ./env-vars.sh

# Check if all necessary environment variables are set
if [[ -z "$PROMETHEUS_USERNAME" || -z "$PROMETHEUS_PASSWORD" || -z "$OTEL_EXPORTER_OTLP_ENDPOINT" || -z "$OTEL_EXPORTER_OTLP_HEADERS" || -z "$OTEL_SERVICE_NAME" ]]; then
  echo "One or more environment variables are not set. Please check your env-vars.sh file."
  exit 1
fi

# Run OpenTelemetry Collector Docker container
docker run --rm -it \
  -v $(pwd)/otel-collector-config.yaml:/otel-collector-config.yaml \
  -e PROMETHEUS_USERNAME="$PROMETHEUS_USERNAME" \
  -e PROMETHEUS_PASSWORD="$PROMETHEUS_PASSWORD" \
  -e OTEL_EXPORTER_OTLP_ENDPOINT="$OTEL_EXPORTER_OTLP_ENDPOINT" \
  -e OTEL_EXPORTER_OTLP_HEADERS="$OTEL_EXPORTER_OTLP_HEADERS" \
  -e OTEL_SERVICE_NAME="$OTEL_SERVICE_NAME" \
  otel/opentelemetry-collector:latest \
  --config otel-collector-config.yaml
