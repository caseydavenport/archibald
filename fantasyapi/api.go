package fantasyapi

import (
  "fmt"
  "encoding/json"
  "archibald/yhandler"
)

type FantasyApi struct {
  Handler 	yhandler.YahooHandler	
  LeagueKey	string
  GameKey	string
  StatCategories string
}

func Unmarshall(j []byte) (map[string]interface{}){
  var i interface{}
  err := json.Unmarshal(j, &i)
  if (err != nil) {
    fmt.Printf("ERROR parsing %s: %s", j, err)
  }
  fmt.Printf("Parsed JSON :%s\n", i)
  return i.(map[string]interface{})
}

func (f FantasyApi) Get(path string) ([]byte){
  fmt.Printf("Getting API resource: %s\n", path)
  f.Handler.Get(path)
  return []byte(`{"Name": "Platypus"}`)
}

func (f FantasyApi) LeagueSettings() (Settings) {
  url := fmt.Sprintf("league/%s/settings?format=json", 
                     f.LeagueKey)
  resp := f.Get(url)
  settings := CreateSettings(resp)
  return settings
}

type Player struct {
} 

func CreateSettings(j []byte) (Settings) {
  s := Unmarshall(j)
  fmt.Printf("Found: Name=%s\n", s["Name"])
  return Settings{}
}

type Settings struct {
}
