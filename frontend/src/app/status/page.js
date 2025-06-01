'use client';
import Link from 'next/link';
import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { getPriceSummary, getHistoricalPrices } from '@/lib/api';

// 動態導入 K線圖元件以避免 SSR 問題
const CandlestickChart = dynamic(() => import('@/components/CandlestickChart'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-96 bg-[#1a2e4a] rounded-lg">
      <div className="text-[#82bee2]">載入 K 線圖中...</div>
    </div>
  )
});

export default function Status() {
  const [chartData, setChartData] = useState([]);
  const [currentStockData, setCurrentStockData] = useState({
    lastPrice: 20.0,
    change: 0,
    changePercent: "0.0%",
    high: 20.0,
    low: 20.0,
    open: 20.0,
    volume: 0
  });
  const [chartDimensions, setChartDimensions] = useState({ width: 800, height: 400 });
  const [selectedTimeframe, setSelectedTimeframe] = useState('日');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // 獲取目前股票價格摘要和歷史資料
        const [priceData, historicalData] = await Promise.all([
          getPriceSummary(),
          getHistoricalPrices(24)
        ]);

        setCurrentStockData(priceData);
        
        // 處理歷史資料為 K 線圖格式
        if (historicalData && historicalData.length > 0) {
          const processedData = processHistoricalDataForCandlestick(historicalData);
          setChartData(processedData);
        }
        
        setError(null);
      } catch (err) {
        console.error('獲取股票資料失敗:', err);
        setError('無法獲取股票資料');
        
        // 如果 API 失敗，產生基於目前價格的基本資料
        const fallbackData = generateFallbackCandlestickData(currentStockData.lastPrice);
        setChartData(fallbackData);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // 處理響應式尺寸
    const handleResize = () => {
      const container = document.getElementById('chart-container');
      if (container) {
        const width = Math.min(container.offsetWidth - 32, 1200);
        const height = Math.max(300, Math.min(width * 0.5, 500));
        setChartDimensions({ width, height });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 模擬 SITCON Camp 2025 股票競賽資料
  const campData = {
    name: "SITCON Camp 2025 股票競賽",
    currentPrice: 1050.25,
    changeAmount: 25.80,
    changePercent: 2.52,
    volume: 156.32, // 萬股
    turnover: 164.55, // 萬元
    date: "2025/06/01",
    open: 1024.45,
    high: 1068.90,
    low: 1015.30,
    close: 1050.25,
    todayVolume: 156.32, // 萬股
    
    // 技術指標 - 適合5天活動
    dayAvg: 1042.15, // 當日均價
    yesterdayClose: 1024.45, // 昨日收盤
    openingPrice: 1024.45, // 開盤價
    
    // 成交統計
    totalVolume: 782.150, // 萬股
    upCount: 12, // 上漲檔數
    upVolume: 425.680, // 萬股
    downCount: 8, // 下跌檔數  
    downVolume: 298.470, // 萬股
    flatCount: 5, // 平盤檔數
    
    // 活動相關
    activeDays: 5,
    currentDay: 1,
    participants: 128,
    activeTraders: 96
  };

  const isPositive = campData.changeAmount > 0;
  const isNegative = campData.changeAmount < 0;

  const stockData = {
    currentPrice: 70,
    changePercent: 20,
    changeAmount: 11.67,
    openPrice: 58.33,
    highPrice: 75,
    lowPrice: 55,
    volume: 1250000,
    turnover: 87500000,
    marketCap: 8750000000,
    peRatio: 15.8,
    pbRatio: 2.1,
    eps: 4.43,
    dividend: 1.20,
    dividendYield: 1.71,
    previousClose: 58.33,
    weekHigh52: 82.50,
    weekLow52: 35.20,
    avgVolume: 980000,
    beta: 1.15,
    rsi: 65.4,
    macd: 2.35
  };

  // 處理歷史資料為 K 線圖格式
  const processHistoricalDataForCandlestick = (historicalData) => {
    const dataByDate = {};
    
    // 按日期分組資料
    historicalData.forEach(trade => {
      const date = new Date(trade.timestamp).toDateString();
      if (!dataByDate[date]) {
        dataByDate[date] = [];
      }
      dataByDate[date].push(trade.price);
    });
    
    // 轉換為 K 線格式
    return Object.keys(dataByDate).map(dateStr => {
      const prices = dataByDate[dateStr];
      const date = new Date(dateStr);
      
      return {
        date,
        open: prices[0],
        high: Math.max(...prices),
        low: Math.min(...prices),
        close: prices[prices.length - 1],
        volume: prices.length * 100 // 估算成交量
      };
    }).sort((a, b) => a.date - b.date);
  };

  // 產生後備 K 線資料
  const generateFallbackCandlestickData = (basePrice = 20.0) => {
    const data = [];
    let currentPrice = basePrice;
    const days = 30;
    
    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));
      
      const open = currentPrice;
      const volatility = (Math.random() - 0.5) * 0.1;
      const close = open * (1 + volatility);
      
      const high = Math.max(open, close) * (1 + Math.random() * 0.05);
      const low = Math.min(open, close) * (1 - Math.random() * 0.05);
      const volume = Math.floor(Math.random() * 1000) + 500;
      
      data.push({ date, open, high, low, close, volume });
      currentPrice = close;
    }
    
    return data;
  };

  return (
    <div className="bg-[#0f203e] min-h-screen pb-24">
      <div className="px-4 md:px-8 pt-8">
        {/* 標題區域 */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-[#82bee2] mb-2">{campData.name}</h1>
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span>第 {campData.currentDay} 天 / 共 {campData.activeDays} 天</span>
            <span>•</span>
            <span>參與者: {campData.participants}人</span>
          </div>
        </div>
        {/* 價格資訊區塊 */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button className="text-[#82bee2] text-xl">◀</button>
            <div>
              <div className="text-4xl font-bold text-white mb-2">
                {campData.currentPrice.toLocaleString()}
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-lg font-semibold ${isPositive ? 'text-green-400' : isNegative ? 'text-red-400' : 'text-gray-400'}`}>
                  {isPositive ? '▲' : isNegative ? '▼' : ''}
                  {Math.abs(campData.changeAmount)}
                </span>
                <span className={`text-sm ${isPositive ? 'text-green-400' : isNegative ? 'text-red-400' : 'text-gray-400'}`}>
                  {campData.changePercent}%
                </span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400 mb-1">成交量(萬股): <span className="text-white">{campData.volume}</span></div>
            <div className="text-sm text-gray-400 mb-1">成交額(萬元): <span className="text-white">{campData.turnover}</span></div>
            <div className="text-sm text-gray-400">參與者: <span className="text-[#82bee2]">{campData.participants}人</span></div>
          </div>
          <button className="text-[#82bee2] text-xl">▶</button>
        </div>


        {/* 週期選擇 */}
        <div className="flex gap-2 mb-4 overflow-x-auto">
          {['第1天', '第2天', '第3天', '第4天', '第5天', '總覽'].map((period) => (
            <button 
              key={period}
              className={`px-3 py-1 text-sm rounded whitespace-nowrap ${
                period === '第1天'
                  ? 'bg-[#82bee2] text-[#0f203e]' 
                  : 'bg-[#1a2e4a] text-[#82bee2] border border-[#82bee2]/30'
              }`}
              onClick={() => setSelectedTimeframe(period)}
            >
              {period}
            </button>
          ))}
          <button className="text-[#82bee2] text-lg">⚙️</button>
        </div>

        {/* 當日資訊 */}
        <div className="bg-[#1a2e4a] rounded-lg p-4 mb-4">
          <div className="text-sm text-gray-400 mb-2">{campData.date} - SITCON Camp 2025 第 {campData.currentDay} 天</div>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-400">開</span>
              <span className="text-green-400 ml-2">{campData.open.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-400">低</span>
              <span className="text-red-400 ml-2">{campData.low.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-400">高</span>
              <span className="text-green-400 ml-2">{campData.high.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-400">收</span>
              <span className="text-green-400 ml-2">{campData.close.toLocaleString()}</span>
            </div>
          </div>
          <div className="mt-2 text-sm">
            <span className="text-gray-400">成交量</span>
            <span className="text-green-400 ml-2">{campData.todayVolume}萬股</span>
            <span className="text-gray-400 ml-4">活躍交易者</span>
            <span className="text-[#82bee2] ml-2">{campData.activeTraders}人</span>
          </div>
          <div className="flex gap-8 mt-2 text-sm">
            <span className="text-gray-400">當日均價 <span className="text-cyan-400">{campData.dayAvg.toLocaleString()}</span></span>
            <span className="text-gray-400">昨收 <span className="text-yellow-400">{campData.yesterdayClose.toLocaleString()}</span></span>
          </div>
        </div>

        {/* K 線圖 */}
        <div className="mb-6">
          <div 
            id="chart-container"
            className="bg-[#1a2e4a] rounded-lg p-4 border border-[#82bee2]/10 overflow-x-auto relative"
            style={{ height: '400px' }}
          >
            {chartData.length > 0 && (
              <CandlestickChart 
                data={chartData} 
                width={chartDimensions.width}
                height={300}
              />
            )}
            
            {/* 圖表控制按鈕 */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-4">
              <button className="w-8 h-8 bg-[#0f203e] text-[#82bee2] rounded border border-[#82bee2]/30 flex items-center justify-center">×</button>
              <button className="w-8 h-8 bg-[#0f203e] text-[#82bee2] rounded border border-[#82bee2]/30 flex items-center justify-center">+</button>
              <button className="w-8 h-8 bg-[#0f203e] text-[#82bee2] rounded border border-[#82bee2]/30 flex items-center justify-center">−</button>
              <button className="w-8 h-8 bg-[#0f203e] text-[#82bee2] rounded border border-[#82bee2]/30 flex items-center justify-center">‹</button>
              <button className="w-8 h-8 bg-[#0f203e] text-[#82bee2] rounded border border-[#82bee2]/30 flex items-center justify-center">›</button>
              <button className="w-8 h-8 bg-[#0f203e] text-[#82bee2] rounded border border-[#82bee2]/30 flex items-center justify-center">⏸</button>
            </div>
          </div>
        </div>

        {/* 成交統計 */}
        <div className="bg-[#1a2e4a] rounded-lg p-4 mb-6">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="text-center">
              <div className="text-yellow-400 font-bold text-lg">{campData.totalVolume}萬股</div>
              <div className="text-gray-400">總成交量</div>
            </div>
            <div className="text-center">
              <div className="text-green-400 font-bold text-lg">{campData.upCount} ({campData.upVolume}萬)</div>
              <div className="text-gray-400">上漲檔數</div>
            </div>
            <div className="text-center">
              <div className="text-red-400 font-bold text-lg">{campData.downCount} ({campData.downVolume}萬)</div>
              <div className="text-gray-400">下跌檔數</div>
            </div>
          </div>
          
          {/* 成交量圖表 - 5天活動期間 */}
          <div className="mt-4 h-32 bg-[#0f203e] rounded relative overflow-hidden">
            <div className="absolute bottom-0 left-0 right-0 flex items-end justify-around h-full px-2">
              {Array.from({length: 5}, (_, i) => (
                <div 
                  key={i} 
                  className={`w-8 rounded-t ${i === 0 ? 'bg-[#82bee2]' : 'bg-gray-600'}`}
                  style={{ height: `${i === 0 ? 70 : Math.random() * 40 + 20}%` }}
                />
              ))}
            </div>
            <div className="absolute bottom-0 left-0 right-0 flex justify-around text-xs text-gray-500 px-2">
              <span>6/1</span>
              <span>6/2</span>
              <span>6/3</span>
              <span>6/4</span>
              <span>6/5</span>
            </div>
          </div>
        </div>

        {/* 底部活動資訊 */}
        <div className="flex justify-center gap-8 mt-8">
          <button className="flex items-center gap-2 text-[#82bee2] hover:text-white transition-colors">
            <span>📤</span>
            <span>分享成績</span>
          </button>
          <Link href="/leaderboard" className="flex items-center gap-2 text-[#82bee2] hover:text-white transition-colors">
            <span>🏆</span>
            <span>排行榜</span>
          </Link>
          <button className="flex items-center gap-2 text-[#82bee2] hover:text-white transition-colors">
            <span>📊</span>
            <span>活動統計</span>
          </button>
        </div>

        {/* 活動進度 */}
        <div className="mt-6 bg-[#1a2e4a] rounded-lg p-4">
          <h3 className="text-[#82bee2] font-semibold mb-3">SITCON Camp 2025 活動進度</h3>
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1 bg-[#0f203e] rounded-full h-2">
              <div 
                className="bg-[#82bee2] h-2 rounded-full transition-all duration-300"
                style={{ width: `${(campData.currentDay / campData.activeDays) * 100}%` }}
              />
            </div>
            <span className="text-sm text-gray-400">{campData.currentDay}/{campData.activeDays} 天</span>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">參與學員</span>
              <span className="text-white">{campData.participants}人</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">活躍交易者</span>
              <span className="text-[#82bee2]">{campData.activeTraders}人</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}