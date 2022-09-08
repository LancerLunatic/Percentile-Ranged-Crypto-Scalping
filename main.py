#region imports
from AlgorithmImports import *
#endregion
import numpy as np
import pandas as pd
from collections import deque

class QuantumOptimizedPrism(QCAlgorithm):

    def Initialize(self):
        
        '''Look back for breakout'''
        self.Lookback = 168
        
        self.SetBrokerageModel(BrokerageName.GDAX, AccountType.Cash)
        self.SetCash(25000)
        self.symbolList = ["BTCUSD", "ETHUSD", "BCHUSD", "UNIUSD", 
                           "XLMUSD", "MKRUSD", "LINKUSD", "ATOMUSD",
                           "LTCUSD"]
                           # "BCHBTC", "ATOMBTC", "DASHBTC",  "XLMBTC", "MKRBTC", "LINKETH", "ETHBTC",
        self.rollingWindow = {}
        self.weights = {}
        self.flashcheck = {}
        
        for name in self.symbolList:
            self.AddCrypto(name, Resolution.Hour, Market.GDAX)
            self.rollingWindow["close_top_{0}".format(name)] = deque(maxlen=self.Lookback)
            self.weights[name] =  0.25
            self.flashcheck[name] = 0
            
        self.SetStartDate(2018, 1, 1)
        self.SetBenchmark("BTCUSD")
        self.SetWarmUp(self.Lookback)
        self.Notify.Sms("17574091415", "Apollos, The Cryptocurrency Algorithm is live trading BTCUSD ETHUSD BCHUSD UNIUSD XLMUSD MKRUSD LINKUSD ATOMUSD LTCUSD")
    def flashcrashcheck(self, symbol, price):
        '''Check for significant price change'''
        pchange = (price - self.flashcheck[symbol]) /  ((price + self.flashcheck[symbol])/2)  * 100
        self.flashcheck[symbol] = price
        
        if pchange >= 10:
            flash = True
            #self.Log("{} - FlashCrash: {}".format(self.Time, pchange))
        else:
            flash = False
            
        return flash
        
    def indicator(self, sym):
        '''Rolling quantile for upper and lower bounds'''
        top = pd.Series(self.rollingWindow["close_top_"+str(sym)]).quantile(0.99)
        bot = pd.Series(self.rollingWindow["close_top_"+str(sym)]).quantile(0.01)
        
        return top, bot

    def OnData(self, data):
        if self.IsWarmingUp: return
        #if not self.rollingWindow.empty
        '''The data is bugged on this day for BTC'''
        if self.Time.day == 10 and self.Time.month == 8 and self.Time.year == 2018:
            return
        
        for symbol in self.symbolList:
            if not data.ContainsKey(symbol): return
            sym_price = data[symbol].Price
            stop = self.flashcrashcheck(symbol, sym_price)
            self.rollingWindow["close_top_{0}".format(symbol)].appendleft(sym_price)
            
            if not self.IsWarmingUp and not stop:
                top, bot = self.indicator(symbol)
                #usdTotal = self.Portfolio.CashBook["USD"].Amount
                #limitPrice = round(self.Securities[symbol].Price * 0.999, 2)
                #quantity = usdTotal * 0.1 / limitPrice
                if sym_price >= top:
                    #self.LimitOrder(symbol, quantity, limitPrice)
                    self.SetHoldings(symbol, self.weights[symbol]) 
                elif sym_price <= bot:
                    self.Liquidate(symbol)
                else:
                    pass
                #if symbol == "BTCUSD":
                #    if sym_price >= top:
                #        self.Notify.Sms("17574091415", "Apollos - Go long BTC Futures")
                #        #self.Debug("text sent to trade")
    def OnOrderEvent(self, orderEvent):
        
        self.Log("{} {}".format(self.Time, orderEvent.ToString()))
        self.Notify.Email("apolloshill@gmail.com", "Coinbase Pro Algorithm Alert", str(orderEvent) + " and Total Unrealized Profit is: " + str(self.Portfolio.TotalUnrealisedProfit))
