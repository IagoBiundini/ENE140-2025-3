import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton # NOVO: Para os botões
import os 
from speech_music_recognition import Speech_audio_recognition, Music_recognition
from bot_Imagem import BotImagem
import time 
import socket

class BotTelegram():
    def __init__(self, chave_api):
        self.bot = telebot.TeleBot(chave_api)
        self.especialista_imagem = BotImagem()
        self._register_handlers()

    def _register_handlers(self):
        # Registro das mensagens normais
        self.bot.message_handler(content_types=['photo', 'voice', 'audio', 'document', 'text'])(self.tratar_mensagem)
        
        # NOVO: Registro do clique nos botões
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            self.responder_escolha(call)

    def criar_menu_audio(self):
        """NOVO: Cria os botões que aparecem embaixo do áudio"""
        markup = InlineKeyboardMarkup()
        # callback_data é o que o código vai ler para saber qual botão foi apertado
        btn_musica = InlineKeyboardButton("🎵 Identificar Música", callback_data="btn_musica")
        btn_texto = InlineKeyboardButton("📝 Transcrever Fala", callback_data="btn_transcrever")
        markup.add(btn_musica, btn_texto)
        return markup

    def tratar_mensagem(self, message):
        """Central de triagem de mensagens"""

        # CASO 1: IMAGEM
        if message.content_type == 'photo':
            # ... (seu código de imagem continua igual)
            self.bot.reply_to(message, "Recebi a imagem! Baixando e processando... ⏳")
            try:
                file_id = message.photo[-1].file_id
                file_info = self.bot.get_file(file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                nome_arquivo = "imagem_temp.jpg"
                with open(nome_arquivo, 'wb') as new_file:
                    new_file.write(downloaded_file)
                resposta_analise = self.especialista_imagem.identificar_arquivo(nome_arquivo)
                self.bot.reply_to(message, resposta_analise)
            except Exception as e:
                self.bot.reply_to(message, f"Deu erro ao processar: {e}")
            finally:
                if os.path.exists("imagem_temp.jpg"):
                    os.remove("imagem_temp.jpg")

        # CASO 2: TEXTO
        elif message.content_type == 'text':
             boas_vindas = (
                "👋 *Olá! Sou o seu Assistente Multitarefa.*\n\n"
                "Estou pronto para processar seus arquivos. Veja o que posso fazer:\n\n"
                "🖼️ *Imagens:* Envie uma foto e eu direi o que há nela.\n"
                "🎤 *Transcrição:* Envie um áudio e eu escreverei o que foi dito.\n"
                "🎵 *Música:* Envie um som e eu direi o nome da música e artista.\n\n"
                "👉 _Basta enviar o arquivo!_"
            )
             self.bot.reply_to(message, boas_vindas, parse_mode="Markdown")

        # CASO 3: ÁUDIO / VOZ 
        elif message.content_type in ['audio', 'voice']:
            # Em vez de processar, apenas baixa e pergunta o que fazer
            self.bot.reply_to(message, "🎤 Áudio recebido! O que deseja fazer?", reply_markup=self.criar_menu_audio())
            
            try:
                file_id = message.voice.file_id if message.content_type == 'voice' else message.audio.file_id
                file_info = self.bot.get_file(file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)

                # Salva com um nome fixo para o processamento posterior
                # Usa o ID do chat para não misturar áudios de pessoas diferentes
                ext = os.path.splitext(file_info.file_path)[1] if file_info.file_path else '.ogg'
                temp_audio_file = f"temp_{message.chat.id}{ext}"

                with open(temp_audio_file, 'wb') as new_file:
                    new_file.write(downloaded_file)
            except Exception as e:
                self.bot.reply_to(message, f"Erro ao baixar áudio: {e}")

    def responder_escolha(self, call):
        chat_id = call.message.chat.id
        arquivo_alvo = None
        
        # Busca o arquivo salvo para este usuário
        for f in os.listdir('.'):
            if f.startswith(f"temp_{chat_id}"):
                arquivo_alvo = f
                break

        if not arquivo_alvo:
            # Em vez de apenas enviar msg, edita o menu que falhou
            self.bot.edit_message_text("❌ Arquivo expirado ou não encontrado.", chat_id, call.message.message_id)
            return

        # Feedback visual imediato
        self.bot.edit_message_text("⏳ Processando... Por favor, aguarde.", chat_id, call.message.message_id)

        try:
            if call.data == "btn_musica":
                # Criamos a instância apenas se fr necessário
                reconhecedor = Music_recognition(arquivo_alvo)
                resultado = reconhecedor.search_music() 
                
                if resultado:
                    url_musica, titulo_artista, visualizacoes = resultado
                    markup_link = InlineKeyboardMarkup().add(
                        InlineKeyboardButton(text="🎧 Abrir no YouTube Music", url=url_musica)
                    )
                    
                    self.bot.send_message(
                        chat_id, 
                        f"✅ *Música Identificada!*\n\n🎵 *Resultado:* {titulo_artista}\n📊 *Visualizações:* {visualizacoes:,}", 
                        reply_markup=markup_link, 
                        parse_mode="Markdown"
                    )
                else:
                    self.bot.send_message(chat_id, "❌ Não identifiquei essa música.")

            elif call.data == "btn_transcrever":
                # Cria a instância do Speech apenas se necessário
                reconhecedor = Speech_audio_recognition(arquivo_alvo)
                resultado = reconhecedor.transcrever_audio()
                
                msg_final = resultado if resultado else "❌ Não consegui entender o que foi dito."
                self.bot.send_message(chat_id, f"📝 *Transcrição:* \n\n_{msg_final}_", parse_mode="Markdown")

        except Exception as e:
            print(f"Erro detalhado: {e}")
            self.bot.send_message(chat_id, "⚠️ Ocorreu um erro técnico ao processar este áudio.")
        
        finally:
            # Apaga a mensagem de "Processando" para limpar o chat
            try:
                self.bot.delete_message(chat_id, call.message.message_id)
            except:
                pass
            
            # Limpeza do arquivo físico
            if arquivo_alvo and os.path.exists(arquivo_alvo):
                os.remove(arquivo_alvo)

    def verificar_internet(self):
        """Método que intermediário que chega a conexão com o servidor do Telegram.        
            Não irá receber mensagem em nem enviar
        """
        try:
            # Tenta conectar ao DNS do Google para checar conexão
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def run(self):
        """
        Fica constantemente rodando, mesmo com o servidor caido, ele tenta conectar
        """
        print("Bot rodando! Pode enviar mensagens...")
        while True:
            if not self.verificar_internet():
                print("⚠️ Sem conexão com a internet. Aguardando...")
                time.sleep(10)
                continue
                
            try:
                self.bot.polling(non_stop=True, interval=0, timeout=20)
            except Exception as e:
                print(f"Erro de rede: {e}. Tentando reconectar...")
                time.sleep(5)

