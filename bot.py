import os

TOKEN = "TOKEN"
PORT = int(os.environ.get('PORT', '8443'))
updater = Updater(TOKEN)
# add handlers
updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path=TOKEN)
updater.bot.set_webhook("https://<appname>.herokuapp.com/" + TOKEN)
updater.idle()
