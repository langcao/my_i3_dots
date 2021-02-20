from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from random import randint, choice
from time import sleep
from os import system
from os.path import exists
from sys import argv
import pyperclip

session = HTMLSession()
response = session.get("https://www.artic.edu/collection")
sp = BeautifulSoup(response.text,'lxml')
for item in sp.find_all("p", {"aria-expanded": "false"}):
	print(item.text.replace(' ','').replace('\n',''))
