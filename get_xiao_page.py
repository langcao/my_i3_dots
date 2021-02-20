from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from urllib.parse import unquote
from random import randint, choice
from time import sleep
from os import system
from os.path import exists
import pyperclip

# page = randint(1, 55)
path = '/home/milklee/Pictures/Wallpapers/Selected/xiao/'
system('cd %s'%path)
url = pyperclip.paste()
print(url)
session = HTMLSession()
response = session.get(url)
sp = BeautifulSoup(response.text,'lxml')
pics = sp.find_all("img")

# content = sp.find_all("div", class_="content")
# pics = content[0].find_all("img")

for item in pics:
	if item["src"].find('http')>-1:
		filename = item["src"]
		filename = path + filename[filename.rfind('/')+1:len(filename)]
		# filename = path+url[url.rfind('=')+1:len(url)-5] + '_' + filename
		if not exists(filename):
			# system('wget %s -O %s'%(item["src"], filename))
			print('       %s =====> %s'%(item["src"], filename))
			urlretrieve(item["src"], filename)
		else:
			print('       Skipping: ' + filename)
	sleep(2)