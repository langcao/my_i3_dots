import imaplib
import email
import base64
import quopri
import os, sys, time
import html2text
from email.header import decode_header, make_header
from mail_head import *


if len(sys.argv)>1:
    user = int(sys.argv[1])
else:
    user = 0

HEAD_ID = 23100
TEXT_ID = 23200

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


def popup_content(content, note_id, level, maxrow=36):
    if isinstance(content, str):
        lines = content.replace('"',"”").replace('`',"｀").replace("'",'’').split('\n')
    else:
        lines = content.split('\n')

    text, omitted = "", ""
    current = 0
    for i, line in enumerate(lines):
        if current >= maxrow:
            # text += '⋮║ The orininal mail has more %d line(s) omitted.'%(len(lines) - current)
            omitted = ' The orininal mail has more %d line(s) omitted.'%(len(lines) - current)
            break
        if len(line)<2 and (i>1 and len(lines[i-1])<2):
            continue
        if len(line)>1:
            pos = len(line)
            while pos>0 and line[pos-1] in ['\n', '\r']:
                pos -= 1
            # print(len(line), pos, line[0:pos])
            if pos>0:
                if current == 0:
                    text += ' ' + line[0:pos]+'\n'
                else:
                    text += '  ' + line[0:pos]+'\n'
                current += 1
        else:
            text += '\n'
            current += 1
    os.system('notify-send.sh -r %d -u %s "%s" "%s"'%(TEXT_ID, level, text, omitted))
    # print(content)

if user < len(NAME):

    imapobj = imaplib.IMAP4_SSL(SERVER[user], '993')
    imapobj.login(ADDRESS[user], PASSWORD[user])

    #workラベル下のメールを取得
    imapobj.select()
    typ, data = imapobj.search(None, 'All')

    #取得したメールから表題と本文を出力し、添付ファイルを同階層に書き出す
    select = data[0].split()
    SHOW_NUM = 1
    for note_id in range(SHOW_NUM):
        num = select[-note_id-1]
        typ, data = imapobj.fetch(num, '(RFC822)')
        mail = email.message_from_string(data[0][1].decode('utf-8'))
        subject = str(make_header(decode_header(mail["Subject"])))
        output = " %s"%(subject)

        date = str(make_header(decode_header(mail["Date"])))
        pos = date.find('+')
        if pos < 0:
            pos = date.find('-')
        day = date[0: pos - 10]
        hms = date[pos - 9: pos - 1]

        sender = str(make_header(decode_header(mail["From"])))
        output += "\n %s  %s <%s>\n %s   %s"%(sender, NAME[user], ADDRESS[user], day, hms)

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
            output += '   %d Attachment(s)'%count

        os.system('notify-send.sh -r %d -u critical "%s" "%s"'%(HEAD_ID, output, attachments))
        if len(sys.argv)>2:
            content = get_content(mail)
            popup_content(content, TEXT_ID, sys.argv[2])

        time.sleep(4)

    imapobj.close()