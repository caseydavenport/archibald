GET_TOKEN_URL = 'https://api.login.yahoo.com/oauth/v2/get_token'
AUTHORIZATION_URL = 'https://api.login.yahoo.com/oauth/v2/request_auth'
REQUEST_TOKEN_URL = 'https://api.login.yahoo.com/oauth/v2/get_request_token'
CALLBACK_URL = 'oob'
BASE_URL="https://query.yahooapis.com/v1/public/"

GAME_KEY=348
LEAGUE_NO=697783

POSITIONS = ['RB', 'WR', 'DEF', 'RB', 'DEF', 'RB', 'QB', 'QB', 'TE', 'K,' 'TE', 'WR', 'WR', 'RB', 'WR']

# Generate the league ID
LEAGUE_ID="%s.l.%s" % (GAME_KEY, LEAGUE_NO)

# Query strings
TEAMS_QUERY="leagues;league_keys=%s/teams?format=json" % LEAGUE_ID
PLAYERS_QUERY = "league/%s/players?format=json" % LEAGUE_ID 
TEAM_PLAYERS_QUERY = "team/%s/players?format=json"   # %s = team_key
XACTION_URL = "league/%s/transactions" % LEAGUE_ID

# Add
ADD_PLAYER_XML = """<?xml version='1.0'?>  
<fantasy_content>  
  <transaction>  
    <type>add</type>  
    <player>  
      <player_key>%s</player_key>  
      <transaction_data>  
        <type>add</type>  
        <destination_team_key>%s</destination_team_key>  
      </transaction_data>  
    </player>  
  </transaction>  
</fantasy_content>
"""

DEL_PLAYER_XML = """<?xml version='1.0'?>  
<fantasy_content>  
  <transaction>  
    <type>drop</type>  
    <player>  
      <player_key>%s</player_key>  
      <transaction_data>  
        <type>drop</type>  
        <source_team_key>%s</source_team_key>  
      </transaction_data>  
    </player>  
  </transaction>  
</fantasy_content>
"""

TRADE_XML = """
<?xml version='1.0'?>  
<fantasy_content>  
  <transaction>  
    <type>pending_trade</type>  
    <trader_team_key>248.l.55438.t.11</trader_team_key>  
    <tradee_team_key>248.l.55438.t.4</tradee_team_key>  
    <trade_note>Yo yo yo yo yo!!!</trade_note>  
    <players>  
      <player>  
        <player_key>248.p.4130</player_key>  
        <transaction_data>  
          <type>pending_trade</type>  
          <source_team_key>248.l.55438.t.11</source_team_key>  
          <destination_team_key>248.l.55438.t.4</destination_team_key>  
        </transaction_data>  
      </player>  
      <player>  
        <player_key>248.p.2415</player_key>  
        <transaction_data>  
          <type>pending_trade</type>  
          <source_team_key>248.l.55438.t.4</source_team_key>  
          <destination_team_key>248.l.55438.t.11</destination_team_key>  
        </transaction_data>  
      </player>  
    </players>  
  </transaction>  
</fantasy_content>  
"""
