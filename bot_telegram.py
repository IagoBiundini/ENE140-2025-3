import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot('8235945672:AAEvnPJIiQO5zDzxsbUQ5--9rOUIBNAg7Ko')
class BotTelegram:
    def __init__(self, token):
        # Inicializa o bot com o token fornecido
        self.bot = telebot.TeleBot(token)
        self.modo_audio = set()   # usuários aguardando áudio
        self.configurar_handlers()

    def criar_menu(self):
        # Cria o teclado de opções (Interface)
        markup = InlineKeyboardMarkup()
        btn_audio = InlineKeyboardButton(text="🎙️ Transcrever Áudio", callback_data="opcao_audio")
        btn_imagem = InlineKeyboardButton(text="🖼️ Identificar Objeto", callback_data="opcao_imagem")
        markup.add(btn_audio, btn_imagem)
        return markup

    def configurar_handlers(self):
        # Gerencia os comandos e mensagens
        
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(msg):
            self.bot.reply_to(msg, "Olá! O que você gostaria de fazer hoje?", 
                             reply_markup=self.criar_menu())

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_reposta(call):
            if call.data == "opcao_audio":
                self.modo_audio.add(call.message.chat.id)
                self.bot.send_message(
                    call.message.chat.id,
                    "🎧 Envie um áudio para transcrição."
                )
            elif call.data == "opcao_imagem":
                self.bot.send_message(call.message.chat.id, "Ótimo! Envie uma foto.")

    def iniciar(self):
        print("Bot rodando dentro da classe...")
        self.bot.polling()
