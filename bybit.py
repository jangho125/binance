import ccxt
import time
import datetime
import pandas as pd
import numpy as np




api_key = "api-key"
secret = "secret"


# binance 객체 생성
bybit = ccxt.bybit(config={
    'apiKey' : api_key,
    'secret' : secret,
    'enableratelimit' : True,
    'options' : {'defaultType' : 'future'}
})





symbol = "BTC/USDT"
fees = 0.0007
timeframe = '4h'
leverage = 3

def cal_target(bybit, symbol):
    # 거래소에서 symbol에 대한 ohlcv 일봉을 얻기
    data = bybit.fetch_ohlcv(
        symbol=symbol,
        timeframe='4h',
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
        timeframe='4h',
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
        timeframe='4h',
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
        timeframe='4h',
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





balance = bybit.fetch_balance()
usdt_balance = balance['total']['USDT']
buy_average = get_avg_price(bybit, symbol)
long_crr = get_best_long_crr(symbol, fees)
short_crr = get_best_short_crr(symbol, fees)
high = highest_value(bybit, symbol)
low = lowest_value(bybit, symbol)
long_k = get_best_long_K(symbol, fees)
short_k = get_best_short_K(symbol, fees)


print(usdt_balance)

position = {
    "type": None,
    "amount": 0
}


while True:
    
    start_time = get_start_time(bybit, symbol, timeframe) 
    now = datetime.datetime.now() 
    end_time = start_time + datetime.timedelta(minutes=240) - datetime.timedelta(seconds=20) # 매매 시작
    time.sleep(1)
    print(start_time)
    print(now)
    print(end_time)    
        
    if start_time < now < end_time:
        long_target, short_target = cal_target(bybit, symbol)
        
        
        
        i = 0
        while i < 4:
            now = datetime.datetime.now()
            btc = bybit.fetch_ticker(symbol)
            cur_price = btc['last']
            amount = cal_amount(usdt_balance, cur_price, leverage)
            time.sleep(1)
            
           
            print("script is running")
            
            
            
            # 1차 매수
            
            if i == 0 and (long_target -100) <= cur_price < (long_target + 100) and long_crr > 1:
                position['type'] = 'long'
                position['amount'] = amount
                bybit.create_market_buy_order(symbol, amount * 0.25)
                time.sleep(1)
                buy_average = get_avg_price(bybit, symbol)
                i += 1
                print("1차 LONG 매수 성공")
            elif i == 0 and (short_target - 100) <= cur_price < (short_target + 100) and short_crr > 1:
                position['type'] = 'short'
                position['amount'] = amount
                bybit.create_market_sell_order(symbol, amount * 0.25)
                time.sleep(1)
                buy_average = get_avg_price(bybit, symbol)
                i += 1
                print("1차 SHORT 매수 성공")
                
            
            # 2차 매수    
            
            if i == 1 and cur_price < float(buy_average) * 0.94:
                position['type'] = 'long'
                position['amount'] = amount
                bybit.create_market_buy_order(symbol, amount * 0.25)
                time.sleep(1)
                buy_average = get_avg_price(bybit, symbol)
                i += 1
                print("2차 LONG 매수 성공")
            elif i == 1 and cur_price > float(buy_average) * 1.06:
                position['type'] = 'short'
                position['amount'] = amount
                bybit.create_market_sell_order(symbol, amount * 0.25)
                time.sleep(1)
                buy_average = get_avg_price(bybit, symbol)
                i += 1
                print("2차 SHORT 매수 성공")
                
                
            # 3차 매수
            
            if i == 2 and cur_price < float(buy_average) * 0.94:
                position['type'] = 'long'
                position['amount'] = amount
                bybit.create_market_buy_order(symbol, amount * 0.5)
                time.sleep(1)
                buy_average = get_avg_price(bybit, symbol)
                i += 1
                print("3차 LONG 매수 성공")
            elif i == 2 and cur_price > float(buy_average) * 1.06:
                position['type'] = 'short'
                position['amount'] = amount
                bybit.create_market_sell_order(symbol, amount * 0.5)
                time.sleep(1)
                buy_average = get_avg_price(bybit, symbol)
                i += 1  
                print("3차 SHORT 매수 성공")
                
            
            # 매도 조건
            
            if i == 3 and cur_price < float(buy_average) * 0.95:
                if position['type'] == 'long':
                    bybit.create_market_sell_order(symbol, amount)
                    time.sleep(1)
                    position['type'] == None
                    print("3차 LONG 매수 후 5% 손절")
                
            elif i == 3 and cur_price > float(buy_average) * 1.05:
                if position['type'] == 'short':
                    bybit.create_market_buy_order(symbol, amount)
                    time.sleep(1)
                    position['type'] == None
                    print("3차 SHORT매수 후 5% 손절")
            
            if cur_price > float(buy_average) * 1.06:
                if i == 0:
                    amount = position['amount'] * 0.25
                elif i == 1:
                    amount = position['amount'] * 0.5
                elif i == 2:
                    amount = position['amount'] 
                elif i == 3:
                    amount = position['amount'] 
                    
                price = high * 0.97
                if position['type'] == 'long':
                    bybit.create_limit_sell_order(symbol, amount, price)
                    time.sleep(1)
                    position['type'] == None
                    print("LONG 익절")
                    
            elif cur_price < float(buy_average) * 0.94:
                if i == 0:
                    amount = position['amount'] * 0.25
                elif i == 1:
                    amount = position['amount'] * 0.5
                elif i == 2:
                    amount = position['amount'] 
                elif i == 3:
                    amount = position['amount']    
                
                price = low * 1.03
                if position['type'] == 'short':
                    bybit.create_limit_buy_order(symbol, amount, price)
                    time.sleep(1)
                    position['type'] == None
                    print("SHORT 익절")
            
            # 매매 종료
            
            if now > end_time:
                if i == 0:
                    amount = position['amount'] * 0.25
                elif i == 1:
                    amount = position['amount'] * 0.5
                elif i == 2:
                    amount = position['amount'] 
                elif i == 3:
                    amount = position['amount']
                    
                if position['type'] == 'long':
                    bybit.create_market_sell_order(symbol, amount)
                    time.sleep(1)
                    position['type'] == None
                    print("4시간 후 LONG 매도")
                    
                    break 
                
                elif position['type'] == 'short':
                    bybit.create_market_buy_order(symbol, amount)
                    time.sleep(1)
                    position['type'] == None
                    print("4시간 후 SHORT 매도")
                    
                    break
