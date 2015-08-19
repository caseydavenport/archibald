from YHandler import *
from teams import Teams, Team, Players
from utils import *
import time
import datetime

game_key=348
league_id=697783

# Create a handler to access Yahoo!
handler = YHandler("auth.csv")

while True:
	try:
		print "\n\n\n"
		print datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
		teams = Teams(handler)	
		
		players = Players(handler)
		
		team0 = teams.teams[0]
		team1 = teams.teams[1]
		team2 = teams.teams[2]
		team3 = teams.teams[3]
		
		p = players.players[0]
		time.sleep(20)
	except AuthException, e:
		handler.reg_user()
		
