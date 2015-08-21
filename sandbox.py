from YHandler import *
from teams import *
from utils import *
import time
import datetime

# Create a handler to access Yahoo!
api = FantasyApi() 
team_key = "348.l.697783.t.4"

MY_TEAM_NAME = "Casey's Team"

thing = raw_input("Refresh token?: ")
if thing == "true":
  api.handler.authd['oauth_token'] = None

if not api.handler.authd.get('oauth_token'):
  api.handler.reg_user()
else:
  api.handler.get_login_token()

try:
	print "\n\n\n"
	print datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	myteam = api.get_team(team_key)
except AuthException, e:
	print "Hit error: %s" % e


def pretty(jsonstring):
	return json.dumps(jsonstring, indent=2)
