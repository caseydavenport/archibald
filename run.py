from fantasyapi import *
from utils import *
from archie import Archibald

prod = raw_input("Metaswitch? (y/n) ")

if prod == "y":
	# Values for MSB
	print "Using Metaswitch League"
	league_no = 597247
	team_no = 10
else:
	# Values for test league
	print "Using TestLeague"
	team_no = raw_input("Which team? [1-4]: ")
	league_no = 697783

# Generate keys for the desired leage / team
team_key = "348.l.%s.t.%s" % (league_no, team_no) 
league_id = "348.l.%s" % league_no

try:
	api = FantasyApi(league_id) 
	api.handler.refresh_token()
except:
	print "Failed to refresh token - register user"
 	FantasyApi.create_handler().reg_user()
	api = FantasyApi(league_id)

try:
	archie = Archibald(api, league_id, team_key)
	archie.start()
except AuthException, e:
	print "Hit API error: %s" % e
	print "Status code: %s" % e.status
