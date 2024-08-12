
# OpenTelemetry Collector - AuthZed Dedicated

This repository provides a simple setup for running the OpenTelemetry Collector in a Docker container, configured to scrape metrics from a Prometheus endpoint and export to a metrics collection service. 

## Prerequisites

- Docker installed on your machine
- A Prometheus endpoint with valid credentials
- A metrics service account and API key

## Setup


2. **Create the `env-vars.sh` File**

   Edit the file named `env-vars.sh` in the root of the repository with the following content:

   ```sh
   export PROMETHEUS_USERNAME='<permission-system-name>'
   export PROMETHEUS_PASSWORD='<permission-system-token>'
   export OTEL_EXPORTER_OTLP_ENDPOINT="https://otel-metrics-service-url"
   export OTEL_EXPORTER_OTLP_HEADERS="your-service-key"
   export OTEL_SERVICE_NAME="authzed-<permission-system-name>"
   ```

   Replace the placeholder values with your actual credentials and configurations.

3. **Create the Configuration File**

   Edit the file named `otel-collector-config.yaml` in the root of the repository.

4. **Make the Script Executable**

   Make the `run-otel-collector.sh` script executable:

   ```bash
   chmod +x run-otel-collector.sh
   ```

5. **Run the Script**

   Run the script to start the OpenTelemetry Collector Docker container with the configured settings:

   ```bash
   ./run-otel-collector.sh
   ```

## Files

- `env-vars.sh`: Contains the environment variables for Prometheus and Honeycomb configuration.
- `otel-collector-config.yaml`: Configuration file for the OpenTelemetry Collector.
- `run-otel-collector.sh`: Shell script to load environment variables and run the OpenTelemetry Collector Docker container.


## Contact

If you have any questions or need further assistance, feel free to open an issue or contact support@authzed.com