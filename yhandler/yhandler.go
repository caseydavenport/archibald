package yhandler

import (
	"bufio"
	"bytes"
	"fmt"
	"github.com/BurntSushi/toml"
	"github.com/dghubble/oauth1"
	"io/ioutil"
	"os"
	"strings"
)

// Declare global constants
const authUrl string = "https://api.login.yahoo.com/oauth/v2/request_auth"
const getTokenUrl string = "https://api.login.yahoo.com/oauth/v2/get_token"
const getReqTokenUrl string = "https://api.login.yahoo.com/oauth/v2/get_request_token"

// TODO - Move this into config file.
const consumerKey string = ""
const consumerSecret string = ""

type YahooHandler struct {
	Config TomlConfig
}

func (y *YahooHandler) LoadSecrets() {
	// Attempt to load from file first.
	fmt.Printf("Attempt to load config file\n")
	var configFile = "config.toml"
	var tomlConfig TomlConfig

	_, err := toml.DecodeFile(configFile, &tomlConfig)
	if err != nil {
		fmt.Printf("Failed to load secrets: %s\n", err)
		return
	}
	y.Config = tomlConfig
	fmt.Printf("Loaded config: %s\n", tomlConfig)

	if y.Config.Secrets.AccessToken == "" {
		fmt.Printf("Unable to load config - authenticating. \n")
		y.Config.Secrets = y.GenerateSecrets()
		y.SaveSecrets()
	}
}

func (y *YahooHandler) SaveSecrets() {
	fmt.Printf("Writing config to disk: \n")
	buf := new(bytes.Buffer)
	err := toml.NewEncoder(buf).Encode(y.Config)
	if err != nil {
		fmt.Printf("Error: %s\n", err)
		return
	}
	fmt.Printf(buf.String())
	err = ioutil.WriteFile("config.toml", buf.Bytes(), 0644)
	if err != nil {
		fmt.Print("Error writing config: %s", err)
	}
	fmt.Printf("Finished writing config to disk\n")
}

func (y YahooHandler) Get(path string) {
	// Check if we've loaded secrets - if not, load them.
	if y.Config.Secrets.AccessToken == "" {
		y.LoadSecrets()
	}

	config := oauth1.NewConfig(consumerKey, consumerSecret)
	token := oauth1.NewToken(y.Config.Secrets.AccessToken, y.Config.Secrets.AccessSecret)
	httpClient := config.Client(oauth1.NoContext, token)

	// Request from the API.
	base := "http://fantasysports.yahooapis.com/fantasy/v2/"
	url := fmt.Sprint(base, path)
	fmt.Printf("GET url: %s", url)
	resp, err := httpClient.Get(url)
	if err != nil {
		fmt.Printf("Error: %s", err)
		return
	}

	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Error: %s", err)
		return
	}

	fmt.Printf("Raw response: \n%v\n", string(body))
}

func (y YahooHandler) GenerateSecrets() Secrets {
	fmt.Printf("Authenticating\n")

	config := &oauth1.Config{
		ConsumerKey:    consumerKey,
		ConsumerSecret: consumerSecret,
		CallbackURL:    "oob",
		Endpoint: oauth1.Endpoint{
			RequestTokenURL: getReqTokenUrl,
			AuthorizeURL:    authUrl,
			AccessTokenURL:  getTokenUrl,
		},
	}

	// Get token / secret.
	requestToken, requestSecret, err := config.RequestToken()
	if err != nil {
		fmt.Printf("Error getting requestToken: %s\n", err)
		return Secrets{}
	}
	fmt.Printf("Got request token/secret: %s/%s\n", requestToken, requestSecret)

	// Get auth URL.
	authURL, err := config.AuthorizationURL(requestToken)
	if err != nil {
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
	if err != nil {
		fmt.Printf("Error getting access token/secret: %s\n", err)
		return Secrets{}
	}

	// Create a secrets struct to hold all the token stuff.
	secrets := Secrets{
		RequestToken:  requestToken,
		RequestSecret: requestSecret,
		Verifier:      verifier,
		AccessToken:   accessToken,
		AccessSecret:  accessSecret,
	}

	// Return
	return secrets
}

type TomlConfig struct {
	ConsumerInfo ConsumerInfo
	Secrets      Secrets
}

type ConsumerInfo struct {
	ConsumerSecret string `toml:"ConsumerSecret"`
	ConsumerKey    string `toml:"ConsumerKey"`
}

type Secrets struct {
	RequestToken  string
	RequestSecret string
	Verifier      string
	AccessToken   string
	AccessSecret  string
}
