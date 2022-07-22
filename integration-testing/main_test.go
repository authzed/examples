// This demonstrates how to perform integration tests against SpiceDB.
//
// Even if you are not using Go, the fundamentals should remain the same:
// 1. Spin up a SpiceDB container running the `serve-testing` command.
// 2. For each independent test, create a SpiceDB client with a random key.
// 3. Run tests. Tests with different keys are safe to run in parallel.
package main

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"testing"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/authzed/authzed-go/v1"
	"github.com/authzed/grpcutil"
	"github.com/ory/dockertest/v3"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// runSpiceDBTestServer spins up a SpiceDB container running the integration
// test server.
func runSpiceDBTestServer(t *testing.T) (port string, err error) {
	pool, err := dockertest.NewPool("") // Empty string uses default docker env
	if err != nil {
		return
	}

	resource, err := pool.RunWithOptions(&dockertest.RunOptions{
		Repository:   "authzed/spicedb",
		Tag:          "latest", // Replace this with an actual version
		Cmd:          []string{"serve-testing"},
		ExposedPorts: []string{"50051/tcp", "50052/tcp"},
	})
	if err != nil {
		return
	}

	// When you're done, kill and remove the container
	t.Cleanup(func() {
		_ = pool.Purge(resource)
	})

	return resource.GetPort("50051/tcp"), nil
}

// spicedbTestClient creates a new SpiceDB client with random credentials.
//
// The test server gives each set of a credentials its own isolated datastore
// so that tests can be ran in parallel.
func spicedbTestClient(t *testing.T, port string) (*authzed.Client, error) {
	// Generate a random credential to isolate this client from any others.
	buf := make([]byte, 20)
	if _, err := rand.Read(buf); err != nil {
		return nil, err
	}
	randomKey := base64.StdEncoding.EncodeToString(buf)

	return authzed.NewClient(
		"localhost:"+port,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpcutil.WithInsecureBearerToken(randomKey),
		grpc.WithBlock(),
	)
}

func TestSpiceDB(t *testing.T) {
	port, err := runSpiceDBTestServer(t)
	if err != nil {
		t.Fatal(err)
	}

	tests := []struct {
		name   string
		schema string
	}{
		{
			"basic readback",
			`definition user {}`,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			client, err := spicedbTestClient(t, port)
			if err != nil {
				t.Fatal(err)
			}

			_, err = client.WriteSchema(context.TODO(), &v1.WriteSchemaRequest{Schema: tt.schema})
			if err != nil {
				t.Fatal(err)
			}

			resp, err := client.ReadSchema(context.TODO(), &v1.ReadSchemaRequest{})
			if err != nil {
				t.Fatal(err)
			}

			if tt.schema != resp.SchemaText {
				t.Fatal(err)
			}
		})
	}
}
