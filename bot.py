#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import requests
import json
import os
import websocket
from copy import copy
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import datetime

PORT = int(os.environ.get('PORT', '8443'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

template = { "ask": -1, "bid": -1, "xem": -1, "timer": 0 }
db = { "XAR": copy(template), "CVZ": copy(template), "XPX": copy(template)}
db["XAR"]["name"] = "xarcade:xar"
db["CVZ"]["name"] = "coinvest:vezcoin"
db["XPX"]["name"] = "prx:xpx"

websocket.enableTrace(True)
ws = websocket.WebSocket()

btc_usd = 0
xpx_btc = 0
xem_btc = 0
cmc_ts = 0

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def priceall(bot, update):
    chat_title = update.message.chat.title
    
    if (chat_title == "Test"):
        update.message.chat.title = "myCoinvest"
        #price(bot, update)
        update.message.chat.title = "ProximaX Wakanda"
        pricexpx(bot, update)
    #endif
#enddef 

def pricexpx(bot, update):
    update.message.chat.send_message("1 {:s} = {:.4f} XEM = {:d} sat = ${:.5f}".format("XPX", xpx_btc / xem_btc, int(xpx_btc * 100000000), xpx_btc * btc_usd))

def kryptono(bot, job):
    global btc_usd, xpx_btc, xem_btc, cmc_ts

    result = ws.recv()
    #logger.info("Received '%s'" % result)
    data = json.loads(result)
    if int(data["t"]) - cmc_ts > 10000:
        btc_usd = float(json.loads(requests.get('https://api.coinmarketcap.com/v1/ticker/bitcoin/').text)[0]["price_usd"])
        xem_btc = float(json.loads(requests.get('https://api.coinmarketcap.com/v1/ticker/nem/').text)[0]["price_btc"])
        cmc_ts = int(data["t"])

    for ticker in data["d"]:
        #if ticker["s"] == "XPX_BTC":
        if ticker["s"] == "TRX_BTC":
            xpx_btc = float(ticker["n"])
            logger.info("%f %f" % (xpx_btc * 100000000, xpx_btc * btc_usd)) 
            break

def price(bot, update):

    chat_title = update.message.chat.title
    
    logger.info(chat_title)
    if (chat_title in ("ProximaX Wakanda", "ProximaX Czech & Slovakia Official")):
        coin_ticker = "XPX"
    elif (chat_title == "myCoinvest"):
        coin_ticker = "CVZ"
    else: 
        return;
    #endif

    coin = db[coin_ticker]
    ctime = datetime.now().timestamp()
    
    if (update.message.date.timestamp() + 10 < ctime):
        logger.info("Request is too old %f %f" % (update.message.date.timestamp(), ctime))
        return
    
    if ((ctime > coin["timer"] + 10) or (coin["bid"] == -1) or (coin["xem"] == -1)):
        logger.info("Pulling data on '{:s}'".format(coin["name"]))
 
        #body = requests.get("https://nemchange.com/Exchange/market/" + coin["name"] + "/nem:xem").text
        body = requests.get("https://nemchange.com//Exchange/actualOrders2/" + coin["name"] + "/nem:xem")
        if (body.text == "{}"):
            return
        #endif

        token = "<td id='ratio2_0'>"
        start = body.text.find(token)
        end = body.text.find("</td>", start)
        ratio = float(body.text[start + len(token) : end])

        coin["bid"] = 1 / ratio
        coin["xem"] = float(json.loads(requests.get('https://api.coinmarketcap.com/v1/ticker/nem/').text)[0]["price_usd"])
        
        coin["timer"] = ctime
    #endif
        
    logger.info("%u '%s'" % (update.message.chat.id, update.message.chat.title))
    #update.message.reply_text("ASK: {:.4f} BID: {:.4f}".format(ask, bid))
    update.message.chat.send_message("1 {:s} = {:.4f} XEM = ${:.5f}".format(coin_ticker, coin["bid"], coin["bid"] * coin["xem"]))

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(os.environ["BOT_TOKEN"], workers = 1)

    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=os.environ["BOT_TOKEN"])
    updater.bot.set_webhook(os.environ["WEB_HOOK"] + os.environ["BOT_TOKEN"])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("price", price))
    dp.add_handler(CommandHandler("priceall", priceall))

    ws.connect("wss://engines.kryptono.exchange/ws/v1/tk/", 
        headers = ["Connection: Upgrade", 
            "Upgrade: websocket", 
            "Host: engines.kryptono.exchange", 
            "Origin: https://kryptono.exchange", 
            "Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits", 
            "Sec-WebSocket-Key: lctUilr7TifuqRxnS4hs0Q==", 
            "Sec-WebSocket-Version: 13"])

    logger.info("Receiving...")
    result = ws.recv()
    logger.info("Received '%s'" % result)

    job = updater.job_queue
    job_sec = job.run_repeating(kryptono, interval=1, first=0)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
 
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
  
    logger.info("Stoping updater") 
    updater.stop()
 
    ws.shutdown()
    ws.close() 


if __name__ == '__main__':
    main()
