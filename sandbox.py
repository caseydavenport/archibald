from YHandler import *
from teams import Teams, Team, Players
from utils import *
import time
import datetime

# Create a handler to access Yahoo!
handler = YHandler("auth.csv")

MY_TEAM_NAME = "Casey's Team"

thing = raw_input("Refresh token?: ")
if thing == "true":
  handler.authd['oauth_token'] = None

if not handler.authd.get('oauth_token'):
  handler.reg_user()
else:
  handler.get_login_token()

try:
	print "\n\n\n"
	print datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	teams = Teams(handler)	
	
	players = Players(handler)

	# Find my team
	myteam = None
	for team in teams.teams:
		if team.name == MY_TEAM_NAME:
			myteam = team
			break
except AuthException, e:
	print "Hit error: %s" % e
