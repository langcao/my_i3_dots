from urllib import request
from urllib.parse import quote
import html2text
import os
import sys
import datetime
from googletrans import Translator

cache_path = os.getenv("HOME")+"/.cache/jukuu/"
jukuu_cache = cache_path + "sentences.txt"
word_cache = cache_path + "words.txt"
log_cache = cache_path + "logs.txt"
del_cache = cache_path + "dels.txt"
lck_path = cache_path + "lck/"
out_cache = cache_path + "output.txt"

zenkaku = "。・．，；：！？＃＄％＆～（）［］｛｝＜＞‘’“”`「」『』＠＾＋－＊／｜０１２３４５６７８９"
hankaku = ".·.,;:!?#$%&~()[]{}<>''\"\"'''\"\"@^+-*/|0123456789"
punctuation = zenkaku + hankaku + ' '
zenkaku += "ＡＢＣＤＥＦＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
hankaku += "ABCDEFHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def strQ2B(ustring):
    """全角转半角"""
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 12288:                              #全角空格直接转换
            inside_code = 32
        elif (inside_code >= 65281 and inside_code <= 65374): #全角字符（除空格）根据关系转化
            inside_code -= 65248
        rstring += chr(inside_code)
    return rstring

def hankakufy(str, word = ""):
	zh = str.replace('\n','').replace('**','')
	for i in range(len(hankaku)):
		zh = zh.replace(zenkaku[i], hankaku[i])
	for c in ".,:/?":
		zh = zh.replace(c, c+' ')
	zh = zh.replace('"', '\\\"')
	if word != "":
		zh=zh.replace(word,''+word+'')
	return zh

def trailling(str):
	rid = "_'·,;:!?#$%&~()[]{}<>=`‘@^“”‘’+-*/|\n"+'"'
	rid += "。・．，；：！？＃＄％＆～（）［］｛｝＜＞＝｀‘＠＾『』「」＋－＊／｜"
	eng = str
	for i in range(len(rid)):
		eng = eng.replace(rid[i], '')
	return eng.lower().lstrip().rstrip()

def alphabet(str):
	eng = ''
	for c in str:
		l = c.lower()
		if l >= 'a' and l <= 'z' or l in [' ', '-']:
			eng += l
	return eng

def get_do(str):
	os.system('dunstify -u critical " Searching prototype of %s" ""'%(str))
	yuan = ''
	variants = ['的复数', '的第三人称单数', '的三单', '的ing形式', '的现在分词', '的比较级', '的最高级', '的过去式', '的过去分词', '的过去式和过去分词', '的过去式及过去分词']
	variants += ['复数', '第三人称单数', '三单', 'ing形式', '现在分词', '比较级', '最高级', '过去式', '过去分词', '过去式和过去分词', '过去式及过去分词']
	for variant in variants:
		cmd = "ydcv '%s' | grep -o '（.*%s' | sed 's\[（ ]\\\\g; s\%s\\\\g'"%(str, variant, variant)
		yuan = alphabet(os.popen(cmd).read())
		if yuan!='':
			if variant[0]!='的':
				variant += '的'
			os.system('dunstify -u critical " %s automatically transferred from %s" " %s 是 %s %s"'%(yuan, str, str, yuan, variant))
			break
	return yuan

def get_ju(str):
	line = str
	for c in '.,?!:':
		line = line.replace(c, c+' ')
	ju = ''
	first = False
	for c in line:
		if not c in [' ', '\t', '\n']:
			ju += c
			first = True
		else:
			if first:
				ju += ' '
				first = False
	ju = ju.rstrip()
	for c in '.,/?!':
		ju = ju.replace(' '+c, c)
		ju = ju.replace(c+' "', c+'"')
		ju = ju.replace(c+" '", c+"'")
	tot = 1
	for c in ju:
		if c == ' ':
			tot += 1
	return ju, tot

def get_ydcv(one, max_trail = 3):
	trail = 0
	while trail < max_trail:
		buff = os.popen('ydcv "%s"'%one)
		mean = buff.read()
		s = mean.find('Translation:\n')
		if s >= 0:
			mean = hankakufy(mean[s+17:-1]).replace("\\ '", "\'")
		if mean.find('Word Explanation:')>=0 or mean.find('Web Reference:')>=0:
			p1 = mean.find("] ")
			p2 = mean.find("\n")
			if p1 > 0:
				mean = hankakufy(mean[p1+2:p2])+' '
			else:
				mean = hankakufy(mean[len(one):p2])+' '
		if mean.find('No result for this query.') < 0:
			break
		else:
			trail += 1
	if trail == max_trail:
		mean = one
	return mean

def get_google(one):
	translation = Translator().translate(one, dest='zh-CN')
	return translation.text

def translate(para, emergence = 'normal'):
	lck_cache = lck_path + "Trans.lck"
	if os.path.isfile(lck_cache):
		os.system('dunstify -u low " Translation engine is occupied." "  Please wait a moment..."')
		return
	os.system('echo > %s'%lck_cache)
	jus, output = '', ''
	pos = 0
	last = len(para)
	para = strQ2B(para).replace('`',"'").replace('-',' ')
	os.system('pkill dunst')
	os.system('dunstify -u %s " Translation engine is triggered..."'%emergence)
	quote1 = False
	quote2 = False
	tot = 0
	while pos < last:
		one = ''
		skip = True
		while pos < last and not para[pos] in '?!;。？！；':
			if not para[pos] in punctuation:
				skip = False
			if para[pos] == '.':
				if pos > 2 and not para[pos-2] in punctuation:
					break
			if para[pos]=='"':
				one += '\\'
			one += para[pos]
			pos += 1
			if one[-1] == "'":
				quote1 = not quote1
			if one[-1] == '"':
				quote2 = not quote2
		if pos < last:
			one += para[pos]
			pos += 1
		if one[-1] == "'":
			quote1 = not quote1
		if one[-1] == '"':
			quote2 = not quote2
		while pos < last:
			if pos < last and quote1 and para[pos]=="'":
				one += '\\\''
				pos += 1
				quote1 = False
			if pos < last and quote2 and para[pos]=='"':
				one += '\\\"'
				pos += 1
				quote2 = False
			if pos < last and para[pos] in ' .?!;。？！；)}”’>[]0123456789':
				one += para[pos]
				pos += 1
			else:
				break
		if not skip:
			# mean = get_ydcv(one)
			mean = Translator().translate(one, dest='zh-CN').text
			os.system('dunstify -u %s " %s" "  %s"'%(emergence, one, mean))
			jus += one
			output += mean.lstrip()
			tot += 1
		elif one[0]!='.':
			os.system('dunstify -u %s " %s"'%(emergence, one))
	os.system('dunstify -u critical " Oringinal text:\n %s" " Translation:\n  %s"'%(jus, output))
	fo = open(out_cache, "w")
	fo.write(' Jukuu output text generated at %s\n\n'%datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
	output = jus + '\n\n' + output
	fo.write(output.replace('\\\"','"'))
	fo.close()
	os.system('rm %s'%lck_cache)

def normalize(str):
	line = hankakufy(str).replace('\\\"','"').replace('/','')
	for c in ".,;:?!([{<)]}>'\"":
		if line.find(c) >= 0:
			line = line.replace(c, ' %s '%c)
	words = line.split()
	current, sentence = '', ''
	quote1, quote2 = True, True
	pos = 0
	while pos <len(words):
		word = words[pos]
		pos += 1
		if word in '([{<':
			sentence += current
			current = word
		elif word in ')]}>':
			current += word
			sentence += current
			current = ''
		elif word in '.,;:?!':
			if current == '':
				sentence += word
			else:
				sentence += current + ' ' + word
				current = ''
		elif word == "'":
			if pos < len(words) and words[pos] in ['d', 'm', 's', 't', 'll', 're', 've']:
				sentence += current + "'" + words[pos]
				current = ''
				pos += 1
			else:
				if quote1:
					current += word
				else:
					sentence += current + word
					current = ''
				quote1 = not quote1
		elif word == '"':
			if quote2:
				current = word
			else:
				sentence += current + word
				current = ''
			quote2 = not quote2
		else:
			current += word
			sentence += ' ' + current
			current = ''
	out = sentence.lstrip()
	bra = '([{<'
	ket = ')]}>'
	for i in range(len(bra)):
		if out.find(bra[i]) < 0:
			out = out.rstrip(ket[i])
	return out

def google(str):
	baidu = 'https://fanyi.baidu.com/#en/zh/'
	guge = 'https://translate.google.cn/#view=home&op=translate&sl=auto&tl=zh-CN&text='
	url = 'https://www.google.com/search?q=' + str
	print(url)
	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"
		}
	req = request.Request(url, headers=headers)
	response = request.urlopen(req)
	data = response.read().decode('utf-8')
	h = html2text.HTML2Text()
	h.ignore_links = True
	content = h.handle(data)

	os.system('echo "%s" > 1'%content)
	fo = open(out_cache, "w")
	fo.write(content)
	fo.close()

	# with request.urlopen(url,) as file:
	# 	data = file.read().decode('utf-8')
	return content

def get_text(word, page, emergence = "normal", show = False):
	output = ""
	url = "http://www.jukuu.com/show-'%s'-%d.html"%(quote(word), page)
	with request.urlopen(url) as file:
		data = file.read().decode('utf-8')
	h = html2text.HTML2Text()
	h.ignore_links = True
	content = h.handle(data)

	for i in range(10):
		key = str(page*10+1+i)+'\. |  '
		p1 = content.find(key)
		if p1==-1:
			i -= 1
			break
		else:
			p1 += len(key)
		p2 = p1+content[p1:-1].find('|')
		eng = content[p1:p2].replace('\n',' ').replace('|',' ').replace('"',"'").replace('**','')
		eng = eng.replace(' ) ','')
		eng = eng.replace('![](images/detail.jpg','')
		eng = normalize(eng).replace(' ', ' ')
		output += str(page*10+1+i)+'. '+ eng
		p3 = p2+content[p2+1:-1].find('|')
		zh = hankakufy(content[p2+1:p3], word)
		zh = '  '+normalize(zh)
		output += '| '+zh+' |\n'
		if show:
			if page != 0 and i == 0:
				os.system('pkill dunst')
			os.system('dunstify -u %s " %s" " %s"'%(emergence, eng, zh))
	return output, i + 1

def get_jukuu(word, page = 0, emergence = "normal", save_cache = True):
	lck_cache = lck_path + "%s"%word
	os.system('echo > %s'%lck_cache)
	output = ""
	if page==0:
		buff = os.popen('ydcv "%s"'%(word))
		mean = buff.read()
		mean = "%s "%word + mean[len(word)+1:-1]
		os.system('pkill dunst')
		os.system('dunstify -u %s " Searching exemplary sentences of %s" "  %s"'%(emergence, word, mean))
		output += mean.replace('\n','|') + '\n'
	else:
		os.system('dunstify -u %s " Searching exemplary sentences of %s" " pp. %d / no. %d－%d"'%(emergence, word, page, page*10+1, page*10+10))
	if page==0 and save_cache:
		fj=open(jukuu_cache,'a')
		fj.write(output)

	one_page, showed_items = get_text(word, page, emergence, True)
	output += '\n'+one_page
	fo = open(out_cache, "w")
	fo.write(' Jukuu output text generated at %s\n\n'%datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
	output = output.replace('|','\n').replace('','').replace('\\\"','"').replace('\\ \"','"')
	fo.write(output)
	fo.close()
	# os.popen("sed -i 's/\s*$//; s/[ ]*[.]/./g; s/[ ]*[ ]/ /g' %s"%out_cache)
	if page==0 and save_cache:
		fj.write(one_page)

	if showed_items == 0:
		os.system('dunstify -u critical " Search engine failed to provide exemplary sentences!" "  对不起，搜索引擎无法提供 %s 的相关例句！"'%(word))
		pp = -1
	else:
		if page==0 and save_cache:
			fo = open(out_cache, "a")
			for pp in range(1,10):
				one_page, count = get_text(word, pp)
				fj.write(one_page)
				output = one_page.replace('|','\n').replace('','').replace('\\\"','"').replace('\\ \"','"')
				fo.write(output)
				if count > 0:
					showed_items += count
				else:
					pp -= 1
					break
			fj.write('\n')
			fj.close()
		os.system('dunstify -u critical " %s  %d exemplary sentences found." "  Pleases press PageUp/Dowm or Numkeys (0～%d)."'%(word, showed_items, pp))
		rectime = datetime.datetime.now().strftime('[%H:%M:%S][%Y-%m-%d (%j,%U)]')
		os.system("sed -i '$a [%2.d/%3.d]%s   %s' %s"%(pp+1, showed_items, rectime, word, word_cache))
	fo.close()
	os.system('rm %s'%lck_cache)


def find_cache(word, page, emergence, save_cache):
	buff = os.popen('grep "%s" %s'%(word,word_cache))
	if buff.read()=="":
		get_jukuu(word, page, emergence, save_cache)
	else:
		get_cache(word, page, emergence)
		os.popen("sed -i '0,/<%s>/{/<%s>/d;}' %s"%(word, word, word_cache))
	pages = int(os.popen("grep '%s' %s | sed 's/^\[//g; s/\/.*//g'"%(word, word_cache)).read())
	line = '<%s> -%d/%d- %s\n'%(word, page, pages, datetime.datetime.now())
	os.popen("sed -i '$a %s' %s"%(line, log_cache))

def get_cache(word, page, emergence):
	output = ""
	buff = os.popen('grep -i "%s " %s'%(word, jukuu_cache))
	mean = buff.read().replace('|','\n').replace('%s'%word, '')
	output += mean +'\n\n'
	if page==0:
		os.system('pkill dunst')
		os.system('dunstify -u %s " Searching exemplary sentences of %s" "  %s"'%(emergence, word, mean))
	else:
		os.system('dunstify -u %s " Searching exemplary sentences of %s" ""'%(emergence, word))
	buff = os.popen('grep -i "%s" %s'%(word, jukuu_cache))
	content = buff.read()
	output += content
	buff = os.popen('grep -i "%s" %s'%(word, out_cache))
	has = buff.read()
	if has == "":
		fo = open(out_cache, "w")
		fo.write(' Jukuu output text generated at %s\n\n'%datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		output = output.replace('|','\n').replace('','').replace('\\\"','"')
		fo.write(output)
		fo.close()

	for i in range(10):
		key = str(page*10+1+i)+'. '
		p1 = content.find(key)
		if p1==-1:
			i -= 1
			break
		else:
			p1 += len(key)
		p2 = p1+content[p1:-1].find('|')
		eng = content[p1:p2]
		p3 = p2+content[p2+1:-1].find('\n')
		if p3 < p2:
			p3 = -1
		zh = content[p2+2:p3]
		if page != 0 and i == 0:
			os.system('pkill dunst')
		os.system('dunstify -u %s " %s" " %s"'%(emergence, eng, zh))
	if i == -1:
		os.system('dunstify -u %s " Search engine falied to provide exemplary sentences" " pp. %d / 搜索引擎已无更多 %s 的相关例句！"'%(emergence, page, word))
	else:
		pages = os.popen("grep '%s' %s | sed 's/^\[//g; s/\/.*//g'"%(word, word_cache)).read()
		pages = pages.replace('\n', '')
		os.system('dunstify -u %s " Exemplary sentences of %s" " pp. %d/%s, no. %d－%d"'%(emergence, word, page, pages, page*10+1, page*10+i+1))

def main():
	if not os.path.isdir(cache_path):
		os.mkdir(cache_path)
		os.mkdir(cache_path+'lck')
		os.system(r"touch {}".format(jukuu_cache))
		os.system(r"touch {}".format(del_cache))
		os.system(r"touch {}".format(out_cache))
		os.system("echo 'Wordlist of %s. Let’s Review！\n' > %s"%(datetime.date.today(), word_cache))
		os.system("echo 'Wordlist .log file created by fandy, %s' > %s"%(datetime.date.today(), log_cache))
	argvs = sys.argv
	word = argvs[1]
	if word=='':
		buff = os.popen('xclip -o')
		line = buff.read()
		ju, tot = get_ju(line)
		if tot > 3 or len(ju) > 30:
			translate(ju)
			return
		word = trailling(line)
	if word=='':
		buff = os.popen('xclip -o')
		line = buff.read()
		ju, tot = get_ju(line)
		if tot > 5 or len(ju) > 30:
			translate(ju, 'critical')
			return
		yuan = get_do(trailling(line))
		if yuan != '':
			word = yuan
		else:
			word = line
	if word == '':
		buff = os.popen('tail -1 %s'%(log_cache))
		line = buff.read()
		pos = line.find("> ")
		if pos > -1:
			word = line[1:pos]
			if os.path.isfile(cache_path + "lck/%s"%word):
				os.system('dunstify -u low " Searching exemplary sentences of %s" "  Please wait a moment for retrieving..."'%(word))
				return
			os.system("sed -i '/<%s>/d' %s"%(word, log_cache))
			os.system("sed -i '/%s/d' %s"%(word, word_cache))
			os.system("sed -i '/%s/d' %s"%(word, jukuu_cache))
			os.system("sed -i '/%s/d' %s"%(word, jukuu_cache))
			os.system("echo '%s' >> %s"%(word, del_cache))
			os.system('dunstify -u critical " %s is removed from Wordlist." "   Right click to undo."'%(word))
		else:
			os.system('dunstify -u critical " Wordlist is empty now." ""')
		return
	if word == '':
		buff = os.popen('tail -1 %s'%(del_cache))
		word = trailling(buff.read())
		if word != "":
			os.system("sed -i '/%s/d' %s"%(word, del_cache))
			find_cache(word, 0, "normal", True)
		else:
			os.system('dunstify -u critical " No more word in Trash." ""')
		return
	if word == '':
		buff = os.popen('tail -1 %s'%(del_cache))
		word = trailling(buff.read())
		if word != "":
			os.system("sed -i '/%s/d' %s"%(word, del_cache))
			os.system('dunstify -u critical " %s is removed from Trash." ""'%(word))
		else:
			os.system('dunstify -u critical " No more word in Trash." ""')
		return
	if word=='':
		buff = os.popen('tail -1 %s'%(log_cache))
		line = buff.read()
		pos = line.find("> ")
		if pos < 0:
			os.system('dunstify " Wordlist is empty. Please select word." "  本地词库为空, 请您选择待查单词进行添加."')
			return
		word = line[1:pos]
	if os.path.isfile(cache_path + "lck/%s"%word):
		os.system('dunstify -u low " Searching exemplary sentences of %s" "  Please wait a moment for retrieving..."'%(word))
		return
	if word in ['', '']:
		os.popen('xclip -i /dev/null')
		buff = os.popen('tail -1 %s'%(log_cache))
		line = buff.read()
		pos = line.find("> ")
		prev = line[1:pos]
		buff = os.popen('grep -1 "%s" %s'%(prev, word_cache))
		line = buff.read()
		pos1 = line.find("")+1
		if pos1 == 0:
			os.system('dunstify " Wordlist is empty. Please select word." "  本地词库为空, 请您选择待查单词进行添加."')
			return
		pos2 = pos1+line[pos1:-1].find("")
		if word == '':
			word = line[pos1:pos2]
			if word == prev:
				buff = os.popen('tail -1 %s'%(word_cache))
				line = buff.read()
				pos1 = line.find("")+1
				pos2 = pos1+line[pos1:-1].find("")
				word = line[pos1:pos2]
		if word == '':
			pos1 = pos2+line[pos2+1:-1].find("")+2
			if pos1 > pos2 + 1:
				pos2 = pos1 + line[pos1:-1].find("")
				word = line[pos1:pos2]
			pos1 = pos2+line[pos2+1:-1].find("")+2
			if pos1 > pos2 + 1:
				pos2 = pos1 + line[pos1:-1].find("")
				word = line[pos1:pos2]
			if word in [prev, '']:
				buff = os.popen('head -3 %s'%(word_cache))
				line = buff.read()
				pos1 = line.find("")+1
				pos2 = pos1+line[pos1:-1].find("")
				word = line[pos1:pos2]
	if word == '':
		os.system('pkill dunst')
		if len(argvs)==2:
			cmd = "sed '/^[^\[]/d; s/\[.*\]//g; /^$/d; s/ //g' %s  | sort; ls -1 %s | sed 's/.*/&/g' "%(word_cache, lck_path)
			buff = os.popen(cmd)
			line = buff.read().replace('\n', '   ')
			if line == "":
				line = '  Empty now.'
			os.system('dunstify " Vocabulary list" "%s"'%line)
		else:
			interval = argvs[2]
			if len(argvs) > 3:
				emergence = argvs[3]
			else:
				emergence = 'normal'
			cmd = "sed '/^[^\[]/d; s/\[.*\]//g; /^$/d; s/ //g' | sort"
			if interval=='minute':
				m_str = datetime.datetime.now().strftime('%H:%M:[0-9][0-9]..%Y-%m-%d')
				buff = os.popen('grep "%s" %s | %s; ls -1 %s | sed "s/.*/&/g"'%(m_str, word_cache, cmd, lck_path))
				line = buff.read()
				if line == "":
					line = '  Empty now.'
				os.system('dunstify -u %s " Vocabulary list (last %s)" "%s"'%(emergence, interval, line))
			elif interval=='hour':
				h_str = datetime.datetime.now().strftime('%H:[0-9][0-9]:[0-9][0-9]..%Y-%m-%d')
				buff = os.popen('grep "%s" %s | %s; ls -1 %s | sed "s/.*/&/g"'%(h_str, word_cache, cmd, lck_path))
				line = buff.read()
				if line == "":
					line = '  Empty now.'
				os.system('dunstify -u %s " Vocabulary list (last %s)" "%s"'%(emergence, interval, line))
			elif interval=='day':
				d_str = datetime.datetime.now().strftime('%Y-%m-%d')
				buff = os.popen('grep "%s" %s | %s; ls -1 %s | sed "s/.*/&/g"'%(d_str, word_cache, cmd, lck_path))
				line = buff.read()
				if line == "":
					line = '  Empty now.'
				os.system('dunstify -u %s " Vocabulary list (last %s)" "%s"'%(emergence, interval, line))
			elif interval=='week':
				w_str = datetime.datetime.now().strftime('(...,%U)')
				buff = os.popen('grep "%s" %s | %s; ls -1 %s | sed "s/.*/&/g"'%(w_str, word_cache, cmd, lck_path))
				line = buff.read().replace('\n', '   ')
				if line == "":
					line = '  Empty now.'
				os.system('dunstify -u %s " Vocabulary list (last %s)" "%s"'%(emergence, interval, line))
			elif interval=='month':
				m_str = datetime.datetime.now().strftime('%Y-%m')
				buff = os.popen('grep "%s" %s | %s; ls -1 %s | sed "s/.*/&/g"'%(m_str, word_cache, cmd, lck_path))
				line = buff.read().replace('\n', '   ')
				if line == "":
					line = '  Empty now.'
				os.system('dunstify -u %s " Vocabulary list (last %s)" "%s"'%(emergence, interval, line))
			elif interval=='year':
				y_str = datetime.datetime.now().strftime('%Y-')
				buff = os.popen('grep "%s" %s | %s; ls -1 %s | sed "s/.*/&/g"'%(y_str, word_cache, cmd, lck_path))
				line = buff.read().replace('\n', '   ')
				if line == "":
					line = '  Empty now.'
				os.system('dunstify -u %s " Vocabulary list (last %s)" "%s"'%(emergence, interval, line))
			elif interval=='sorted':
				cmd = "sed '/^[^\[]/d; s/\[.*\]//g; /^$/d; s/ //g' %s | sort; ls -1 %s | sed 's/.*/&/g' "%(word_cache, lck_path)
				buff = os.popen(cmd)
				line = buff.read().replace('\n', '   ')
				if line == "":
					line = '  Empty now.'
				os.system('dunstify -u %s " Vocabulary list (%s order)" "%s"'%(emergence, interval, line))
			elif interval=='inversed':
				cmd = "sed '/^[^\[]/d; s/\[.*\]//g; /^$/d; s/ //g' %s | sort | tac; ls -1 %s | sed 's/.*/&/g' "%(word_cache, lck_path)
				buff = os.popen(cmd)
				line = buff.read().replace('\n', '   ')
				if line == "":
					line = '  Empty now.'
				os.system('dunstify -u %s " Vocabulary list (%s order)" "%s"'%(emergence, interval, line))
			elif interval=='':
				buff = os.popen("tac %s"%del_cache)
				line = buff.read().replace('\n', '   ')
				if line == "":
					line = '  Empty now.'
				os.system('dunstify -u %s " Wordlist in Trash" "%s"'%(emergence, line))
			else:
				cmd = "sed '/^[^\[]/d; s/\[.*\]//g; /^$/d; s/ //g' %s | tac; ls -1 %s | sed 's/.*/&/g' "%(word_cache, lck_path)
				buff = os.popen(cmd)
				line = buff.read().replace('\n', '   ')
				if line == "":
					line = '  Empty now.'
				os.system('dunstify -u %s " Vocabulary list (%s order)" "%s"'%(emergence, interval, line))
		return
	if word == '':
		user = os.popen("whoami").read().replace('\n', '')
		cmd = "ps -ef | grep 'get_jukuu.py' | grep python | grep -v  | sed 's/^%s[ ]*//g; s/[ ].*$//g'"%user
		pids = os.popen(cmd).read().split()
		for pid in pids:
			os.popen("kill %s"%pid)
		os.popen("pkill dunst")
		os.popen('rm %s*'%lck_path)
		return
	if len(argvs)==2:
		find_cache(word, 0, "normal", True)
	else:
		if argvs[2] in ['', 'PageUp', 'PageDown']:
			os.popen('xclip -i /dev/null')
			buff = os.popen('grep -i "<%s>" %s | tail -1'%(word, log_cache))
			line = buff.read()
			pos = len("<%s> -"%word)
			page = int(line[pos:pos+1])
			if argvs[2]!='':
				if argvs[2]=='PageUp':
					page -= 1
				else:
					page += 1
				buff = os.popen('grep -i "%s" %s | tail -1'%(word, word_cache))
				line = buff.read()
				tot = int(line[1:3])
				if tot > 0:
					page %= tot
				else:
					page = 0
		else:
			page = int(argvs[2])
		if len(argvs)==3:
			find_cache(word, page, "normal", False)
		else:
			emergence = argvs[3]
			if len(argvs)==4:
				find_cache(word, page, emergence, False)
			else:
				save_cache = int(argvs[4])
				find_cache(word, page, emergence, save_cache)

if __name__ == "__main__":
    main()
    # print(google(sys.argv[1]))