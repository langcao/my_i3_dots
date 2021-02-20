from os import system

path = '/home/milklee/Pictures/Artworks/'
path_to = '/home/milklee/.config/i3/'
system('ls %s | shuf -n 1 | sed \'s/\\.[^.]*$//\' > %s.temp.txt'%(path, path_to))
f = open('%s.temp.txt'%path_to)
filename = f.read()
system('feh --bg-max %s%s'%(path,filename.replace(' ','_').replace('\n','.jpg')))
system('pkill dunst')
system('dunstify "%s"'%(filename.replace('_',' ').replace('','\n').replace('','\n').replace('', '\n').replace('[','(').replace(']',')').replace('￥','/').replace('；',';').replace('’','\'').replace('”','\\"').replace('＆','&')))
system('rm %s.art.shw'%path_to)
