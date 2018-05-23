#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import requests
import json
import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import datetime

ENV = "test"

params = {
    "master": {
        "token": "554022144:AAFDYJkAZSH6flnmPujbJ1nmtnaJ7DPMTZA",
        "webhook": "https://shielded-peak-77662.herokuapp.com/"
    },
    "test": {
        "token": "603298832:AAGLTud_E45rzm8rtx9eneodOOJJJqxzVsM",
        "webhook": "https://pacific-chamber-20771.herokuapp.com/"
    }
}    

env = params[ENV]

PORT = int(os.environ.get('PORT', '8443'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

template = { "ask": -1, "bid": -1, "xem": -1, "timer": 0 }
db = { "XAR": template, "CVZ": template }
db["XAR"]["name"] = "xarcade:xar"
db["CVZ"]["name"] = "coinvest:vezcoin"

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def price(bot, update):

    chat_title = update.message.chat.title

    if (chat_title == "Test"):
        coin_ticker = "XAR"
    elif (chat_title == "myCoinvest"):
        coin_ticker = "CVZ"
    else: 
        return;
    #endif

    coin = db[coin_ticker]
    ctime = datetime.now().timestamp()

    if ((ctime > coin["timer"] + 10) or (coin["ask"] == -1) or (coin["bid"] == -1) or (coin["xem"] == -1)):
        logger.info("Pulling data on '{:s}'".format(coin["name"]))
 
        body = requests.get("https://nemchange.com/Exchange/market/" + coin["name"] + "/nem:xem").text

        token = '<td id = "ratio2_0">'
        start = body.find(token)
        end = body.find("</td>", start)
        ask = float(body[start + len(token) : end])

        token = '<td id = "ratio_0">'
        start = body.find(token, end)
        end = body.find("</td>", start)
        bid = float(body[start + len(token) : end])

        xem = float(json.loads(requests.get('https://api.coinmarketcap.com/v1/ticker/nem/').text)[0]["price_usd"])
        
        timer = ctime
    #endif
        
    logger.info("%d '%s'" % (update.message.chat.id, update.message.chat.title))
    #update.message.reply_text("ASK: {:.4f} BID: {:.4f}".format(ask, bid))
    update.message.chat.send_message("1 {:s} = {:.4f} XEM = ${:.5f}".format(coin_ticker, coin["bid"], coin["bid"] * coin["xem"]))

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(env["token"], workers = 1)

    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=env["token"])
    updater.bot.set_webhook(env["webhook"] + env["token"])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("price", price))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
