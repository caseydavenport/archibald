import json
from YHandler import *
from utils import *


class FantasyApi(object):
	def __init__(self):
		self.handler = YHandler('auth.csv')
		self.league_key = LEAGUE_ID

	def get(self, url):
		resp = self.handler.api_req(url)
		return resp.json()['fantasy_content']

	def get_team(self, team_key):
		url = "team/%s?format=json" % team_key
		team = self.get(url)
		return Team(team, self)

	def all_teams(self):
		url = TEAMS_QUERY
		resp = self.get(url)
		teams = resp['leagues']['0']['league'][1]['teams']
		count = int(teams['count'])

		# Iterate through results, create Team objects
		_teams = []
		for i in range(count):
			_teams.append(Team(teams[str(i)], self))
		return _teams

	def players(self, pos=None, status=None, sort=None, count=25, start=0):
		"""
		Return a list of players using the given filters.
		By default, returns 25 players starting from 0, with no other 
		filter criteria.
		"""
		# Decide the URL to use for this query
		filter_str = "count=%s&start=%s" % (count, start)
		if sort:
			filter_str = "&sort=%s" % sort
		if pos:
			filter_str += "&position=%s" % pos
		if status:
			filter_str += "&status=%s" % status
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

	def drop(self, player):
		assert player.droppable 
		assert player.team_key == self.team_key 
		drop_str = DEL_PLAYER_XML % (player.player_key, self.team_key)
		head = {'Content-Type': 'application/xml'}
		self.api.handler.api_req(XACTION_URL, req_meth="POST", 
				data=drop_str, headers=head )

	def add(self, player):
		assert not player.owned
		add_str = ADD_PLAYER_XML % (player.player_key, self.team_key)	
		head = {'Content-Type': 'application/xml'}
		self.api.handler.api_req(XACTION_URL, req_meth="POST", 
				data=add_str, headers=head )

	def replace(self, player, new_player):
		"""
		Drops one player, adds another. 
		"""
#		assert player.owned
#		assert not new_player.owned
#		assert player.team_key == self.team_key 
		replace_str = ADD_DROP_XML % (new_player.player_key, self.team_key,
					      player.player_key, self.team_key)
		head = {'Content-Type': 'application/xml'}
		self.api.handler.api_req(XACTION_URL, req_meth="POST", 
				data=replace_str, headers=head )
	
	@property
	def players(self):
		# Get JSON from server
		url = TEAM_PLAYERS_QUERY % self.team_key
		players_json = self.api.get(url)
		players = players_json['team'][1]['players']
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

		# Set a bunch of attrs
		for thing in self.player_json['player'][0]:
			if isinstance(thing, dict):
				for k,v in thing.items():
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

	@property
	def percent_owned(self):
		url = "player/%s/percent_owned?format=json" % self.player_key
		ownership = self.api.get(url)
		_percent_owned = 0
		for d in ownership['player'][1]['percent_owned']:
			if 'value' in d:
				_percent_owned = d['value']
		return _percent_owned

	def _get_ownership(self):
		# Build URL
		base = "league/%s/players;" % LEAGUE_ID
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
