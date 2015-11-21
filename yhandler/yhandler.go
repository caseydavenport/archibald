package yhandler

import (
	"bufio"
	"bytes"
	"fmt"
	"github.com/BurntSushi/toml"
	"github.com/dghubble/oauth1"
	"github.com/kardianos/osext"
	"io/ioutil"
	"os"
	"path/filepath"
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
	ConfigFile string
	Config     TomlConfig
}

func (y *YahooHandler) LoadSecrets() {
	// Attempt to load from file first.
	dir, err := osext.ExecutableFolder()
	if err != nil {
		fmt.Printf("Failed to get running dir: %s\n", err)
	}

	y.ConfigFile = filepath.Join(dir, "config.toml")
	var tomlConfig TomlConfig
	fmt.Printf("Attempt to load config file: %s\n", y.ConfigFile)

	_, err = toml.DecodeFile(y.ConfigFile, &tomlConfig)
	if err != nil {
		fmt.Printf("Failed to load secrets: %s\n", err)
		os.Exit(1)
	}
	y.Config = tomlConfig
	fmt.Printf("Loaded config: %s\n", tomlConfig)

	if y.Config.Secrets.AccessToken == "" {
		fmt.Printf("No config present - generating. \n")
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
		os.Exit(1)
	}
	fmt.Printf(buf.String())
	err = ioutil.WriteFile(y.ConfigFile, buf.Bytes(), 0644)
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

	if y.Config.ConsumerInfo.ConsumerSecret == "" {
		fmt.Printf("Missing ConsumerSecret")
		os.Exit(1)
	}
	if y.Config.ConsumerInfo.ConsumerKey == "" {
		fmt.Printf("Missing ConsumerKey")
		os.Exit(1)
	}
	if y.Config.Secrets.AccessSecret == "" {
		fmt.Printf("Missing AccessSecret")
		os.Exit(1)
	}
	if y.Config.ConsumerInfo.AccessKey == "" {
		fmt.Printf("Missing AccessKey")
		os.Exit(1)
	}

	config := oauth1.NewConfig(y.Config.ConsumerInfo.ConsumerKey, y.Config.ConsumerInfo.ConsumerSecret)
	token := oauth1.NewToken(y.Config.Secrets.AccessToken, y.Config.Secrets.AccessSecret)
	httpClient := config.Client(oauth1.NoContext, token)

	// Request from the API.
	base := "https://fantasysports.yahooapis.com/fantasy/v2/"
	url := fmt.Sprint(base, path)
	fmt.Printf("GET url: %s\n", url)
	resp, err := httpClient.Get(url)
	if err != nil {
		fmt.Printf("Error: %s", err)
		os.Exit(1)
	}

	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Error: %s", err)
		os.Exit(1)
	}

	fmt.Printf("Raw response: \n%v\n", string(body))
}

func (y YahooHandler) GenerateSecrets() Secrets {
	fmt.Printf("Authenticating\n")

	// Requires that ConsumerInfo has been setup.
	config := &oauth1.Config{
		ConsumerKey:    y.Config.ConsumerInfo.ConsumerKey,
		ConsumerSecret: y.Config.ConsumerInfo.ConsumerSecret,
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
		os.Exit(1)
	}
	fmt.Printf("Got request token/secret: %s/%s\n", requestToken, requestSecret)

	// Get auth URL.
	authURL, err := config.AuthorizationURL(requestToken)
	if err != nil {
		fmt.Printf("Error getting authorization URL: %s\n", err)
		os.Exit(1)
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
		os.Exit(1)
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
