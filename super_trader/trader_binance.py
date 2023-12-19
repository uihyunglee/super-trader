import json
import os
import time
from datetime import datetime as dt
from datetime import timedelta as td

import ccxt
import requests

from super_trader import SuperTrader


class BinanceTrader(SuperTrader):
    def __init__(self, is_spot=True):
        super().__init__()
        self.exchange = self.get_binance_broker(is_spot)
        self.send_msg(f'set_binance_broker(is_spot={is_spot})...OK', slack=True)

    def read_api_key(self):
        config_path = os.path.join(os.getcwd(), "config.json")
        if os.path.exists(config_path):
            with open('config.json', 'r') as json_file:
                _config = json.load(json_file)
            if 'binance' in _config:
                binance_info = _config['binance']
                required_keys = ["api_key", "secret"]
                if all(key in binance_info for key in required_keys):
                    return binance_info
                else:
                    raise ValueError("binance in config.json must contain 'api_key', and 'secret' key.")
            else:
                raise ValueError("config.json must contain 'binance' key.")
        else:
            raise FileNotFoundError("config.json must exist in the path. ")
        
    def get_binance_broker(self, is_spot):
        binance_info = self.read_api_key()
        exchange = ccxt.binance(config={
            'apiKey': binance_info["api_key"], 
            'secret': binance_info["secret"],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot' if is_spot else 'future'
            }
        })
        return exchange
    
    def check_market_open(self):
        self.send_msg('check_market_open...OK', slack=True)  # The binance market is always opend.
    
    def check_system(self):
        try:
            ccxt.binance().fetch_ticker('BTC/USDT')
            self.send_msg('check_system...OK', slack=True)
        except Exception as e:
            self.send_msg('check_system...FAILED', log_level='warning', slack=True)
            raise Exception(str(e))