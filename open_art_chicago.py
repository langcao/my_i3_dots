from os.path import exists
from os import system

path = '/home/milklee/.config/i3/'
path_to = '/home/milklee/Pictures/Artworks/'
filename = ''
if exists('%s.art.shw'%path):
	with open(path+'.art.txt') as f:
		filename += f.read()
else:
	with open(path+'.temp.txt') as f:
		filename += f.read()
filename = filename.replace('\n', ' ') + '.jpg'
filename =  path_to + filename.replace('\n','').replace(' ','_').replace('(','[').replace(')',']').replace('/','￥').replace(';','；').replace('\'','’').replace('"','”')
if exists(filename):
	system('feh %s'%(filename))