from fantasyapi import *
from utils import *
from archie import Archibald
import datetime


# Values for test league
team_no = 4
league_no = 697783

# Generate keys for the desired leage / team
team_key = "348.l.%s.t.%s" % (league_no, team_no) 
league_id = "348.l.%s" % league_no

api = FantasyApi(league_id) 

thing = raw_input("Get new token?: ")
if thing == "true":
  api.handler.reg_user()
else:
  api.handler.refresh_token()

try:

	print "\n%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
       
	# Get my team
	print "Getting team"
	myteam = api.get_team(team_key)
	print "Getting empty positions"
	empty = myteam.empty_positions()
	print "Getting benched players"
	benched = myteam.benched_players()
	print "Getting all players"
	players = myteam.players
	p = players[0]

	arch = Archibald(api, league_id, team_key)

except AuthException, e:
	print "Hit API error: %s" % e
	print "Status code: %s" % e.status
