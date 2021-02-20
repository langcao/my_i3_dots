from os.path import exists
from os import system

path = '/home/milklee/.config/i3/'
path_to = '/home/milklee/Pictures/Artworks/'

filename = ''
with open(path+'.art.txt') as f:
	filename += f.read()
filename = filename.replace('\n', '').replace('\n', '').replace('\n', '') + '.jpg'
filename =  path_to + filename.replace(' ','_').replace('(','[').replace(')',']').replace('/','￥').replace(';','；').replace('\'','’').replace('"','”').replace('&','＆')
print(filename)
if exists(filename):
	system('dunstify -u low " Already present in %s"'%(path_to))
else:
	system('dunstify -u low " Saving artworks to %s"'%(path_to))
	system('cp %s.art.jpg %s'%(path, filename))