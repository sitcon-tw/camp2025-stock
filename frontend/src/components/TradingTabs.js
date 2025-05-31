'use client';

import React, { useState } from 'react';

const TradingTabs = ({ currentPrice = 70 }) => {
  const [activeTab, setActiveTab] = useState('orderbook');

  // 模擬五檔
  const orderbookData = {
    sells: [
      { price: currentPrice + 5, quantity: 1250, total: (currentPrice + 5) * 1250 },
      { price: currentPrice + 4, quantity: 2100, total: (currentPrice + 4) * 2100 },
      { price: currentPrice + 3, quantity: 1800, total: (currentPrice + 3) * 1800 },
      { price: currentPrice + 2, quantity: 3200, total: (currentPrice + 2) * 3200 },
      { price: currentPrice + 1, quantity: 2800, total: (currentPrice + 1) * 2800 },
    ],
    buys: [
      { price: currentPrice - 1, quantity: 2900, total: (currentPrice - 1) * 2900 },
      { price: currentPrice - 2, quantity: 3100, total: (currentPrice - 2) * 3100 },
      { price: currentPrice - 3, quantity: 1900, total: (currentPrice - 3) * 1900 },
      { price: currentPrice - 4, quantity: 2400, total: (currentPrice - 4) * 2400 },
      { price: currentPrice - 5, quantity: 1600, total: (currentPrice - 5) * 1600 },
    ]
  };

  // 模擬交易紀錄數據
  const tradeHistory = [
    { time: '14:32:15', price: currentPrice, quantity: 500, change: +0.5 },
    { time: '14:31:42', price: currentPrice - 1, quantity: 300, change: -0.3 },
    { time: '14:31:05', price: currentPrice + 1, quantity: 800, change: +1.2 },
    { time: '14:30:33', price: currentPrice - 2, quantity: 450, change: -0.8 },
    { time: '14:30:12', price: currentPrice + 2, quantity: 650, change: +1.8 },
    { time: '14:29:48', price: currentPrice - 1, quantity: 200, change: -0.4 },
    { time: '14:29:21', price: currentPrice, quantity: 750, change: +0.2 },
    { time: '14:28:56', price: currentPrice + 1, quantity: 400, change: +0.9 },
    { time: '14:28:23', price: currentPrice - 3, quantity: 320, change: -1.2 },
    { time: '14:27:45', price: currentPrice + 3, quantity: 580, change: +2.1 },
  ];

  const OrderBookTab = () => (
    <div className="space-y-4">
      {/* 賣盤 */}
      <div>
        <h4 className="text-red-400 text-sm font-semibold mb-2">賣盤</h4>
        <div className="space-y-1">
          {orderbookData.sells.reverse().map((order, index) => (
            <div key={index} className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-red-400 font-mono">${order.price}</div>
              <div className="text-gray-300 text-right font-mono">{order.quantity.toLocaleString()}</div>
              <div className="text-gray-400 text-right font-mono">${order.total.toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 當前價格 */}
      <div className="border-t border-b border-[#82bee2]/20 py-2 text-center">
        <span className="text-white font-bold text-lg">${currentPrice}</span>
      </div>

      {/* 買盤 */}
      <div>
        <h4 className="text-green-400 text-sm font-semibold mb-2">買盤</h4>
        <div className="space-y-1">
          {orderbookData.buys.map((order, index) => (
            <div key={index} className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-green-400 font-mono">${order.price}</div>
              <div className="text-gray-300 text-right font-mono">{order.quantity.toLocaleString()}</div>
              <div className="text-gray-400 text-right font-mono">${order.total.toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 表頭 */}
      <div className="grid grid-cols-3 gap-2 text-xs text-[#82bee2] border-t border-[#82bee2]/20 pt-2">
        <div>價格</div>
        <div className="text-right">數量</div>
        <div className="text-right">總額</div>
      </div>
    </div>
  );

  const TradeHistoryTab = () => (
    <div className="space-y-2">
      {/* 表頭 */}
      <div className="grid grid-cols-4 gap-2 text-xs text-[#82bee2] border-b border-[#82bee2]/20 pb-2">
        <div>時間</div>
        <div className="text-center">價格</div>
        <div className="text-center">數量</div>
        <div className="text-center">漲跌</div>
      </div>

      {/* 交易紀錄 */}
      <div className="space-y-1 max-h-96 overflow-y-auto">
        {tradeHistory.map((trade, index) => (
          <div key={index} className="grid grid-cols-4 gap-2 text-xs hover:bg-[#1a2e4a]/50 p-2 rounded">
            <div className="text-gray-300 font-mono">
              {trade.time}
            </div>
            <div className="text-white font-mono text-center">
              ${trade.price}
            </div>
            <div className="text-gray-300 text-center font-mono">
              {trade.quantity.toLocaleString()}
            </div>
            <div className={`text-center font-mono font-semibold ${
              trade.change > 0 ? 'text-red-400' : 'text-green-400'
            }`}>
              {trade.change > 0 ? '+' : ''}{trade.change.toFixed(1)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

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
