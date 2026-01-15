import tensorflow_hub as hub
import numpy as np
import librosa
import json
import wave
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import pandas as pd
import os

class AudioService:
    def __init__(self):
        self.df = pd.read_csv('data/yamnet_class_map.csv')
        self.nomes_classes = list(self.df['display_name'])

        self.transcritiveis = [
            'Speech', 'Child speech, kid speaking',
            'Conversation', 'Narration, monologue', 'Chatter'
        ]

        self.yamnet = hub.load(
            'https://www.kaggle.com/models/google/yamnet/TensorFlow2/yamnet/1'
        )

        self.idiomas_path = {
            'pt': 'idiomas/portugues',
            'es': 'idiomas/espanhol',
            'en': 'idiomas/ingles',
            'fr': 'idiomas/frances',
            'de': 'idiomas/alemao',
            'cn': 'idiomas/chines',
            'hi': 'idiomas/hindi',
            'ru': 'idiomas/russo',
            'ar': 'idiomas/arabe'
        }

    def converter_para_wav(self, arquivo, saida):
        audio = AudioSegment.from_file(arquivo)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(saida, format='wav')
        conteudo, _ = librosa.load(saida, sr=None, mono=True)
        return conteudo

    def classificar_audio(self, audio):
        scores, _, _ = self.yamnet(audio)
        medias = np.mean(scores.numpy(), axis=0)
        return medias

    def transcrever(self, wav_path, idioma):
        model = Model(self.idiomas_path[idioma])
        wf = wave.open(wav_path, 'rb')
        rec = KaldiRecognizer(model, wf.getframerate())

        texto = ''
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                texto += json.loads(rec.Result()).get('text', '') + ' '

        texto += json.loads(rec.FinalResult()).get('text', '')
        wf.close()
        return texto.strip()
