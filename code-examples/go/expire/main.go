package main

import (
	"context"
	"log"
	"time"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/authzed/authzed-go/v1"
	"github.com/authzed/grpcutil"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/types/known/timestamppb"
)

func main() {
	client, err := authzed.NewClient(
		//this example uses a local SpiceDB without TLS
		"localhost:50051",
		grpcutil.WithInsecureBearerToken("abc123"),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		log.Fatalf("unable to initialize client: %s", err)
	}

	now := time.Now()

	//sets the expirationTime 20 seconds from now
	expirationTime := now.Add(20 * time.Second)

	request := &v1.WriteRelationshipsRequest{Updates: []*v1.RelationshipUpdate{
		{
			Operation: v1.RelationshipUpdate_OPERATION_CREATE,
			Relationship: &v1.Relationship{
				Resource: &v1.ObjectReference{
					ObjectType: "document",
					ObjectId:   "1",
				},
				Relation: "viewer",
				Subject: &v1.SubjectReference{
					Object: &v1.ObjectReference{
						ObjectType: "user",
						ObjectId:   "tim",
					},
				},
				//OptionalExpiresAt specifies the expiration time.
				OptionalExpiresAt: timestamppb.New(expirationTime),
			},
		},
	}}

	_, err = client.WriteRelationships(context.Background(), request)
	if err != nil {
		log.Fatalf("failed to write relationship: %s", err)
	}
}
