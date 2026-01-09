from bot_audio import BotAudio
from bot_imagem import BotImagem

class BotMultimodal(BotAudio, BotImagem):
    def __init__(self, token):
        super().__init__(token)
