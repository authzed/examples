package data

import (
	"context"
	"fmt"
	"log"

	v0 "github.com/authzed/authzed-go/proto/authzed/api/materialize/v0"
	"github.com/fatih/color"
	"github.com/kataras/golog"
	"google.golang.org/protobuf/encoding/prototext"
)

func Write(change *v0.PermissionSetChange) {

	switch oneOf := change.GetChild().(type) {
	//s2s
	case *v0.PermissionSetChange_ChildSet:
		s2s(change, oneOf)
		color.Blue(prototext.Format(change))
		fmt.Println("------------------------------------------------")
	//m2s
	case *v0.PermissionSetChange_ChildMember:
		m2s(change, oneOf)
		color.Green(prototext.Format(change))
		fmt.Println("------------------------------------------------")
	default:
		log.Fatalf("Unknown child type")
	}

}

func s2s(change *v0.PermissionSetChange, childSet *v0.PermissionSetChange_ChildSet) {
	//see comment above
	conn := connInit("sets")
	defer conn.Close(context.Background())

	query := `INSERT INTO set_to_set (child_type, child_id, child_relation, parent_type, parent_id, parent_relation)
		VALUES ($1, $2, $3, $4, $5, $6)`
	_, err := conn.Exec(context.Background(), query,
		childSet.ChildSet.ObjectType,
		childSet.ChildSet.ObjectId,
		childSet.ChildSet.PermissionOrRelation,
		change.ParentSet.ObjectType,
		change.ParentSet.ObjectId,
		change.ParentSet.PermissionOrRelation)
	if err != nil {
		golog.Errorf("unable to insert %v into set_to_set table: %v", change, err)
	}

}

func m2s(change *v0.PermissionSetChange, childMember *v0.PermissionSetChange_ChildMember) {
	//I wonder if this is the most effecient way to init the conn
	conn := connInit("sets")
	defer conn.Close(context.Background())

	query := `INSERT INTO member_to_set (member_type, member_id, member_relation, set_type, set_id, set_relation)
		VALUES ($1, $2, $3, $4, $5, $6)`
	_, err := conn.Exec(context.Background(), query,
		childMember.ChildMember.ObjectType,
		childMember.ChildMember.ObjectId,
		childMember.ChildMember.OptionalPermissionOrRelation,
		change.ParentSet.ObjectType,
		change.ParentSet.ObjectId,
		change.ParentSet.PermissionOrRelation)
	if err != nil {
		golog.Errorf("unable to insert %v into member_to_set table: %v", change, err)
	}

}
