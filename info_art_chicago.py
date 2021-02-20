from os import system
from os.path import exists

path = '/home/milklee/Pictures/Artworks/'
path_to = '/home/milklee/.config/i3/'
if exists('%s.art.shw'%path_to):
	system('dunstify "$(cat %s.art.txt)"'%path_to)
else:
	f = open('%s.temp.txt'%path_to)
	filename = f.read()
	filename = filename.replace(' ','_').replace('\n','')
	system('exec pkill zenity')
	system('exec zenity --info --title="Artwork Info" --text="<big><big>%s</big></big>" --no-wrap'%(filename.replace('_',' ').replace('','\n').replace('[','(').replace(']',')').replace('￥','/').replace('；',';').replace('’','\'').replace('”','"')))