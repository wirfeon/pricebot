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
import base64
import time

PORT = int(os.environ.get('PORT', '8443'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)


websocket.enableTrace(True)
ws = websocket.WebSocket()

btc_usd = 0
xpx_btc = 0
xem_btc = 0
xpx_eth = 0
xem_usd = 0
cmc_ts = 0
eth_btc = 0
eth_usd = 0
xpx_eth_q = 0
xpx_btc_q = 0
xpx_know = 0
xpx_know_q = 0
know_usdt = 0

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
    global btc_usd, xpx_btc, xem_btc, xem_usd, cmc_ts, eth_btc, eth_usd, xpx_eth, xpx_eth_q, xpx_btc_q, xpx_know, xpx_know_q, know_usdt
    
    eth_v = xpx_eth_q * eth_usd
    btc_v = xpx_btc_q * btc_usd
    know_v = xpx_know_q * know_usdt
    total = eth_v + btc_v + know_v

    know_share = know_v / total
    eth_share = eth_v / total
    btc_share = btc_v / total

    xpx_usd = xpx_eth * eth_usd * eth_share + xpx_btc * btc_usd * btc_share + xpx_know * know_usdt * know_share
    update.message.chat.send_message("1 {:s} = ${:.5f} = {:d} sat = {:.4f} XEM".format("XPX", xpx_usd, int(xpx_usd / btc_usd * 100000000), xpx_usd / xem_usd))
    logger.info("ETH %.2f BTC %.2f KNOW %.2f" % (eth_share, btc_share, know_share))

def scraper(bot, job):
    global btc_usd, xpx_btc, xem_btc, xem_usd, cmc_ts, eth_btc, eth_usd, xpx_eth, xpx_eth_q, xpx_btc_q, xpx_know, xpx_know_q, know_usdt

    while 1:
        result = {}
        i = 0

        while i < 3:
            try:
                result = ws.recv()
                break
            except Exception:
                ws.connect("wss://engines.kryptono.exchange/ws/v1/tk/", 
                    headers = ["Connection: Upgrade", 
                        "Upgrade: websocket", 
                        "Host: engines.kryptono.exchange", 
                        "Origin: https://kryptono.exchange", 
                        "Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits", 
                        "Sec-WebSocket-Key: %s==" % base64.b64encode(bytes(datetime.now().isoformat(), 'utf-8')), 
                        "Sec-WebSocket-Version: 13"])
            #endtry

            i += 1
        #endwhile

        if (result == {}):
            return

        data = json.loads(result)
        diff = datetime.now().timestamp() * 1000 - int(data["t"])
        logger.info("Scraping %.2f" % (datetime.now().timestamp() * 1000 - int(data["t"])))
        if (diff < 3000): break
    #endwhile

    if int(data["t"]) - cmc_ts > 10000:
        btc_usd = float(json.loads(requests.get('https://api.coinmarketcap.com/v1/ticker/bitcoin/').text)[0]["price_usd"])
        
        xx = json.loads(requests.get('https://api.coinmarketcap.com/v1/ticker/nem/').text)[0]
        xem_btc = float(xx["price_btc"])
        xem_usd = float(xx["price_usd"])
        
        xx = json.loads(requests.get('https://api.coinmarketcap.com/v1/ticker/ethereum/').text)[0]
        eth_btc = float(xx["price_btc"])
        eth_usd = float(xx["price_usd"])
        
        cmc_ts = int(data["t"])
    #endif

    for ticker in data["d"]:
        if ticker["s"] == "XPX_BTC":
            xpx_btc = float(ticker["n"])
            xpx_btc_q = float(ticker["q"])
        elif ticker["s"] == "XPX_ETH":
            xpx_eth = float(ticker["n"])
            xpx_eth_q = float(ticker["q"])
        elif ticker["s"] == "XPX_KNOW":
            xpx_know = float(ticker["n"])
            xpx_know_q = float(ticker["q"])
        elif ticker["s"] == "KNOW_USDT":
            know_usdt = float(ticker["n"])
        #endif
    #endfor

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
    #coin["xem"] = float(json.loads(requests.get('https://api.coinmarketcap.com/v1/ticker/nem/').text)[0]["price_usd"])
        
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
    
    i = 0
    while i < 2:
        try:
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
                    "Sec-WebSocket-Key: %s" % base64.b64encode(bytes(datetime.now().isoformat(), 'utf-8')), 
                    "Sec-WebSocket-Version: 13"])

            logger.info("Receiving...")
            result = ws.recv()
            logger.info("Received '%s'" % result)

            job = updater.job_queue
            job_sec = job.run_repeating(scraper, interval=3, first=0)

            # log all errors
            dp.add_error_handler(error)

            # Start the Bot
            updater.start_polling()
        except Exception as e:
            logger.warn("Exception: %s" % e)
            updater.stop()
            ws.shutdown()
            ws.close() 
        #endtry
    
        i += 1
        time.sleep(1)
    #endwhile
         
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    logger.info("Polling")
    updater.idle()

    logger.info("Stoping updater") 
    updater.stop()
 
    ws.shutdown()
    ws.close() 

if __name__ == '__main__':
    main()
