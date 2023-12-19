from abc import ABCMeta, abstractmethod
import json, sys
from datetime import datetime as dt

import requests
from sl4p import *


class SuperTrader(metaclass=ABCMeta):
    def __init__(self):
        self.log = self.get_logger()
        self.set_slack()
        self.check_market_open()
        self.check_system()

    def get_logger(self):
        log_cfg = {
            "LOG": {
                "console_level": "INFO",
                "console_format": "simple",
                
                "logging_level": "DEBUG",
                "logging_format": "basic",

                "logfile_savedir": "logs",
                "logfile_name": f"{dt.now().strftime('%Y%m%d')}",
                "save_period_type": "D"
            }
        }
        logger = sl4p.getLogger(__file__, cfg=log_cfg)
        logger.info("Start Trading with SL4P Logging!")

        log = {}
        log['debug'] = logger.debug
        log['info'] = logger.info
        log['warning'] = logger.warning
        log['error'] = logger.error
        log['critical'] = logger.critical
        return log
    
    def set_slack(self):
        with open('config.json', 'r') as json_file:
            _config = json.load(json_file)
        slack_info = _config['slack']
        self.token = slack_info['token']
        self.channel = slack_info['channel']
        self.send_msg('set_slack...OK')
        return True

    def send_msg(self, msg, log_level='info', slack=False):
        self.log[log_level](msg)
        if slack:
            cur_time = dt.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                slack_res = requests.post(
                    url="https://slack.com/api/chat.postMessage",
                    headers={"Authorization": "Bearer "+ self.token},
                    data={"channel": self.channel, "text": f'[{cur_time}] {msg}'}
                )
            except:
                msg = 'Slack message sending failed. Please check info_slack.'
                self.send_msg(msg, log_level='warning', slack=False)
                
    def exit_system(self):
        self.send_msg('Exit the program.', log_level='info', slack=True)
        sys.exit(0)
        
    def check_market_open(self):
        today = dt.now()
        is_weekend = today.weekday() in [5,6]
        
        year = str(today.year)
        with open("config.json", "r") as json_file:
            _config = json.load(json_file)
        holidays = _config['holiday']    
        this_year_holidays = holidays[year]
        today = int(today.strftime('%Y%m%d'))
        is_holiday = today in this_year_holidays
        
        if is_weekend or is_holiday:
            self.send_msg('Today is Closed day.')
            self.exit_system()
        else:
            self.send_msg('check_market_open...OK', slack=True)
    
    def check_system(self):
        """시스템 체크하여 문제 있으면 에러 발생 후 종료"""
        pass
    
    def buy(self, code, price, qty):
        """price='market'으로 시장가 매수"""
        pass
    
    def sell(self, code, price, qty):
        """price='market'으로 시장가 매도"""
        pass
    
    def get_ohlcv(self, code, start, end):
        """과거 기간 OHLCV 조회"""
        pass
    
    def get_stock_balance(self, code, acc_display=False):
        """잔고 조회"""
        pass
    
    def get_cur_cash(self):
        """예수금 조회"""
        pass
    
    def get_cur_price(self, code):
        """현재가 조회"""
        pass
    
    def sell_all(self):
        """보유 종목 전량 매도"""
        pass