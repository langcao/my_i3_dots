from googletrans import Translator
from os import system, popen
import subprocess
import unidecode

NOTIFY_ID = 362751

text = popen('xsel').read()
if text:
	print(text)
	word = unidecode.unidecode(text)
	word = word.replace("'",'')
	print(word)
	system("dunstify -r %d '%s'"%(NOTIFY_ID-1, text))
	system("dunstify -r %d -u low '%s'"%(NOTIFY_ID+1, word))
	system("dunstify -r %d -u low 'Translating...'"%NOTIFY_ID)

	translator = Translator()
	a = translator.translate(word)
	trans = a.text
	trans = trans.replace("'","’")
	system("dunstify -r %d '%s'"%(NOTIFY_ID-1, text))
	system("dunstify -r %d -u low '%s'"%(NOTIFY_ID+1, word))
	system("dunstify -r %d '%s'"%(NOTIFY_ID, trans))