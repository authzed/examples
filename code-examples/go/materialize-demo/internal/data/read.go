package data

import (
	"context"
	"fmt"
	"log"
	"os"

	"text/tabwriter"

	"github.com/fatih/color"
	"github.com/kataras/golog"
)

// PrintTableContents prints the contents of the member_to_set and set_to_set tables
func PrintTableContents() error {
	golog.Info("Printing table contents")

	err := printMemberToSet()
	if err != nil {
		return err
	}
	err = printSetToSet()
	if err != nil {
		return err
	}

	return nil
}

// printMemberToSet prints the contents of the member_to_set table
func printMemberToSet() error {
	conn := connInit("sets")
	defer conn.Close(context.Background())

	rows, err := conn.Query(context.Background(), "SELECT member_type, member_id, member_relation, set_type, set_id, set_relation FROM member_to_set")
	if err != nil {
		return err
	}
	defer rows.Close()

	fmt.Println("\nContents of member_to_set:")
	w := tabwriter.NewWriter(os.Stdout, 15, 0, 1, ' ', tabwriter.AlignRight|tabwriter.Debug)
	fmt.Fprintln(w, "MemberType\tMemberID\tMemberRelation\tSetType\tSetID\tSetRelation\t")

	color.Set(color.FgGreen)

	for rows.Next() {
		var memberType, memberId, memberRelation, setType, setId, setRelation string
		err := rows.Scan(&memberType, &memberId, &memberRelation, &setType, &setId, &setRelation)
		if err != nil {
			log.Fatalf("unable to scan member_to_set row: %v", err)
		}
		fmt.Fprint(w, memberType+"\t")
		fmt.Fprint(w, memberId+"\t")
		fmt.Fprint(w, memberRelation+"\t")
		fmt.Fprint(w, setType+"\t")
		fmt.Fprint(w, setId+"\t")
		fmt.Fprintln(w, setRelation+"\t")
	}
	w.Flush()

	color.Unset()
	return nil
}

// printSetToSet prints the contents of the set_to_set table
func printSetToSet() error {
	conn := connInit("sets")
	defer conn.Close(context.Background())

	rows, err := conn.Query(context.Background(), "SELECT child_type, child_id, child_relation, parent_type, parent_id, parent_relation FROM set_to_set")
	if err != nil {
		return err
	}
	defer rows.Close()

	fmt.Println("\nContents of set_to_set:")
	color.Set(color.FgBlue)
	w := tabwriter.NewWriter(os.Stdout, 15, 0, 1, ' ', tabwriter.AlignRight|tabwriter.Debug)
	fmt.Fprintln(w, "ChildType\tChildID\tChildRelation\tParentType\tParentID\tParentRelation\t")

	for rows.Next() {
		var childType, childId, childRelation, parentType, parentId, parentRelation string
		err := rows.Scan(&childType, &childId, &childRelation, &parentType, &parentId, &parentRelation)
		if err != nil {
			log.Fatalf("unable to scan set_to_set row: %v", err)
		}
		fmt.Fprint(w, childType+"\t")
		fmt.Fprint(w, childId+"\t")
		fmt.Fprint(w, childRelation+"\t")
		fmt.Fprint(w, parentType+"\t")
		fmt.Fprint(w, parentId+"\t")
		fmt.Fprintln(w, parentRelation+"\t")
	}
	w.Flush()
	color.Unset()
	return nil
}

func FindDocumentsUserCanView(userID string) error {
	conn := connInit("sets")
	defer conn.Close(context.Background())

	query := `
		SELECT DISTINCT 
			s2s.parent_id AS document_id
		FROM 
			member_to_set mts
		JOIN 
			set_to_set s2s 
		ON 
			mts.set_type = s2s.child_type 
			AND mts.set_id = s2s.child_id 
		WHERE 
			mts.member_type = 'user'
			AND mts.member_id = $1;
	`
	color.Set(color.FgYellow)
	fmt.Printf("Performing query to find documents user can view: %s\n", query)
	color.Unset()

	rows, err := conn.Query(context.Background(), query, userID)
	if err != nil {
		return err
	}
	defer rows.Close()

	fmt.Printf("Documents that user %s can view:\n", userID)
	color.Set(color.FgRed)
	for rows.Next() {
		var documentID string
		err := rows.Scan(&documentID)
		if err != nil {
			return err
		}
		fmt.Printf("%s\n",
			documentID)
	}
	color.Unset()

	return nil
}
