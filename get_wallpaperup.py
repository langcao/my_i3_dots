from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from urllib.parse import unquote
from random import randint, choice
from time import sleep
from os import system
from os.path import exists
import pyperclip

path = '/home/milklee/Pictures/Wallpapers/Retina/'
system('cd %s'%path)
# url = pyperclip.paste()
url = 'https://www.wallpaperup.com/search/results/cats_ids:8+resolution:=:2880x1800/'
for page in range(19,38):
	print('Page #%d'%page)
	session = HTMLSession()
	response = session.get(url+str(page))
	sp = BeautifulSoup(response.text,'lxml')
	content = sp.find_all("div", class_="thumb-adv")
	for one in content:
		pics = one.find_all("a")
		keywd = pics[0]["href"]
		pos = keywd.rfind('/')
		name = keywd[pos+1:len(keywd)].replace('html','jpg')
		if not exists(path+name):
			url = 'https://www.wallpaperup.com' + pics[0]["href"]
			response = session.get(url)
			sp = BeautifulSoup(response.text,'lxml')
			paper = sp.find_all("div", class_="thumb-wrp")
			pic = paper[0].find_all("img")
			url = pic[0]["data-original"]
			print('     %s =====> %s'%(url, name))
			urlretrieve(url, path+name)
			# sleep(2)
		else:
			print('     skipped: %s'%name)
	break