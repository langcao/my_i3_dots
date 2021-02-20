from requests_html import HTMLSession
from time import sleep
from random import choice
from os import system

session = HTMLSession()
text = session.get('https://bbs.fudan.edu.cn/v18/tdoc?board=Joke').text
pos = 0
sel = []
while True:
    s = text.find('繁', pos)
    if s < 0:
        break
    else:
        sel.append(s)
        pos = s + 1
# pos = sel[-1]
pos = choice(sel)
joke = text[pos-21:pos-2]
url = 'https://bbs.fudan.edu.cn/v18/tcon?new=1&bid=67&f=' + joke
res = session.get(url).html.text
start = res.find('Joke')+4
end = res.find('--')
pieces = res[start:end].split()
st = ''
maxlen = 0
for piece in pieces[3:len(pieces)]:
    if maxlen < len(piece):
        maxlen = len(piece)
    if piece[0] in '0123456789' and piece.find('、'):
        skip = piece.find('、')
        st += '\n'+piece[skip+1:-1]+'\n'
    else:
        st += piece+'\n'
title = pieces[0] + ' ' + pieces[1] + ' ' + pieces[2] + ' @ bbs.fudan.edu.cn '
if maxlen > 70:
    system('exec zenity --info --title="%s" --text="<big><big>%s</big></big>" --width=1000'%(title, st[1:-1]))
else:
    system('exec zenity --info --title="%s" --text="<big><big>%s</big></big>" --no-wrap'%(title, st[1:-1]))
