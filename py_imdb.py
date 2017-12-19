#!/usr/bin/python3   

from bs4 import BeautifulSoup
import urllib.request
import re
from socket import error as SocketError
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import sys
import urllib3
import getopt
from imdb_ratings import *



def usage():
	print(('usage: %s [-l imdblink] [-j json] [-h help] ...' % argv[0]))
	return 100
	

def help():
	print("This python script will extract all the information (seasons,episodes,episode director,actors,season rating,per episode rating,duration, episode name etc"
		"\nimdblink: Link of the tv shows, you want to get information about"
		"\njson file name, only if you want to save the information in csv too, by default, it save it in json file")
	return usage()


def get_url_response(url):
	hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
	html = ''
	try:
		req = urllib.request.Request(url, None, hdr)
		with urllib.request.urlopen(req) as response:
			html = response.read()
		return html

	except:
	    print('error')

def main(argv):

	imdb_url = 'http://www.imdb.com'
	website_url = 'http://www.imdb.com/title/tt0375355/?ref_=ttep_ep_tt'
	json_filename = ''
	content_type = ''

	try:
	    (opts, args) = getopt.getopt(argv[1:], 'l:j:h')
	except getopt.GetoptError:
		return usage()

	for (k, v) in opts:
		if k == '-l': 
			website_url = v 

		elif k == '-j': 
			json_filename = v

		else: return help()


	season_dict = {} # Main Dictonary

	soup = BeautifulSoup(get_url_response(website_url),'lxml') # to get the html source of the page

	release_info = soup.find('a',title=re.compile('release dates'))
	for info_dates in release_info.stripped_strings:
		season_dict['release_dates'] = info_dates

	#print("Release Dates: ",season_dict['release_dates'])
	isDocumentary = False

	#Genre
	genres = soup.find_all('span',itemprop='genre')
	genres_list = []
	for genre in range(len(genres)):
		#print(genres[genre].string)
		genres_list.append(genres[genre].string)
		if('Documentary' in genres[genre].string):
			isDocumentary = True

	season_dict['genre'] = genres_list

	if('TV' not in info_dates):
		content_type = 'M'
		season_dict['total_seasons'] = 1
		season_dict['total_episodes'] = 1
	else:
		if(isDocumentary):
			content_type = 'D'
			season_dict['release_dates'] = season_dict['release_dates'].replace('TV Mini-Series','')
			season_dict['release_dates'] = season_dict['release_dates'].strip(' ()')
		else:
			content_type = 'T'
			season_dict['release_dates'] = season_dict['release_dates'].replace('TV Series','')
			season_dict['release_dates'] = season_dict['release_dates'].strip(' ()')

	duration = None
	duration = soup.find('time',itemprop='duration')
	if(duration != None):
		for cur in duration.stripped_strings:
			season_dict['duration'] = cur 

		#print(season_dict['duration'])
	else:
		season_dict['play_time'] = 'NA'

	season_dict['imdb_link'] = website_url

	#Title
	title = soup.find('h1',itemprop='name')
	if(content_type == 'T'):
		season_dict['title'] = " ".join(title.string.split())
	else:
		season_dict['title'] = 	" ".join(title.contents[0].split())

	if(len(json_filename) < 2):
		json_filename = "".join(title.contents[0].split())

	original_title = None
	original_title_string = ''
	original_title != soup.find('div',class_='originalTitle')
	if(original_title != None):
		for string in soup.find('div',class_='originalTitle').strings:
			original_title_string = original_title_string + string
		
		season_dict['title'] = season_dict['title'] +'-' +  original_title_string

	print('Title: ',season_dict['title'])

	#Rating
	season_rating = soup.find('span',itemprop='ratingValue')
	#print(season_rating.string)
	season_dict['season_ratings'] = season_rating.string


	#Rating Count
	season_user_ratings = soup.find('span',itemprop='ratingCount')
	season_dict['imdb_score_votes'] = int(season_user_ratings.string.replace(',',''))
	#print('Votes: ', season_dict['imdb_score_votes'])

	#Ratings Json
	rating_link = soup.find('div',class_='imdbRating').find('a',href=re.compile("ratings"))['href']
	print('Rating Link: ', imdb_url + rating_link)
	rating_json = making_ratings_json(BeautifulSoup(get_url_response(imdb_url+rating_link),'lxml'),season_dict['imdb_score_votes'],imdb_url+rating_link)
	season_dict['rating_details'] = rating_json


	#Content Rating
	content_rating = soup.find('meta',itemprop='contentRating')
	# #print(content_rating['content'])
	season_dict['content_rating'] = content_rating['content']


	#Creators
	season_creators = []
	creators=''
	if(content_type == 'T'):
		creators = soup.find_all('span',itemprop='creator')
	else:
		creators = soup.find_all('span',itemprop='director')

	for creator in range(len(creators)):
		season_creators.append(creators[creator].find('span',itemprop='name').string)
		#print(creators[creator].find('span',itemprop='name'))

	season_dict['creators'] = season_creators

	#print(season_dict['creators'])

	#Cast
	cast_characters = []
	all_cast = soup.find('table',class_='cast_list')
	cast_name = all_cast.find_all('span',itemprop='name')
	character_name = all_cast.find_all('td',class_='character')
	for names in range(len(cast_name)):
		cast_characters.append(cast_name[names].string)
		#print(cast_name[names].string)
	season_dict['cast'] = cast_characters

	languages_list = []
	languages = soup.find_all('a',href=re.compile("primary_language="))
	for lan in range(len(languages)):
		print('Languages: ', languages[lan].string)
		languages_list.append(languages[lan].string)
	
	season_dict['languages'] = languages_list

	season_description = soup.find('div', itemprop='description')
	for description in season_description.stripped_strings:
		season_dict['season_description'] = description
		#print(description)


	if(content_type == 'T'):

		#Episode Guide
		episode_guide = soup.find_all('span',class_='bp_sub_heading')
		for total_epi in range(len(episode_guide)):
			#print('List: ',episode_guide[total_epi].string)
			if('episode' in episode_guide[total_epi].string):
				season_dict['total_episodes'] = int(episode_guide[total_epi].string.split()[0])
				#print(episode_guide[total_epi].string.split()[0])

		#Season Episode
		season_episode = soup.find_all('a',href=re.compile("season="))
		
		#print('total seasons: ',season_episode[0].string)
		
		season_year = soup.find_all('a',href=re.compile("ref_=tt_eps_yr_"))
		#To confirm till 2017
		latest_year = season_year[0].string

		if(int(latest_year) > 2017):
			season_to_search = int(season_episode[0].string)-(int(latest_year)-2017)
		else:
			season_to_search = int(season_episode[0].string)

		#print('Season to Search: ', season_to_search)
		#print('Latest: ', latest_year)

		season_link = season_episode[0]['href'] # /title/tt0108778/episodes?season=10&ref_=tt_eps_sn_10
		season_dict['total_seasons'] = season_to_search

		per_season_list = []
		count_total_episodes = 0 #sometimes total episodes is different from the actual episodes


		for each_season in range(season_to_search):
		#for each_season in range(1): #for test
			per_season_dict = {}
			per_episode_list = []
			season_url = imdb_url + season_link[:season_link.find('=')+1] + str(each_season+1) + '&ref_=tt_eps_sn_' + str(each_season+1)
			print('='*60)
			print(season_dict['title'], '-',each_season + 1 , season_url)
			print('='*60)

			each_season_soup= BeautifulSoup(get_url_response(season_url),'lxml')

			episodes_link = each_season_soup.find_all('div',itemprop='episodes')
			#print(len(episodes_link))
			#print(episodes_link[0])
			for every_episode in range(len(episodes_link)):
				count_total_episodes = count_total_episodes + 1
				per_episode_dict = {}
				#per_episode_dict['title'] = " ".join(title.string.split())
				per_episode_dict['episode_num'] = every_episode + 1
				per_episode_dict['episode_name'] = episodes_link[every_episode].find('a',itemprop='name')['title']
				per_episode_dict['season_num'] = each_season + 1
				#print(db_episodes['episode_name'])

				#each_episode_soup= BeautifulSoup(episodes_link[every_episode],'lxml')
				for airDate in episodes_link[every_episode].find('div',class_='airdate').stripped_strings:
					#print(airDate)
					per_episode_dict['realease_date'] = airDate

				per_episode_dict['episode_imdb_link'] = imdb_url + episodes_link[every_episode].find('a',itemprop='name')['href']

				#print(episodes_link[every_episode].find('span',class_=re.compile('ipl-rating-star__rating')).string)
				if(episodes_link[every_episode].find('span',class_=re.compile('ipl-rating-star__total-votes')) != None):
					per_episode_dict['rating'] = float(episodes_link[every_episode].find('span',class_=re.compile('ipl-rating-star__rating')).string)
				
					#print(episodes_link[every_episode].find('span',class_=re.compile('ipl-rating-star__total-votes')).string)
					per_episode_dict['episode_score_votes'] = int(episodes_link[every_episode].find('span',class_=re.compile('ipl-rating-star__total-votes')).string.strip('()').replace(',',''))
					
					for every_description in episodes_link[every_episode].find('div',class_='item_description').stripped_strings:
						#print(every_description)
						per_episode_dict['episode_description'] = every_description

					#print (json.dumps(per_episode_dict,indent=4))

					per_episode_list.append(per_episode_dict)
					#print('Length: ',len(per_episode_list))

				print('Episode Extracted ',per_episode_dict['episode_name'], '. Season-Num: ', per_episode_dict['season_num'])
				
			per_season_dict['season-'+str(each_season+1)] = per_episode_list
			per_season_list.append(per_season_dict)


		season_dict['Seasons'] = per_season_list
		if(count_total_episodes != season_dict['total_episodes']):

			#print('Updating Total Episodes: ', count_total_episodes ,' and ', season_dict['total_episodes'])
			season_dict['total_episodes'] = count_total_episodes



	with open('./sample_outputs/' + json_filename +'.json', 'w') as fp:
		json.dump(season_dict, fp,indent=4)
	
	print('Data extracted successfully for : ',season_dict['title'])

if __name__ == '__main__':
    sys.exit(main(sys.argv))