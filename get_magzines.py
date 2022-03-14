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
# path = '/home/milklee/Videos/Magzine/The\ New\ Yorker/'
path = '/home/milklee/Videos/Magzine/'
system('cd %s'%path)
# url = pyperclip.paste()
url = "http://magzdb.org/j/1798"
print(url)
session = HTMLSession()
response = session.get(url)
sp = BeautifulSoup(response.text,'lxml')
links = []
for link in sp.findAll('a'):
    links.append(link.get('href'))

for issue in links[::-1]:
	if not issue == None and issue.find('num')>-1:
		if int(issue[5:len(issue)])>4059134:
			continue
		print(issue)
		session = HTMLSession()
		response = session.get("http://magzdb.org" + issue)
		sp = BeautifulSoup(response.text,'lxml')
		for link in sp.findAll('a'):
			file = link.get('href')
			if file.find('file')>-1:
				name = "http://magzdb.org" + file[2:]
				session = HTMLSession()
				res = session.get(name)
				tmp = BeautifulSoup(res.text,'lxml')
				for dl in tmp.findAll('a'):
					mag = dl.get('href')
					if not mag == None and mag.find('pdf')>-1:
						filename = path + mag[mag.rfind('/')+1:len(mag)].replace(' ', '_')
						print(mag)
						if not exists(filename):
							system('wget "%s" -O %s'%(mag, filename))
							# urlretrieve(link, filename)
							sleep(3)
							# print('       Downloading: ' + filename)
						else:
							print('       Skipping: ' + filename)

# for block in content:
# 	pics = block.find_all("img", class_="zoom")
# 	if len(pics)>0:
# 		for item in pics:
# 			if item.has_key("file"):
# 				link = item["file"]
# 				filename = path + link[link.rfind('/')+1:len(link)]
# 				if not exists(filename):
# 					system('wget %s -O %s'%(link, filename))
# 					# print('       %s =====> %s'%(link, path))
# 					# urlretrieve(link, filename)
# 				else:
# 					print('       Skipping: ' + filename)
# 				# sleep(1)