import json
from YHandler import *
from utils import *


class FantasyApi(object):
	def __init__(self, league_key):
		self.handler = YHandler('auth.csv')
		self.league_key = league_key 
		self.game_key = GAME_KEY

	def get(self, url):
		resp = self.handler.api_req(url)
		return resp.json()['fantasy_content']

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

	def stat_categories(self):
		"""
		Retuns valid stat categories for NFL 2015
		"""
		url = "game/%s/stat_categories?format=json" % self.game_key
		resp = self.get(url)

		# Populate list with found stats
		_stats = []
		for stat_json in resp['game'][1]['stat_categories']['stats']:
			_stats.append(StatField(stat_json))
		return _stats 

	def players(self, pos=None, status=None, sort=None, count=25, start=0,
		sort_type="season", sort_season="2014"):
		"""
		Return a list of players using the given filters.
		By default, returns 25 players starting from 0, with no other 
		filter criteria.
		"""
		# TODO: For some reason, the API doesn't like W/R/T - it returns an empty list.
		# For now, replace this position with RB
		if pos == "W/R/T":
			print "Hack: Replacing W/R/T with RB"
			pos = "RB"

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
		
		# Query and find players json
		agents = self.get(url)
		players = agents['league'][1]['players']
		count = int(players['count'])

		# Get player objects from the returned data
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
			# For some reashon, the API raises an error when dropping a player
			# and indicates that player X is "not on your roster".  It appears
			# benign.
			if "not on your roster" in e.text:
				pass
			else:
				raise

	def add(self, player):
		assert not player.owned
		url = "league/%s/transactions" % self.league_key
		add_str = ADD_PLAYER_XML % (player.player_key, self.team_key)	
		head = {'Content-Type': 'application/xml'}
		try:
			self.api.handler.api_req(url, req_meth="POST", 
					data=add_str, headers=head )
		except AuthException, e:
			# For some reashon, the API raises an error when dropping a player
			# and indicates that player X is "not on your roster".  It appears
			# benign.
			if "on another team's roster" in e.text:
				pass
			else:
				raise

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
			# For some reashon, the API raises an error when dropping a player
			# and indicates that player X is "not on your roster".  It appears
			# benign.
			if "not on your roster" in e.text:
				pass
			else:
				raise

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

		# Set ownership fields
		self._get_ownership()
	
	def __eq__(self, other):
		if not isinstance(other, Player):
			return False
		return self.player_key == other.player_key

	def __str__(self):
		return self.full_name

	@property
	def percent_owned(self):
		url = "player/%s/percent_owned?format=json" % self.player_key
		ownership = self.api.get(url)
		_percent_owned = 0
		for d in ownership['player'][1]['percent_owned']:
			if 'value' in d:
				_percent_owned = d['value']
		return _percent_owned

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

	def stats(self):
		url = "player/%s/stats?format=json" % self.player_key
		resp = self.api.get(url)
		return resp

	def _get_ownership(self):
		# Build URL
		base = "league/%s/players;" % self.api.league_key 
                specific = "player_keys=%s/ownership?format=json" % self.player_key	
		url = base + specific

		# Query for Ownership stats
		resp = self.api.get(url)
		o = resp['league'][1]['players']['0']['player'][1]['ownership']
		try:
			self.owner_team_name = o['owner_team_name']
			self.ownership_type = o['ownership_type']
			self.team_key = o['owner_team_key']
			self.owned = True
		except KeyError:
			self.ownership_type = ""
			self.owner_team_name = ""
			self.team_key = ""
			self.owned = False 

class StatField(object):
	def __init__(self, stat_json):
		self.stat_json = stat_json
		
		# Get fields from given json.
		self.stat_id = self.stat_json['stat']['stat_id']
		self.sort_order = self.stat_json['stat']['sort_order']
		self.display_name = self.stat_json['stat']['display_name']
		self.name = self.stat_json['stat']['name']

		# Create list of positions for which this stat is valid.
		self.position_types = [] 
		for pos in self.stat_json['stat']['position_types']:
			self.position_types.append(pos['position_type'])
