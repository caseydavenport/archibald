from YHandler import *
from fantasyapi import *
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
			print "Current starting linup value: %s" % self.linup_value(players)

			# Drop any players which are undesirable.
			print "Drop any unwanted players"
			players = self.drop_bad_players(players, myteam)

			# Ensure the best players are in the starting linup.
			#print "Ensure best players in starting linup"
			#self.ensure_best_playing(myteam, players)

			# Query for team state.
			benched = myteam.benched_players()
			empty = myteam.empty_positions()
	
			# Make sure there are no disabled players in starting lineup.
			print "Replace any disabled players"
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
			elif len(players) < MAX_PLAYERS:
				# If there are empty slots but they are bench slots, just top
				# off the players on the team with good candidates.
				print "Topping off benched slots"
				empty = MAX_PLAYERS - len(players)
				self.top_off(myteam, empty)

			# Check for players for which there are better alternative.
			print "Comparing and swapping free-agents / waivers"
			self.compare_swap_players(myteam, None)

			# Sleep until next iteration
			self.sleep(1, 0, 0)

	def sleep(self, days, hours, minutes):
		seconds = minutes * 60
		seconds += hours * 3600
		seconds += days * 24 * 60 * 60
		print "Sleeping for %sd %sh %sm" % (days, hours, minutes)
		time.sleep(seconds)

	def linup_value(self, players):
		"""
		Returns the total estimated value index of the starting linup.
		"""
		value = 0
		for p in players:
			if p.current_position == "BN":
				continue
			value += p.value()
		return value

	def drop_bad_players(self, players, team):
		"""
		Drops players from the team which are deemed unworthy.
		"""
		for player in players:
			if not player.droppable:
				continue

			if player.percent_owned < 50:
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
			eligible += self.api.players(status="W", count=5, pos=pos, sort="PTS") 
			eligible = sorted(eligible, key=lambda p: p.value(), reverse=True)
			for e in eligible:
				if e.status == OK:
					print "Filling position %s with %s" % (pos, e) 
					team.add(e)
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
				print "%s is disabled" % p
				cur_pos = p.current_position
				if p.droppable:
					replacements = self.api.players(pos=cur_pos, status="FA", 
									count=1, sort="PTS")
					replacements += self.api.players(pos=cur_pos, status="W",
									 count=1, sort="PTS")
					replacements = sorted(replacements, key=lambda p: p.value(), reverse=True)
					try:
						repl = replacements[0]
					except IndexError:
						# No valid replacements, just continue.
						continue
					else:
						print " ** Dropping %s for %s" % (p, repl)
						team.replace(p, repl)
				else:
					# Cannot drop this player - search through bench
					benched = team.benched_players(cur_pos)
					if benched:
						print " ** Swapping %s with benched player %s" % (p, benched[0])
						team.set_position(p, 'BN')
						team.set_position(benched[0], cur_pos)

	def fill_empty_slots(self, team, empty, benched):
		"""
		Ensures there are no empty slots in the starting linup that could be filled 
		by one of the team's benched players.
		"""
		_filled = []
		for pos in empty:
			for player in benched[:]:
				if pos in player.valid_positions() and player.status not in BAD_STATUSES:
					# Player is eligible for open position, and is in OK status.
					print "Benched player %s -> %s" % (player, pos)
					team.set_position(player, pos)
					del benched[benched.index(player)]
					_filled.append(pos)
					break
		for pos in _filled:
			del empty[empty.index(pos)]	
		return empty

	def ensure_best_playing(self, team, players):
		"""
		Maximize the value of the starting linup by replacing starters with
		benched players if they are better.
		"""
		players = players or team.players

		for p in players:
			pos = p.current_position
			if pos == "BN":
				# Ignore benched players
				continue

			# Get benched players who can play this position.	
			eligible = team.benched_players(pos)
			
			if not eligible:
				print "No eligible benched players for pos: %s" % pos
				continue
			
			# Sort by value, find highest-value who is not injured.
			eligible = sorted(eligible, key=lambda p: p.value(), reverse=True) 
			for e in eligible:
				if e.status not in BAD_STATUSES:
					if p.status == OK and e.status != OK:
						# If replacing an OK player with a non-OK player,
						# make sure the risk is worth it.
						print "Perform cost comparison..."
						if e.value() > p.value() * 1.25:
							print "Swapping %s for %s" % (p, e)
					elif p.status != OK and e.status == OK:
						# Replacing a non-OK with an OK player - barrier 
						# for entry is lower.
						print "Perform cost comparison..."
						if e.value() > p.value() * .8:
							print "Swapping %s for %s" % (p, e)
					elif e.value() > p.value():
						# They have the same status and the replacement 
						# has more points.
						print "Swapping %s for %s" % (p, e)
					else:
						# The current player is the best.
						print "Current %s (%s) is best on team" % (pos, p)

					# We've made a decision - break this loop.
					break


	def top_off(self, team, num_empty=0):
		"""
		Fills up any empty slots on the given team with free-agents / waivers that look
		promising.  		
		"""
		# Get the top 10 based on current season points.
		eligible = self.api.players(status="FA", sort="PTS", count=5)
		eligible += self.api.players(status="W", sort="PTS", count=5)

		# Sort based on estimated value points.
		eligible = sorted(eligible, key=lambda p: p.value(), reverse=True)

		# Add eligible players to team
		for p in eligible:
			if not num_empty:
				break

			if p.status == OK: 
				# Player is status OK and position has not been chosen yet.
				print "Adding player %s" % p
				team.add(p)
				num_empty -= 1
		print "Unfilled slots: %s" % num_empty
		return num_empty

	def compare_swap_players(self, team, players):
		"""
		Checks to see if there are any free agents available that are worth acquiring.
		If there are, drops appropriate players in order to pick them up.
		"""
		players = players or team.players

		# For each player, get some elibile players based on points.
		for p in players:
			# If this player is not droppable, there is no point in comparing.  Skip.
			if not p.droppable:
				print "Player %s is not droppable, skip" % p
				continue

			# Determine the position to check swaps for.
			pos = p.current_position
			if pos == "BN":
				try:
					pos = p.valid_positions()[0]
					print "Player %s is benched, assume position %s" % (p, pos) 
				except IndexError:
					print " ** NO VALID POSITIONS FOR PLAYER %s" % p
					continue

			# Find some potential replacement players from free-agents and waivers.
			eligible = set()
			eligible.update(self.api.players(pos=pos,
							  status="FA",
							  sort="PTS",
							  count=5,
                                                          sort_season=CURRENT_SEASON-1))
			eligible.update(self.api.players(pos=pos,
						  status="W",
						  sort="PTS",
						  count=5,
                                                  sort_season=CURRENT_SEASON-1))
			eligible.update(self.api.players(pos=pos,
							  status="FA",
						          count=5,
							  sort="PTS"))
			eligible.update(self.api.players(pos=pos,
						  count=5,
						  status="W",
						  sort="PTS"))

			# Find most eligible
			most_eligible = p
			most_eligible_value = p.value()
			current_value = most_eligible_value
			print "Current %s (%s) value: %s" % (pos, p, most_eligible_value)
			while eligible:
				_next = eligible.pop()
				val = _next.value()
				print " - Checking %s (%s)" % (_next, val)
				if (_next.status != OK):
					print "   ** Not status OK"
				elif val > most_eligible_value: 
					most_eligible = _next
					most_eligible_value = val
			print "Most eligible %s: %s" % (pos, most_eligible)

			# Check if more valuable than current player by 10% buffer.
			BUFFER = 1.1
			score_to_beat = current_value * BUFFER
			print "Score to beat: %s" % score_to_beat
			if most_eligible.value() > score_to_beat:
				print "Drop %s (%s) for %s (%s)" % (p, current_value,
								most_eligible, most_eligible_value)
				team.replace(p, most_eligible)
