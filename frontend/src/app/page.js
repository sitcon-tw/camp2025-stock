'use client';

import { useState, useEffect } from 'react';
import HeaderBar from "@/components/HeaderBar";
import StockChart from "@/components/StockChart";
import TradingTabs from "@/components/TradingTabs";
import { getPriceSummary } from "@/lib/api";

export default function Home() {
  const [stockData, setStockData] = useState({
    lastPrice: 70,
    change: 0,
    changePercent: 0,
    high: 75,
    low: 65,
    open: 70,
    volume: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStockData = async () => {
      try {
        setLoading(true);
        const data = await getPriceSummary();
        setStockData(data);
        setError(null);
      } catch (err) {
        console.error('獲取股票資料失敗:', err);
        setError('無法獲取股票資料');
        // 保持默認值
      } finally {
        setLoading(false);
      }
    };

    fetchStockData();
    
    // 每30秒更新一次資料
    const interval = setInterval(fetchStockData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const currentPrice = stockData.lastPrice;
  const changePercent = parseFloat(stockData.changePercent) || 0;
  const isPositive = changePercent > 0;
  const isNegative = changePercent < 0;

  return (
    <div className="bg-[#0f203e] min-h-screen items-center justify-center pb-36">
      <div className="flex flex-col h-screen px-8 mb-10">
        <HeaderBar />
        
        {/* 載入狀態 */}
        {loading && (
          <div className="flex justify-center items-center mt-8">
            <div className="text-[#82bee2] text-lg">載入中...</div>
          </div>
        )}
        
        {/* 錯誤狀態 */}
        {error && (
          <div className="mt-8 p-4 bg-red-900/30 border border-red-600 rounded-lg">
            <div className="text-red-400 text-sm">{error}</div>
          </div>
        )}
        
        {/* 股市趨勢圖 */}
        <div className="mt-8" style={{
          marginBottom: '6rem',
        }}>
          <StockChart 
            currentPrice={currentPrice}
            changePercent={changePercent}
          />
        </div>
        
        {/* 開盤價 今日最低 今日最高 */}
        <div className="mt-4">
          <h4 className="text-[#82bee2] text-lg font-semibold mb-2">今日股市資訊</h4>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-[#1a2e4a] p-4 rounded-lg">
              <h5 className="text-sm text-[#82bee2]">開盤價</h5>
              <p className="text-xl font-bold">${stockData.open.toFixed(2)}</p>
            </div>
            <div className="bg-[#1a2e4a] p-4 rounded-lg">
              <h5 className="text-sm text-[#82bee2]">今日最低</h5>
              <p className="text-xl font-bold">${stockData.low.toFixed(2)}</p>
            </div>
            <div className="bg-[#1a2e4a] p-4 rounded-lg">
              <h5 className="text-sm text-[#82bee2]">今日最高</h5>
              <p className="text-xl font-bold">${stockData.high.toFixed(2)}</p>
            </div>
          </div>
        </div>
        
        {/* 成交量資訊 */}
        <div className="mt-4">
          <div className="bg-[#1a2e4a] p-4 rounded-lg">
            <h5 className="text-sm text-[#82bee2]">成交量</h5>
            <p className="text-xl font-bold">{stockData.volume.toLocaleString()} 股</p>
          </div>
        </div>
        
        {/* 五檔股價 和 交易紀錄 的 TAB */}
        <div className="mt-6">
          <TradingTabs currentPrice={currentPrice} />
        </div>
      </div>
    </div>
  );
}
