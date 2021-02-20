from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from random import randint, choice
from time import sleep
from os import system
from os.path import exists
from sys import argv
import pyperclip

path = '/home/milklee/.config/i3/'

def get_query():
	if exists(path+'.artist'):
		query = '.query_artist.txt'
		sort = 'artist_ids'
	else:
		query = '.query.txt'
		sort = 'q'
	f = open(path+query)
	key = f.read()
	f.close()
	if len(key)==0:
		url = 'https://www.artic.edu/collection?page=' + str(randint(1, 200))
	else:
		key = key[0:len(key)-1]
		url = 'https://www.artic.edu/collection?%s=%s'%(sort, key)
		session = HTMLSession()
		response = session.get(url+'&page=200')
		sp = BeautifulSoup(response.text,'lxml')
		res = sp.find_all("a", class_="f-buttons")
		if res:
			max_page = 200
		else:
			response = session.get(url)
			sp = BeautifulSoup(response.text,'lxml')
			res = sp.find_all("a", class_="f-buttons")
			if res:
				max_page = int(res[-1].text)
			else:
				max_page = 1
		print(key, max_page)
		url = "%s&page=%d"%(url, randint(1, max_page))
		
	return url, key

if exists('%s.art.lck'%path):
	system('dunstify -u low " Another Instance is Running. Waiting..."')
else:
	system('touch %s.art.lck'%path)
	url, key = get_query()
	session = HTMLSession()
	system('dunstify -u critical " ART INSTITVTE CHICAGO" " Searching <i>%s</i>..."'%key)
	print(url)
	response = session.get(url)
	items = []
	for item in response.html.absolute_links:
		if item[22:30]=='artworks':
			items.append(item)
	if items:
		item = choice(items)
		pyperclip.copy(item)
		system('pkill dunst')
		system('dunstify -u critical " Retrieving Artwork Infomation from..." " <i>%s</i>"'%item[0:item.rfind('/')])
		art = session.get(item)
		sp = BeautifulSoup(art.text,'lxml')
		res = sp.find("meta", property="og:title")["content"]
		title =  res[0:res.find('|')-1]
		res = sp.find("meta", property="og:description")["content"]
		description =  res[res.find(',')+1:len(res)].lstrip()
		res = sp.find_all("p", class_="title f-secondary o-article__inline-header-display")
		for br in res[1].select("br"): br.replace_with("\n ")
		line =  res[1].text
		if len(line) > 220:
			line = line[0:line.rfind('\n')]
		print(line)
		img = sp.find("meta", property="og:image")["content"]
		filename = '/home/milklee/.config/i3/.art.jpg'
		urlretrieve(img, '%s.art.jpg'%path)
		system('touch %s.art.shw'%path)
		system('feh --bg-max %s.art.jpg'%path)
		system('pkill dunst')
		system('dunstify -t 10000 " %s\n %s" " %s"'%(title.replace('"','\\"'), description.replace('"','\\"'), line.replace('"','\\"')))
		system('dunstify -u low " ART INSTITVTE CHICAGO" " Searching <i>%s </i>Done!"'%key)
		with open('%s.art.txt'%path, mode='w') as f:
		    f.write(" %s\n %s\n %s"%(title, description, line))
		system('rm %s.art.lck'%path)
	else:
		system('pkill dunst')
		system('dunstify -u low " Sorry, we couldn’t find any results matching your criteria."')
		system('rm %s.art.lck'%path)