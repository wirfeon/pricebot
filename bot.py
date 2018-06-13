#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import requests
import json
import os
from copy import copy
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import datetime
import base64
import time

PORT = int(os.environ.get('PORT', '8443'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

btc_usd = 0
xem_usd = 0
xpx_usd = 0

nemchange_tickers = {
    "CVZ": "coinvest:vezcoin"
}

def priceall(bot, update):
    chat_title = update.message.chat.title
    
    if (chat_title == "Test"):
        update.message.chat.title = "myCoinvest"
        price(bot, update)
        update.message.chat.title = "ProximaX Wakanda"
        price(bot, update)
    #endif
#enddef 

def pricexpx(bot, update):
    global xpx_usd, xem_usd, btc_usd
 
    update.message.chat.send_message("1 {:s} = ${:.5f} = {:d} sat = {:.4f} XEM".format("XPX", xpx_usd, int(xpx_usd / btc_usd * 100000000), xpx_usd / xem_usd))

def coingecko(coin):
    response = requests.get("https://api.coingecko.com/api/v3/coins/" + coin).text
    data = json.loads(response)

    return float(data["market_data"]["current_price"]["usd"])
    
def scraper(bot, job):
    global xpx_usd, xem_usd, btc_usd

    logger.info("Scraping coingecko")
    xpx_usd = coingecko("proximax")
    xem_usd = coingecko("nem")
    btc_usd = coingecko("bitcoin")
    logger.info("Done")

    
def nemchange(bot, update, ticker):
    global xem_usd

    logger.info("Pulling data on '{:s}'".format(ticker))
 
    body = requests.get("https://nemchange.com//Exchange/actualOrders2/" + nemchange_tickers[ticker] + "/nem:xem")
    if (body.text == "{}"):
        logger.warn("Empty response")
        return
    #endif

    token = "<td id='ratio2_0'>"
    start = body.text.find(token)
    end = body.text.find("</td>", start)
    ratio = float(body.text[start + len(token) : end])

    bid = 1 / ratio
        
    update.message.chat.send_message("1 {:s} = {:.4f} XEM = ${:.5f}".format(ticker, bid, bid * xem_usd))

def price(bot, update):

    chat_title = update.message.chat.title
    logger.info("Request from %lu'%s'" % (update.message.chat.id, chat_title))

    ctime = datetime.now().timestamp()
    
    if (update.message.date.timestamp() + 10 < ctime):
        logger.warn("Request is too old %f %f" % (update.message.date.timestamp(), ctime))
        return
    #endif

    if (chat_title in ("ProximaX Wakanda", "ProximaX Czech & Slovakia Official")):
        pricexpx(bot, update)
    elif (chat_title == "myCoinvest"):
        nemchange(bot, update, "CVZ")
    else: 
        return;
    #endif
    

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():
    updater = None

    i = 0
    while i < 2:
        try:
            # Create the EventHandler and pass it your bot's token.
            updater = Updater(os.environ["BOT_TOKEN"], workers = 1)

            updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=os.environ["BOT_TOKEN"])
            updater.bot.set_webhook(os.environ["WEB_HOOK"] + os.environ["BOT_TOKEN"])
            break
        except Exception as e:
            logger.warn("Exception: %s" % e)
            if (updater):
                updater.stop()
        #endtry
        
        i += 1
        time.sleep(1)
    #endwhile

    if (not updater):
        return

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("price", price))
    dp.add_handler(CommandHandler("priceall", priceall))

    job = updater.job_queue
    job_sec = job.run_repeating(scraper, interval=10, first=0)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    logger.info("Polling")
    updater.idle()

    logger.info("Stoping updater") 
    updater.stop()
 
if __name__ == '__main__':
    main()
