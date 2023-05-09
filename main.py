import os
import logging
from kiteconnect import KiteTicker
from datetime import datetime
import requests
import csv
import io

access_token = os.environ['access_token']
api_key = os.environ['api_key']

logging.basicConfig(level=logging.DEBUG)

response = requests.get("https://api.kite.trade/instruments/NFO")
s = response.content


def conversion(fut_price, ce_price, pe_price, strike, quantity):
  return (fut_price - strike - ce_price + pe_price) * quantity


def reversal(fut_price, ce_price, pe_price, strike, quantity):
  return (strike + ce_price - pe_price - fut_price) * quantity


index_input = input('Enter Index (N/BN): ')
synth_expiry_date = input('Enter Synthetic Expiry Date (YYYY-MM-DD): ')
strike = int(input('Enter Strike: '))
fut_expiry_month = f"-{input('Enter FUT Expiry Month (MM): ')}-"

if index_input.lower() == 'bn':
  index_token = 260105
  index = 'BANKNIFTY'
elif index_input.lower() == 'n':
  index_token = 256265
  index = 'NIFTY'

reader = csv.reader(io.StringIO(s.decode('utf-8')))
for row in reader:
  if str(row[5]) == synth_expiry_date and row[3] == index and row[6] == str(
      strike):
    if row[9] == 'CE':
      CE_token = int(row[0])
      print(row)
    elif row[9] == 'PE':
      PE_token = int(row[0])
      print(row)
  if fut_expiry_month in str(row[5]) and row[3] == index and row[9] == 'FUT':
    fut_token = int(row[0])

sub = [CE_token, PE_token, fut_token, index_token]

# Initialise
kws = KiteTicker(api_key, access_token)


def on_ticks(ws, ticks):
  # Callback to receive ticks.
  # print("Ticks: {}".format(ticks))
  for tick in ticks:
    global FUT_SELL, FUT_BUY, CE_BUY, CE_SELL, PE_BUY, PE_SELL, spot
    if tick['instrument_token'] == fut_token:
      FUT_SELL = tick['depth']['buy'][0]['price']
      FUT_BUY = tick['depth']['sell'][0]['price']
    elif tick['instrument_token'] == CE_token:
      CE_BUY = tick['depth']['sell'][0]['price']
      CE_SELL = tick['depth']['buy'][0]['price']
    elif tick['instrument_token'] == PE_token:
      PE_SELL = tick['depth']['buy'][0]['price']
      PE_BUY = tick['depth']['sell'][0]['price']
    else:
      spot = tick['last_price']
  now = datetime.now()
  timestamp = now.strftime('%H:%M:%S:%f')
  conversion_synth = "{:.2f}".format(float(strike + CE_BUY - PE_SELL))
  conversion_synth_premium = "{:.2f}".format(
    float(float(conversion_synth) - spot))
  fut_premium = "{:.2f}".format(float(FUT_SELL - spot))
  out = str(
    f'{timestamp[:-4]} {index_input.upper()} {str(strike)}'
    f' Synth Premium : {conversion_synth_premium}'
    f' FUT Premium : {fut_premium}'
    f' Conversion : {"{:.2f}".format(float(fut_premium) - float(conversion_synth_premium))}'
  )
  with open('conversion_data.txt', 'a') as f:
    f.write(out)
    f.write('\n')
  print(out)


def on_connect(ws, response):
  # Callback on successful connect.
  # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
  ws.subscribe(sub)

  # Set RELIANCE to tick in `full` mode.
  ws.set_mode(ws.MODE_FULL, sub)


def on_close(ws, code, reason):
  # On connection close stop the event loop.
  # Reconnection will not happen after executing `ws.stop()`
  ws.stop()


# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()
