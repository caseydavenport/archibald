import json
from utils import *

class Teams(object):
	def __init__(self, handler):
		self.query_resp = json.loads(handler.api_req(TEAMS_QUERY).content)
		self.teams = []
                self.handler = handler
		for team_id, team_json in self.query_resp['fantasy_content']['leagues']['0']['league'][1]['teams'].items():
			print "Found team %s" % team_id
			if team_id != "count":
				self.teams.append(Team(team_json, handler))

class Team(object):
	def __init__(self, team_json, handler):
		self.team_json = team_json
		self.handler = handler
		self.players = []

		# Set attributes based on the received team_json
		for x in self.team_json['team'][0]:
			if isinstance(x, dict):
				for k,v in x.items():
					setattr(self, k, v)

		# Create roster object
		self.roster = Roster(self)

class Roster(object):
	def __init__(self, team):
		self.handler = team.handler 
		self.team = team
		self.players_by_num = {}

		# Get JSON from server
		resp = self.handler.api_req(TEAM_PLAYERS_QUERY % self.team.team_key)
		self.players_json = json.loads(resp.content)
		self.stripped = self.players_json['fantasy_content']['team'][1]['players']

		# Set attributes based on the received json 
		for k,player_json in self.stripped.items():
			if k != 'count':
				# Found players dict - all players 
				players = self.players_by_num.setdefault(k, [])
				p = Player(player_json, self.handler, self.team) 
				players.append(p)
				self.team.players.append(p)


class Players(object):
	def __init__(self, handler):
		self.players_json = json.loads(handler.api_req(PLAYERS_QUERY).content)
		self.handler = handler
		self.players = []
		for k,pj in self.players_json['fantasy_content']['league'][1]['players'].items():
			if k != 'count':
				self.players.append(Player(pj, self.handler, None))


class Player(object):
	def __init__(self, player_json, handler, team=None):
		self.handler = handler
		self.player_json = player_json
		self.team = team

		# Set a bunch of attrs
		for thing in self.player_json['player'][0]:
			if isinstance(thing, dict):
				for k,v in thing.items():
					setattr(self, k, v)

		# Redo some fields 
		self.player_name = self.name['full']
		self.display_position = str(self.display_position)

	def drop(self):
		assert self.team
		drop_str = DEL_PLAYER_XML % (self.player_key, self.team.team_key)
		head = {'Content-Type': 'application/xml'}
		self.handler.api_req(XACTION_URL, req_meth="POST", data=drop_str, headers=head )

	def add(self, team_key):
		add_str = ADD_PLAYER_XML % (self.player_key, team_key)	
		head = {'Content-Type': 'application/xml'}
		self.handler.api_req(XACTION_URL, req_meth="POST", data=add_str, headers=head )

