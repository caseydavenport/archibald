from YHandler import *
from teams import *
from utils import *
import json
import time
import datetime

# Create a handler to access Yahoo!
api = FantasyApi(LEAGUE_ID) 
team_key = "348.l.697783.t.4"

thing = raw_input("Get new token?: ")
if thing == "true":
  api.handler.reg_user()
else:
  api.handler.refresh_token()

try:
	while True:
		print "\n%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	
		# Get my team
		myteam = api.get_team(team_key)
		empty = myteam.empty_positions()
		benched = myteam.benched_players()
		players = myteam.players
	
		# Make sure there are no disabled players.
		for p in players:
			if p.status in BAD_STATUSES and not p in benched:
				cur_pos = p.current_position
				if p.droppable:
					replacements = api.players(pos=cur_pos, status="FA", count=1)
					repl = replacements[0]
					myteam.replace(p, repl)
					print "Replaced %s with %s" % (p, repl)
				else:
					# Cannot drop this player - search through bench
					benched = myteam.benched_players(cur_pos)
					if benched:
						print "Swapping %s with benched player %s" % (p, benched[0])
						myteam.set_position(p, 'BN')
						myteam.set_position(benched[0], cur_pos)
					else:
						print "No benched players - look for free agents"
					
	
		# Make sure there are no empty slots that could be occupied.
		for p in benched:
			for pos in p.valid_positions():
				if pos in empty and p.status == OK:
					# Player is eligible for open position, and is in OK status.
					print "Benched player %s -> %s" % (p, pos)
					myteam.set_position(p, pos)
					del empty[empty.index(pos)]
					break

		# Sleep before accessing again.
		mins = 29
		time.sleep(mins * 60)
	
	#	for player in players:
	#		eligible = api.players(pos=player.display_position,
	#				status="FA",
	#				count=1)
	#		print "Player: %s, (Can drop: %s) " % (player.full_name, player.droppable)
	#		for e in eligible:
	#			if player.droppable:
	#				print "Replace with: %s" % e.full_name
	#				myteam.replace(player, e)
	#				break
except AuthException, e:
	print "Hit API error: %s" % e
