from pycmus import remote
from os import system
import sys
import time
from pynput import mouse
from pynput.mouse import Listener

def on_move(x, y):
    pass

def on_click(x, y, button, pressed):
	global start, index, lrc, title
	try:
		cmus = remote.PyCmus()
	except:
		system('dunstify -u critical "  Cmus is not running."')
		sys.exit()

	try:
		title = cmus.get_status_dict()['tag']['title']
		print(title)
		filename = "/home/milklee/.config/lyrics/temp.lrc"
		f = open(filename)
		data = f.read()
		f.close()
	except:
		system('dunstify -u critical "  Lyrics file not found."')
		sys.exit()

	lrc = data.split('\n')
	cmus.player_play()
	start = time.time()
	index = 0

def on_scroll(x, y, dx, dy):
	global start, index, lrc, title
	elapse = time.time() - start
	m = int(elapse/60)
	if m < 10:
		mm = '0'+str(m)
	else:
		mm = str(m)
	s = int(elapse - m*60)
	if s < 10:
		ss = '0'+str(s)
	else:
		ss = str(s)
	d = int((elapse - int(elapse))*100)
	if d < 10:
		dd = '0'+str(d)
	else:
		dd = str(d)
	line = '[%s:%s.%s]%s'%(mm,ss,dd,lrc[index])
	filename = "/home/milklee/.config/lyrics/%s_.lrc"%title
	filename = "/home/milklee/.config/lyrics/temp_.lrc"
	print(line)
	system('echo "%s" >> %s'%(line, filename))
	index += 1
	if index==len(lrc):
		print('Lyrics is saved to %s'%filename)
		sys.exit()


with Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
	listener.join()