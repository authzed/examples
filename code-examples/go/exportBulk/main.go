package main

import (
	"context"
	"io"
	"log"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/authzed/authzed-go/v1"
	"github.com/authzed/grpcutil"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

const spicedbEndpoint = "localhost:50051"

func main() {
	client, err := authzed.NewClient(
		spicedbEndpoint,
		//this example connects to an insecure endpoint
		grpcutil.WithInsecureBearerToken("abc123"),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		log.Fatalf("unable to initialize client: %s", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	var cursor *v1.Cursor
	exportResults := make([]*v1.Relationship, 0)
	batchCount := 0

	// Prepare request with cursor if available
	request := &v1.ExportBulkRelationshipsRequest{
		//optimal limit is around 1,000
		OptionalLimit: 1000,
	}
	if cursor != nil {
		request.OptionalCursor = cursor
	}

	// Fetch the stream
	stream, err := client.PermissionsServiceClient.ExportBulkRelationships(ctx, request)
	if err != nil {
		log.Fatalf("failed to export relationships: %s", err)
	}

	batchSize := 0
	for {
		item, err := stream.Recv()
		if err == io.EOF {
			// End of the current stream
			break
		}
		if err != nil {
			log.Fatalf("stream error: %s", err)
		}

		// Append relationships and update the cursor
		exportResults = append(exportResults, item.Relationships...)
		cursor = item.AfterResultCursor
		batchSize += len(item.Relationships)
		batchCount++

		log.Printf("Processed batch %d. %d relationships so far.\n", batchCount, batchSize)
	}

	log.Printf("Export complete: %d relationships retrieved\n", len(exportResults))
}
