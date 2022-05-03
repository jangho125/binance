from contextlib import closing
import ccxt
import time
import datetime
import pandas as pd
import numpy as np
import telegram
from pybit.usdt_perpetual import HTTP
import urllib3
import urllib3, socket
from urllib3.connection import HTTPConnection
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests.exceptions import ReadTimeout
import requests

    
"""
retries = Retry(connect=5, read=3, redirect=3)
http_session = requests.Session()
http_session.mount('https://api.bybit.com', HTTPAdapter(max_retries=retries))
"""




#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
bot = telegram.Bot(token='5382077543:AAGGW3Tkd91p0UqUFP8JRbwYA-d4k5q5ybQ')
chat_id = 5319359286

api_key = "gjNFGc1OwP5s8LOaZR"
secret = "h9IwB4c07TOh8dT9hMB1nDhOSJH3ntGuvvtk"
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


# binance 객체 생성
bybit = ccxt.bybit(config={
    'apiKey' : api_key,
    'secret' : secret,
    'enableratelimit' : True,
    'options' : {'defaultType' : 'future'}
})
session = HTTP(
    endpoint="https://api.bybit.com", 
    api_key= api_key, 
    api_secret= secret,
    request_timeout=300,
    force_retry=True,
    retry_codes=True,
    max_retries=6000,
    retry_delay=5
)

symbol = "BTC/USDT"
fees = 0.0007
timeframe = '4h'
minute = 240
leverage = 3

rate_long_miuns = 0.998 #0.996
rate_short_minus = 1.002 #1.004

take_long_profit = 1.02 #1.01
take_short_profit = 0.98 #0.99

long_loss_cut = 0.99 # 0.99
short_loss_cut = 1.01 #1.01

def cal_target(bybit, symbol):
    # 거래소에서 symbol에 대한 ohlcv 일봉을 얻기
    data = bybit.fetch_ohlcv(
        symbol=symbol,
        timeframe=timeframe,
        since=None,
        limit=12
    )

    # 일봉 데이터를 데이터프레임 객체로 변환
    df = pd.DataFrame(
        data = data,
        columns=['datetime', 'open', 'high', 'low', 'close', 'volume']
    )
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)

    # 전일 데이터와 금일 데이터로 목표가 계산
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    long_target = today['open'] + (yesterday['high'] - yesterday['low']) * long_k
    short_target = today['open'] - (yesterday['high'] - yesterday['low']) * short_k
    
    time.sleep(1)
    return long_target, short_target

def cal_amount(usdt_balance, cur_price, leverage):
    portion = 0.5
    usdt_trade = usdt_balance * portion
    amount = (usdt_trade) * leverage / cur_price
    time.sleep(1)
    return amount

def get_ohlcv(bybit, symbol):
    # 거래소에서 symbol에 대한 ohlcv 일봉을 얻기
    data = bybit.fetch_ohlcv(
        symbol=symbol,
        timeframe=timeframe,
        since=None,
        limit=12
    )

    df = pd.DataFrame(
        data = data,
        columns=['datetime', 'open', 'high', 'low', 'close', 'volume']
    )
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    
    return df

def get_long_crr(df, fees, k):
    
    df = get_ohlcv(bybit, symbol)
    
    df['range'] = df['high'].shift(1) - df['low'].shift(1)
    df['targetPrice'] = df['open'] + df['range'] * k
    df['drr'] = np.where(df['high'] > df['targetPrice'], 
    		(df['close'] / (df['targetPrice']) * (1 - fees)), 1)
    return df['drr'].cumprod()[-2]

def get_best_long_K(symbol, fees) :
    df = get_ohlcv(bybit, symbol)
    time.sleep(1)
    max_crr = 0
    long_K = 0.5
    for k in np.arange(0.1, 1.0, 0.1) :
        crr = get_long_crr(df, fees, k)
        if crr > max_crr :
            max_crr = crr
            long_K = k
    return long_K

def get_best_long_crr(symbol, fees) :
    df = get_ohlcv(bybit, symbol)
    time.sleep(1)
    max_crr = 0
    for k in np.arange(0.1, 1.0, 0.1) :
        long_crr = get_long_crr(df, fees, k)
        if long_crr > max_crr :
            max_crr = long_crr
    return long_crr

def get_short_crr(df, fees, k):
    
    df = get_ohlcv(bybit, symbol)
    
    df['range'] = df['high'].shift(1) - df['low'].shift(1)
    df['targetPrice'] = df['open'] - df['range'] * k
    df['drr'] = np.where(df['low'] < df['targetPrice'], 
    		(df['targetPrice'] / (df['close']) * (1 - fees)), 1)
    return df['drr'].cumprod()[-2]

def get_best_short_K(symbol, fees) :
    df = get_ohlcv(bybit, symbol)
    time.sleep(1)
    max_crr = 0
    short_K = 0.5
    for k in np.arange(0.1, 1.0, 0.1) :
        crr = get_short_crr(df, fees, k)
        if crr > max_crr :
            max_crr = crr
            short_K = k
    return short_K

def get_best_short_crr(symbol, fees) :
    df = get_ohlcv(bybit, symbol)
    time.sleep(1)
    max_crr = 0
    for k in np.arange(0.1, 1.0, 0.1) :
        short_crr = get_short_crr(df, fees, k)
        if short_crr > max_crr :
            max_crr = short_crr
    return short_crr

def get_start_time(bybit, symbol, timeframe):
    data = bybit.fetch_ohlcv(symbol, timeframe = timeframe, limit = 2)
    df = pd.DataFrame(
        data = data,
        columns=['datetime', 'open', 'high', 'low', 'close', 'volume']
    )
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    start_time = df.index[0]
    
    time.sleep(1)
    return start_time

def get_avg_price(bybit, symbol):
    

    markets = bybit.load_markets()
    symbol = 'BTC/USDT'
    market = bybit.market(symbol)
    response = bybit.private_linear_get_position_list({'symbol':market['id']})

    buy_average = response['result'][0]['entry_price']
    
    return buy_average

def highest_value(bybit, symbol):
    # 거래소에서 symbol에 대한 ohlcv 일봉을 얻기
    data = bybit.fetch_ohlcv(
        symbol=symbol,
        timeframe=timeframe,
        since=None,
        limit=1
    )

    df = pd.DataFrame(
        data = data,
        columns=['datetime', 'open', 'high', 'low', 'close', 'volume']
    )
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    
    highest_value = df['high'][-1]
    time.sleep(1)
    return highest_value

def lowest_value(bybit, symbol):
    # 거래소에서 symbol에 대한 ohlcv 일봉을 얻기
    data = bybit.fetch_ohlcv(
        symbol=symbol,
        timeframe=timeframe,
        since=None,
        limit=1
    )

    df = pd.DataFrame(
        data = data,
        columns=['datetime', 'open', 'high', 'low', 'close', 'volume']
    )
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    
    lowest_value = df['low'][-1]
    time.sleep(1)
    return lowest_value




while True:
    
    start_time = get_start_time(bybit, symbol, timeframe) 
    now = datetime.datetime.now() 
    end_time = start_time + datetime.timedelta(minutes=minute) - datetime.timedelta(seconds=300) 
    time.sleep(1)
        
    balance = bybit.fetch_balance()
    usdt_balance = balance['total']['USDT']
    buy_average = get_avg_price(bybit, symbol)
    long_crr = get_best_long_crr(symbol, fees)
    short_crr = get_best_short_crr(symbol, fees)
    high = highest_value(bybit, symbol)
    low = lowest_value(bybit, symbol)
    long_k = get_best_long_K(symbol, fees)
    short_k = get_best_short_K(symbol, fees)
        
    position = {
        "type": None,
        "amount": 0
    }
        

    if start_time < now < end_time:
        long_target, short_target = cal_target(bybit, symbol)
        
        
        
        
        print(start_time)
        print(now)
        print(end_time)
        print(usdt_balance)
        print(long_k, long_crr)
        print(short_k, short_crr)
        print("high", "low")
        print(high, low)
        print("long_target", "short_target")
        print(long_target, short_target)
        print("매매 시작")
        
        op_mode = False
        
        i = 0
        
        while i < 4:
            now = datetime.datetime.now()
            btc = bybit.fetch_ticker(symbol)
            cur_price = btc['last']
            total_amount = round(cal_amount(usdt_balance, cur_price, leverage), 3)
                
            
            time.sleep(1)
                
                # 1차 매수
                
            if i == 0 and op_mode == False:
                    
                    if i == 0 and (long_target - 50) <= cur_price < (long_target + 50) and long_crr > 1:
                        amount = total_amount * 0.25
                        position['type'] = 'long'
                        position['amount'] = amount
                        session.place_active_order(
                            symbol="BTCUSDT",
                            side="Buy",
                            order_type="Market",
                            qty= amount,
                            price=cur_price,
                            time_in_force="GoodTillCancel",
                            reduce_only=False,
                            close_on_trigger=False
                            )
                        time.sleep(10)
                        first_opening_price = bybit.fetch_closed_orders(symbol, None, 1)
                        first_purchase = first_opening_price[0]['price']
                        print(first_purchase)
                        print("1차 LONG 매수 성공")
                        
                        time.sleep(10)
                        i += 1
                        op_mode = True
                                               
                    elif i == 0 and (short_target - 50) <= cur_price < (short_target + 50) and short_crr > 1:
                        amount = total_amount * 0.25
                        position['type'] = 'short'
                        position['amount'] = amount
                        session.place_active_order(
                            symbol="BTCUSDT",
                            side="Sell",
                            order_type="Market",
                            qty= amount,
                            price=cur_price,
                            time_in_force="GoodTillCancel",
                            reduce_only=False,
                            close_on_trigger=False
                            )
                        time.sleep(10)
                        first_opening_price = bybit.fetch_closed_orders(symbol, None, 1)
                        first_purchase = first_opening_price[0]['price']
                        print(first_purchase)
                        print("1차 SHORT 매수 성공")
                        
                        time.sleep(10)
                        i += 1
                        op_mode = True
                        
                    elif i == 0 and now > end_time:
                        print("i = 0 4시간 후 매매 종료")
                        break
                    
                    else:
                        print("i = 0, waiting")
                    
                # 2차 매수    
                
            elif i == 1 and op_mode == True:
                    
                    if i == 1 and cur_price < float(first_purchase) * rate_long_miuns and position['type'] == 'long':
                        amount = total_amount * 0.25
                        position['type'] = 'long'
                        position['amount'] = amount
                        session.place_active_order(
                            symbol="BTCUSDT",
                            side="Buy",
                            order_type="Market",
                            qty= amount,
                            price=cur_price,
                            time_in_force="GoodTillCancel",
                            reduce_only=False,
                            close_on_trigger=False
                            )
                        time.sleep(10)
                        second_opening_price = bybit.fetch_closed_orders(symbol, None, 1)
                        second_purchase = second_opening_price[0]['price']
                        print(second_purchase)
                        print("2차 LONG 매수 성공")
                        time.sleep(1)
                        i += 1
                                              
                    elif i == 1 and cur_price > float(first_purchase) * rate_short_minus and position['type'] == 'short':
                        amount = total_amount * 0.25
                        position['type'] = 'short'
                        position['amount'] = amount
                        session.place_active_order(
                            symbol="BTCUSDT",
                            side="Sell",
                            order_type="Market",
                            qty= amount,
                            price=cur_price,
                            time_in_force="GoodTillCancel",
                            reduce_only=False,
                            close_on_trigger=False
                            )
                        time.sleep(10)
                        second_opening_price = bybit.fetch_closed_orders(symbol, None, 1)
                        second_purchase = second_opening_price[0]['price']
                        print(second_purchase)
                        print("2차 SHORT 매수 성공")
                        
                        time.sleep(10)
                        i += 1
                    
                # 익절
                                           
                    elif i == 1 and cur_price > float(first_purchase) * take_long_profit and position['type'] == 'long':
                        if position['type'] == 'long':
                            price = float(high) - 100
                            amount = total_amount * 0.25
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Sell",
                                order_type="Limit",
                                qty= amount,
                                price=price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("LONG 익절")
                            
                            break
                    
                    elif i == 1 and cur_price < float(first_purchase) * take_short_profit and position['type'] == 'short':
                        if position['type'] == 'short':
                            price = float(low) + 100
                            amount = total_amount * 0.25
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Buy",
                                order_type="Limit",
                                qty= amount,
                                price=price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("SHORT 익절")
                            
                            break
                    
                    elif i == 1 and now > end_time:
                        if position['type'] == 'long':
                            amount = total_amount * 0.25
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Sell",
                                order_type="Market",
                                qty= amount,
                                price=cur_price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("4시간 후 LONG 매도")
                            
                            break
                    
                            
                        
                        elif position['type'] == 'short':
                            amount = total_amount * 0.25
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Buy",
                                order_type="Market",
                                qty= amount,
                                price=cur_price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("4시간 후 SHORT 매도")
                            
                            
                            break
                
                    else:
                        print("i = 1, waiting")
                    
                # 3차 매수
                
            elif i == 2 and op_mode == True:
                    
                    if i == 2 and cur_price < float((first_purchase + second_purchase) / 2) * rate_long_miuns and position['type'] == 'long':
                        amount = total_amount * 0.5
                        position['type'] = 'long'
                        position['amount'] = amount 
                        session.place_active_order(
                            symbol="BTCUSDT",
                            side="Buy",
                            order_type="Market",
                            qty= amount,
                            price=cur_price,
                            time_in_force="GoodTillCancel",
                            reduce_only=False,
                            close_on_trigger=False
                            )
                        time.sleep(10)
                        third_opening_price = bybit.fetch_closed_orders(symbol, None, 1)
                        third_purchase = third_opening_price[0]['price']
                        print(third_purchase)
                        time.sleep(10)
                        i += 1
                        print("3차 LONG 매수 성공")
                        
                        
                    elif i == 2 and cur_price > float((first_purchase + second_purchase) / 2) * rate_short_minus and position['type'] == 'short':
                        amount = total_amount * 0.5
                        position['type'] = 'short'
                        position['amount'] = amount 
                        session.place_active_order(
                            symbol="BTCUSDT",
                            side="Sell",
                            order_type="Market",
                            qty= amount,
                            price=cur_price,
                            time_in_force="GoodTillCancel",
                            reduce_only=False,
                            close_on_trigger=False
                            )
                        time.sleep(10)
                        third_opening_price = bybit.fetch_closed_orders(symbol, None, 1)
                        third_purchase = third_opening_price[0]['price']
                        print(third_purchase)
                        time.sleep(10)
                        i += 1  
                        print("3차 SHORT 매수 성공")
                        
                    
                # 익절
                        
                    elif i == 2 and cur_price > float((first_purchase + second_purchase) / 2) * take_long_profit and position['type'] == 'long':
                        if position['type'] == 'long':
                            price = float(high) - 100
                            amount = total_amount * 0.5
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Sell",
                                order_type="Limit",
                                qty= amount,
                                price=price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("LONG 익절")
                            
                            break
                    
                    elif i == 2 and cur_price < float((first_purchase + second_purchase) / 2) * take_short_profit and position['type'] == 'short':
                        if position['type'] == 'short':
                            price = float(low) + 100
                            amount = total_amount * 0.5
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Buy",
                                order_type="Limit",
                                qty= amount,
                                price=price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("SHORT 익절")
                            
                            break
                    
                    elif i == 2 and now > end_time:
                        if position['type'] == 'long':
                            amount = total_amount * 0.5
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Sell",
                                order_type="Market",
                                qty= amount,
                                price=cur_price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("4시간 후 LONG 매도")
                            
                            break
                        
                        elif position['type'] == 'short':
                            amount = total_amount * 0.5
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Buy",
                                order_type="Market",
                                qty= amount,
                                price=cur_price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("4시간 후 SHORT 매도")
                            
                            break
                    
                    else:
                        print("i = 2, waiting")
                    
                    
                # 손절
            
            elif i == 3 and op_mode == True:
                    
                    if i == 3 and cur_price < float((first_purchase + second_purchase + third_purchase) / 3) * long_loss_cut and position['type'] == 'long':
                        
                        if position['type'] == 'long':
                            amount = total_amount
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Sell",
                                order_type="Market",
                                qty= amount,
                                price=cur_price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("3차 LONG 매수 후 5% 손절")
                            
                            break
                        
                    elif i == 3 and cur_price > float((first_purchase + second_purchase + third_purchase) / 3) * short_loss_cut and position['type'] == 'short':
                        
                        if position['type'] == 'short':
                            amount = total_amount
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Buy",
                                order_type="Market",
                                qty= amount,
                                price=cur_price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("3차 SHORT매수 후 5% 손절")
                            
                            break
                            
                # 익절
                        
                    elif i == 3 and cur_price > float((first_purchase + second_purchase + third_purchase) / 3) * take_long_profit and position['type'] == 'long':
                        if position['type'] == 'long':
                            price = float(high) - 100
                            amount = total_amount
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Sell",
                                order_type="Limit",
                                qty= amount,
                                price=price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("LONG 익절")
                            
                            break
                    
                    elif i == 3 and cur_price < float((first_purchase + second_purchase + third_purchase) / 3) * take_short_profit and position['type'] == 'short':
                        if position['type'] == 'short':
                            price = float(low) + 100
                            amount = total_amount
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Buy",
                                order_type="Limit",
                                qty= amount,
                                price=price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("SHORT 익절")
                                                    
                            break
                    
                    elif i == 3 and now > end_time:
                        if position['type'] == 'long':
                            amount = total_amount
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Sell",
                                order_type="Market",
                                qty= amount,
                                price=cur_price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("4시간 후 LONG 매도")
                            
                            break
                        
                        elif position['type'] == 'short':
                            amount = total_amount
                            session.place_active_order(
                                symbol="BTCUSDT",
                                side="Buy",
                                order_type="Market",
                                qty= amount,
                                price=cur_price,
                                time_in_force="GoodTillCancel",
                                reduce_only=True,
                                close_on_trigger=False
                                )
                            time.sleep(10)
                            position['type'] == None
                            print("4시간 후 SHORT 매도")
                            
                            break
                    
                    else:
                        print("i = 3, waiting")
                            
            else:
                    print("else")
    
    
    elif now > end_time:
        print("매매 종료")
