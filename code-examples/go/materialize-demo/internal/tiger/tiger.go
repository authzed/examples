package tiger

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log"
	"materialize/internal/data"

	v0 "github.com/authzed/authzed-go/proto/authzed/api/materialize/v0"
	"github.com/authzed/grpcutil"
	"github.com/kataras/golog"
	"google.golang.org/grpc"
)

func clientInit() *grpc.ClientConn {
	systemCerts, err := grpcutil.WithSystemCerts(grpcutil.SkipVerifyCA)
	if err != nil {
		log.Fatalf("unable to load system CA certificates: %s", err)
	}

	// Correct the gRPC connection initialization
	tigerConn, err := grpc.NewClient(
		"localhost:50054",
		systemCerts,
		grpcutil.WithBearerToken(""),
	)
	if err != nil {
		log.Fatalf("failed to connect to gRPC server: %v", err)
	}

	return tigerConn
}

func Lps() error {
	tigerConn := clientInit()

	defer tigerConn.Close()

	tigerClient := v0.NewWatchPermissionSetsServiceClient(tigerConn)

	//to do: implement a loop here
	stream, err := tigerClient.LookupPermissionSets(context.Background(), &v0.LookupPermissionSetsRequest{
		Limit: uint32(500),
	})
	if err != nil {
		return err
	}

	resp, err := stream.Recv()
	if err != nil {
		return err
	}

	golog.Info("Streaming initial hydration of permission sets from LookupPermissionSets API")

	data.Write(resp.Change)

	for {
		resp, err = stream.Recv()
		if errors.Is(err, io.EOF) {
			break
		}

		data.Write(resp.Change)
	}

	return nil
}

func Wps() error {

	tigerConn := clientInit()

	defer tigerConn.Close()

	tigerClient := v0.NewWatchPermissionSetsServiceClient(tigerConn)

	golog.Info("Streaming updates from WatchPermissionSets API...")

	stream, err := tigerClient.WatchPermissionSets(context.Background(), &v0.WatchPermissionSetsRequest{ /*zed token could go here*/ })
	if err != nil {
		return err
	}

	for {
		resp, err := stream.Recv()
		if errors.Is(err, io.EOF) {
			break
		}
		switch response := resp.Response.(type) {
		case *v0.WatchPermissionSetsResponse_Change:
			data.Write(response.Change)
		case *v0.WatchPermissionSetsResponse_CompletedRevision:
			//todo: fix this jankiness
			fmt.Println("")
		case *v0.WatchPermissionSetsResponse_LookupPermissionSetsRequired:
			fmt.Println("")
		default:
			fmt.Println("Unknown response type")
		}

	}
	return nil
}
