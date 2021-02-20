from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from urllib.parse import unquote
from random import randint, choice
from time import sleep
from os import system
from os.path import exists
import pyperclip

path = '/home/milklee/Pictures/Wallpapers/Haven/Anime/'
system('cd %s'%path)
url = pyperclip.paste()
print(url)
# url = 'https://wallhaven.cc/search?q=id%3A37&categories=110&purity=100&resolutions=2880x1800&sorting=relevance&order=desc&page='
# for page in range(1,10):
# 	print('Page #%d'%page)
session = HTMLSession()
# response = session.get(url+str(page))
response = session.get(url)
sp = BeautifulSoup(response.text,'lxml')
content = sp.find_all("a", class_="preview")
if not content:
	print("Connection error! Please try again...")
for one in content:
	keywd = one["href"]
	print(keywd)
	pos = keywd.rfind('/')
	name = path + keywd[pos+1:len(keywd)] + '.jpg'
	if not exists(name):
		response = session.get(keywd)
		sp = BeautifulSoup(response.text,'lxml')
		paper = sp.find_all("img", id="wallpaper")
		url = paper[0]["src"]
		# print('     %s =====> %s'%(url, name))
		# urlretrieve(url, path+name)
		system('wget %s -O %s'%(url, name))
		# sleep(2)
	else:
		print('     skipped: %s'%name)