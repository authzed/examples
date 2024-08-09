
# OpenTelemetry Collector for AuthZed Dedicated Metrics

This guide explains how to deploy the OpenTelemetry Collector Contributor image to collect metrics from AuthZed Dedicated and push them to Datadog.

## Prerequisites

- Docker installed on your machine.
- Access to AuthZed Dedicated instance.
- Datadog API key.

## Deployment

### Step 1: Prepare the Configuration File

Create a configuration file named `otel-config.yaml` with the following content. Be sure to replace the placeholders with your actual values:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: 'prometheus'
          metrics_path: /api/v1alpha/metrics
          scrape_interval: 15s
          static_configs:
            - targets: ['<YOUR_AUTHZED_DEDICATED_INSTANCE>']
          basic_auth:
            username: '<PS_NAME>'
            password: '<METRICS_TOKEN>'

exporters:
  datadog:
    api:
      site: "<YOUR_DATADOG_SITE>"
      key: "<YOUR_DATADOG_API_KEY>"

service:
  pipelines:
    metrics:
      receivers: [prometheus]
      processors: []
      exporters: [datadog]
```

### Step 2: Deploy the OpenTelemetry Collector

Run the following Docker command to deploy the OpenTelemetry Collector:

```bash
docker run --rm -d --name otel-collector -v "$(pwd)/otel-config.yaml:/otel-config.yaml" otel/opentelemetry-collector-contrib:latest --config=/otel-config.yaml
```

This command will start the OpenTelemetry Collector, which will begin scraping metrics from your AuthZed Dedicated instance and exporting them to Datadog.

### Step 3: Verify the Metrics in Datadog

Log in to your Datadog account and navigate to the metrics section. You should see the metrics from your AuthZed Dedicated instance being reported.

## Configuration Details

- `<YOUR_AUTHZED_DEDICATED_INSTANCE>`: Replace with the URL of your AuthZed Dedicated instance (e.g., `example.app.aws.authzed.net`).
- `<PS_NAME>` and `<METRICS_TOKEN>`: Replace with the username and password for basic authentication to access your AuthZed metrics endpoint.
- `<YOUR_DATADOG_SITE>`: Replace with your Datadog site URL (e.g., `us5.datadoghq.com`).
- `<YOUR_DATADOG_API_KEY>`: Replace with your Datadog API key.

## Troubleshooting

If you encounter issues:

- Ensure that the `otel-config.yaml` file is correctly configured and that all placeholders are replaced with actual values.
- Check the Docker container logs for any errors:

  ```
  docker logs otel-collector
  ```

- Verify that your AuthZed Dedicated instance is accessible and that the credentials are correct.
- Confirm that your Datadog API key and site are correct.