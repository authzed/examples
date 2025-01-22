## Multiple Validation Files with a Single Schema

This requires zed version v0.25.0.

This folder demonstrates a structure for a schema and validation files that
can be run in a single `zed validate` command and used as a template
for writing multiple independent tests of a single schema.

Running the following:

```
zed validate validations/*
```

in this folder will validate the schema and run all validations in all schema files.

Note the use of `schemaFile: ` in the validation files - this allows the validation file to
reference the schema without the schema needing to be inline.
