from YHandler import *
from teams import *
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
	
	all_players = Players(ALL_PLAYERS_QUERY, handler)

	free_players_query = STATUS_PLAYERS_QUERY % (LEAGUE_ID, FREE_AGENT)
	#free_players = Players(free_players_query, handler)

	# Find my team
	myteam = None
	for team in teams.teams:
		if team.name == MY_TEAM_NAME:
			myteam = team
			break

	eligible_by_pos = {}
	for playa in myteam.players:
		print "%s (%s)" % (playa.player_name, playa.display_position)
		for playa2 in all_players.players:
			if playa2.display_position == playa.display_position:
				if not playa2.owned:
					print "  **%s" % playa2.player_name
					eligible = eligible_by_pos.setdefault(playa.display_position, [])
					eligible.append(playa2)
	
	for pos, players in eligible_by_pos.iteritems():
		# Find the best eligible player
		best = players[0] 
		for p in players:
			if p.percent_owned > best.percent_owned:
				best = p
			
		for p in myteam.players_at_pos(pos):	
			if best.percent_owned > p.percent_owned:
				print "Drop %s for %s" % (p.player_name, best.player_name)
				p.drop()	
				best.add(myteam.team_key)

except AuthException, e:
	print "Hit error: %s" % e


def pretty(jsonstring):
	return json.dumps(jsonstring, indent=2)
