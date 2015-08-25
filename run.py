from YHandler import *
from teams import *
from utils import *
from archie import Archibald
import json
import time
import datetime

# Values for MSB
league_no = 597247
team_no = 10


# Values for test league
#team_no = 4
#league_no = 697783


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
	archie = Archibald(api, league_id, team_key)
	archie.start()

except AuthException, e:
	print "Hit API error: %s" % e
	print "Status code: %s" % e.status
