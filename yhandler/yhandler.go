package yhandler

import (
  "fmt"
  "github.com/dghubble/oauth1"
  "bufio"
  "os"
  "strings"
  "io/ioutil"
)

// Declare global constants
const authUrl string = "https://api.login.yahoo.com/oauth/v2/request_auth"
const getTokenUrl string = "https://api.login.yahoo.com/oauth/v2/get_token"
const getReqTokenUrl string = "https://api.login.yahoo.com/oauth/v2/get_request_token"

// TODO - Move this into config file.
const consumerKey string = ""
const consumerSecret string = ""

type YahooHandler struct { 
  Secrets Secrets
}

func (y *YahooHandler) LoadSecrets() {
  y.Secrets = y.GenerateSecrets()
}

func (y YahooHandler) Get (path string) {
  // Check if we've loaded secrets - if not, load them.
  if (y.Secrets.AccessToken == "") {
    y.LoadSecrets()
  }

  config := oauth1.NewConfig(consumerKey, consumerSecret)
  token := oauth1.NewToken(y.Secrets.AccessToken, y.Secrets.AccessSecret)
  httpClient := config.Client(oauth1.NoContext, token)

  // Request from the API.
  base := "http://fantasysports.yahooapis.com/fantasy/v2/"
  url := fmt.Sprint(base, path)
  fmt.Printf("GET url: %s", url)
  resp, err := httpClient.Get(url)
  if (err != nil) {
    fmt.Printf("Error: %s", err)
  }

  defer resp.Body.Close()
  body, err := ioutil.ReadAll(resp.Body)
  if (err != nil) {
    fmt.Printf("Error: %s", err)
  }

  fmt.Printf("Raw response: \n%v\n", string(body))
}

func (y YahooHandler) GenerateSecrets () Secrets {
  fmt.Printf("Authenticating\n")

  config := &oauth1.Config{
    ConsumerKey: consumerKey,
    ConsumerSecret: consumerSecret,
    CallbackURL: "oob",
    Endpoint: oauth1.Endpoint{
      RequestTokenURL: getReqTokenUrl,
      AuthorizeURL: authUrl,
      AccessTokenURL: getTokenUrl,
    },
  }

  // Get token / secret.
  requestToken, requestSecret, err := config.RequestToken()
  if (err != nil) {
    fmt.Printf("Error getting requestToken: %s\n", err)
    return Secrets{}
  }
  fmt.Printf("Got request token/secret: %s/%s\n", requestToken, requestSecret)

  // Get auth URL.
  authURL, err := config.AuthorizationURL(requestToken)
  if (err != nil) {
    fmt.Printf("Error getting authorization URL: %s\n", err)
    return Secrets{} 
  }
  fmt.Printf("Auth URL: %s\n", authURL) 

  reader := bufio.NewReader(os.Stdin)
  fmt.Printf("Enter token: ")
  verifier, _ := reader.ReadString('\n')
  fmt.Printf("Read verifier: %s\n", verifier)

  // Trim the verifier
  verifier = strings.Trim(verifier, "\n")

  accessToken, accessSecret, err := config.AccessToken(requestToken, requestSecret, verifier)
  if (err != nil) {
    fmt.Printf("Error getting access token/secret: %s\n", err)
    return Secrets{} 
  }

  // Create a secrets struct to hold all the token stuff.
  secrets := Secrets{
    RequestToken: requestToken,
    RequestSecret: requestSecret,
    Verifier: verifier,
    AccessToken: accessToken,
    AccessSecret: accessSecret,
  }

  // Return
  return secrets
}

type Secrets struct {
  RequestToken string
  RequestSecret string
  Verifier string
  AccessToken string
  AccessSecret string
}
