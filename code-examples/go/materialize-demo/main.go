package main

import (
	"bufio"
	"fmt"
	"materialize/internal/data"
	"materialize/internal/spice"
	"materialize/internal/tiger"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/kataras/golog"
)

func init() {
}

func main() {
	defer fmt.Println("Goodbye!")

	fmt.Println("Welcome to the WatchPermissionSets demonstration!")
	fmt.Println("\nHere is the schema for todays demo:\n")
	err := spice.ReadSchema()
	if err != nil {
		golog.Errorf("unable to read schema: %v", err)
		return
	}
	fmt.Println("")
	fmt.Println("Also, the Permission System has been seeded with some initial relationship data.")
	halt()
	//spins up embedded in-memory postgres DB
	//"db" is needed to stop at the end of the program
	db, err := data.DbStart()
	if err != nil {
		golog.Errorf("unable to start embedded postgres: %v", err)
		golog.Info("assuming postgres already running (embedded or standalone), continuing...")
	}
	//cleans up embedded in-memory postgres DB
	defer func() {
		err := data.DbStop(db)
		if err != nil {
			golog.Errorf("unable to stop embedded postgres: %v", err)
			return
		}
	}()

	err = data.PrepareDatabase()
	if err != nil {
		golog.Errorf("unable to prepare database: %v", err)
		return
	}
	maxRetries := 2
	for i := 0; i <= maxRetries; i++ {
		halt()
		err = tiger.Lps()
		if err != nil {
			golog.Errorf("unable to hydrate permission sets: %v", err)
		}
		if err == nil {
			break
		}
		if i == maxRetries {
			golog.Errorf("unable to hydrate permission sets after %d retries: %v", maxRetries, err)
			return
		}
	}

	halt()
	err = data.PrintTableContents()
	if err != nil {
		golog.Errorf("unable to print table contents: %v", err)
		return
	}
	halt()
	err = data.FindDocumentsUserCanView("tim")
	if err != nil {
		golog.Errorf("unable to find documents user can view: %v", err)
		return
	}
	halt()

	var wg sync.WaitGroup

	wg.Add(1)

	go func() {
		defer wg.Done()
		tiger.Wps()
	}()

	time.Sleep(2 * time.Second)

	err = spice.WriteRelationship()
	if err != nil {
		if strings.Contains(err.Error(), "AlreadyExists") {
			err = spice.DeleteRelationship()
			if err != nil {
				golog.Errorf("unable to delete relationship: %v", err)
				return
			}
			err = spice.WriteRelationship()
			if err != nil {
				golog.Errorf("unable to write relationship, after deleting it: %v", err)
				return
			}
		} else {
			golog.Errorf("unable to write relationship: %v", err)
			return
		}
	}

	defer func() {
		err = spice.DeleteRelationship()
		if err != nil {
			golog.Errorf("unable to delete relationship: %v", err)
			return
		}
	}()

	halt()
	err = data.FindDocumentsUserCanView("tim")
	if err != nil {
		golog.Errorf("unable to find documents user can view: %v", err)
		return
	}

}

func halt() {
	fmt.Print("Press 'Enter' to continue...\n")
	bufio.NewReader(os.Stdin).ReadBytes('\n')
}
