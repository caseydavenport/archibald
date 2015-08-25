from YHandler import *
from teams import *
from utils import *
import json
import time
import datetime

MAX_PLAYERS = 15
MIN_PLAYERS = 9


class Archibald(object):
	def __init__(self, api, league_key, team_key):
		self.team_key = team_key
		self.league_key = league_key
		self.api = api 

	def start(self):
		while True:
			print "\nCheck @ %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
			myteam = self.api.get_team(self.team_key)
			print "Checking team: %s" % myteam.name
			players = myteam.players

			# Drop any players which are undesirable.
			print "Drop any unwanted players"
			players = self.drop_bad_players(players, myteam)

			# Query for team state.
			benched = myteam.benched_players()
			empty = myteam.empty_positions()
	
			# Make sure there are no disabled players in starting lineup.
			self.replace_disabled(myteam, players, benched)

			# Fill any empty slots in the starting lineup using benched players.
			print "Filling empty slots: %s" % empty
			empty = self.fill_empty_slots(myteam, empty, benched)

			# Fill any remaining empty slots in the starting linup using free agents.
			# This relies on us having room for recruitment.
			if empty and len(players) < MAX_PLAYERS:
				# TODO: Calculate how many free slots vs how many we need to recruit.
				print "Recruiting free agents"
				self.recruit_free_agents(empty, myteam)

			# Sleep until next iteration
			mins = 60
			print "Done - sleeping for %s mins" % mins
			time.sleep(mins * 60)

	def drop_bad_players(self, players, team):
		"""
		Drops players from the team which are deemed unworthy.
		"""
		for player in players:
			if player.percent_owned < 50 and player.droppable:
				print "Dropping unwanted player %s" % player
				team.drop(player)
				del players[players.index(player)]
			elif player.status != OK and player.percent_owned < 90:
				print "Dropping disabled player %s" % player
				team.drop(player)
				del players[players.index(player)]
		return players

	def recruit_free_agents(self, empty, team):
		"""
		Fills empty slots in the starting linup with recruits from free agency.
		"""
		for pos in empty[:]:
			# Find the best available free agent based on points for this position.
			print "Finding eligible players for pos %s" % pos
			eligible = self.api.players(status="FA", count=5, pos=pos, sort="PTS") 
			for e in eligible:
				if e.status == OK:
					print "Filling position %s with %s" % (pos, e) 
					team.add(e)
	
					# Find the player now that he has been added to the team,
					# and make sure his position is set.
					replaced = team.get_player(e.player_key)
					team.set_position(replaced, pos)
					del empty[empty.index(pos)]
					break
		return empty

	def replace_disabled(self, team, players, benched):
		"""
		Iterates through players and ensures that no players which are disabed
		(e.g. injured, out, etc) are in the starting lineup.
		"""
		for p in players:
			if p.status in BAD_STATUSES and not p in benched:
				cur_pos = p.current_position
				if p.droppable:
					replacements = self.api.players(pos=cur_pos, status="FA", count=1, sort="PTS")
					repl = replacements[0]
					team.replace(p, repl)
					print "Replaced %s with %s" % (p, repl)
				else:
					# Cannot drop this player - search through bench
					benched = team.benched_players(cur_pos)
					if benched:
						print "Swapping %s with benched player %s" % (p, benched[0])
						team.set_position(p, 'BN')
						team.set_position(benched[0], cur_pos)
					else:
						print "No benched players - look for free agents"

	def fill_empty_slots(self, team, empty, benched):
		"""
		Ensures there are no empty slots in the starting linupe that could be filled 
		by one of the team's benched players.
		"""
		_filled = []
		for pos in empty:
			for player in benched[:]:
				if pos in player.valid_positions() and player.status == OK:
					# Player is eligible for open position, and is in OK status.
					print "Benched player %s -> %s" % (player, pos)
					team.set_position(player, pos)
					del benched[benched.index(player)]
					_filled.append(pos)
					break
		for pos in _filled:
			del empty[empty.index(pos)]	
		return empty
