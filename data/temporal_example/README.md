# Distributed Writes to SpiceDB with Temporal

This is a "quick start" example that demonstrates how you can use Temporal to maintain a consistent state across SpiceDB and an application DB (Postgres in this example) in the event of failures.

Before beginning this example walkthrough, it is recommended to have basic knowledge of Temporal. [Here](https://docs.temporal.io/evaluate/understanding-temporal) is a good place to start with Temporal.

## Prerequisites
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Temporal CLI](https://docs.temporal.io/cli#install)
- [Python 3](https://www.python.org/downloads/)
- [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/) (included with Python if you installed via Homebrew or python.org) 

## Running this Example

Follow these steps to run this example:

### Setup
1. Clone the SpiceDB examples repo: ` git clone git@github.com:authzed/examples.git`
2. Change into the Docker Compose directory `cd examples/data/temporal_example/compose`
3. Start SpiceDB and Postgres with `docker-compose up -d`
4. Change to the parent directory: `cd ..`
5. Start a development Temporal Server: `temporal server start-dev`
6. Setup a virtual env: `python3 -m venv env`, then `source env/bin/activate`.
7. Install dependencies: `python3 -m pip install authzed temporalio psycopg`
8. Setup the Postgres DB and SpiceDB: `python3 run_migrations.py`
9. Start the Temporal Worker: `python3 run_worker.py`

### Experiencing Temporal
10. Run the Temporal workflow (worker should still be running while you are doing this): `python3 run_workflow.py --author bob --post some_post`
11. Simulate a Postgres failure by stopping the Docker container running Postgres: `docker stop dev-postgres`
12. Run the Temporal workflow (worker should still be running while you are doing this): `python3 run_workflow.py --author bob --post another_post`
13. Notice that the initial attempt failed.
14. Restart Postgres: `docker start dev-postgres`
15. Wait a few seconds and notice that the Postgres write activity succeeds and that the workflow succeeds. 😎

## Important Takeaways from this Example

- This example uses Temporal's default [retry policy](https://docs.temporal.io/encyclopedia/retry-policies) for Activities and Workflows. This means that an Activity will indefinitely try to complete a successful execution.

- Both Postgres and SpiceDB writes in this example are idempotent. In the case of the record already existing, there will be no errors and the workflow will complete successfully. [Temporal recommends that all activities be idempotent.](https://docs.temporal.io/activity-definition#idempotency)

- This example uses a single Temporal Task Queue partition. [Task Queues with a single partition](https://docs.temporal.io/task-queue#task-ordering) are almost always first-in, first-out, with rare edge case exceptions.

- This example writes directly to SpiceDB and Postgres. For many use cases, Temporal will make API requests to distributed microservices that in turn make requests to SpiceDB and an app DB.
