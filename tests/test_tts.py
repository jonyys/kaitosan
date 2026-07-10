import sys
sys.path.append('/home/kaitosan/robot')

from ai.text_to_speech import TextToSpeech

tts = TextToSpeech(device=1)
tts.hablar("Hola Laura, soy Kaito tu robot de escritorio. ¿Cómo estás hoy?")