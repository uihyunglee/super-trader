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