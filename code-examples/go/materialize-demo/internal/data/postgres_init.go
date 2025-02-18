package data

import (
	"fmt"
	"log"

	"github.com/fatih/color"
	embeddedpostgres "github.com/fergusstrange/embedded-postgres"
	"github.com/kataras/golog"

	"context"
	"io"

	"github.com/jackc/pgx/v5"

	"strings"
)

func DbStart() (*embeddedpostgres.EmbeddedPostgres, error) {
	golog.Info("Starting embedded postgres")

	// Redirect the embedded postgres logs to ioutil.Discard to suppress them
	postgres := embeddedpostgres.NewDatabase(embeddedpostgres.DefaultConfig().
		Logger(io.Discard))
	err := postgres.Start()
	if err != nil {
		return postgres, err
	}

	golog.Info("Started embedded postgres")

	return postgres, nil
}

// to do: stop the db in the event of a fatalf
func DbStop(postgres *embeddedpostgres.EmbeddedPostgres) error {
	golog.Info("Stopping embedded postgres")
	err := postgres.Stop()
	if err != nil {
		return err
	}
	golog.Info("Stopped embedded postgres")

	return nil
}

// connInit lets you specify the logical database you want to connect to
func connInit(db string) *pgx.Conn {
	conn, err := pgx.Connect(context.Background(), "postgres://postgres:postgres@localhost:5432/"+db)
	if err != nil {
		log.Fatalf("unable to connect to database: %v", err)
	}

	return conn
}

func createDatabase() error {

	golog.Info("Creating logical database called 'sets'")

	conn := connInit("postgres")
	defer conn.Close(context.Background())

	// Create the database if it doesn't exist
	_, err := conn.Exec(context.Background(), "CREATE DATABASE sets")

	if err != nil {
		if strings.Contains(err.Error(), "SQLSTATE 42P04") {
			golog.Info("Database called 'sets' already exists.  Continuing...")
			return nil
		}
		return err
	}

	return nil
}

func truncateTable(tableName string) error {
	conn := connInit("sets")
	defer conn.Close(context.Background())

	_, err := conn.Exec(context.Background(), "TRUNCATE TABLE "+tableName+";")
	if err != nil {
		golog.Error(err)
		return err
	}

	return nil
}

func createTables() error {
	conn := connInit("sets")
	defer conn.Close(context.Background())

	m2sTable := `CREATE TABLE member_to_set (
		member_type varchar(100),
		member_id varchar(100),
		member_relation varchar(100),
		set_type varchar(100),
		set_id varchar(100),
		set_relation varchar(100)
	);`
	_, err := conn.Exec(context.Background(), m2sTable)

	if err != nil {
		if strings.Contains(err.Error(), "SQLSTATE 42P07") {
			truncateTable("member_to_set")
			golog.Info("Table member_to_set already exists.  Table truncated and continuing...")
		} else {
			return err
		}
	} else {
		color.Set(color.FgGreen)
		fmt.Printf("Created member_to_set table: %v\n", m2sTable)
		color.Unset()
	}

	s2sTable := `CREATE TABLE set_to_set (
		child_type varchar(100),
		child_id varchar(100),
		child_relation varchar(100),
		parent_type varchar(100),
		parent_id varchar(100),
		parent_relation varchar(100)
	);`
	_, err = conn.Exec(context.Background(), s2sTable)
	if err != nil {
		if strings.Contains(err.Error(), "SQLSTATE 42P07") {
			truncateTable("set_to_set")
			golog.Info("Table set_to_set already exists.  Table truncated and continuing...")
			return nil
		}
		return err
	} else {
		color.Set(color.FgBlue)
		fmt.Printf("Created set_to_set table: %v\n", s2sTable)
		color.Unset()
	}
	return nil
}

func PrepareDatabase() error {
	err := createDatabase()
	if err != nil {
		return err
	}
	err = createTables()
	if err != nil {
		return err
	}

	return nil
}
