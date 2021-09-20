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
# path = '/home/milklee/Pictures/Wallpapers/Selected/xiao/'
path = '~/Downloads/.h'
system('cd %s'%path)
file = 'booklist.txt'
system('touch %s/%s'%(path, file))
NOTIFY_ID=56437281

# url = pyperclip.paste()
# print(url)
session = HTMLSession()
# link = "https://libgen.is/search.php?&req=Universitext&phrase=0&view=simple&column=series&sort=year&sortmode=DESC&page="
link = "https://libgen.is/search.php?req=%E4%B8%AD%E5%9B%BD%E8%8F%9C%E8%B0%B1&page="

page = 1
# for page in range(14, 74):
print('============== page:%d ============== '%page)
system("dunstify -r %d '%s%d'"%(NOTIFY_ID, link, page))
response = session.get('%s%d'%(link, page))
links = response.html.absolute_links
for link in links:
	if link.find('http://library.lol/')>=0:
		print(link)
		book = session.get(link)
		down = book.html.absolute_links
		for one in down:
			if one.find('http://31.42.184.140')>=0:
				system('echo %s >> %s/%s'%(one, path, file))
				system('wget %s'%one)