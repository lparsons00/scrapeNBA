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
