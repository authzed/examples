package main

import (
	"context"
	"fmt"
	"log"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/authzed/spicedb/pkg/cmd/datastore"
	"github.com/authzed/spicedb/pkg/cmd/server"
	"github.com/authzed/spicedb/pkg/cmd/util"
	"golang.org/x/sync/errgroup"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	server, err := newSpiceDBServer(ctx)
	if err != nil {
		log.Fatal("unable to configure server: ", err)
	}

	var wg errgroup.Group
	wg.Go(func() error {
		if err := server.Run(ctx); err != nil {
			log.Print("error while running server: ", err)
			return err
		}
		return nil
	})

	conn, err := server.GRPCDialContext(ctx)
	if err != nil || conn == nil {
		log.Fatal("unable to get gRPC connection: ", err)
	}

	schemaSrv := v1.NewSchemaServiceClient(conn)
	permSrv := v1.NewPermissionsServiceClient(conn)

	_, err = schemaSrv.WriteSchema(ctx, &v1.WriteSchemaRequest{
		Schema: `definition user {}
                 definition resource {
                   relation viewer: user
                   permission view = viewer
                 }`,
	})
	if err != nil {
		log.Fatal("unable to write schema: ", err)
	}

	resp, err := permSrv.WriteRelationships(ctx, &v1.WriteRelationshipsRequest{Updates: []*v1.RelationshipUpdate{
		{
			Operation: v1.RelationshipUpdate_OPERATION_CREATE,
			Relationship: &v1.Relationship{
				Resource: &v1.ObjectReference{
					ObjectId:   "my_book",
					ObjectType: "resource",
				},
				Relation: "viewer",
				Subject: &v1.SubjectReference{
					Object: &v1.ObjectReference{
						ObjectId:   "john_doe",
						ObjectType: "user",
					},
				},
			},
		},
	}})
	if err != nil {
		log.Fatal("unable to write relationships: ", err)
	}

	token := resp.GetWrittenAt()
	checkResp, err := permSrv.CheckPermission(ctx, &v1.CheckPermissionRequest{
		Permission:  "view",
		Consistency: &v1.Consistency{Requirement: &v1.Consistency_AtLeastAsFresh{AtLeastAsFresh: token}},
		Resource: &v1.ObjectReference{
			ObjectId:   "my_book",
			ObjectType: "resource",
		},
		Subject: &v1.SubjectReference{
			Object: &v1.ObjectReference{
				ObjectId:   "john_doe",
				ObjectType: "user",
			},
		},
	})
	if err != nil {
		log.Fatal("unable to issue PermissionCheck: ", err)
	}

	log.Printf("check result: %s", checkResp.Permissionship.String())
	cancel()
	wg.Wait()
}

func newSpiceDBServer(ctx context.Context) (server.RunnableServer, error) {
	ds, err := datastore.NewDatastore(ctx,
		datastore.DefaultDatastoreConfig().ToOption(),
		datastore.WithRequestHedgingEnabled(false),
	)
	if err != nil {
		return nil, fmt.Errorf("unable to start memdb datastore: %s", err)
	}

	configOpts := []server.ConfigOption{
		server.WithGRPCServer(util.GRPCServerConfig{
			Network: util.BufferedNetwork,
			Enabled: true,
		}),
		server.WithGRPCAuthFunc(func(ctx context.Context) (context.Context, error) {
			return ctx, nil
		}),
		server.WithHTTPGateway(util.HTTPServerConfig{HTTPEnabled: false}),
		server.WithMetricsAPI(util.HTTPServerConfig{HTTPEnabled: false}),
		// disable caching since it's all in memory
		server.WithDispatchCacheConfig(server.CacheConfig{Enabled: false, Metrics: false}),
		server.WithNamespaceCacheConfig(server.CacheConfig{Enabled: false, Metrics: false}),
		server.WithClusterDispatchCacheConfig(server.CacheConfig{Enabled: false, Metrics: false}),
		server.WithDatastore(ds),
	}

	return server.NewConfigWithOptionsAndDefaults(configOpts...).Complete(ctx)
}
