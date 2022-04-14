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
from pynput.keyboard import Key, Listener, KeyCode
import requests
import vlc
import ssl
import re
from prettytable import PrettyTable

NOTIFY_ID = 62231
PLAY_ID = 622331
GRAMM_ID = 162231
MEAN_ID = 462231
PAGE_ID = 362231
DICT_ID = 562231
EXAM_ID = 762231
MAX_ROW_LENGTH = 100
EXAM_PER_PAGE = 10

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
	return len(s) + int(num)

def split_row(s):
	if len(s) > MAX_ROW_LENGTH:
		i = 0
		split = ''
		for c in s:
			split += c
			i += full_count(c)
			if i > MAX_ROW_LENGTH:
				split += '\n  '
				i = 0
		return split
	else:
		return s

def adjust_tab(out, name='', tab_width=2):
	x = PrettyTable()
	item = [_.split('\t') for _ in out.split('\n')]
	for i, row in enumerate(item):
		if i:
			x.add_row(row[:-1])
		else:
			if name:
				row[0] = name
			x.field_names = row[:-1]
	# print(x)
	# return x.get_string()

	# item = [x.split('\t') for x in out.split('\n')]
	rc, lc = len(item), len(item[0])-1
	adj = ['  ' for _ in item]
	adj[0] = ' '
	for j in range(0, lc):
		lens = [full_count(item[i][j]) for i in range(rc)]
		for i in range(rc):
			adj[i] += item[i][j] + ' '*(max(lens) - full_count(item[i][j]) + tab_width)
	s = ''
	for row in adj:
		s += row + '\n'

	return s[:-1]

system('xdotool key "Escape"')
sound_path = "/tmp/Russian"
if not os.path.exists(sound_path):
	os.mkdir(sound_path)
tmp = popen('xsel').read()
tmp = tmp.strip()
tmp.replace("`",'')
if tmp.find(' ')>-1:
	tmp = tmp[0:tmp.find(' ')]
if tmp.find('\n')>-1:
	tmp = tmp[0:tmp.find('\n')]
tmp = "".join([x.lower() for x in tmp if x.isalpha()])
pron = unidecode(tmp)
pron = pron.replace("'","’")
word = remove_accents(tmp)
# word = tmp
system("dunstify -t 0 -r %d ' %s [%s]'"%(NOTIFY_ID, word, pron))

translator = Translator()
try:
	a = translator.translate(tmp)
	trans = a.text
except:
	system("dunstify -r %d -u low 'Переводимое слово не обнаружено.\nNo translatable word dectected.'"%NOTIFY_ID)
else:
	trans = trans.replace("'","’")
	pron = pron.replace("'","’")
	if word == trans:
		system("dunstify -r %d -u low 'Русское слово не обнаружено.\n%s - No Russian word dectected.'"%(NOTIFY_ID, tmp))
	else:
		url = "https://www.igimu.com/index.php?q=%s"%(quote(word))
		print("https://www.igimu.com/index.php?q=%s"%word)
		context = ssl._create_unverified_context()
		res = urlopen(url, context=context)
		soup = BeautifulSoup(res, "html.parser")
		mean = soup.findAll('p', class_='exp')
		for one in mean:
			for i in one.select("br"):
				i.replace_with(',')
		key = soup.findAll('h2', class_='keyword')
		if mean[0].text == '暂无释义.':
			orgn, pron_orgn, expl = key[-1].text, unidecode(key[-1].text), mean[-1].text
		else:
			orgn, pron_orgn, expl = key[0].text, unidecode(key[0].text), mean[0].text
		orgn = orgn.replace('е"', 'ё')
		pron_orgn = pron_orgn.replace("'","’")
		expl = expl.replace("【船舶】","").replace("【航空】","")
		expl = re.sub(' +', ' ', expl)
		item = expl.split(',')
		expl = ''
		for one in item:
			if expl.find(one)==-1:
				expl += one + ', '
		if expl:
			expl = expl[:-2]
		print(expl)
		expl = split_row(expl)
		system("dunstify -t 0 -r %d ' %s [%s] %s' '  %s.'"%(MEAN_ID, orgn, pron_orgn, trans, expl))

		page = soup.findAll('div', class_='subExp view')
		sel = ''
		for each in page:
			for i in each.select("br"):
				i.replace_with('; ')
			if len(sel)<len(each.text):
				sel = each.text
		sel = "".join([s for s in sel.strip().splitlines(True) if s.strip()])
		sel = re.sub(' +', ' ', sel)
		sel = sel.replace("'","’")
		orgn = sel[0:sel.find('\n')].strip()
		pron_orgn = unidecode(orgn)
		pron_orgn = pron_orgn.replace("'","’")
		sel = sel[sel.find('\n'):-1].strip().replace("\n"," ").replace(").",")").replace("~","")
		print(sel)
		sel = split_row(sel)

		exam_ru = soup.findAll('p', class_='exam-a')
		rus, chn = [], []
		for one in exam_ru:
			rus.append(split_row(re.sub(' +', ' ', one.text).replace('\n', '').replace('\r', '').strip()))
		exam_cn = soup.findAll('p', class_='exam-b')
		for one in exam_cn:
			chn.append(split_row(re.sub(' +', ' ', one.text).replace('\n', '').replace('\r', '').strip()))
		offset = 0
		for i in range(EXAM_PER_PAGE):
			ch = i + offset
			if ch < len(rus):
				system("dunstify -t 0 -r %d -u low ' %s' '   %s'"%(EXAM_ID + i, rus[ch], chn[ch]))

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
					one = item.text
					out += one.replace('е"', 'ё') + '\t'
				decl = row.findAll("td")
				for item in decl:
					one = item.text
					out += one.replace('е"', 'ё').replace(', ', '/').replace('//', '/') + '\t'
				out += '\n'
			# out = rid_comma(out)
			if title and h3 and i<len(h3):
				out = adjust_tab(out[0:len(out)-1], h3[i].text)
			else:
				out = adjust_tab(out[0:len(out)-1], orgn)
			if not out in declist:
				declist.append(out)
		if declist:
			ind = 0
			system("dunstify -t 0 -r %d ' %s [%s] %s'"%(NOTIFY_ID, word, pron, trans))
			system("dunstify -t 0 -r %d '%s' ' pp. %d / %d'"%(GRAMM_ID, declist[ind], ind+1, len(declist)))

		file = "%s/%s.mp3"%(sound_path,word)
		if not os.path.exists(file):
			read = soup.find('a', class_='speaker')
			if read:
				# print(read['data-url'])
				system("dunstify -t 0 -r %d ' Восстановление произношения...'"%PLAY_ID)
				urlretrieve(read['data-url'], file)
			else:
				system("dunstify -t 0 -r %d ' %s [%s] %s'"%(NOTIFY_ID, word, pron, trans))
				system("dunstify -t 0 -r %d -u low ' Нет  .'"%PLAY_ID)
				exit()

		def read_word():
			system("dunstify -t 0 -r %d ' %s [%s] %s'"%(NOTIFY_ID, word, pron, trans))
			system("dunstify -t 0 -r %d -u low ' %s [%s]\t\t Press ⌘+⇧+o to browse online.'"%(PLAY_ID, word, pron))
			p = vlc.MediaPlayer(file)
			p.play()

		def on_press(key):
			COMBINATIONS = [
				{Key.shift, Key.cmd_l, KeyCode(char='o')},
    			{Key.shift, Key.cmd_l, KeyCode(char='O')}
			]
			global ind, offset, orgn, pron_orgn, expl, word, pron, trans
			# print('{0} release'.format(key))
			if any([key in COMBO for COMBO in COMBINATIONS]):
				current.add(key)
				if any(all(k in current for k in COMBO) for COMBO in COMBINATIONS):
					system("google-chrome-stable  --new-window %s"%url)
			if key in [Key.space]:
				p = vlc.MediaPlayer(file)
				p.play()
			if key in [Key.enter]:
				for i in range(EXAM_PER_PAGE):
					system("dunstify -C %d"%(EXAM_ID + i))
				system("dunstify -t 0 -r %d ' %s [%s] %s' '  %s'"%(DICT_ID, orgn, pron_orgn, trans, sel))
			if declist and key in [Key.right]:
				ind += 1
				if ind >= len(declist):
					ind = 0
				system("dunstify -t 0 -r %d '%s' ' pp. %d / %d'"%(GRAMM_ID, declist[ind], ind+1, len(declist)))
			if declist and key in [Key.left]:
				ind -= 1
				if ind < 0:
					ind = len(declist) - 1
				system("dunstify -t 0 -r %d '%s' ' pp. %d / %d'"%(GRAMM_ID, declist[ind], ind+1, len(declist)))
			if key in [Key.down]:
				system("dunstify -C %d"%DICT_ID)
				offset += EXAM_PER_PAGE
				for i in range(EXAM_PER_PAGE):
					ch = (i + offset) % len(rus)
					system("dunstify -t 0 -r %d -u low ' %s' '   %s'"%(EXAM_ID + i, rus[ch], chn[ch]))
			if key in [Key.up]:
				system("dunstify -C %d"%DICT_ID)
				offset -= EXAM_PER_PAGE
				for i in range(EXAM_PER_PAGE):
					ch = (i + offset) % len(rus)
					system("dunstify -t 0 -r %d -u low ' %s' '   %s'"%(EXAM_ID + i, rus[ch], chn[ch]))

		def on_release(key):
			if key in [Key.esc]:
				system("killall dunst")
				return False

		read_word()
		ind, offset = 0, 0
		current = set()
		with Listener(on_press=on_press, on_release=on_release) as listener:
			listener.join()