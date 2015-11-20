package main 

import (
  "fmt"
  "time"
  "archibald/fantasyapi"
)

type Archibald struct {
  TeamKey	string
  LeagueKey	string
  Api	    	fantasyapi.FantasyApi	
}

func (a Archibald) Start(){
  fmt.Printf("Starting Archibald: %s\n", a)

  a.Api.LeagueSettings()

  a.Sleep(0,0,1)
}

func (a Archibald) Sleep(d int, h int, s int){
  sec := d * 24 * 60 * 60
  sec = sec + (h * 60 * 60)
  sec = sec + s
  fmt.Printf("Sleeping for %d:%d:%d\n", d, h, s)

  // Cast to Duration (nanoseconds)
  sleepTime := time.Duration(sec * 1000 * 1000 * 1000)
  time.Sleep(sleepTime)
}

func main() {
  // Create a new Archibald instance.
  var teamKey = "348.l.597247.t.10"
  var leagueKey = "348.l.597247"
  var gameKey = "348"
  var api = fantasyapi.FantasyApi{
    LeagueKey: leagueKey,
    GameKey: gameKey, 
    StatCategories: "",
  }
  var archie = Archibald{TeamKey: teamKey,
                         LeagueKey: leagueKey,
                         Api: api}
  fmt.Printf("Created Archie: %s\n", archie)

  // Start Archibald.
  archie.Start()
}
