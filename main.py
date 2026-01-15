from bot_telegram import BotTelegram

"Aqui será rodado o código - Tenha a chave de acesso do bot Telegram em mãos"

token = input("Digite seu token (Chave de acesso feito no BOTFather)")
TOKEN = token

bot_instance = BotTelegram(chave_api=TOKEN)
bot_instance.run()