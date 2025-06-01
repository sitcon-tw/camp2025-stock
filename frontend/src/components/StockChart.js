'use client';

import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { getHistoricalPrices } from '@/lib/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const StockChart = ({ currentPrice = 70, changePercent = 20 }) => {
  const [chartData, setChartData] = useState({ data: [], labels: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistoricalData = async () => {
      try {
        setLoading(true);
        
        // 獲取過去6小時的歷史價格資料
        const historicalData = await getHistoricalPrices(6);
        
        if (historicalData && historicalData.length > 0) {
          const data = historicalData.map(item => item.price);
          const labels = historicalData.map(item => {
            const date = new Date(item.timestamp);
            return date.toLocaleTimeString('zh-TW', { 
              hour: '2-digit', 
              minute: '2-digit'
            });
          });
          
          setChartData({ data, labels });
        } else {
          // 如果沒有歷史資料，生成模擬資料
          const fallbackData = generateFallbackData();
          setChartData(fallbackData);
        }
        
        setError(null);
      } catch (err) {
        console.error('獲取歷史資料失敗:', err);
        setError('無法獲取歷史資料');
        
        // 使用模擬資料作為後備
        const fallbackData = generateFallbackData();
        setChartData(fallbackData);
      } finally {
        setLoading(false);
      }
    };

    fetchHistoricalData();
    
    // 每分鐘更新一次圖表
    const interval = setInterval(fetchHistoricalData, 60000);
    
    return () => clearInterval(interval);
  }, [currentPrice]);

  // 生成模擬資料的後備函數
  const generateFallbackData = () => {
    const basePrice = currentPrice * 0.95; // 從當前價格的95%開始
    const dataPoints = 30;
    const data = [];
    const labels = [];
    
    for (let i = 0; i < dataPoints; i++) {
      // 生成隨機波動，最終趨向當前價格
      const progress = i / (dataPoints - 1);
      const volatility = (Math.random() * 4 - 2) * (1 - progress); // 波動隨時間減少
      const trendTowardsCurrentPrice = (currentPrice - basePrice) * progress;
      const price = basePrice + trendTowardsCurrentPrice + volatility;
      
      data.push(Math.max(price, currentPrice * 0.8)); // 確保價格不會過低
      
      // 生成時間標籤
      const date = new Date();
      date.setMinutes(date.getMinutes() - (dataPoints - i) * 2); // 每2分鐘一個點
      labels.push(date.toLocaleTimeString('zh-TW', { 
        hour: '2-digit', 
        minute: '2-digit'
      }));
    }
    
    // 確保最後一個點是當前價格
    data[dataPoints - 1] = currentPrice;
    
    return { data, labels };
  };
  
  // 決定線條顏色（基於整體趨勢）
  const isPositive = changePercent > 0;
  const lineColor = isPositive ? '#ef4444' : '#22c55e'; // 紅色上漲，綠色下跌
  const gradientColor = isPositive ? 'rgba(239, 68, 68, 0.1)' : 'rgba(34, 197, 94, 0.1)';

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 32, 62, 0.9)',
        titleColor: '#82bee2',
        bodyColor: '#ffffff',
        borderColor: '#82bee2',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            return `價格: $${context.parsed.y.toFixed(2)}`;
          }
        }
      },
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false,
    },
    scales: {
      x: {
        display: true,
        grid: {
          color: 'rgba(130, 190, 226, 0.1)',
        },
        ticks: {
          color: '#82bee2',
          maxTicksLimit: 6,
        },
      },
      y: {
        display: true,
        position: 'right',
        grid: {
          color: 'rgba(130, 190, 226, 0.1)',
        },
        ticks: {
          color: '#82bee2',
          callback: function(value) {
            return '$' + value.toFixed(0);
          }
        },
      },
    },
    elements: {
      point: {
        radius: 0,
        hoverRadius: 6,
      },
      line: {
        tension: 0.3,
        borderWidth: 2,
      },
    },
  };

  const data = {
    labels: chartData.labels,
    datasets: [
      {
        label: 'SITC 價格',
        data: chartData.data,
        borderColor: lineColor,
        backgroundColor: (context) => {
          const chart = context.chart;
          const { ctx, chartArea } = chart;
          if (!chartArea) return null;
          
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, gradientColor);
          gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
          return gradient;
        },
        fill: true,
        pointBackgroundColor: lineColor,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
      },
    ],
  };

  if (loading) {
    return (
      <div className="w-full h-64 md:h-80 flex items-center justify-center">
        <div className="text-[#82bee2]">載入圖表中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-64 md:h-80 flex items-center justify-center">
        <div className="text-red-400 text-sm">{error}</div>
      </div>
    );
  }

  return (
    <div className="w-full h-64 md:h-80">
      <div className="mb-4">
        <h3 className="text-[#82bee2] text-lg font-semibold mb-2">SITC 股價走勢</h3>
        <div className="flex items-center space-x-4">
          <span className="text-white text-2xl font-bold">${currentPrice.toFixed(2)}</span>
          <span className={`text-lg font-semibold ${
            changePercent > 0 ? 'text-red-400' : changePercent < 0 ? 'text-green-400' : 'text-gray-400'
          }`}>
            {changePercent > 0 ? '+' : ''}{changePercent.toFixed(2)}%
          </span>
        </div>
      </div>
      <div className="h-full">
        <Line options={options} data={data} />
      </div>
    </div>
  );
};

export default StockChart;
