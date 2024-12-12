# Spicedb Observability with the Datadog Agent

## Overview
This is a repository that demonstrates a configuration of SpiceDB and the Datadog Agent
that supports sending metrics and traces to Datadog. This is not the only valid configuration
and should be adapted to your use case.

The metrics produced in this configuration are submitted as custom metrics. We're actively working
on an official SpiceDB integration that would make the metrics into standard metrics and simplify
setup and configuration.

### Running in Production
A "real" deployment would use a container runtime of some sort. One approach would be to
run the datadog agent as a sidecar; another would be to run a set of agents using
the [Datadog Operator](https://docs.datadoghq.com/getting_started/containers/datadog_operator/)
and then point them at your SpiceDB instances using [annotations](https://docs.datadoghq.com/containers/kubernetes/integrations).
This repository is only intended to communicate the agent check configuration
and the required SpiceDB configuration.

## Running this repo
```
mv placeholder.env .env
```

Define your `DD_API_KEY` in the env file.

Run `docker compose up`.

### Thumper
This is an internal load-testing tool that we built a while back. We use it in this project to
exercise gRPC endpoints so that there are traces and metrics to look at.

## The Dashboard
This is a preview of the dashboard that will be bundled with the SpiceDB Community integration.
It shows throughput, latency, and some basic node CPU and memory metrics. Note that the CPU and memory
metrics may be missing context from the container runtime environment, such as limits provided by kubernetes.

Also note that the dashboard uses the metrics exported by SpiceDB as histogram metrics, which Datadog then internally
converts to its distribution-style metrics. There's likely some loss in resolution as a result; if this is a concern,
and 100% of traces are being collected, it may make more sense to make the latency graphs reference the trace
distribution supplied by Datadog.

To use the dashboard, grab `spicedb-dashboard.json` and import it into Datadog.

## Tracing
SpiceDB supports OTLP export of traces. This is configured in the environment variables in `docker-compose.yml` on
the `datadog` and `spicedb` services. Traces are pushed by SpiceDB to the Datadog agent via its OTLP endpoint,
and then the agent forwards them to Datadog.

## Metrics
SpiceDB exposes a Prometheus metrics endpoint on port 9090 by default. This can be scraped by the Datadog Agent
using its Openmetrics integration, which is compatible with the Prometheus metrics format. The configuration is
visible in `conf.d/openmetrics.d/conf.yaml`.

## Logs
SpiceDB writes structured JSON logs to stdout, which can be collected through your normal log collection mechanisms.

### All Available Metrics
The configuration in `conf.d/openmetrics.d/conf.yaml` currently only includes those metrics required to drive the dashboard.
If additional metrics are desired, their names and descriptions can be found in `all_metrics.txt`.
