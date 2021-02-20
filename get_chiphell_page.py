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
path = '/home/milklee/Pictures/Wallpapers/Chiphell/'
system('cd %s'%path)
url = pyperclip.paste()
print(url)
session = HTMLSession()
response = session.get(url)
sp = BeautifulSoup(response.text,'lxml')
content = sp.find_all("td", class_="plc")
# print(content)
for block in content:
	pics = block.find_all("img", class_="zoom")
	if len(pics)>0:
		for item in pics:
			if item.has_key("file"):
				link = item["file"]
				filename = path + link[link.rfind('/')+1:len(link)]
				if not exists(filename):
					system('wget %s -O %s'%(link, filename))
					# print('       %s =====> %s'%(link, path))
					# urlretrieve(link, filename)
				else:
					print('       Skipping: ' + filename)
				# sleep(1)