# Examples

[![Docs](https://img.shields.io/badge/docs-authzed.com-%234B4B6C "Authzed Documentation")](https://docs.authzed.com)
[![Discord Server](https://img.shields.io/discord/844600078504951838?color=7289da&logo=discord "Discord Server")](https://discord.gg/jTysUaxXzM)
[![Twitter](https://img.shields.io/twitter/follow/authzed?color=%23179CF0&logo=twitter&style=flat-square "@authzed on Twitter")](https://twitter.com/authzed)

This repository houses various examples for various aspects of SpiceDB.

[SpiceDB] is an open source database system for managing security-critical application permissions inspired by Google's [Zanzibar] paper.

Developers create a schema that models their permissions requirements and use a [client library] to apply the schema to the database, insert data into the database, and query the data to efficiently check permissions in their applications.

[SpiceDB]: https://github.com/authzed/spicedb
[Zanzibar]: https://authzed.com/blog/what-is-zanzibar/
[client library]: https://github.com/orgs/authzed/repositories?q=client+library

Examples in this repository include:

- How to set up SpiceDB with tracing: see [tracing](./tracing)
- How to invoke SpiceDB as a library: see [library](./library)
- How to run SpiceDB in a Kubernetes cluster: see [kubernetes](./kubernetes)
- CI/CD Workflows

Have questions? Join our [Discord].

Looking to contribute? See [CONTRIBUTING.md].

[Discord]: https://authzed.com/discord
[CONTRIBUTING.md]: https://github.com/authzed/spicedb/blob/main/CONTRIBUTING.md
