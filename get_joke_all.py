from requests_html import HTMLSession
from time import sleep
from random import choice
from os import system

session = HTMLSession()
page = choice(range(2974,4666,20))
# for page in range(range(2974,4706):
text = session.get('https://bbs.fudan.edu.cn/bbs/tdoc?bid=67&start=' + str(page)).text
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
print(page, sel)
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

print(st)