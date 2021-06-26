import imaplib
import email
import base64
import quopri
import codecs
import unicodedata
import os, sys, re
from email.header import decode_header, make_header
from mail_head import *


SHOW_NUM = 10

EMAIL_PATH = '/tmp/emails/'
if not os.path.exists(EMAIL_PATH):
    os.system('mkdir %s'%EMAIL_PATH)
for add in ADDRESS:
    if not os.path.exists(EMAIL_PATH + add):
        os.system('mkdir %s'%(EMAIL_PATH + add))

def get_content(msg):
    charset = msg.get_content_charset()
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_maintype()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text' and 'attachment' not in cdispo:
                payload = part.get_payload(decode=True)
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


def split_content(content, attach_count, maxrow=40, maxcol=144):
    if isinstance(content, str):
        content = re.sub(r'<.*?>', '', content)
        lines = content.split('\n')
    else:
        temp = codecs.decode(content, encoding="ISO-8859-1")
        lines = temp.split('\n')

    filename = EMAIL_PATH + ADDRESS[user] + '/content_%d'%note_id
    f = open(filename, 'w')

    current = 0
    omitted = ""
    prev_empty = True
    for i, line in enumerate(lines):
        text = ""
        if current >= maxrow - attach_count:
            # text += '⋮║ The orininal mail has more %d line(s) omitted.'%(len(lines) - current)
            omitted = ' The orininal mail has more %d line(s) omitted.'%(len(lines) - current)
            break
        if len(line)<2 and (i>1 and len(lines[i-1])<2):
            continue
        if len(line)>1:
            pos = len(line)
            while pos>0 and line[pos-1] in ['\n', '\r']:
                pos -= 1
            if pos>0:
                if current == 0:
                    text = ' ' + line[0:pos]+'\n'
                else:
                    text = '  ' + line[0:pos]+'\n'
                for c in line:
                    if unicodedata.east_asian_width(c) in ['F', 'W']:
                        pos += 1
                current += 1+ int(pos/maxcol)
                prev_empty = True
        elif prev_empty:
            text = '\n'
            current += 1
            prev_empty = False

        f.write(text.replace('"',"”").replace("'",'’'))

    f.write(omitted)
    f.close()

args = sys.argv

for user, _ in enumerate(ADDRESS):

    if len(args)>1:
        user = int(args[1])

    imapobj = imaplib.IMAP4_SSL(SERVER[user], '993')
    imapobj.login(ADDRESS[user], PASSWORD[user])

    imapobj.select()
    typ, data = imapobj.search(None, 'ALL')
    NEW_NUM=len(data[0])

    select = data[0].split()
    for note_id in range(min(NEW_NUM, SHOW_NUM)):
        output = " %s <%s> (%d)\n"%(NAME[user], ADDRESS[user], note_id+1)

        num = select[-note_id-1]
        typ, data = imapobj.fetch(num, '(RFC822)')
        try:
        	mail = email.message_from_string(data[0][1].decode('utf-8'))
        except:
        	mail = email.message_from_string(data[0][1].decode('ISO-8859-1'))
        subject = str(make_header(decode_header(mail["Subject"])))
        output += " %s"%(subject)

        date = str(make_header(decode_header(mail["Date"])))
        pos = date.find('+')
        if pos < 0:
            pos = date.find('-')
        if pos < 0:
            pos = date.find('GMT')
        day = date[0: pos - 10]
        hms = date[pos - 9: pos - 1]

        sender = str(make_header(decode_header(mail["From"])))
        try:
            receiver = str(make_header(decode_header(mail["To"])))
        except:
            receiver =  "Unknown"
        output += "\n %s  %s\n %s   %s"%(sender, receiver, day, hms)

        count, attachments = 0, ""
        for part in mail.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            filename = part.get_filename()
            if filename:
                count += 1
                fname, charset = decode_header(filename)[0]
                if charset:
                    attachments += ' %s\n'%fname.decode(charset)
        if count>0:
            output += '   %d Attachment(s)\n%s'%(count, attachments)

        filename = EMAIL_PATH + ADDRESS[user] + '/header_%d'%note_id
        output = output.replace('"','”')
        os.system('echo "%s" > %s'%(output, filename))

        content = get_content(mail)
        split_content(content, count)

    if len(args)>1:
        break

imapobj.close()