# Integration Testing against SpiceDB

This demonstrates how to perform integration tests against SpiceDB.

Even if you are not using Go, the fundamentals should remain the same:

1. Spin up a SpiceDB container running the `serve-testing` command.
2. For each independent test, create a SpiceDB client with a random key.
3. Run tests. Tests with different keys are safe to run in parallel.
