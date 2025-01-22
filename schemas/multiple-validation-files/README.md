## Multiple Validation Files with a Single Schema

This folder demonstrates a structure for a schema and validation files that
can be run in a single `zed validate` command and used as a template
for writing multiple independent tests of a single schema.

Running the following:

```
zed validate validations/*
```

in this folder will validate the schema and run all validations in all schema files.
