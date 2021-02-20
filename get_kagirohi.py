from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from urllib.parse import unquote
from random import randint, choice
from time import sleep
from os import system
from os.path import exists

# page = randint(1, 55)
path = '/home/milklee/Pictures/Wallpapers/Kagirohi'
for page in range(7,56):
	print('========= page. %d ========='%page)
	url = 'http://kagirohi.art/page/' + str(page)
	session = HTMLSession()
	response = session.get(url)
	sp = BeautifulSoup(response.text,'lxml')
	imgs = sp.find_all("a", class_="post-overlay")
	for img in imgs:
		img = choice(imgs)["href"]
		print(unquote(img))
		response = session.get(img)
		sp = BeautifulSoup(response.text,'lxml')
		pics = sp.find_all("figure", class_="wp-block-image")
		if len(pics)==0:
			pics = sp.find_all("div", class_="wp-caption")
		# pics = sp.find_all("div", class_="wp-caption")
		for pic in pics:
			items = pic.find_all("a")
			for item in items:
				filename = item["href"]
				filename = filename[filename.rfind('/'):len(filename)]
				if not exists(path+filename):
					print('       Download: ' + filename)
					urlretrieve(item["href"], path+filename)
				else:
					print('       Skipping: ' + filename)
				sleep(1)