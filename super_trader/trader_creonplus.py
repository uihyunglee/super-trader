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
    cpOrderHist = win32com.client.Dispatch('CpTrade.CpTd5341')
    
    def __init__(self):
        self.cpTdUtil.TradeInit()
        self.acc = self.cpTdUtil.AccountNumber[0]
        self.accFlag = self.cpTdUtil.GoodsList(self.acc, 1)
        super().__init__()
        
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
    
    def get_cur_total_asset(self):
        self.cpTdUtil.TradeInit()
        self.cpBalance.SetInputValue(0, self.acc)
        self.cpBalance.SetInputValue(1, self.accFlag[0])
        self.cpBalance.SetInputValue(2, 50)
        self.cpBalance.SetInputValue(3, '2')
        self.cpBalance.BlockRequest()
        total_asset = self.cpBalance.GetHeaderValue(3)
        return total_asset
    
    def get_cur_price(self, codes, price_type=['price']):
        codes = codes.copy()
        type_dict = {'price':4,'ask':5,'bid':6,'vol':7}
        cur_info_dict = {}
        while len(codes):
            codes_str = ''.join(codes[:110])
            codes = codes[110:]

            self.cpStockMstM.SetInputValue(0, codes_str)  # max: 110
            self.cpStockMstM.BlockRequest()

            data_len = self.cpStockMstM.GetHeaderValue(0)
            for i in range(data_len):
                code = self.cpStockMstM.GetDataValue(0,i)
                cur_info_dict[code] = {}
                for pt in price_type:
                    cur_data = self.cpStockMstM.GetDataValue(type_dict[pt],i)
                    cur_info_dict[code].update({pt:cur_data})
        return pd.DataFrame(cur_info_dict).T
    
    def get_trad_price(self, cur_price_df, td_type, tic=1):
        if td_type == 'buy':
            df = cur_price_df.apply(lambda p: p - (self.cpStockCode.GetPriceUnit(p.index, p) * tic), axis=1)
        elif td_type == 'sell':
            df = cur_price_df.apply(lambda p: p + (self.cpStockCode.GetPriceUnit(p.index, p) * tic), axis=1)
        return df
    
    def buy(self, code, price, qty):
        try:
            self.cpTdUtil.TradeInit()
            
            self.cpOrder.SetInputValue(0, "2")  # 1:매도, 2:매수
            self.cpOrder.SetInputValue(1, self.acc)  # 계좌
            self.cpOrder.SetInputValue(2, self.accFlag[0])  # 상품 구분
            self.cpOrder.SetInputValue(3, code)  # 종목코드
            self.cpOrder.SetInputValue(4, qty)  # 매수 수량
            if price == 'market':
                self.cpOrder.SetInputValue(8, "03")
            else:
                self.cpOrder.SetInputValue(5, price)  # 매수 가격
                self.cpOrder.SetInputValue(8, "01")  # 주문호가 1: 보통, 3: 시장가, 5:조건부, 12: 최유리, 13: 최우선
            
            rq = self.cpOrder.BlockRequest()
            self.send_msg(f'매수 주문 요청: [{code}, {price}, {qty}]-> {rq}', log_level='info', slack=True)
            dibstatus = self.cpOrder.GetDibStatus()
            self.send_msg(f'통신상태: {dibstatus} {self.cpOrder.GetDibMsg1()}')
            
            if (rq == 0) and (dibstatus == 0):
                self.send_msg(f'매수 주문 정상 처리: [{code}, {price}, {qty}]-> {rq}', log_level='debug', slack=False)
                return True
            elif rq == 4: # 주문요청제한초과
                self.send_msg(f'매수 주문 제한: [{code}, {price}, {qty}]-> {rq}', log_level='debug', slack=False)
                remain_time = self.cpCybos.LimitRequestRemainTime
                time.sleep(remain_time/1000)
                return self.buy(code, price, qty)
            else:
                return False
                
        except Exception as e:
            self.send_msg(f'buy({code}, {price}, {qty}) exception! -> {e}', log_level='error', slack=True)
    
    def sell(self, code, price, qty):
        try:
            self.cpTdUtil.TradeInit()
            
            self.cpOrder.SetInputValue(0, "1")
            self.cpOrder.SetInputValue(1, self.acc)
            self.cpOrder.SetInputValue(2, self.accFlag[0])
            self.cpOrder.SetInputValue(3, code)
            self.cpOrder.SetInputValue(4, qty)
            if price == 'market':
                self.cpOrder.SetInputValue(8, "03")
            else:
                self.cpOrder.SetInputValue(5, price)
                self.cpOrder.SetInputValue(8, "01")
            
            rq = self.cpOrder.BlockRequest()
            self.send_msg(f'매도 주문 요청: [{code}, {price}, {qty}]-> {rq}', log_level='info', slack=True)
            dibstatus = self.cpOrder.GetDibStatus()
            self.send_msg(f'통신상태: {dibstatus} {self.cpOrder.GetDibMsg1()}')
            
            if (rq == 0) and (dibstatus == 0):
                self.send_msg(f'매도 주문 정상 처리: [{code}, {price}, {qty}]-> {rq}', log_level='debug', slack=False)
                return True
            elif rq == 4: # 주문요청제한초과
                self.send_msg(f'매도 주문 제한: [{code}, {price}, {qty}]-> {rq}', log_level='debug', slack=False)
                remain_time = self.cpCybos.LimitRequestRemainTime
                time.sleep(remain_time/1000)
                return self.sell(code, price, qty)
            else:
                return False
                
        except Exception as e:
            self.send_msg(f'sell({code}, {price}, {qty}) exception! -> {e}', log_level='error', slack=True)

    def sell_all(self):
        holding_stocks = self.get_stock_balance('all')
        for stock in holding_stocks:
            self.sell(stock['code'], 'market', stock['qty'])
        while self.get_stock_balance('all'):
            time.sleep(1)
        self.send_msg('Sell all holding stocks...OK', slack=True)

    def get_today_order_history(self):
        self.cpTdUtil.TradeInit()
        self.cpOrderHist.SetInputValue(0, self.acc)
        self.cpOrderHist.SetInputValue(1, self.accFlag[0])
        self.cpOrderHist.SetInputValue(4, '0')
        self.cpOrderHist.SetInputValue(5, 20)
        self.cpOrderHist.BlockRequest()

        cnt = self.cpOrderHist.GetHeaderValue(6)

        for i in range(cnt):
            code = self.cpOrderHist.GetDataValue(3, i)
            prc_type = self.cpOrderHist.GetDataValue(6, i)  # 01: 보통, 03: 시장가
            order_qty = self.cpOrderHist.GetDataValue(7, i)
            exec_qty = self.cpOrderHist.GetDataValue(10, i)
            order_prc = self.cpOrderHist.GetDataValue(8, i)  # 0: 시장가
            exec_prc = self.cpOrderHist.GetDataValue(11, i)
            order_type = self.cpOrderHist.GetDataValue(35, i)  # 1:매도, 2: 매수

            self.send_msg(f"{code}, {prc_type}, {order_qty}, {exec_qty}, {order_prc}, {exec_prc}, {order_type}")