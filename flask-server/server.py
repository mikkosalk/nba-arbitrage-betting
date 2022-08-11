from flask import Flask
import requests
import urllib.request
from urllib.request import Request, urlopen
import pandas as pd
import re
from bs4 import BeautifulSoup

abbrev_names = {'AtlantaHawks': 'ATL', 'ATLHawks': 'ATL', 'BostonCeltics': 'BOS', 'BOSCeltics': 'BOS',
     'BrooklynNets': 'BKN', 'BKNNets': 'BKN', 'CharlotteHornets': 'CHA', 'CHAHornets': 'CHA',
     'ChicagoBulls': 'CHI', 'CHIBulls': 'CHI', 'DallasMavericks': 'DAL', 'DALMavericks': 'DAL',
     'DenverNuggets': 'DEN', 'DENNuggets': 'DEN', 'DetroitPistons': 'DET', 'DETPistons': 'DET',
     'GoldenStateWarriors': 'GSW', 'GSWWarriors': 'GSW', 'GSWarriors': 'GSW', 'HoustonRockets': 'HOU', 'HOURockets': 'HOU',
     'IndianaPacers': 'IND', 'INDPacers': 'IND', 'LosAngelesClippers': 'LAC', 'LAClippers': 'LAC',
     'LosAngelesLakers': 'LAL', 'LALakers': 'LAL', 'MemphisGrizzlies': 'MEM', 'MEMGrizzlies': 'MEM',
     'MiamiHeat': 'MIA', 'MIAHeat': 'MIA', 'MilwaukeeBucks': 'MIL', 'MILBucks': 'MIL', 
     'MinnesotaTimberwolves': 'MIN', 'MINTimberwolves': 'MIN', 'NewOrleansPelicans': 'NOP',
     'NOPelicans': 'NOP', 'NewYorkKnicks': 'NYK', 'NYKnicks': 'NYK', 'OklahomaCityThunder': 'OKC',
     'OKCThunder': 'OKC', 'OrlandoMagic': 'ORL', 'ORLMagic': 'ORL', 'Philadelphia76ers': 'PHI',
     'PHI76ers': 'PHI', 'PhoenixSuns': 'PHX', 'PHXSuns': 'PHX', 'PHOSuns': 'PHX', 'PortlandTrailBlazers': 'POR',
     'PORTrailBlazers': 'POR', 'SacramentoKings': 'SAC', 'SACKings': 'SAC', 'SanAntonioSpurs': 'SAS',
     'SASpurs': 'SAS', 'TorontoRaptors': 'TOR', 'TORRaptors': 'TOR', 'UtahJazz': 'UTA', 'UTJazz': 'UTA',
     'WashingtonWizards': 'WAS', 'WASWizards': 'WAS'}

#bookie websites
URL = 'https://www.sportsbetting.ag/sportsbook/basketball/nba'
URL1 = 'https://sportsbook.draftkings.com/leagues/basketball/88670846'
urls = {0: URL, 1: URL1}
sites = {0: "SportsBetting", 1: "DraftKings Sportsbook"}

#fake header to get data from site 
hdr = {'User-Agent': 'Mozilla/5.0'}
req = Request(URL,headers=hdr)
page = urlopen(req)

req1 = Request(URL1,headers=hdr)
page1 = urlopen(req1)

#HTML source
soup = BeautifulSoup(page, features='html.parser')
soup1 = BeautifulSoup(page1, features='html.parser')
#print(soup2.prettify())

#scrape data
teamsHTML = soup.find_all('td', attrs={'class': 'col_teamname bdevtt'})
oddsHTML = soup.find_all('td', attrs={'class': 'odds bdevtt moneylineodds displayOdds'})

teamsHTML1 = soup1.find_all('div', attrs={'class': 'event-cell__name-text'})
oddsHTML1 = soup1.find_all('span', attrs={'class': 'sportsbook-odds american no-margin default-color'})

teams = []
odds = []
teams1 = []
odds1 = []

#american odds to decimal odds
def dec_odds(odd):
  res = []
  for k in range(len(odd)):
    if(int(odd[k])>=0):
      res.append(int(odd[k])/100+1)
    else:
      res.append(1-(100/int(odd[k])))
  return res

#clean team names data
def clean_teams(ht):
  res = []
  for h in ht:
    res.append(abbrev_names[h.getText().replace('\n','').replace('\t','').replace(' ','')])
  return res

#clean odds data
def clean_odds(odd):
  res = []
  for o in odd:
    res.append(o.getText().replace('\n','').replace('\t',''))
  return res

teams = clean_teams(teamsHTML)
odds = clean_odds(oddsHTML)
teams1 = clean_teams(teamsHTML1)
odds1 = clean_odds(oddsHTML1)

#compile data from one site into dataframe
def site_data(t, o):
  rows = []
  for i in range(0,len(t), 2):
    row = []
    row.append(t[i])
    row.append(t[i+1])
    row.append(o[i])
    row.append(o[i+1])
    rows.append(row)
  return pd.DataFrame(columns=['Team 1', 'Team 2', 'T1 Odds', 'T2 Odds'], data=rows)

odds = dec_odds(odds)
odds1 = dec_odds(odds1)

df = site_data(teams, odds)
df1 = site_data(teams1, odds1)

#data
site1_data = [['Memphis Grizzlies', 'Golden State Warriors', 3.95, 1.274], ['Denver Nuggets', 'Philadelphia 76ers', 1.6, 1.9]]
site2_data = [['Memphis Grizzlies', 'Golden State Warriors', 1.5, 2.8], ['Denver Nuggets', 'Philadelphia 76ers', 1.4, 2.5]]
s1 = pd.DataFrame(columns=['Team 1', 'Team 2', 'T1 Odds', 'T2 Odds'], data=site1_data)
s2 = pd.DataFrame(columns=['Team 1', 'Team 2', 'T1 Odds', 'T2 Odds'], data=site2_data)
data = [s1, s2]

#function to find arbitrage possibility for all games
def arb(l):
  res = "<hr>"
  if not l:
    return
  num_of_games = len(l[0])
  for i in range(num_of_games):
    res+=(arb_game(l, i))
    res+="<hr>"
  return res

#helper function for a single game
def arb_game(l, game):
  res = ""
  team1_odds = []
  team1max = (float('-inf'), -1)
  team2_odds = []
  team2max = (float('-inf'), -1)
  for i in range(len(l)):
    if l[i].iloc[game][2] > team1max[0]:
      team1max = (l[i].iloc[game][2], i)
    if l[i].iloc[game][3] > team2max[0]:
      team2max = (l[i].iloc[game][3], i)
  arbit = 100*(1/team1max[0]+1/team2max[0])
  res = res + '<p>The best possible arbitrage percentage for '+ l[i].iloc[game][0]+ ' vs '+ l[i].iloc[game][1]+' is '+f'{arbit:.2f}'+ '%.</p>'
  if arbit < 100:
    res = res + '<p>There is an arbitrage opportunity by betting on '+ l[i].iloc[game][0]+ ' on <a href='+ urls[team1max[1]]+'>'+sites[team1max[1]]+ '</a> and '+ l[i].iloc[game][0]+ ' on <a href='+ urls[team2max[1]]+'>'+sites[team2max[1]]+ '</a></p>'
  elif arbit >=0:
    res = res + '<p>There is no arbitrage opportunity for '+ l[i].iloc[game][0]+ ' vs '+ l[i].iloc[game][1]+ ' ¯\_(ツ)_/¯</p>'
  else:
    return '<p>ERROR</p>'
  return res

app = Flask(__name__)

@app.route("/data")
def members():
  #when NBA starts again change s1, s2 to df, df1, data to [df, df1]
  return {"members": ["<p>"+sites[0]+"</p>",s1.to_html(), "<p>"+sites[1]+"</p>", s2.to_html(), arb(data)]}


if __name__ == "__main__":
    app.run(debug=True)