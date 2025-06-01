'use client';

import React, { useState, useEffect } from 'react';
import { getPriceDepth, getRecentTrades } from '@/lib/api';

const TradingTabs = ({ currentPrice = 70 }) => {
  const [activeTab, setActiveTab] = useState('orderbook');
  const [orderbookData, setOrderbookData] = useState({
    sells: [],
    buys: []
  });
  const [tradeHistory, setTradeHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // 同時獲取五檔報價和交易記錄
        const [depthData, tradesData] = await Promise.all([
          getPriceDepth(),
          getRecentTrades(20)
        ]);

        // 處理五檔資料
        setOrderbookData({
          sells: depthData.sell || [],
          buys: depthData.buy || []
        });

        // 處理交易記錄資料
        setTradeHistory(tradesData || []);
        
        setError(null);
      } catch (err) {
        console.error('獲取交易資料失敗:', err);
        setError('無法獲取交易資料');
        
        // 使用模擬資料作為後備
        setOrderbookData({
          sells: [
            { price: currentPrice + 5, quantity: 1250 },
            { price: currentPrice + 4, quantity: 2100 },
            { price: currentPrice + 3, quantity: 1800 },
            { price: currentPrice + 2, quantity: 3200 },
            { price: currentPrice + 1, quantity: 2800 },
          ],
          buys: [
            { price: currentPrice - 1, quantity: 2900 },
            { price: currentPrice - 2, quantity: 3100 },
            { price: currentPrice - 3, quantity: 1900 },
            { price: currentPrice - 4, quantity: 2400 },
            { price: currentPrice - 5, quantity: 1600 },
          ]
        });
        
        setTradeHistory([
          { timestamp: '14:32:15', price: currentPrice, quantity: 500 },
          { timestamp: '14:31:42', price: currentPrice - 1, quantity: 300 },
          { timestamp: '14:31:05', price: currentPrice + 1, quantity: 800 },
          { timestamp: '14:30:33', price: currentPrice - 2, quantity: 450 },
          { timestamp: '14:30:12', price: currentPrice + 2, quantity: 650 },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // 每30秒更新一次資料
    const interval = setInterval(fetchData, 30000);
    
    return () => clearInterval(interval);
  }, [currentPrice]);

  const OrderBookTab = () => (
    <div className="space-y-4">
      {loading && (
        <div className="text-center text-[#82bee2] py-8">載入中...</div>
      )}
      
      {error && (
        <div className="text-center text-red-400 text-sm py-2">{error}</div>
      )}
      
      {!loading && (
        <>
          {/* 賣盤 */}
          <div>
            <h4 className="text-red-400 text-sm font-semibold mb-2">賣盤</h4>
            <div className="space-y-1">
              {orderbookData.sells.slice().reverse().map((order, index) => {
                const total = order.price * order.quantity;
                return (
                  <div key={index} className="grid grid-cols-3 gap-2 text-xs">
                    <div className="text-red-400 font-mono">${order.price.toFixed(2)}</div>
                    <div className="text-gray-300 text-right font-mono">{order.quantity.toLocaleString()}</div>
                    <div className="text-gray-400 text-right font-mono">${total.toLocaleString()}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 當前價格 */}
          <div className="border-t border-b border-[#82bee2]/20 py-2 text-center">
            <span className="text-white font-bold text-lg">${currentPrice.toFixed(2)}</span>
          </div>

          {/* 買盤 */}
          <div>
            <h4 className="text-green-400 text-sm font-semibold mb-2">買盤</h4>
            <div className="space-y-1">
              {orderbookData.buys.map((order, index) => {
                const total = order.price * order.quantity;
                return (
                  <div key={index} className="grid grid-cols-3 gap-2 text-xs">
                    <div className="text-green-400 font-mono">${order.price.toFixed(2)}</div>
                    <div className="text-gray-300 text-right font-mono">{order.quantity.toLocaleString()}</div>
                    <div className="text-gray-400 text-right font-mono">${total.toLocaleString()}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 表頭 */}
          <div className="grid grid-cols-3 gap-2 text-xs text-[#82bee2] border-t border-[#82bee2]/20 pt-2">
            <div>價格</div>
            <div className="text-right">數量</div>
            <div className="text-right">總額</div>
          </div>
        </>
      )}
    </div>
  );

  const TradeHistoryTab = () => {
    // 格式化時間
    const formatTime = (timestamp) => {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('zh-TW', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    };

    // 計算價格變動（與前一筆交易比較）
    const calculateChange = (currentPrice, index) => {
      if (index >= tradeHistory.length - 1) return 0;
      const prevPrice = tradeHistory[index + 1].price;
      return currentPrice - prevPrice;
    };

    return (
      <div className="space-y-2">
        {loading && (
          <div className="text-center text-[#82bee2] py-8">載入中...</div>
        )}
        
        {error && (
          <div className="text-center text-red-400 text-sm py-2">{error}</div>
        )}
        
        {!loading && (
          <>
            {/* 表頭 */}
            <div className="grid grid-cols-4 gap-2 text-xs text-[#82bee2] border-b border-[#82bee2]/20 pb-2">
              <div>時間</div>
              <div className="text-center">價格</div>
              <div className="text-center">數量</div>
              <div className="text-center">變動</div>
            </div>

            {/* 交易紀錄 */}
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {tradeHistory.map((trade, index) => {
                const change = calculateChange(trade.price, index);
                return (
                  <div key={index} className="grid grid-cols-4 gap-2 text-xs hover:bg-[#1a2e4a]/50 p-2 rounded">
                    <div className="text-gray-300 font-mono">
                      {formatTime(trade.timestamp)}
                    </div>
                    <div className="text-white font-mono text-center">
                      ${trade.price.toFixed(2)}
                    </div>
                    <div className="text-gray-300 text-center font-mono">
                      {trade.quantity.toLocaleString()}
                    </div>
                    <div className={`text-center font-mono font-semibold ${
                      change > 0 ? 'text-red-400' : change < 0 ? 'text-green-400' : 'text-gray-400'
                    }`}>
                      {change > 0 ? '+' : ''}{change !== 0 ? change.toFixed(2) : '-'}
                    </div>
                  </div>
                );
              })}
              {tradeHistory.length === 0 && !loading && (
                <div className="text-center text-gray-400 py-8">暫無交易記錄</div>
              )}
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div className="relative">
      {/* 標籤頁 - 書籤樣式 */}
      <div className="flex relative z-10">
        <button
          onClick={() => setActiveTab('orderbook')}
          className={`px-6 py-3 text-sm font-medium relative ${
            activeTab === 'orderbook'
              ? 'bg-[#1a2e4a] text-[#82bee2] border-t border-l border-r border-[#82bee2]/30 rounded-t-lg -mb-px z-20'
              : 'bg-[#0f203e] text-[#82bee2]/70 hover:text-[#82bee2] hover:bg-[#1a2e4a]/50 rounded-t-lg mr-1 z-10'
          }`}
        >
          五檔股價
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-6 py-3 text-sm font-medium relative ${
            activeTab === 'history'
              ? 'bg-[#1a2e4a] text-[#82bee2] border-t border-l border-r border-[#82bee2]/30 rounded-t-lg -mb-px z-20'
              : 'bg-[#0f203e] text-[#82bee2]/70 hover:text-[#82bee2] hover:bg-[#1a2e4a]/50 rounded-t-lg mr-1 z-10'
          }`}
        >
          交易紀錄
        </button>
      </div>

      {/* 內容區域 */}
      <div className={`bg-[#1a2e4a] rounded-lg border border-[#82bee2]/30 p-4 min-h-[400px] ${
        activeTab === 'orderbook' ? 'rounded-tl-none' : ''
      }`}>
        {activeTab === 'orderbook' ? <OrderBookTab /> : <TradeHistoryTab />}
      </div>
    </div>
  );
};

export default TradingTabs;
