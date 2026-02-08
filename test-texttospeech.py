import pyttsx3
import re

eng = pyttsx3.init()

voices = eng.getProperty('voices')
for voice in voices:
    if re.search("/en", voice.id):
        eng.setProperty('voice', voice.id)
        print("English Voice ID: " + voice.id)
        eng.say('The quick brown fox jumped over the lazy dog.')
        eng.runAndWait()
    else:
        print("Non-english voice (" + voice.id + ")")

#eng.say("This is what I am talking about.")
#eng.runAndWait()
eng.stop()