'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import StockDetails from '@/components/StockDetails';
import { generateCandlestickData } from '@/lib/stockDataGenerator';
import HeaderBar from '@/components/HeaderBar';

// 動態導入 K線圖組件以避免 SSR 問題
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
  const [chartDimensions, setChartDimensions] = useState({ width: 800, height: 400 });

  useEffect(() => {
    // 生成 K 線圖數據
    const data = generateCandlestickData(60, 70);
    setChartData(data);

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

  return (
    <div className="bg-[#0f203e] min-h-screen pb-24">
      <div className="px-4 md:px-8 pt-8">
        {/* 標題和股票基本資訊 */}
        <HeaderBar />
        

        {/* K 線圖 */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
            <h2 className="text-xl font-bold text-[#82bee2]">K 線圖</h2>
            <div className="flex gap-2 mt-2 md:mt-0">
              <button className="px-3 py-1 bg-[#82bee2] text-[#0f203e] rounded text-sm font-medium">1天</button>
              <button className="px-3 py-1 bg-[#1a2e4a] text-[#82bee2] rounded text-sm border border-[#82bee2]/30">5天</button>
              <button className="px-3 py-1 bg-[#1a2e4a] text-[#82bee2] rounded text-sm border border-[#82bee2]/30">1月</button>
              <button className="px-3 py-1 bg-[#1a2e4a] text-[#82bee2] rounded text-sm border border-[#82bee2]/30">3月</button>
              <button className="px-3 py-1 bg-[#1a2e4a] text-[#82bee2] rounded text-sm border border-[#82bee2]/30">1年</button>
            </div>
          </div>
          <div 
            id="chart-container"
            className="bg-[#1a2e4a] rounded-lg p-4 border border-[#82bee2]/10 overflow-x-auto"
          >
            {chartData.length > 0 && (
              <CandlestickChart 
                data={chartData} 
                width={chartDimensions.width}
                height={chartDimensions.height}
              />
            )}
          </div>
        </div>

        {/* 公司基本資訊 */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-[#82bee2] mb-4">公司資訊</h2>
          <div className="bg-[#1a2e4a] rounded-lg p-6 border border-[#82bee2]/10">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-[#82bee2] font-semibold mb-3">公司簡介</h3>
                <p className="text-gray-300 text-sm leading-relaxed">
                  SITCON Camp 是台灣學生計算機年會的重要活動，專注於培育年輕的資訊科技人才。
                  作為科技教育領域的創新者，持續推動開源文化與技術交流，
                  在學生社群中享有極高聲譽。
                </p>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">產業類別</span>
                  <span className="text-white">教育科技</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">成立時間</span>
                  <span className="text-white">2013年</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">總部</span>
                  <span className="text-white">台灣</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">員工數</span>
                  <span className="text-white">500+</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">上市時間</span>
                  <span className="text-white">2020年</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 詳細資訊 */}
        <StockDetails stockData={stockData} />

        {/* 最新消息 */}
        <div className="mt-8">
          <h2 className="text-xl font-bold text-[#82bee2] mb-4">最新消息</h2>
          <div className="space-y-4">
            {[
              {
                time: '2小時前',
                title: 'SITCON Camp 2025 報名開放，預計吸引千名學生參與',
                summary: '今年夏令營將首次舉辦股票交易競賽，結合教育與實務操作...',
                type: '公司新聞'
              },
              {
                time: '1天前',
                title: '第四季營收創新高，年增35%',
                summary: '受惠於線上教育平台快速成長，第四季營收達到歷史新高...',
                type: '財報消息'
              },
              {
                time: '3天前',
                title: '與多所大學簽署合作協議，拓展教育版圖',
                summary: '將與台大、清大、交大等頂尖學府合作開發新型態程式教育課程...',
                type: '合作消息'
              }
            ].map((news, index) => (
              <div key={index} className="bg-[#1a2e4a] rounded-lg p-4 border border-[#82bee2]/10 hover:border-[#82bee2]/30 transition-colors cursor-pointer">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-2">
                  <div className="flex items-center gap-2 mb-2 md:mb-0">
                    <span className="px-2 py-1 bg-[#82bee2]/20 text-[#82bee2] text-xs rounded">{news.type}</span>
                    <span className="text-gray-400 text-sm">{news.time}</span>
                  </div>
                </div>
                <h3 className="text-white font-semibold mb-2">{news.title}</h3>
                <p className="text-gray-300 text-sm">{news.summary}</p>
              </div>
            ))}
          </div>
        </div>

        {/* 分析師建議 */}
        <div className="mt-8">
          <h2 className="text-xl font-bold text-[#82bee2] mb-4">分析師建議</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[#1a2e4a] rounded-lg p-4 border border-[#82bee2]/10">
              <h3 className="text-[#82bee2] font-semibold mb-2">投資評級</h3>
              <div className="flex items-center justify-between mb-2">
                <span className="text-green-400 font-bold text-lg">買入</span>
                <span className="text-sm text-gray-400">5/7 分析師</span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">買入</span>
                  <span className="text-green-400">5</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">持有</span>
                  <span className="text-yellow-400">2</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">賣出</span>
                  <span className="text-red-400">0</span>
                </div>
              </div>
            </div>
            
            <div className="bg-[#1a2e4a] rounded-lg p-4 border border-[#82bee2]/10">
              <h3 className="text-[#82bee2] font-semibold mb-2">目標價位</h3>
              <div className="text-lg font-bold text-white mb-2">$85.00</div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">最高</span>
                  <span className="text-white">$95.00</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">平均</span>
                  <span className="text-white">$85.00</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">最低</span>
                  <span className="text-white">$75.00</span>
                </div>
              </div>
            </div>

            <div className="bg-[#1a2e4a] rounded-lg p-4 border border-[#82bee2]/10">
              <h3 className="text-[#82bee2] font-semibold mb-2">風險評估</h3>
              <div className="text-lg font-bold text-yellow-400 mb-2">中等</div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Beta 係數</span>
                  <span className="text-white">{stockData.beta}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">波動率</span>
                  <span className="text-white">18.5%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">流動性</span>
                  <span className="text-green-400">高</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}