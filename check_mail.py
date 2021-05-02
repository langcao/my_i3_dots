import imaplib
import sys, os, datetime
import timeout_decorator
from numpy import loadtxt

NAME = ['Lang Cao', 'Xun Li', 'Lang Cao', 'Lang Cao', 'Xun Li']
ADDRESS = ['lcao@zzu.edu.cn', 'li_xun@ircn.jp', 'cao@ircn.jp', 'lcao@g.ecc.u-tokyo.ac.jp', 'milkquick@gmail.com']
PASSWORD = ['miaomiao1982', '20200608lixun', 'miaomiao1982','miaomiao-1982', 'kkmiudnpygdsyflj']
SERVER = ['mail.v.zzu.edu.cn', 'ircn.sakura.ne.jp', 'ircn.sakura.ne.jp', 'imap.gmail.com', 'imap.gmail.com']

EMAIL_PATH = '/tmp/emails/'
MAIL_NUM = EMAIL_PATH + 'new_mail_num.txt'
LCK_FLAG = EMAIL_PATH + 'receiving.lck'

@timeout_decorator.timeout(120, timeout_exception=StopIteration)
def check():
	if not os.path.exists(EMAIL_PATH):
		os.system('python ~/.i3/save_mail.py')

	if not os.path.exists(LCK_FLAG):
		os.system('touch %s'%(LCK_FLAG))

		now = datetime.datetime.now()
		moment = str(now.time())
		print(moment[0:moment.find('.')-3])

		if os.path.exists(MAIL_NUM):
			news = loadtxt(MAIL_NUM)
		else:
			news = [-1 for _ in NAME]

		try:
			with open(MAIL_NUM, "w") as f:
				for user, _ in enumerate(ADDRESS):
					imapobj = imaplib.IMAP4_SSL(SERVER[user], '993')
					imapobj.login(ADDRESS[user], PASSWORD[user])

					imapobj.select()
					typ, data = imapobj.search(None, 'Unseen')
					num = len(data[0].split())
					f.write("%d\n"%num)
					if num > news[user]:
						os.system('python ~/.i3/save_mail.py %d'%user)
						if news[user] >= 0:
							os.system('dunstify -r %d -u critical "✉ %d New message(s)  %s %s"'%(321567+user, num-news[user], moment[0:moment.find('.')-3], ADDRESS[user]))
						else:
							os.system('dunstify -r %d -u low "✉ %d Unseen message(s)  %s %s"'%(321567+user, num, moment[0:moment.find('.')-3], ADDRESS[user]))
				imapobj.close()
		except:
			print('Timeout...')
			os.system('rm %s'%(MAIL_NUM))
			f.close()
			os.system('rm %s'%(LCK_FLAG))
		else:
			print('Success!')
			f.close()
			os.system('rm %s'%(LCK_FLAG))

if __name__ == '__main__':
	check()