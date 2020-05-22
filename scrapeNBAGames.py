#####################################################################
#	basic scrapping code (scrapes from basketball-reference.com) 	#
# 	utilizes beautiful soup framework & panda framework to quickly  #
#   and easily scrape all stats and  stores stats in a excel db		#
#####################################################################
from urllib import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import lxml.html
import numpy as np
import math
import operator
import collections
from collections import OrderedDict
from datetime import date

#intoduce team abbreaviations for elo ratings mainly from practicallyy predictable
teams = pd.DataFrame(columns =["teamName", "abbr"])
new_row = {'teamName':'BOSTON CELTICS' , 'abbr':'BOS'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'NEW YORK KNICKS' , 'abbr':'NYK'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'BROOKLYN NETS' , 'abbr':'BKN'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'TORONTO RAPTORS' , 'abbr':'TOR'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'PHILADELPHIA 76ERS' , 'abbr':'PHI'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'MILWAUKEE BUCKS' , 'abbr':'MIL'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'CHICAGO BULLS' , 'abbr':'CHI'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'CLEVELAND CAVALIERS' , 'abbr':'CLE'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'INDIANA PACERS' , 'abbr':'IND'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'DETROIT PISTONS' , 'abbr':'DET'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'ATLANTA HAWKS' , 'abbr':'ATL'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'MIAMI HEAT' , 'abbr':'MIA'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'CHARLOTTE HORNETS' , 'abbr':'CHA'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'ORLANDO MAGIC' , 'abbr':'ORL'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'WASHINGTON WIZARDS' , 'abbr':'WAS'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'PORTLAND TRAIL BLAZERS' , 'abbr':'POR'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'UTAH JAZZ' , 'abbr':'UTA'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'DENVER NUGGETS' , 'abbr':'DEN'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'OKLAHOMA CITY THUNDER' , 'abbr':'OKC'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'MINNESOTA TIMBERWOLVES' , 'abbr':'MIN'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'LOS ANGELES CLIPPERS' , 'abbr':'LAC'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'LOS ANGELES LAKERS' , 'abbr':'LAL'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'SACRAMENTO KINGS' , 'abbr':'SAC'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'PHOENIX SUNS' , 'abbr':'PHO'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'GOLDEN STATE WARRIORS' , 'abbr':'GSW'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'MEMPHIS GRIZZLIES' , 'abbr':'MEM'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'DALLAS MAVERICKS' , 'abbr':'DAL'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'NEW ORLEANS PELICANS' , 'abbr':'NOP'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'HOUSTON ROCKETS' , 'abbr':'HOU'}
teams = teams.append(new_row, ignore_index=True)
new_row = {'teamName':'SAN ANTONIO SPURS' , 'abbr':'SAS'}
teams = teams.append(new_row, ignore_index=True)

#Home and road team win probabilities implied by Elo ratings and home court adjustment
def win_probs( home_elo, road_elo, hca_elo):
	h = math.pow(10, home_elo/400)
	r = math.pow(10, road_elo/400)
	a = math.pow(10, hca_elo/400)
	denom = r + a*h
	home_prob = a*h / denom
	road_prob = r / denom
	return home_prob, road_prob;

#Calibrate Elo home court adjustment to fit a teams historical home win percentage
def hca_calibrate( home_win_prob):
    if home_win_prob <= 0 or home_win_prob >= 1:
        raise ValueError('invalid home win probability', home_win_prob)
    a = home_win_prob / (1 - home_win_prob)
    hca = 400 * math.log10(a)
    return hca
hca_elo = hca_calibrate(home_win_prob=0.598)

#Update Elo ratings for a given match up.
def update( winner, home_elo, road_elo, hca_elo, k, probs=False):
    home_prob, road_prob = win_probs(home_elo=home_elo, road_elo=road_elo, hca_elo=hca_elo)
    if winner[0].upper() == 'H':
        home_win = 1
        road_win = 0
    elif winner[0].upper() in ['R', 'A', 'V']: # road, away or visitor are treated as synonyms
        home_win = 0
        road_win = 1
    else:
        raise ValueError('unrecognized winner string', winner)
    new_home_elo = home_elo + k*(home_win - home_prob)
    new_road_elo = road_elo + k*(road_win - road_prob)
    if probs:
        return new_home_elo, new_road_elo, home_prob, road_prob
    else:
        return new_home_elo, new_road_elo

#Compute simple Elo ratings over the course of an NBA season.
def simple_nba_elo( box_scores, teams, hca_elo, k):
    latest_elos = {teamName: 1500 for teamName in teams['teamName']}
    matchups = box_scores.sort_values(by='game_location', ascending=False).copy()
    home_probs = []
    road_probs = []
    home_elos = []
    road_elos = []
    elo_ts = []
    for game in matchups.itertuples():
    	if game.game_location == "home":
        	home_team = game.teamName
        	road_team = game.oppoTeam
        	winner = 'H' if game.result == 'won' else 'R'
        	home_elo = latest_elos[home_team]
        	road_elo = latest_elos[road_team]
        	(new_home_elo, new_road_elo, home_prob, road_prob) = update(
            	winner=winner,
            	home_elo=home_elo,
            	road_elo=road_elo,
            	hca_elo=hca_elo,
            	k=k,
            	probs=True
        	)
	        home_info = OrderedDict({
	            'date': game.date,
	            'game_id': game.gameID,
	            'abbr': home_team,
	            'opp_abbr': road_team,
	            'home_road': 'H',
	            'win_loss': game.result,
	            'win_prob': home_prob,
	            'opp_prior_elo': latest_elos[road_team],
	            'prior_elo': latest_elos[home_team],
	            'new_elo': new_home_elo,
	        })
	        elo_ts.append(home_info)
	        road_info = OrderedDict({
	            'date': game.date,
	            'game_id': game.gameID,
	            'abbr': road_team,
	            'opp_abbr': home_team,
	            'home_road': 'R',
	            'win_loss': 'won' if game.result == 'lost' else 'lost',
	            'win_prob': road_prob,
	            'opp_prior_elo': latest_elos[home_team],
	            'prior_elo': latest_elos[road_team],
	            'new_elo': new_road_elo,
	        })
	        elo_ts.append(road_info)
	        latest_elos[home_team] = new_home_elo
	        latest_elos[road_team] = new_road_elo
	        home_probs.append(home_prob)
	        road_probs.append(road_prob)
	        home_elos.append(new_home_elo)
	        road_elos.append(new_road_elo)

	#note to self: idk if this below will work in the long term
	#just break laptop if it doesnt work bc fk that
    matchups['win_prob'] = home_prob
    matchups['road_prob'] = road_prob
    matchups['home_elos'] = new_home_elo
    matchups['road_elos'] = new_road_elo
    return matchups, pd.DataFrame(elo_ts), latest_elos


# NBA seasons we will be analyzing
# note: leave out 2012 because of nba lockout
year = [2011, 2013, 2014, 2015, 2016, 2017, 2018, 2019]
month = [ "november", "december", "january", "february", "march"]
searchValues = []
temp = []
dates = []

for x in year:
	for y in month:
		# URL page we will scraping 
		url = "https://www.basketball-reference.com/leagues/NBA_{}_games-{}.html".format(x, y)
		print(url)
		html = urlopen(url)
		soup = BeautifulSoup(html)
		results = soup.find(id = "schedule")
		gameIDS = results.find_all('th')

		#find all the search values (to plug into the url)
		for gIDS in gameIDS:
    			link = gIDS.get('csk')
    			if link != None:
    				searchValues.append(link)

    	#find all the team abbreviations for to calculate rest days
        gameIDS = results.find_all('td')
        for gIDS in gameIDS:
    			link = gIDS.get('csk')
    			if link != None:
    				temp.append(link)

    	#calculate rest days
        for x in range(len(temp)):
			searchV = temp[x]
			searchV = searchV[:3]
			for i in range(x):
				prev = temp[x-i-1]
				prev = prev[:3]
				if(prev == searchV):
					holder = temp[x-i-1]
					one = int(holder[10:12])
					two = int(holder[8:10])
					three = int(holder[4:8])
					fdate = date(three, two, one)
					holder = temp[x]
					one = int(holder[10:12])
					two = int(holder[8:10])
					three = int(holder[4:8])
					ldate = date(three, two, one)
					holder = ldate - fdate
					dates.append(holder)
					break

#stats that we want for our future machine learning 
stats = pd.DataFrame(columns =["teamName", "oppoTeam", "minutes", "fgm", "fga", "fgp", "fg3m", "fg3a", 
	"fg3p", "ftm", "fta", "ftp", "orb", "drb", "trb", "ast", "stl", "blk", "tov", "fouls", "pts", "result", 
	"game_location", "date", "year", "gameID", "prev_game"])

indexNum = 0           
    
#for every single nba game (defined above) get all the defined stats  
for Y in searchValues:
	url = "https://www.basketball-reference.com/boxscores/{}.html".format(Y)
	print(url)
	html = urlopen(url)
	soup = BeautifulSoup(html)

	results = soup.find_all(class_="table_outer_container")[1]
	nameA = results.find('caption').get_text()
	resultsA = results.find('tfoot')
	nameA = nameA[:-11]
	nameA = nameA.upper()
	#needs to check for OT because the html slightly changes
	OT = resultsA.find_all("td")[0].get_text()
	if OT == "240":
		OTChecker = 9
	elif OT == "265":
		OTChecker = 10
	elif OT == "290":
		OTChecker = 11
	elif OT == "315":
		OTChecker = 12
	elif OT == "340":
		OTChecker = 13
	elif OT == "365":
		OTChecker = 14
	elif OT == "390":
		OTChecker = 15
	#just incase of lots of OT
	
	
	resultsB = soup.findAll(class_="section_content")[OTChecker]
	nameB = resultsB.find('caption').get_text()
	resultsB = resultsB.find("tfoot")
	nameB = nameB[:-11]
	nameB = nameB.upper()

	#add data to two arrays for home and away
	teamA = np.array([])
	teamB = np.array([])
	#teamName
	teamA = np.append(teamA, nameA)
	teamB = np.append(teamB, nameB)
	#oppoName
	teamA = np.append(teamA, nameB)
	teamB = np.append(teamB, nameA)

	for x in range(19): 
		if x == 18:
			#result
			a = resultsA.find_all("td")[x].get_text()
			b = resultsB.find_all("td")[x].get_text()
			teamA = np.append(teamA, a)
			teamB = np.append(teamB, b)
			if a > b:
				teamA = np.append(teamA, "won")
				teamB = np.append(teamB, "lost")
			else:
				teamB = np.append(teamB, "won")
				teamA = np.append(teamA, "lost")
		else: 
			teamA = np.append(teamA, resultsA.find_all("td")[x].get_text())
			teamB = np.append(teamB, resultsB.find_all("td")[x].get_text())
		

	
	#game_location	
	teamA = np.append(teamA, "away")
	teamB = np.append(teamB, "home")
	#date of game
	ID = Y
	date = ID[:-4]
	teamA = np.append(teamA, date)
	teamB = np.append(teamB, date)
	date = date[:-4]
	#year of game
	teamA = np.append(teamA, date)
	teamB = np.append(teamB, date)
	#unique game ID
	teamA = np.append(teamA, ID)
	teamB = np.append(teamB, ID)
	#rest days(calculated above)
	teamA = np.append(teamA, dates[indexNum])
	teamB = np.append(teamB, dates[indexNum])


	new_row = {'teamName':teamA[0] , 'oppoTeam':teamA[1], 'minutes':teamA[2], 'fgm':teamA[3], 'fga':teamA[4], 
	'fgp':teamA[5], 'fg3m':teamA[6],'fg3a':teamA[7], 'fg3p':teamA[8], 'ftm':teamA[9], 'fta':teamA[10], 
	'ftp':teamA[11], 'orb':teamA[12], 'drb':teamA[13], 'trb':teamA[14], 'ast':teamA[15], 'stl':teamA[16],
	'blk':teamA[17], 'tov':teamA[18], 'fouls':teamA[19], 'pts':teamA[20], 'result':teamA[21], 
	'game_location':teamA[22],'date':teamA[23], 'year':teamA[24], 'gameID': teamA[25], 'prev_game':teamA[26]}
	stats = stats.append(new_row, ignore_index=True)

	new_row = {'teamName':teamB[0] , 'oppoTeam':teamB[1],'minutes':teamB[2], 'fgm':teamB[3], 'fga':teamB[4], 
	'fgp':teamB[5], 'fg3m':teamB[6],'fg3a':teamB[7], 'fg3p':teamB[8], 'ftm':teamB[9], 'fta':teamB[10], 
	'ftp':teamB[11], 'orb':teamB[12], 'drb':teamB[13], 'trb':teamB[14], 'ast':teamB[15], 'stl':teamB[16],
	'blk':teamB[17], 'tov':teamB[18], 'fouls':teamB[19], 'pts':teamB[20], 'result':teamB[21], 
	'game_location':teamB[22], 'date':teamB[23], 'year':teamB[24], "gameID": teamB[25], 'prev_game':teamB[26]}
	stats = stats.append(new_row, ignore_index=True)
	indexNum += 1
	#print(stats)



#save all data to my local nba folder
#if copying this code to a different machine you must change the below save locations
stats.to_excel(r"C:/Users/Parsons/Desktop/nba/test.xlsx", sheet_name='sheet1', index=False)

print("Completed Scrape to Test Excel File.")

#create elo model for all nba games 
matchups, elo_hist, curr_elos = simple_nba_elo(box_scores=stats, teams=teams, hca_elo=hca_elo, k=20)

#save all elo data to my local nba folder
#again, if moing code to a different machine we must change below save locations
matchups.to_excel(r"C:/Users/Parsons/Desktop/nba/test2.xlsx", sheet_name='sheet1', index=False)
elo_hist.to_excel(r"C:/Users/Parsons/Desktop/nba/test3.xlsx", sheet_name='sheet1', index=False)
