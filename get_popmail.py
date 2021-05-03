import poplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import base64
import os


def fetchmail(cli, msg_no):
    content = cli.retr(msg_no)[1]
    msg = email.message_from_bytes(b'\r\n'.join(content))
    from_ = get_header(msg, 'From')
    date = get_header(msg, 'Date')
    subject = get_header(msg, 'Subject')
    content = get_content(msg)
    return (subject, content, from_, date)


def get_header(msg, name):
    header = ''
    if msg[name]:
        for tup in decode_header(str(msg[name])):
            if type(tup[0]) is bytes:
                charset = tup[1]
                if charset:
                    header += tup[0].decode(tup[1])
                else:
                    header += tup[0].decode()
            elif type(tup[0]) is str:
                header += tup[0]
    return header


def get_content(msg):
    charset = msg.get_content_charset()
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_maintype()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text' and 'attachment' not in cdispo:
                payload = part.get_payload(decode=True)  # decode
                break
    else:
        payload = msg.get_payload(decode=True)
    try:
        if payload:
            if charset:
                return payload.decode(charset)
            else:
                return payload.decode()
        else:
            return ""
    except:
        return payload


def popup_subject(msg):
    subject, sender, date = msg[0].replace('\n',''), msg[2], msg[3]
    pos = date.find('+')
    day = date[0: pos - 10]
    hms = date[pos - 9: pos - 1]
    output = " %s\n %s  %s <%s>\n %s   %s"%(subject, sender, NAME[user], ADDRESS[user], day, hms)
    # print(output)
    os.system('notify-send -u critical "%s"'%(output))


def popup_content(msg):
    lines = msg[1].replace('\r','\n').split('\n')
    content = ""
    for i, line in enumerate(lines):
        print(len(line), line)
        if len(line)>=1:
            if len(line)<=1 and (i>1 and len(lines[i-1])<=1):
                continue
            content += '  ' + line + '\n'
    os.system('notify-send -u critical "%s"'%(content))


NAME = ['Lang Cao', 'Xun Li', 'Lang Cao']
ADDRESS = ['lcao@zzu.edu.cn', 'li_xun@ircn.jp', 'cao@ircn.jp']
PASSWORD = ['miaomiao1982', '20200608lixun', 'miaomiao1982']
SERVER = ['mail.v.zzu.edu.cn', 'ircn.sakura.ne.jp', 'ircn.sakura.ne.jp']

user = 0
cli = poplib.POP3(SERVER[user])
cli.user(ADDRESS[user])
cli.pass_(PASSWORD[user])

resp, mails, octets = cli.list()
index = len(mails)
msg = fetchmail(cli, index)
popup_subject(msg)
popup_content(msg)