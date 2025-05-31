'use client';

import React from 'react';
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
  // 生成模擬的股價數據
  const generateStockData = () => {
    const basePrice = 50;
    const dataPoints = 30;
    const data = [];
    const labels = [];
    
    for (let i = 0; i < dataPoints; i++) {
      // 生成隨機波動
      const volatility = Math.random() * 10 - 5; // -5 到 5 的隨機數
      const price = i === 0 ? basePrice : data[i - 1] + volatility;
      data.push(Math.max(price, 20)); // 確保價格不會低於20
      
      // 生成時間標籤（過去30天）
      const date = new Date();
      date.setDate(date.getDate() - (dataPoints - i));
      labels.push(date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' }));
    }
    
    // 將最後一個點設為當前價格
    data[dataPoints - 1] = currentPrice;
    
    return { data, labels };
  };

  const { data: stockData, labels } = generateStockData();
  
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
    labels,
    datasets: [
      {
        label: 'SITC 價格',
        data: stockData,
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

  return (
    <div className="w-full h-64 md:h-80">
      <div className="h-full">
        <Line options={options} data={data} />
      </div>
    </div>
  );
};

export default StockChart;
