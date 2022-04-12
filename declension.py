import os
from os import system, popen
from unidecode import unidecode
import unicodedata
from googletrans import Translator
import unicodedata, re
from urllib.request import urlopen, urlretrieve
from urllib.parse import quote
from bs4 import BeautifulSoup
import simpleaudio as sa
from pynput.keyboard import Key, Listener
import requests
import vlc
import ssl

NOTIFY_ID = 62231
PLAY_ID = 622331
GRAMM_ID = 162231
MEAN_ID = 462231

def remove_accents(input_str):
	nfkd_form = unicodedata.normalize('NFKD', input_str)
	return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def rid_comma(out):
	rows = out.split('\n')
	mod = []
	for row in rows:
		if row.find(',') == -1:
			mod.append(row)
		else:
			lst = 0
			pos = row.find(',')
			line = '\t\t\t\t'
			while pos>-1:
				prev = row[lst:pos+1]
				end = row.find('\t', pos)
				blk = row[pos+1:end]
				line += blk + '\t'
				lst = end
				pos = row.find(',', lst)
			prev += row[lst:-1]
			mod.append(prev)
			mod.append(line)
	s = ''
	for row in mod:
		s += row + '\n'

	return s

def full_count(s):
	num = 0
	for i in range(len(s)):
		if unicodedata.east_asian_width(s[i]) in ['W', 'F']:
			num += 1
		if unicodedata.east_asian_width(s[i]) in ['A']:
			num += 0.15
	return int(len(s) + num)

def adjust_tab(out, tab_width=2):
	item = [x.split('\t') for x in out.split('\n')]
	rc, lc = len(item)-1, len(item[0])-2
	adj = ['' for _ in item]
	for j in range(0, lc):
		lens = [full_count(item[i][j]) for i in range(rc)]
		for i in range(rc):
			adj[i] += item[i][j] + ' '*(max(lens) + tab_width - full_count(item[i][j]))
	s = ''
	for row in adj:
		s += row + '\n'

	return s[:-1]

system('xdotool key "Escape"')
sound_path = "/tmp/Russian"
if not os.path.exists(sound_path):
	os.mkdir(sound_path)
tmp = popen('xsel').read()
print(tmp)
if tmp.find(' ')>-1:
	tmp = tmp[0:tmp.find(' ')]
if tmp.find('\n')>-1:
	tmp = tmp[0:tmp.find('\n')]
tmp = "".join([x.lower() for x in tmp if x.isalpha()])
pron = unidecode(tmp)
word = remove_accents(tmp)

translator = Translator()
try:
	a = translator.translate(tmp)
	trans = a.text
except:
	system("dunstify -r %d 'Переводимое слово не обнаружено.\nNo translatable word dectected.'"%NOTIFY_ID)
else:
	trans = trans.replace("'","’")
	pron = pron.replace("'","’")
	if word == trans:
		system("dunstify -r %d 'Русское слово не обнаружено.\n%s - No Russian word dectected.'"%(NOTIFY_ID, tmp))
	else:
		system("dunstify -r %d '%s [%s]'"%(NOTIFY_ID, word, pron))

		url = "https://www.igimu.com/index.php?q=%s"%(quote(word))
		print(url)
		context = ssl._create_unverified_context()
		res = urlopen(url, context=context)
		soup = BeautifulSoup(res, "html.parser")
		soup.br.replace_with(", ")
		mean = soup.findAll('p', class_='exp')
		key = soup.findAll('h2', class_='keyword')
		if mean[0].text == '暂无释义.':
			orgn, pron_orgn, expl = key[-1].text, unidecode(key[-1].text), mean[-1].text
		else:
			orgn, pron_orgn, expl = key[0].text, unidecode(key[0].text), mean[0].text
		pron_orgn = pron_orgn.replace("'","’")
		system("dunstify -r %d '%s [%s] %s' '%s.'"%(MEAN_ID, orgn, pron_orgn, trans, expl))

		grammar = soup.findAll('table')
		title = soup.find('div', class_='grammardiv')
		if title:
			h3 = title.findAll('h3')
		declist = []
		for i, table in enumerate(grammar):
			rows = table.findAll("tr")
			out = ''
			for row in rows:
				items = row.findAll("th")
				for item in items:
					out += item.text+'\t'
				decl = row.findAll("td")
				for item in decl:
					out += item.text+'\t'
				out += '\n'
			# out = rid_comma(out)
			out = adjust_tab(out)
			if title and h3 and i<len(h3):
				out = ' ' + h3[i].text + ' \n' + out
			declist.append(out)
		if declist:
			ind = 0
			system("dunstify -r %d '%s [%s] %s'"%(NOTIFY_ID, word, pron, trans))
			system("dunstify -r %d '%s' 'Страница %d / %d'"%(GRAMM_ID, declist[ind], ind+1, len(declist)))

		file = "%s/%s.mp3"%(sound_path,word)
		if not os.path.exists(file):
			read = soup.find('a', class_='speaker')
			if read:
				print(read['data-url'])
				system("dunstify -r %d ' Восстановление произношения...'"%PLAY_ID)
				urlretrieve(read['data-url'], file)
			else:
				system("dunstify -r %d '%s [%s] %s'"%(NOTIFY_ID, word, pron, trans))
				system("dunstify -r %d -u low ' Нет произношения.'"%PLAY_ID)
				exit()

		def read_word():
			system("dunstify -r %d '%s [%s] %s'"%(NOTIFY_ID, word, pron, trans))
			system("dunstify -r %d -u low ' %s'"%(PLAY_ID, word))
			p = vlc.MediaPlayer(file)
			p.play()

		def on_press(key):
			global ind, orgn, pron_orgn, expl, word, pron, trans
			# print('{0} release'.format(key))
			if key in [Key.enter]:
				system("dunstify -r %d '%s [%s] %s' '%s.'"%(MEAN_ID, orgn, pron_orgn, trans, expl))
			if key in [Key.space]:
				system("dunstify -r %d '%s [%s]'"%(NOTIFY_ID, word, pron))
				read_word()
			if key in [Key.down, Key.right]:
				ind += 1
				if ind >= len(declist):
					ind = 0
				system("dunstify -r %d '%s [%s]'"%(NOTIFY_ID, word, pron))
				system("dunstify -r %d '%s' 'Страница %d / %d'"%(GRAMM_ID, declist[ind], ind+1, len(declist)))
			if key in [Key.up, Key.left]:
				ind -= 1
				if ind < 0:
					ind = len(declist) - 1
				system("dunstify -r %d '%s [%s]'"%(NOTIFY_ID, word, pron))
				system("dunstify -r %d '%s' 'Страница %d / %d'"%(GRAMM_ID, declist[ind], ind+1, len(declist)))

		def on_release(key):
			if key in [Key.esc]:
				system("killall dunst")
				return False

		read_word()
		ind = 0
		with Listener(on_press=on_press, on_release=on_release) as listener:
			listener.join()