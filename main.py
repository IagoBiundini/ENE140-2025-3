import os
from bot_multimodal import BotMultimodal

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN não encontrado nas variáveis de ambiente")

bot = BotMultimodal(TOKEN)
bot.run()

