from pycmus import remote
from os import system
from os.path import exists
import sys
import subprocess

if exists('/tmp/cmus_lyrics.lck'):
	print('lck')
	sys.exit()
else:
	system('touch /tmp/cmus_lyrics.lck')

try:
	cmus = remote.PyCmus()
except:
	system('dunstify -r %d  -u low" Cmus is not running. "'%tag)
	system('rm /tmp/cmus_lyrics.lck')
	sys.exit()

title = ''
ind = -1
tag = 779 # Notification ID for Lyrics
system('dunstify -r %d -u critical " Lyrics file is loading..."'%tag)
while True:
	flag = True
	try:
		dic = cmus.get_status_dict()
		pos = int(dic['position'])
	except:
		system('dunstify -r %d -u low " Lyrics is now stopped. "'%tag)
		flag = False

	if flag and not dic['tag']['title']==title:
		try:
			print(dic['tag']['title'])
			filename = "/home/milklee/.config/lyrics/%s.lrc"%dic['tag']['title']
			f = open(filename)
			data = f.read()
			f.close()
			title = dic['tag']['title']
			lines = data.split('\n')
			times = []
			lrc = []
			for line in lines:
				if line.find('[')==0:
					times.append(int(line[1:3])*60+int(line[4:6])+int(line[7:9])/100)
					lrc.append(line[line.find(']')+1:len(line)])
		except:
			system('dunstify -r %d -u low " Lyrics file not found. "'%tag)
			# system('dunstify -C %d'%tag)				
			flag = False
	
	if flag:
		prev = ind
		ind = -1
		while ind < len(lrc)-1 and pos > times[ind+1]:
			ind += 1
		if not ind==prev:
			if ind >=0 and ind < len(lrc)-1:
				system('dunstify -r %d -u critical "♪ %s" "   %s ♪"'%(tag, lrc[ind]+' ', lrc[ind+1]))
			else:
				if ind==-1:
					system('dunstify -r %d -u critical "♪ %s ♪"'%(tag, lrc[0]))
				else:
					system('dunstify -r %d -u critical "♪ %s ♪"'%(tag, lrc[ind]))