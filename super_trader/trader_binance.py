import json
import os
import time

import ccxt

from super_trader import SuperTrader


class BinanceTrader(SuperTrader):
    def __init__(self, is_future=False):
        super().__init__()
        self.is_future = is_future
        self.exchange = self.get_binance_broker()
        self.send_msg(f'set_binance_broker(is_future={self.is_future})...OK', slack=True)

    def get_binance_broker(self):
        binance_info = self.read_api_key()
        exchange = ccxt.binance(config={
            'apiKey': binance_info["api_key"],
            'secret': binance_info["secret"],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future' if self.is_future else 'spot'
            }
        })
        return exchange

    def check_market_open(self):
        self.send_msg('check_market_open...OK', slack=True)  # The binance market is always open.
        return True

    def check_system(self):
        try:
            ccxt.binance().fetch_ticker('BTC/USDT')
            self.send_msg('check_system...OK', slack=True)
            return True
        except Exception as e:
            self.send_msg('check_system...FAILED', log_level='warning', slack=True)
            raise Exception(str(e))

    def get_cur_price(self, symbol):
        symbol_price = self.exchange.fetch_ticker(symbol)
        cur_price = symbol_price['last']
        return cur_price

    def get_total_usdt(self):
        balance = self.exchange.fetch_balance(params={'type': 'future' if self.is_future else 'spot'})
        balance_usdt = balance['USDT']
        total_usdt = balance_usdt['total']
        return float(total_usdt)

    def get_holding_position(self, symbol):
        positions = self.exchange.fetch_positions(symbols=[symbol])
        amount = positions[0]['info']['positionAmt']  # 추후 여러 자산 투자 시 변경
        return float(amount)

    def get_unrealized_profit(self, symbol):
        positions = self.exchange.fetch_positions(symbols=[symbol])
        unrealized_profit = positions[0]['info']['unRealizedProfit']
        return float(unrealized_profit)

    def send_market_order(self, symbol, qty):
        side = 'buy' if qty > 0 else 'sell'
        qty = abs(qty)
        self.send_msg(f'send_market_order -> symbol: {symbol}, side: {side}, qty: {qty}')
        order = self.exchange.create_order(
            symbol=symbol,
            type='market',
            side=side,
            amount=qty
        )
        return order['id']

    def check_order_completion(self, symbol, order_id):
        while True:
            time.sleep(0.1)
            order = self.exchange.fetchOrder(symbol=symbol, id=order_id)
            if order['info']['status'] == 'FILLED':
                self.send_msg(f'check_order_completion...OK')
                return order['info']

    def execute_order(self, symbol, qty):
        order_id = self.send_market_order(symbol, qty)
        order_info = self.check_order_completion(symbol, order_id)

        info_col = ['time', 'updateTime', 'orderId', 'type', 'side', 'symbol',
                    'price', 'avgPrice', 'origQty', 'executedQty']
        info_lst = [order_info[col] for col in info_col]
        self.send_msg(f'execute_order: {info_lst}')
        return info_lst

    def end_all_position(self, symbol):
        prev_qty = self.get_holding_position(symbol)
        self.send_msg(f'end_all_position -> symbol: {symbol}, prev_qty: {prev_qty}')
        if prev_qty != 0:
            self.execute_order(symbol, -prev_qty)
            self.send_msg(f'end_all_position...OK')
        return True

    def cancel_open_order(self, symbol, order_id=None, all_order=False):
        self.send_msg(
            f"cancel_open_order -> {'all_order: ' + str(all_order) if all_order else 'order_id: ' + order_id}",
            slack=True)
        if all_order:
            resp = self.exchange.cancel_all_orders(symbol=symbol)
            if resp['code'] == '200':
                self.send_msg(f"cancel_open_order...OK", slack=True)
        else:
            resp = self.exchange.cancel_order(id=order_id, symbol=symbol)
            if resp['status'] == 'canceled':
                self.send_msg(f"cancel_open_order...OK", slack=True)

    def set_leverage(self, symbol, leverage):
        self.send_msg(f"set_leverage -> symbol: {symbol}, leverage: {leverage}")
        self.exchange.set_leverage(leverage, symbol)
        self.send_msg("set_leverage...OK")
        return True

    def get_leverage(self, symbol):
        positions = self.exchange.fetch_positions(symbols=[symbol])
        leverage = positions[0]['leverage']
        return leverage

    def set_margin_mode(self, symbol, margin_mode):
        self.send_msg(f"set_margin_mode -> symbol: {symbol}, margin_mode: {margin_mode}")
        resp = self.exchange.set_margin_mode(marginMode=margin_mode, symbol=symbol)
        if resp['code'] == 200:
            self.send_msg("set_margin_mode...OK")
            return True
        elif resp['code'] == -4046:
            self.send_msg(f"margin_mode is already {margin_mode}")
            return False

    @staticmethod
    def read_api_key():
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
