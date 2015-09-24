import math

# The current season year
CURRENT_SEASON = 2015

# Game key - set to NFL 2015
GAME_KEY=348

# Positions, and the nubmer of each per-team.
# TODO: Get this from league settings.
POSITIONS = {
	'RB':  1, 
	'W/R/T': 1,
	'WR':  2, 
	'DEF': 1,
	'BN':  1, 
	'QB':  1, 
	'TE':  1,
	'K,': 1,
	'BN': 5,
}

# Possible player status fields
INJURED = "IR" 
DISABLED = "DL"
NOT_ACTIVE = "NA"
PROBABLE = "P"
QUESTIONABLE = "Q"
OUT = "O"
OK = "OK"
BAD_STATUSES = [INJURED, DISABLED, NOT_ACTIVE, OUT]

# Player states 
ALL = "A"
FREE_AGENT = "FA"
WAIVER = "W"
TAKEN = "T"
KEEPERS = "K"

# XML to add a player.
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

# XML to drop a player.
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

# XML to simultaneously add/drop players.
ADD_DROP_XML = """<?xml version='1.0'?>
<fantasy_content>  
  <transaction>  
    <type>add/drop</type>  
    <players>  
      <player>  
        <player_key>%s</player_key>  
        <transaction_data>  
          <type>add</type>  
          <destination_team_key>%s</destination_team_key>  
        </transaction_data>  
      </player>  
      <player>  
        <player_key>%s</player_key>  
        <transaction_data>  
          <type>drop</type>  
          <source_team_key>%s</source_team_key>  
        </transaction_data>  
      </player>  
    </players>  
  </transaction>  
</fantasy_content>
"""

# Template for modifying roster - needs one or more PLAYER_POS_XMLs within.
ROSTER_XML = """<?xml version="1.0"?>  
<fantasy_content>  
  <roster>  
    <coverage_type>week</coverage_type>  
    <week>%s</week>  
    <players>  

       %s

    </players>  
  </roster>  
</fantasy_content> 
"""

# XML for making a roster change.  One or more can be included in
# a ROSTER_XML block.
PLAYER_POS_XML = """
<player>
  <player_key>%s</player_key>
  <position>%s</position>
</player>
"""

# XML to propose a trade.
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
