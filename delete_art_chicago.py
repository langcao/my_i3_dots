from os import system
from os.path import exists

path = '/home/milklee/Pictures/Artworks/'
path_to = '/home/milklee/.config/i3/'

if exists('%s.art.shw'%path_to):
	filename = ''
	with open(path_to+'.art.txt') as f:
		filename += f.read()
	filename = filename.replace('\n', '')
	filename = filename.replace(' ','_').replace('\n','').replace('(','[').replace(')',']').replace('/','￥').replace(';','；').replace('\'','’').replace('"','”').replace('&','＆')
else:
	f = open('%s.temp.txt'%path_to)
	filename = f.read()
	filename = filename.replace(' ','_').replace('\n','')
print(filename)
full = '%s%s.jpg'%(path, filename)
print(full)
if exists(full):
	system('dunstify -u low " Remove pricture from %s"'%(path))
	system('rm %s'%full)
	# Load
	system('ls %s | shuf -n 1 | sed \'s/\\.[^.]*$//\' > %s.temp.txt'%(path, path_to))
	f = open('%s.temp.txt'%path_to)
	filename = f.read()
	system('feh --bg-max %s%s'%(path,filename.replace(' ','_').replace('\n','.jpg')))
	system('xdotool key ctrl+shift+space')
	system('dunstify "%s"'%(filename.replace('_',' ').replace('','\n').replace('','\n').replace('', '\n').replace('[','(').replace(']',')').replace('￥','/').replace('；',';').replace('’','\'').replace('”','\\"').replace('＆','&')))
	if exists('%s.art.shw'%path_to):
		system('rm %s.art.shw'%path_to)
else:
	system('dunstify -u low " Already absent in %s"'%(path))
