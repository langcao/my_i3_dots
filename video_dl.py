import sys, os

args = sys.argv
name = args[1]
if len(args)>2:
	offset = int(args[2])
else:
	offset = 1
print(name)
notify_id = 3526178

with open(name) as f:
	lines = f.readlines()

for i, line in enumerate(lines):
	cmd = "youtube-dl -f best -o '%s%d.%%(ext)s' %s"%(name, i+offset	 , line)
	print(cmd)
	os.system('dunstify -r %d -u critical "Downloading %s%d" "%s"'%(notify_id, name, i+offset, line))
	os.system(cmd)

os.system('dunstify -C %d'%notify_id)