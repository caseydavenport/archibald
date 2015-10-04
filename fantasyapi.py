import json
from YHandler import *
from utils import *
import random


class FantasyApi(object):
	def __init__(self, league_key):
		self.handler = self.create_handler() 
		self.league_key = league_key 
		self.game_key = GAME_KEY
		self.league_settings = self._league_settings()
		self.stat_categories = self._stat_categories()

	@classmethod
	def create_handler(cls):
		return YHandler('auth.csv')

	def get(self, url):
		resp = self.handler.api_req(url)
		return resp.json()['fantasy_content']

	def _league_settings(self):
		url = "league/%s/settings?format=json" % self.league_key
		resp = self.get(url)
		settings = Settings(resp['league'][1]['settings'][0], self)	
		return settings

	def get_team(self, team_key):
		url = "team/%s?format=json" % team_key
		team = self.get(url)
		return Team(team, self)

	def all_teams(self):
		url = "leagues;league_keys=%s/teams?format=json" % self.league_key
		resp = self.get(url)
		teams = resp['leagues']['0']['league'][1]['teams']
		count = int(teams['count'])

		# Iterate through results, create Team objects
		_teams = []
		for i in range(count):
			_teams.append(Team(teams[str(i)], self))
		return _teams

	def stat_with_id(self, stat_id):
		"""
		Returns a tuple of StatField, StatModifier for the givne ID.
		If the stat does not count towards fantasy points, None will be returned
		for the modifier.
		"""
		cats = self.stat_categories
		mods = self.league_settings.stat_modifiers()
		return cats[stat_id], mods.get(stat_id)

	def _stat_categories(self):
		"""
		Retuns valid stat categories for NFL 2015.
		"""
		url = "game/%s/stat_categories?format=json" % self.game_key
		resp = self.get(url)

		# Populate list with found stats
		_stats = {}
		for stat_json in resp['game'][1]['stat_categories']['stats']:
			s = StatField(stat_json)
			_stats[s.stat_id] = s
		return _stats 

	def players(self, pos=None, status=None, sort=None, count=25, start=0,
		sort_type="season", sort_season=CURRENT_SEASON):
		"""
		Return a list of players using the given filters.
		By default, returns 25 players starting from 0, with no other 
		filter criteria.
		"""
		# TODO: For some reason, the API doesn't like W/R/T - it returns an empty list.
		# For now, replace this position with RB
		if pos == "W/R/T":
			pos = random.choice(["RB", "WR", "TE"])
			print " == HACK: Replacing W/R/T with %s ==" % pos

		# Decide the URL to use for this query
		filter_str = "count=%s&start=%s" % (count, start)
		filter_str += "&sort_type=%s&sort_season=%s" % (sort_type, sort_season)
		if pos:
			filter_str += "&position=%s" % pos
		if status:
			filter_str += "&status=%s" % status
		if sort:
			filter_str += "&sort=%s" % sort

		url = "league/%s/players?%s&format=json" % (self.league_key, filter_str) 
		
		# Query and find players json.
		agents = self.get(url)
		players = agents['league'][1]['players']
	
		# If no players were found, return an empty list.
		if len(players) == 0:
			return []
		
		# Get player objects from the returned data
		count = int(players['count'])
		_players = []
		for i in range(count):
			_players.append(Player(players[str(i)], self, None))
		return _players 


class Team(object):
	def __init__(self, team_json, api):
		self.team_json = team_json
		self.api = api
		self.league_key = api.league_key

		# Set attributes based on the received team_json
		for x in self.team_json['team'][0]:
			if isinstance(x, dict):
				for k,v in x.items():
					setattr(self, k, v)

	def __eq__(self, other):
		if not isinstance(other, Team):
			return False
		return self.team_key == other.team_key

	def players_at_pos(self, pos):
		l = [] 
		for player in self.players:
			if player.display_position == pos:
				l.append(player)
		return l

	def get_player(self, player_key):
		for player in self.players:
			if player.player_key == player_key:
				return player
		raise KeyError("Player not found on team")

	def drop(self, player):
		assert player.droppable 
		assert player.team_key == self.team_key 
		url = "league/%s/transactions" % self.league_key
		drop_str = DEL_PLAYER_XML % (player.player_key, self.team_key)
		head = {'Content-Type': 'application/xml'}

		try:	
			self.api.handler.api_req(url, req_meth="POST", 
					data=drop_str, headers=head )
		except AuthException, e:
			pass

	def add(self, player):
		assert not player.owned
		url = "league/%s/transactions" % self.league_key
		add_str = ADD_PLAYER_XML % (player.player_key, self.team_key)	
		head = {'Content-Type': 'application/xml'}
		try:
			self.api.handler.api_req(url, req_meth="POST", 
					data=add_str, headers=head )
		except AuthException, e:
			pass

	def replace(self, old_player, new_player):
		"""
		Drops one player, adds another. 
		"""
		assert old_player.owned
		assert not new_player.owned
		assert old_player.team_key == self.team_key 
		url = "league/%s/transactions" % self.league_key
		replace_str = ADD_DROP_XML % (new_player.player_key, self.team_key,
					      old_player.player_key, self.team_key)
		head = {'Content-Type': 'application/xml'}

		try:
			self.api.handler.api_req(url, req_meth="POST", 
					data=replace_str, headers=head )
		except AuthException, e:
			pass

	def swap_positions(self, p1, p2):
		"""
		Swaps two player positions in the lineup.
		"""
		# If one player is not editible, then we can't swap - log and return.
		if not p1.is_editable or not p2.is_editable:
			print "Cannot edit player(s), skipping swap"
			return

		# Get current positions
		pos1 = p1.current_position
		pos2 = p2.current_position

		# Bench player2 so we can stick player1 in that slot.
		self.set_position(p2, "BN")

		# Put player1 in player2's spot.
		self.set_position(p1, pos2)

		# Put player2 in player1's original spot.
		self.set_position(p2, pos1)

	def set_position(self, player, pos):
		"""
		Sets the given player to the specified position.
		"""
		# TODO: Get week from better source than 'player'
		assert pos in player.valid_positions() or pos == 'BN'
		player_xml = PLAYER_POS_XML % (player.player_key, pos) 
		roster_xml = ROSTER_XML % (player.current_week, player_xml)

		url = "team/%s/roster" % self.team_key 
		head = {'Content-Type': 'application/xml'}
		self.api.handler.api_req(url, 'PUT', data=roster_xml, headers=head)


	def empty_positions(self):
		"""
		Returns a list of positions on the team which are not filled.
		"""
		positions = ['QB', 'WR', 'WR', 'RB', 'RB', 'TE', 'W/R/T', 'K', 'DEF']
		for player in self.players:
			curr_pos = player.current_position

			# Only count players not on the bench, since we don't count 
			# 'BN' as an eligible position.
			if curr_pos != 'BN':
				# Remove this player's position from the list
				# since it is accounted for.
				del positions[positions.index(curr_pos)]
		return positions

	def benched_players(self, pos=None):
		"""
		Returns all benched players on this team.
		If a position is given, will only return players which can
		play the given position.
		"""
		_players = []
		for player in self.players:
			if player.current_position == 'BN':
				if not pos or pos in player.valid_positions():
					_players.append(player)
		return _players
			

	@property
	def players(self):
		# Get players JSON from roster resource.
		url = "team/%s/roster/players?format=json" % self.team_key
		self.roster_json = self.api.get(url)
		players = self.roster_json['team'][1]['roster']['0']['players']
		count = players['count']

		# Set attributes based on the received json 
		_players = []
		for i in range(count):
			p = Player(players[str(i)], self.api, self) 
			_players.append(p)
		return _players
	

class Player(object):
	def __init__(self, player_json, api, team=None):
		self.api = api 
		self.player_json = player_json
		self.team = team
		self.status = OK 
		self._percent_owned = None
		self._ownership_type = None
		self._owner_team_name = None
		self._team_key = None
		self._owned = None
		
		# Set as many attributes as we can from the JSON
		for block in self.player_json['player']:
			if isinstance(block, list):
				# If this is a list, iterate through it.
				for thing in block:
					if isinstance(thing, dict):
						for k,v in thing.items():
							setattr(self, k, v)
			elif isinstance(block, dict):
				# If it is a dict, set attributes.
				for k,v in block.items():
					setattr(self, k, v)

		# Redo some fields so they are proper Python types, etc. 
		self.full_name = self.name['full']
		self.droppable = (self.is_undroppable == '0')
		self.bye_week = self.bye_weeks['week']

		# Convert int to a boolean, make sure field exists.
		# Players not on a team do not have this attribute.
		if hasattr(self, "is_editable"):
			self.is_editable = (self.is_editable == 1)
		else:
			self.is_editable = False

	def __eq__(self, other):
		if not isinstance(other, Player):
			return False
		return self.player_key == other.player_key

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash(self.player_key)

	def __str__(self):
		return self.full_name

	@property
	def is_bye(self):
		return self.bye_week == self.current_week

	@property
	def percent_owned(self):
		if self._percent_owned is None:
			url = "player/%s/percent_owned?format=json" % self.player_key
			ownership = self.api.get(url)
			for d in ownership['player'][1]['percent_owned']:
				if 'value' in d:
					self._percent_owned = d['value']
		return self._percent_owned

	def valid_positions(self):
		"""
		Returns list of valid positions for this player.
		"""
		positions = []
		for position_dict in self.eligible_positions:
				positions.append(position_dict['position'])
		return positions

	@property
	def current_position(self):
		return self.selected_position[1]['position']

	@property
	def current_week(self):
		return self.selected_position[0]['week']

	def stats(self, season=CURRENT_SEASON):
		url = "player/%s/stats?type=season&season=%s&format=json" % (self.player_key, season)
		resp = self.api.get(url)
		
		# Return dict
		_stats = {}
		for s in resp['player'][1]['player_stats']['stats']:
			stat = PlayerStat(s)
			_stats[stat.stat_id] = stat
		return _stats 

	def fantasy_points(self, season=CURRENT_SEASON):
		pts = 0
		for stat_id, stat in self.stats(season).iteritems():
			_, mod = self.api.stat_with_id(stat_id)
			if mod:
				# If a modifier exists, it means points can be earned
				# for this stat.  Add the points to the total.
				pts += stat.value * mod.value
		return pts

	def value(self):
		"""
		Returns a numeric value assocaited with the worth of this player.  Uses a variety of 
		weighted metrics to calculated an estimated "worth"
		"""
		value_pts = 0

		# Add points from the current season.
		value_pts += self.fantasy_points()

		return value_pts

	@property
	def owner_team_name(self):
		if self._owner_team_name is None:
			self._get_ownership()
		return self._owner_team_name

	@property
	def ownership_type(self):
		if self._ownership_type is None:
			self._get_ownership()
		return self._ownership_type

	@property
	def team_key(self):
		if self._team_key is None:
			self._get_ownership()
		return self._team_key

	@property
	def owned(self):
		if self._owned is None:
			self._get_ownership()
		return self._owned

	def _get_ownership(self):
		# Build URL
		base = "league/%s/players;" % self.api.league_key 
                specific = "player_keys=%s/ownership?format=json" % self.player_key	
		url = base + specific

		# Query for Ownership stats
		resp = self.api.get(url)
		o = resp['league'][1]['players']['0']['player'][1]['ownership']
		try:
			self._owner_team_name = o['owner_team_name']
			self._ownership_type = o['ownership_type']
			self._team_key = o['owner_team_key']
			self._owned = True
		except KeyError:
			self._ownership_type = ""
			self._owner_team_name = ""
			self._team_key = ""
			self._owned = False 


class Settings(object):
	def __init__(self, settings_json, api):
		self.settings_json = settings_json
		self.api = api

		for k, v in settings_json.items():
			setattr(self, "_%s" % k, v)

	def stat_modifiers(self):
		_mods = {}
		for s in self._stat_modifiers['stats']:
			m = StatModifer(s)
			_mods[m.stat_id] = m
		return _mods 


class PlayerStat(object):
	"""
	Represents an individual player's stats in a given category.
	"""
	def __init__(self, stat_json):
		self.stat_json = stat_json
		self.stat_id = int(stat_json['stat']['stat_id'])
		self.value = float(stat_json['stat']['value']) 

class StatField(object):
	"""
	Represents a stat that is presnet in this league.
	"""
	def __init__(self, stat_json):
		self.stat_json = stat_json
		
		# Get fields from given json.
		self.stat_id = int(self.stat_json['stat']['stat_id'])
		self.sort_order = self.stat_json['stat']['sort_order']
		self.display_name = self.stat_json['stat']['display_name']
		self.name = self.stat_json['stat']['name']

		# Create list of positions for which this stat is valid.
		self.position_types = [] 
		for pos in self.stat_json['stat']['position_types']:
			self.position_types.append(pos['position_type'])

	def __str__(self):
		return "StatField(%s, id=%s)" % (self.name, self.stat_id)		


class StatModifer(object):
	"""
	Represents the modifier used to calulate fantasy points for a given stat.
	"""
	def __init__(self, stat_modifier):
		self.stat_json = stat_modifier
		
		self.stat_id = int(self.stat_json['stat']['stat_id'])	
		self.bonuses = self.stat_json['stat'].get('bonuses', [])
		self.value = float(self.stat_json['stat']['value'])

	def __str__(self):
		return "StatModifier(id=%s, points=%s)" % (self.stat_id, self.value)
