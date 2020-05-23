#####################################################################
#	attempt at creating an elo model from our scraped data 			#
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
    		if game.teamName == "CHARLOTTE BOBCATS":
    			home_team = "CHARLOTTE HORNETS"
    		elif game.teamName == "NEW ORLEANS HORNETS":
    			home_team = "NEW ORLEANS PELICANS"
    		elif game.teamName == "NEW JERSEY NETS":
    			home_team = "BROOKLYN NETS"
    		else:
        		home_team = game.teamName

        	if game.oppoTeam == "CHARLOTTE BOBCATS":
        		road_team = "CHARLOTTE HORNETS"
        	elif game.oppoTeam =="NEW ORLEANS HORNETS":
    			road_team = "NEW ORLEANS PELICANS"
    		elif game.oppoTeam == "NEW JERSEY NETS":
    			road_team = "BROOKLYN NETS"
        	else:
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
    matchups['home_elos'] = home_elo
    matchups['road_elos'] = road_elo
    return matchups, pd.DataFrame(elo_ts), latest_elos


x1 = pd.ExcelFile("test.xlsx")
df = x1.parse("sheet1")

matchups, elo_hist, curr_elos = simple_nba_elo(box_scores=df, teams=teams, hca_elo=hca_elo, k=20)
#save all elo data to my local nba folder
#again, if moing code to a different machine we must change below save locations
#matchups.to_excel(r"C:/Users/Parsons/Desktop/nba/test2.xlsx", sheet_name='sheet1', index=False)
elo_hist.to_excel(r"C:/Users/Parsons/Desktop/nba/test3.xlsx", sheet_name='sheet1', index=False)
