# Description

This docker compose sets up SpiceDB with an open-telemetry based stack for tracing (OTEL Collector, Tempo and Grafana).
This is for demonstration purposes and not meant to be used as a production observability setup.

- SpiceDB is configured to send OTEL traces to an instance of the otel-collector
- otel-collector exports traces to tempo, the latter acting as tracing backend
- grafana is configured with tempo as datasource

## Usage

```shell
docker compose up
```

Grafana will be available locally at http://localhost:3000 with Tempo set up as datasource for tracing.

Issue some requests to spicedb so we can start collecting traces

```bash
zed context set example localhost:50051 foobar --insecure
zed schema write schema.zed
zed schema read
zed relationship create document:1 writer user:1
zed permission check document:1 view user:1
```
