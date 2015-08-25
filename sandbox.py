from YHandler import *
from teams import *
from utils import *
from archie import Archibald
import json
import time
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
#	print "Getting Stat Resource"
#	stats = api.stat_categories()

	# Fill empty slots
	MAX = 15
	MIN = 9
	for pos in empty:
		# Assume no bench players can fill the spot.
		if len(players) >= MAX:
			# If we have max players, we must drop one first.
			# Use "percent_owned" as an initial indicator of success - drop any
			# which noone wants.
			for player in players:
				if player.percent_owned < 50 and player.droppable:
					print "Dropping unwanted player %s" % player
					myteam.drop(player)
					del players[players.index(player)]
				elif player.status != OK and player.percent_owned != 100:
					print "Dropping disabled player %s" % player
					myteam.drop(player)
					del players[players.index(player)]
			if len(players) >= MAX:
				# TODO: Still greater than max - need to pick the right
				# player to drop.
				pass
				

		# Find the best available free agent based on points for this position.
		print "Finding eligible players for pos %s" % pos
		eligible = api.players(status="FA", count=5, pos=pos, sort="PTS") 
		for e in eligible:
			if e.status == OK:
				print "Filling position %s with %s" % (pos, e) 
				myteam.add(e)

				# Find the player now that he has been added to the team.
				replaced = myteam.get_player(e.player_key)
				myteam.set_position(replaced, pos)
				break

	empty = myteam.empty_positions()
	print "Remaining empty: %s" % empty

except AuthException, e:
	print "Hit API error: %s" % e
	print "Status code: %s" % e.status
