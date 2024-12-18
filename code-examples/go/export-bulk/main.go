package main

import (
	"context"
	"errors"
	"io"
	"log"
	"time"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/authzed/authzed-go/v1"
	"github.com/authzed/grpcutil"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

const spicedbEndpoint = "localhost:50051"
const maxRetries = 5

func main() {
	client, err := authzed.NewClient(
		spicedbEndpoint,
		grpcutil.WithInsecureBearerToken("abc123"),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		log.Fatalf("unable to initialize client: %s", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	var cursor *v1.Cursor
	var exportResults []*v1.Relationship

	totalProcessed := 0

	var endOfFile bool

	request := &v1.ExportBulkRelationshipsRequest{
		OptionalLimit: 1000,
	}

	retries := 0

	for {
		if cursor != nil {
			request.OptionalCursor = cursor
		}
		stream, err := client.PermissionsServiceClient.ExportBulkRelationships(ctx, request)
		if err != nil {
			retry(&retries, err)
			continue
		}

		for {
			item, err := stream.Recv()
			if errors.Is(err, io.EOF) {
				endOfFile = true
				break
			}
			if err != nil {
				log.Printf("Stream error: %s", err)
				retry(&retries, err)
				break
			}

			exportResults = append(exportResults, item.Relationships...)

			cursor = item.AfterResultCursor

			totalProcessed += len(item.Relationships)
			log.Printf("Processed total: %d.", totalProcessed)

		}

		if endOfFile {
			break
		}
	}

	log.Printf("Export complete: %d relationships retrieved\n", totalProcessed)

}

func retry(retries *int, err error) {
	*retries++
	if *retries >= maxRetries {
		log.Fatalf("Max retries reached: %s", err)
	}
	log.Printf("Retrying (%d/%d) after error: %s", *retries, maxRetries, err)
	time.Sleep(time.Second * time.Duration(*retries)) // Backoff
}
