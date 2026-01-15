from TOKEN import str_token
from bot import *

token = ""

if not token:
    from TOKEN import str_token
    token = str_token

if __name__ == "__main__":
    open("log.txt", "w").close()
    TOKEN = token
    app = BotTelegram(TOKEN)
    app.run()