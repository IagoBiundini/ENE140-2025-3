import os
import json
import wave
import numpy as np
import pandas as pd
import tensorflow_hub as hub
import librosa
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer
from deep_translator import GoogleTranslator
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes)
from bot_telegram import BotTelegram

class BotAudio(BotTelegram):
    def __init__(self, token):
        super().__init__(token)
        self.df = pd.read_csv('yamnet_class_map.csv')
        self.nomes_classes = list(self.df['display_name'])
        self.transcritiveis = ['Speech', 'Child speech, kid speaking', 'Conversation', 'Narration, monologue', 'Chatter']
        self.yamnet = hub.load('https://www.kaggle.com/models/google/yamnet/TensorFlow2/yamnet/1')
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
        self.idiomas_nomes = {
            'pt': '🇧🇷 Português',
            'es': '🇪🇸 Espanhol',
            'en': '🇺🇸 Inglês',
            'fr': '🇫🇷 Francês',
            'de': '🇩🇪 Alemão',
            'cn': '🇨🇳 Chinês',
            'hi': '🇮🇳 Hindi',
            'ru': '🇷🇺 Russo',
            'ar': '🇸🇦 Árabe'
        }


    def wav_audio(self, arq, arq_formatado):

        audio = AudioSegment.from_file(arq)
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)
        audio.export(arq_formatado, format='wav')

        conteudo_wav, _ = librosa.load(arq_formatado, sr=None, mono=True)
        return conteudo_wav

    def transcrever_audio(self, context):
        idioma = context.user_data['idioma']

        idioma_caminho = self.idiomas_path[idioma]
        idioma_model = Model(idioma_caminho) 

        audio = context.user_data['caminho_wav']

        wf = wave.open(audio, 'rb')
        rec = KaldiRecognizer(idioma_model, wf.getframerate())

        texto_final = ''

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                resultado = json.loads(rec.Result())
                texto_final += resultado.get('text', '') + ' '

        resultado_final = json.loads(rec.FinalResult())
        texto_final += resultado_final.get('text', '')

        wf.close()
        return texto_final.strip()

    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):    
        menu1 = InlineKeyboardMarkup([
            [
                InlineKeyboardButton('Selecionar Idioma', callback_data='sel_idioma'),
                InlineKeyboardButton('❓ Ajuda', callback_data='ajuda')
            ]
        ])

        if update.message:
            await update.message.reply_text('*Área de Reconhecimento de Áudio*\n\nSeja Bem Vindo!\nEscolha uma das opções abaixo:', reply_markup=menu1, parse_mode='Markdown')
            return
        elif update.callback_query:
            await update.callback_query.edit_message_text('*Área de Reconhecimento de Áudio*\n\nSeja Bem Vindo!\nEscolha uma das opções abaixo:', reply_markup=menu1, parse_mode='Markdown')
            return

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.answer_callback_query(update.callback_query.id)

        await update.callback_query.edit_message_reply_markup(reply_markup=None)

        opcao = update.callback_query.data

        if opcao == 'sel_idioma':        
            menu2 = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('🇧🇷 Português', callback_data='pt'),
                    InlineKeyboardButton('🇪🇸 Espanhol', callback_data='es'),    
                    InlineKeyboardButton('🇺🇸 Inglês', callback_data='en')
                ],
                [    
                    InlineKeyboardButton('🇩🇪 Alemão', callback_data='de'),
                    InlineKeyboardButton('🇫🇷 Francês', callback_data='fr'),
                    InlineKeyboardButton('🇨🇳 Chinês', callback_data='cn')
                ],
                [    
                    InlineKeyboardButton('🇮🇳 Hindi', callback_data='hi'),
                    InlineKeyboardButton('🇷🇺 Russo', callback_data='ru'),
                    InlineKeyboardButton('🇸🇦 Árabe', callback_data='ar')
                ],
                [
                    InlineKeyboardButton('Voltar ao início desta área', callback_data= 'reinicio')
                ]
            ])
            await update.callback_query.edit_message_text('🌍 Selecione o Idioma do Áudio:\n\n', reply_markup=menu2)
            return

        elif opcao in self.idiomas_nomes:
            idioma = opcao
            idioma_caminho = self.idiomas_path[idioma]

            if not os.path.exists(idioma_caminho):
                await update.callback_query.edit_message_text("❗❗❗ *Como foi dito no README do repositório, É NECESSÁRIO"
                " BAIXAR A PASTA 'idiomas' para utilizar a área de reconhecimento de áudios.\n\n Por favor, siga as instruções"
                " disponibilizadas no README.\n\nAssim que você instalar, rode o código novamente.*", parse_mode='Markdown')

                return
            
            context.user_data['idioma'] = opcao
            menu3 = InlineKeyboardMarkup([[InlineKeyboardButton('🔁 Alterar Idioma', callback_data='sel_idioma')]])
            await update.callback_query.edit_message_text(f'Idioma selecionado {self.idiomas_nomes[opcao][:2]}! Envie seu áudio.', reply_markup=menu3)
            return

        elif opcao == 'ajuda':
            menu_retorno = InlineKeyboardMarkup([[InlineKeyboardButton('Voltar ao início desta área', callback_data= 'reinicio')]])
            await update.callback_query.edit_message_text(
                    '🆘 Ajuda\n\n'
                    '1. Selecione o idioma do áudio\n'
                    '2. Envie um arquivo de áudio ou mensagem de voz\n'
                    '3. Aguarde a Classificação\n\n'
                    '3.1. Aguarde a Transcrição\n\n'
                    '3.1.1. Aguarde a Tradução\n\n'
                    '📝 *Formatos de áudio:*\n'
                    '• Mensagem de voz do Telegram\n'
                    '• Quaisquer arquivos de áudio\n\n'
                    '⚠️ *Recomendações:*\n'
                    '• Áudios claros e sem ruídos\n'
                    '• Áudios curtos',
                    reply_markup = menu_retorno,
                    parse_mode='Markdown'
                )
            return

        elif opcao == 'inicio':
            await self.start(update, context) 
            
        elif opcao == 'reinicio':
            await self.start(update, context) 

        elif opcao == 'traduzir':
            menu_traducao = InlineKeyboardMarkup([
                [
                InlineKeyboardButton('🇧🇷 Português', callback_data='trad_pt'),
                InlineKeyboardButton('🇪🇸 Espanhol', callback_data='trad_es'),
                InlineKeyboardButton('🇺🇸 Inglês', callback_data='trad_en')
            ],
            [
                InlineKeyboardButton('🇫🇷 Francês', callback_data='trad_fr'),
                InlineKeyboardButton('🇩🇪 Alemão', callback_data='trad_de'),
                InlineKeyboardButton('🇮🇹 Italiano', callback_data='trad_it')
            ],
            [
                InlineKeyboardButton('🇷🇺 Russo', callback_data='trad_ru'),
                InlineKeyboardButton('🇸🇦 Árabe', callback_data='trad_ar'),
                InlineKeyboardButton('🇮🇳 Hindi', callback_data='trad_hi')
            ],
            [
                InlineKeyboardButton('🇯🇵 Japonês', callback_data='trad_ja'),
                InlineKeyboardButton('🇰🇷 Coreano', callback_data='trad_ko'),
                InlineKeyboardButton('🇨🇳 Chinês', callback_data='trad_zh-CN')
            ],
            [
                InlineKeyboardButton('Voltar ao início desta área', callback_data= 'reinicio')
            ]
            ])
            await update.callback_query.message.reply_text('🌍 *Selecione o idioma para tradução:*', reply_markup=menu_traducao, parse_mode='Markdown')
            return

        elif opcao[:5] == 'trad_':
            trad_idioma = opcao[5:]
            idioma = context.user_data['idioma']
            texto = context.user_data['texto']

            tradutor = GoogleTranslator(source=idioma, target=trad_idioma)

            traducao = tradutor.translate(texto)

            menu_retorno = InlineKeyboardMarkup([[InlineKeyboardButton('Voltar ao início desta área', callback_data= 'reinicio')]])

            await update.callback_query.edit_message_text(f'*Tradução:*\n\n{traducao}', parse_mode='Markdown', reply_markup=menu_retorno)

        elif opcao in ['top1', 'top3', 'top10']:
            medias = context.user_data.get('pontuacoes')

            prob_fala = 0

            for indice, classe in enumerate(self.nomes_classes):
                if classe in self.transcritiveis:
                    prob_fala += medias[indice]

            fala = False

            indices_3 = np.argsort(medias)[-3:][::-1]
            top3 = [self.nomes_classes[i] for i in indices_3]
            
            for classe in self.transcritiveis:
                if classe in top3:
                    fala = True
                    break

            if fala or prob_fala > 0.15:
                menu_retorno = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton('Transcrever o Áudio', callback_data='transcrever')
                    ],
                    [
                        InlineKeyboardButton('Voltar ao Ínício desta área', callback_data='inicio')
                    ]
                ])

            else:
                menu_retorno = InlineKeyboardMarkup([[InlineKeyboardButton('Voltar ao início desta área', callback_data='inicio')]])

            texto = ""
            if opcao == 'top1':
                indice_max = medias.argmax()
                texto = f'*Classe Mais Provável:*\n\n{self.nomes_classes[indice_max]}'
            elif opcao == 'top3':
                indices = np.argsort(medias)[-3:][::-1]
                texto = '*3️⃣ Classes Mais Prováveis:*\n\n' + "\n".join([f"{self.nomes_classes[i]}: {medias[i]*100:.2f}%" for i in indices])
            elif opcao == 'top10':
                indices = np.argsort(medias)[-10:][::-1]
                texto = '*🔟 Classes Mais Prováveis:*\n\n' + "\n".join([f"{self.nomes_classes[i]}: {medias[i]*100:.2f}%" for i in indices])

            await update.callback_query.message.reply_text(texto, parse_mode='Markdown', reply_markup=menu_retorno)

        elif opcao == 'transcrever':

            menu6 = InlineKeyboardMarkup([
                [InlineKeyboardButton('Traduzir', callback_data='traduzir')],
                [InlineKeyboardButton('Voltar ao início desta área', callback_data='inicio')]
            ])

            texto = self.transcrever_audio(context)
            context.user_data['texto'] = texto

            await update.callback_query.message.reply_text(f'*Transcrição:*\n\n{texto}',parse_mode='Markdown',reply_markup=menu6)
            return

    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        if not context.user_data.get('idioma'):
            await update.message.reply_text("Escolha um idioma antes de enviar o áudio.")
            await self.start(update, context)
            return

        idioma = context.user_data['idioma']
        idioma_print = self.idiomas_nomes[idioma]
        
        await update.message.reply_text(f'Processando áudio em {idioma_print[3:]}...')
   
        if update.message.audio:
            id_arq = update.message.audio.file_id
            nome_arq = update.message.audio.file_name
            arq_formato = os.path.splitext(nome_arq)[1]

        elif update.message.voice: 
            id_arq = update.message.voice.file_id
            nome_arq = f'voz_{update.message.message_id}.ogg'
            arq_formato = '.ogg'

        else:
            await update.message.reply_text('Envie um áudio válido.')
            return
        
        arq_upload = await context.bot.get_file(id_arq)
        await arq_upload.download_to_drive(nome_arq)
        wav_nome = nome_arq.replace(arq_formato, '.wav')

        wav_conteudo = self.wav_audio(nome_arq, wav_nome)
        context.user_data['wav_conteudo'] = wav_conteudo
        context.user_data['caminho_wav'] = wav_nome

        audio = context.user_data['wav_conteudo']

        scores, embeddings, log_mel_spectrogram = self.yamnet(audio)
        scores.shape.assert_is_compatible_with([None, 521])
        embeddings.shape.assert_is_compatible_with([None, 1024])
        log_mel_spectrogram.shape.assert_is_compatible_with([None, 64])

        medias = np.mean(scores.numpy(), axis=0)
        context.user_data['pontuacoes'] = medias

        menu_top = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Top 1️⃣',callback_data = 'top1'),
            InlineKeyboardButton('Top 3️⃣',callback_data = 'top3'),
            InlineKeyboardButton('Top 🔟',callback_data = 'top10')
        ]
    ])
        await update.message.reply_text('Seu áudio foi processado, escolha quantas opções voce deseja ver:', reply_markup = menu_top)
        return