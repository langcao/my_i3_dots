from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from urllib.parse import unquote
from random import randint, choice
from time import sleep
from os import system
from os.path import exists
import pyperclip

path = '/home/milklee/Pictures/Wallpapers/Selected/insho/玄幻武侠/'
session = HTMLSession()
# page = randint(1, 115)
for page in range(87,124):
	print('========= page. %d ========='%page)
	if page == 1:
		url = 'http://www.habwg.com/html/part/index28.html'
	else:
		url = 'http://www.habwg.com/html/part/index28_%d.html'%page
	response = session.get(url)
	sp = BeautifulSoup(response.text,'lxml')
	content = sp.find_all("ul", class_="textList")
	text = content[0].find_all("a")
	# item = choice(text)
	for item in text:
		url = 'http://www.habwg.com' + item["href"]
		response = session.get(url)
		response.encoding = "gbk"
		sp = BeautifulSoup(response.text,'lxml')
		content = sp.find_all("div", class_="mainArea")
		line = unquote(content[0].text).replace(' ','').replace('"','').replace('。','').replace('.','').replace('(','[').replace(')',']').replace('【','[').replace('】',']').replace('|','_').replace('"','”').replace('\'','‘')
		title = line[line.rfind('»')+3:len(line)-1]
		if len(title) < 19:
			full = path+title+'.txt'
			if not exists(full):
				print('    Download %s  =====>  《%s》 '%(url, title))
				text = unquote(content[1].text.replace('$','').replace('\n。','').replace('\r','\n').replace('\n\n','\n').replace('\n」','」').replace('\n」','」'))
				# system('echo "%s" > %s'%(text, full))
				file = open(full, 'w')
				file.write(text)
				file.close()
			else:
				print('    Skipping %s  =====>  《%s》 '%(url, title))
			# sleep(1)

