#!/bin/bash

#to do: handle this in the app logic

# Find the process ID (PID) using lsof to identify processes using port 5432
PID=$(lsof -ti :5432)

# Check if PID is not empty
if [ -z "$PID" ]; then
  echo "No process is running on port 5432."
else
  # Kill the process
  kill -9 $PID
  echo "Killed process with PID $PID running on port 5432."
fi

zed relationship delete document:789 folder folder:abc --endpoint=materialize-demo-epic-herring-5707.us-east-1.demo.aws.authzed.net:443 --token=sdbst_h256_e4b91fcb2d3eb39d75c507b5fc4595494aa36f70db44f39a8a0ab5c3ba6eb836be7d8b225a0cd1bd8a036aed5e461dd0ab044dca0dbc525a2026638e2aa8dd3521bbeb74fdfc752f440e56010c48a42208fbd2b198f59e46030ef7e33db40c4e