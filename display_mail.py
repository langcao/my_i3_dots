import imaplib
import sys, os
NAME = ['Lang Cao', 'Xun Li', 'Lang Cao', 'Lang Cao', 'Xun Li']
ADDRESS = ['lcao@zzu.edu.cn', 'li_xun@ircn.jp', 'cao@ircn.jp', 'lcao@g.ecc.u-tokyo.ac.jp', 'milkquick@gmail.com']
PASSWORD = ['miaomiao1982', '20200608lixun', 'miaomiao1982','miaomiao-1982', 'kkmiudnpygdsyflj']
SERVER = ['mail.v.zzu.edu.cn', 'ircn.sakura.ne.jp', 'ircn.sakura.ne.jp', 'imap.gmail.com', 'imap.gmail.com']

DEFAULT_USER = 0
SHOW_NUM = 10
DEFAULT_PAGE = 0
EMAIL_PATH = '/tmp/emails/'
CURR_USER = EMAIL_PATH + 'current_user.txt'
MAIL_NUM = EMAIL_PATH + 'new_mail_num.txt'
LCK_FLAG = EMAIL_PATH + 'receiving.lck'
SHOW_FLAG = EMAIL_PATH + 'showing.lck'
HEAD_ID=23100
TEXT_ID=23200

if not os.path.exists(SHOW_FLAG):
    os.system('touch %s'%(SHOW_FLAG))

    if not os.path.exists(CURR_USER):
        os.system('echo "%d" > %s'%(DEFAULT_USER, CURR_USER))
        for _ in NAME:
            os.system('echo "%s" >> %s'%(DEFAULT_PAGE, CURR_USER))

    with open(CURR_USER, "r") as f:
        text = f.readlines()
    f.close()
    user = int(text[0])
    pages = [int(text[i+1]) for i,_ in enumerate(NAME)]
    page = pages[user]

    if len(sys.argv)>1:
        if sys.argv[1] == 'prev':
            if user > 0:
                user -= 1
            else:
                user = len(NAME) - 1
            page = pages[user]
        elif sys.argv[1] == 'next':
            if user < len(NAME) - 1:
                user += 1
            else:
                user = 0
            page = pages[user]
        elif sys.argv[1] == 'up':
            if page > 0:
                page -= 1
            else:
                page = SHOW_NUM - 1
            pages[user] = page
        elif sys.argv[1] == 'down':
            if page < SHOW_NUM - 1:
                page +=1
            else:
                page = 0
            pages[user] = page

        os.system('echo "%d" > %s'%(user, CURR_USER))
        for pp in pages:
            os.system('echo "%d" >> %s'%(pp, CURR_USER))

    if os.path.exists(LCK_FLAG):
        print(" %s (checking...)"%(ADDRESS[user]))
    else:
        with open(MAIL_NUM, "r") as f:
            num = f.readlines()
        f.close()
        print(" %s (%d)"%(ADDRESS[user], int(num[user])))

    if len(sys.argv)>1:
        filename = EMAIL_PATH + ADDRESS[user] + '/header_%d'%page
        os.system('dunstify -r %d -u critical "$(cat %s)"'%(HEAD_ID, filename))
        filename = EMAIL_PATH + ADDRESS[user] + '/content_%d'%page
        os.system('dunstify -r %d -u low "$(cat %s)"'%(TEXT_ID, filename))

    os.system('rm %s'%(SHOW_FLAG))
else:
    print(" Checking too frequently...")