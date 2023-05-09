import os
from kiteconnect import KiteConnect

access_token = os.environ['access_token']
api_key = os.environ['api_key']

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token=access_token)

params = [{
  "exchange": "NSE",
  "tradingsymbol": "INFY",
  "transaction_type": "BUY",
  "variety": "regular",
  "product": "CNC",
  "order_type": "MARKET",
  "quantity": 1,
  "price": 0,
  "trigger_price": 0
  }]

margin_detail = kite.order_margins(params)

print(margin_detail)