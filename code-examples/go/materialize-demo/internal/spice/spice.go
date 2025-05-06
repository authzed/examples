package spice

import (
	"context"
	"log"

	pb "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/authzed/authzed-go/v1"
	"github.com/authzed/grpcutil"
	"github.com/fatih/color"
	"github.com/jzelinskie/stringz"
	"github.com/kataras/golog"
)

func clientInit() *authzed.Client {
	systemCerts, err := grpcutil.WithSystemCerts(grpcutil.VerifyCA)
	if err != nil {
		log.Fatalf("unable to load system CA certificates: %s", err)
	}

	spiceClient, err := authzed.NewClient(
		"materialize-demo-epic-herring-5707.us-east-1.demo.aws.authzed.net:443",
		//insert token here
		grpcutil.WithBearerToken(""),
		systemCerts,
	)
	if err != nil {
		log.Fatalf("unable to initialize client: %s", err)
	}

	return spiceClient
}

func ReadSchema() error {
	client := clientInit()

	request := &pb.ReadSchemaRequest{}

	resp, err := client.ReadSchema(context.Background(), request)

	//todo: look at how zed formats the schema, maybe use a library from there for this
	if err != nil {
		return err
	} else {
		color.Blue(stringz.Join("\n\n", resp.SchemaText))
	}
	return nil
}

func WriteRelationship() error {
	client := clientInit()

	objectType := "document"
	objectID := "789"
	relation := "folder"
	subjectObjectType := "folder"
	subjectObjectID := "abc"

	request := &pb.WriteRelationshipsRequest{Updates: []*pb.RelationshipUpdate{
		{
			Operation: pb.RelationshipUpdate_OPERATION_CREATE,
			Relationship: &pb.Relationship{
				Resource: &pb.ObjectReference{
					ObjectType: objectType,
					ObjectId:   objectID,
				},
				Relation: relation,
				Subject: &pb.SubjectReference{
					Object: &pb.ObjectReference{
						ObjectType: subjectObjectType,
						ObjectId:   subjectObjectID,
					},
				},
			},
		},
	}}
	_, err := client.WriteRelationships(context.Background(), request)
	if err != nil {
		return err
	}

	golog.Infof("Wrote relationship: %s %s %s %s %s", objectType, objectID, relation, subjectObjectType, subjectObjectID)

	return nil
}

func DeleteRelationship() error {
	client := clientInit()

	objectType := "document"
	objectID := "789"
	relation := "folder"
	subjectObjectType := "folder"
	subjectObjectID := "abc"

	request := &pb.WriteRelationshipsRequest{Updates: []*pb.RelationshipUpdate{
		{
			Operation: pb.RelationshipUpdate_OPERATION_DELETE,
			Relationship: &pb.Relationship{
				Resource: &pb.ObjectReference{
					ObjectType: objectType,
					ObjectId:   objectID,
				},
				Relation: relation,
				Subject: &pb.SubjectReference{
					Object: &pb.ObjectReference{
						ObjectType: subjectObjectType,
						ObjectId:   subjectObjectID,
					},
				},
			},
		},
	}}
	_, err := client.WriteRelationships(context.Background(), request)
	if err != nil {
		return err
	}

	golog.Infof("Cleaned up (deleted) relationship: %s %s %s %s %s", objectType, objectID, relation, subjectObjectType, subjectObjectID)

	return nil
}
