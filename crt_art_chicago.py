from os import system
from os.path import exists

path = '/home/milklee/.config/i3/'
if not exists('%s.art.shw'%path):
	system('touch %s.art.shw'%path)
	system('feh --randomize --bg-max %s.art.jpg'%path)
	system('xdotool key ctrl+shift+space')
	system('dunstify "$(cat %s.art.txt)"'%path)