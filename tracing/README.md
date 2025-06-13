# Description

This docker compose sets up SpiceDB with an OTEL stack for tracing ([OTEL](https://opentelemetry.io/) Collector, [Tempo](https://grafana.com/docs/tempo/latest/) and [Grafana](https://grafana.com/)).
This is for demonstration purposes and not meant to be used as a production observability setup.

- SpiceDB is configured to send OTEL traces to an instance of the otel-collector.
- otel-collector exports traces to Tempo, the latter acting as tracing backend.
- Grafana is configured with Tempo as datasource.

## Usage

```shell
docker compose up
```

Grafana will be available locally at http://localhost:3000 with Tempo set up as datasource for tracing.

Issue some requests to SpiceDB using the [zed cli](https://github.com/authzed/zed) so we can generate some traces:

```bash
zed context set example localhost:50051 foobar --insecure
zed schema write schema.zed
zed schema read
zed relationship create document:1 writer user:1
zed permission check document:1 view user:1
```
