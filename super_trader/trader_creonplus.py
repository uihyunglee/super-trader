import ctypes
import win32com.client
import time

import numpy as np
import pandas as pd

from .super_trader import SuperTrader


class CreonPlusTrader(SuperTrader):
    cpCybos = win32com.client.Dispatch('CpUtil.CpCybos')
    cpTdUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')
    cpStockMstM = win32com.client.Dispatch("DsCbo1.StockMstM")
    cpStockCode = win32com.client.Dispatch("CpUtil.CpStockCode")
    cpBalance = win32com.client.Dispatch('CpTrade.CpTd6033')
    cpCash = win32com.client.Dispatch('CpTrade.CpTdNew5331A')
    cpOrder = win32com.client.Dispatch('CpTrade.CpTd0311')
    
    def __init__(self):
        super().__init__()
        self.cpTdUtil.TradeInit()
        self.acc = self.cpTdUtil.AccountNumber[0]
        self.accFlag = self.cpTdUtil.GoodsList(self.acc, 1)
        
    def check_system(self):
        if not ctypes.windll.shell32.IsUserAnAdmin():
            raise Exception('check_creon_system() : admin user -> FAILED')
        if (self.cpCybos.IsConnect == 0):
            raise Exception('check_creon_system() : connect to server -> FAILED')
        if (self.cpTdUtil.TradeInit(0) != 0):
            raise Exception('check_creon_system() : init trade -> FAILED')
        self.send_msg('check_creon_system...OK')

    def get_stock_balance(self, code, acc_display=False):
        self.cpTdUtil.TradeInit()
        self.cpBalance.SetInputValue(0, self.acc)
        self.cpBalance.SetInputValue(1, self.accFlag[0])
        self.cpBalance.SetInputValue(2, 50)
        self.cpBalance.SetInputValue(3, '2')
        self.cpBalance.BlockRequest()
        
        stocks_cnt = self.cpBalance.GetHeaderValue(7)
        if (code == 'all') and acc_display:
            acc_name = self.cpBalance.GetHeaderValue(0)
            total_asset = self.cpBalance.GetHeaderValue(3)
            total_profit = self.cpBalance.GetHeaderValue(4)
            total_rtn = self.cpBalance.GetHeaderValue(8)
            cash = self.cpBalance.GetHeaderValue(9)
            stock_asset = self.cpBalance.GetHeaderValue(11)

            self.send_msg(f'계좌명       : {acc_name}', log_level='info', slack=True)
            self.send_msg(f'총 자산      : {total_asset:,}원', log_level='info', slack=True)
            self.send_msg(f'총 수익금    : {total_profit:,}원', log_level='info', slack=True)
            self.send_msg(f'총 수익률    : {total_rtn:.2f}%', log_level='info', slack=True)
            self.send_msg(f'보유 주식 수 : {stocks_cnt}종목', log_level='info', slack=True)
            self.send_msg(f'주식 평가금액: {stock_asset}', log_level='info', slack=True)
            self.send_msg(f'예수금       : {cash:,}원', log_level='info', slack=True)
        
        stocks = []
        for i in range(stocks_cnt):
            stock_name = self.cpBalance.GetDataValue(0, i)#
            today_buy_cnt = self.cpBalance.GetDataValue(6, i)
            e_stock_qty = self.cpBalance.GetDataValue(7, i)#
            e_stock_asset = self.cpBalance.GetDataValue(9, i)#
            e_stock_profit = self.cpBalance.GetDataValue(10, i)#
            e_stock_rtn = self.cpBalance.GetDataValue(11, i)
            stock_code = self.cpBalance.GetDataValue(12, i)#
            avg_buy_price = self.cpBalance.GetDataValue(18, i)#
            
            if code == 'all':
                if acc_display:
                    print_info1 = f'{i+1} {stock_code}({stock_name}): '
                    print_info2 = f'{e_stock_qty:,}주 * {avg_buy_price:,}원 + {e_stock_profit:,}원 = {e_stock_asset:,}원'
                    print_info3 = f' | {e_stock_rtn:.2f}% | 금일 체결: {today_buy_cnt}'
                    self.send_msg(print_info1 + print_info2 + print_info3, log_level='info', slack=True)
                stocks.append({'code': stock_code, 'qty': e_stock_qty})
            
            if code == stock_code:
                return stock_code, e_stock_qty
        if code == 'all':
            return stocks
        else:
            return code, 0
    
    def get_cur_cash(self):
        self.cpTdUtil.TradeInit()
        self.cpCash.SetInputValue(0, self.acc)
        self.cpCash.SetInputValue(1, self.accFlag[0])
        self.cpCash.BlockRequest()
        return self.cpCash.GetHeaderValue(9)