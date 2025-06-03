'use client';

import React, { useState, useEffect, useRef } from 'react';
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
import { getPercentageBasedColor } from '@/lib/utils';
import CandlestickChart from './CandlestickChart';

// 註冊 Chart.js 相關元件
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

// 自訂背景 Plugin (深藍底)
const BackgroundColorPlugin = {
    id: 'custom_canvas_background_color',
    beforeDraw: (chart) => {
        const ctx = chart.ctx;
        ctx.save();
        ctx.globalCompositeOperation = 'destination-over';
        ctx.fillStyle = '#0f203e'; // 深藍色背景
        ctx.fillRect(0, 0, chart.width, chart.height);
        ctx.restore();
    }
};
ChartJS.register(BackgroundColorPlugin);

const StockChart = ({ currentPrice = 20.0, changePercent = 0 }) => {
    const [chartData, setChartData] = useState({ data: [], labels: [] });
    const [candlestickData, setCandlestickData] = useState([]);
    const [averageData, setAverageData] = useState({ data: [], labels: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [displayMode, setDisplayMode] = useState('real'); // 'candlestick' | 'real' | 'average'
    const [zoomLevel, setZoomLevel] = useState(1);
    const [panOffset, setPanOffset] = useState(0);
    const chartRef = useRef(null);
    const isDragging = useRef(false);
    const lastMouseX = useRef(0);

    // 控制「檢視」Modal 是否開啟
    const [modalOpen, setModalOpen] = useState(false);

    useEffect(() => {
        const fetchHistoricalData = async () => {
            try {
                setLoading(true);
                const historicalData = await getHistoricalPrices(24);

                if (historicalData && historicalData.length > 0) {
                    // 1. 真實價格 (Line Chart)
                    const realPriceData = historicalData.map(item => item.price);
                    const labels = historicalData.map(item => {
                        const date = new Date(item.timestamp);
                        return date.toLocaleTimeString('zh-TW', {
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                    });
                    setChartData({ data: realPriceData, labels });

                    // 2. 模擬 K 線數據 (每 4 筆合成 1 根)
                    const candlesticks = [];
                    for (let i = 0; i < historicalData.length; i += 4) {
                        const chunk = historicalData.slice(i, i + 4);
                        if (chunk.length > 0) {
                            const open = chunk[0].price;
                            const close = chunk[chunk.length - 1].price;
                            const high = Math.max(...chunk.map(d => d.price));
                            const low = Math.min(...chunk.map(d => d.price));
                            candlesticks.push({
                                open,
                                high,
                                low,
                                close,
                                timestamp: chunk[0].timestamp
                            });
                        }
                    }
                    setCandlestickData(candlesticks);

                    // 3. 計算 5 期移動平均 (Line Chart)
                    const period = 5;
                    const movingAverages = [];
                    for (let i = period - 1; i < realPriceData.length; i++) {
                        const sum = realPriceData
                            .slice(i - period + 1, i + 1)
                            .reduce((a, b) => a + b, 0);
                        movingAverages.push(sum / period);
                    }
                    setAverageData({
                        data: movingAverages,
                        labels: labels.slice(period - 1)
                    });                    // 4. 如果是 K 線，讓最右邊顯示最新的蠟燭
                    if (candlesticks.length > 0) {
                        const chartWidth = 1200;
                        const scaledWidth = chartWidth * zoomLevel;
                        const visibleCandles = Math.floor(chartWidth / 20);
                        if (candlesticks.length > visibleCandles) {
                            const totalWidth =
                                (candlesticks.length - 1) * (scaledWidth / (candlesticks.length - 1));
                            const offsetToShowLast = -(totalWidth - chartWidth + 100);
                            setPanOffset(offsetToShowLast);
                        }
                    }
                } else {
                    setChartData({ data: [], labels: [] });
                    setCandlestickData([]);
                    setAverageData({ data: [], labels: [] });
                }
                setError(null);
            } catch (err) {
                console.error('獲取歷史資料失敗:', err);
                setError('無法獲取歷史資料');
                setChartData({ data: [], labels: [] });
                setCandlestickData([]);
                setAverageData({ data: [], labels: [] });
            } finally {
                setLoading(false);
            }
        };

        fetchHistoricalData();
        const interval = setInterval(fetchHistoricalData, 60000); // 每分鐘重新抓一次
        return () => clearInterval(interval);
    }, [currentPrice]);

    // ------ 滑鼠/觸控縮放、平移邏輯 (僅在 candlestick 模式下生效) ------
    const handleMouseDown = (e) => {
        if (displayMode !== 'candlestick') return;
        e.preventDefault();
        isDragging.current = true;
        lastMouseX.current = e.clientX || (e.touches && e.touches[0].clientX);
    };
    const handleMouseMove = (e) => {
        if (!isDragging.current || displayMode !== 'candlestick') return;
        e.preventDefault();
        const clientX = e.clientX || (e.touches && e.touches[0].clientX);
        const deltaX = clientX - lastMouseX.current;
        setPanOffset(prev => prev + deltaX * 0.5);
        lastMouseX.current = clientX;
    };
    const handleMouseUp = () => {
        isDragging.current = false;
    };
    const handleWheel = (e) => {
        if (displayMode !== 'candlestick') return;
        e.preventDefault();
        const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
        setZoomLevel(prev => Math.max(0.5, Math.min(3, prev * zoomFactor)));
    };
    const handleTouchStart = (e) => {
        if (displayMode !== 'candlestick') return;
        if (e.touches.length === 1) {
            isDragging.current = true;
            lastMouseX.current = e.touches[0].clientX;
        }
    };
    const handleTouchMove = (e) => {
        if (displayMode !== 'candlestick') return;
        e.preventDefault();
        if (e.touches.length === 1 && isDragging.current) {
            const deltaX = e.touches[0].clientX - lastMouseX.current;
            setPanOffset(prev => prev + deltaX * 0.8);
            lastMouseX.current = e.touches[0].clientX;
        }
    };
    const handleTouchEnd = () => {
        isDragging.current = false;
    };
    const resetZoomPan = () => {
        setZoomLevel(1);
        if (candlestickData.length > 0) {
            const chartWidth = 1200;
            const scaledWidth = chartWidth * 1;
            const visibleCandles = Math.floor(chartWidth / 20);
            if (candlestickData.length > visibleCandles) {
                const totalWidth =
                    (candlestickData.length - 1) * (scaledWidth / (candlestickData.length - 1));
                const offsetToShowLast = -(totalWidth - chartWidth + 100);
                setPanOffset(offsetToShowLast);
            } else {
                setPanOffset(0);
            }
        } else {
            setPanOffset(0);
        }
    };
    // -------------------------------------------------------------------

    // 根據 displayMode 回傳對應資料
    const getCurrentData = () => {
        switch (displayMode) {
            case 'real':
                return chartData;
            case 'average':
                return averageData;
            default:
                return chartData;
        }
    };    // 判斷漲跌，決定線條顏色 - 使用百分比閾值邏輯
    const currentData = getCurrentData();
    const lineColor = currentData.data.length > 0
        ? getPercentageBasedColor(currentPrice, currentData.data, 30)
        : '#82bee2'; // 預設顏色

    const gradientColor = lineColor === '#ef4444'
        ? 'rgba(239, 68, 68, 0.2)'  // 紅色漸層
        : lineColor === '#22c55e'
            ? 'rgba(34, 197, 94, 0.2)'  // 綠色漸層
            : 'rgba(130, 190, 226, 0.2)'; // 藍色漸層

    // 折線圖（真實價／平均價）設定
    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(15, 32, 62, 0.9)',
                titleColor: '#82bee2',
                bodyColor: '#ffffff',
                borderColor: '#82bee2',
                borderWidth: 1,
                callbacks: {
                    title: (context) => `時間：${context[0].label}`,
                    label: (context) => `價格：${Math.round(context.parsed.y)}`,
                },
            },
            custom_canvas_background_color: {} // 啟用深色背景 Plugin
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false,
        },
        scales: {
            x: {
                display: false,
                grid: { display: false },
            },
            y: {
                display: true,
                position: 'right',
                grid: {
                    color: 'rgba(130, 190, 226, 0.1)',
                },
                ticks: {
                    color: '#82bee2',
                    callback: (value) => Math.round(value),
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

    // 準備折線圖資料对象
    const data = {
        labels: getCurrentData().labels,
        datasets: [
            {
                label: displayMode === 'average' ? '平均價' : '價格',
                data: getCurrentData().data,
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
                pointBorderColor: '#0f203e',
                pointBorderWidth: 2,
            },
        ],
    };

    // loading / error 狀態
    if (loading) {
        return (
            <div className="w-full h-48 md:h-56 flex items-center justify-center bg-[#0f203e] rounded-lg">
                <div className="text-[#82bee2]">載入圖表中...</div>
            </div>
        );
    }
    if (error) {
        return (
            <div className="w-full h-48 md:h-56 flex items-center justify-center bg-[#0f203e] rounded-lg">
                <div className="text-red-400 text-sm">{error}</div>
            </div>
        );
    }

    return (
        <div className="relative w-full bg-[#0f203e] rounded-lg">
            {/* 右上角「檢視」按鈕 */}
            <div className="flex justify-end mb-2 w-full">
                <button
                    onClick={() => setModalOpen(true)}
                    className="px-3 py-1 bg-[#1A325F] text-[#AFE1F5] rounded-2xl text-xs font-medium hover:bg-[#2A4F7F] transition-colors ml-auto"
                >
                    檢視
                </button>
            </div>            {/* 圖表區塊 (矮化高度，簡潔顯示) */}
            <div className="w-full h-full flex flex-col justify-center items-center rounded-lg overflow-hidden">
                <div className="h-48 md:h-52 mb-2 w-full">
                    {displayMode === 'candlestick' ? (
                        <div
                            className="h-full cursor-move select-none"
                            onMouseDown={handleMouseDown}
                            onMouseMove={handleMouseMove}
                            onMouseUp={handleMouseUp}
                            onMouseLeave={handleMouseUp}
                            onWheel={handleWheel}
                            onTouchStart={handleTouchStart}
                            onTouchMove={handleTouchMove}
                            onTouchEnd={handleTouchEnd}
                            style={{ touchAction: 'pan-x pan-y' }}                        >                            <CandlestickChart
                                data={candlestickData}
                                width={1200}
                                height={200}
                                zoomLevel={zoomLevel}
                                panOffset={panOffset}
                            />
                        </div>
                    ) : (
                        <Line options={options} data={data} ref={chartRef} />
                    )}
                </div>

                {/* K 線模式下：顯示縮放與重置控制 */}
                {displayMode === 'candlestick' && (
                    <div className="flex flex-col space-y-2 pb-2">
                        <div className="flex justify-center items-center space-x-2">
                            <span className="text-[#82bee2] text-xs">縮放：</span>
                            <button
                                onClick={() => setZoomLevel(prev => Math.max(0.5, prev * 0.8))}
                                className="w-6 h-6 bg-[#1A325F] text-[#82bee2] rounded-full transition flex items-center justify-center"
                                title="縮小"
                            >
                                –
                            </button>
                            <div className="px-1 py-1 bg-[#1A325F] text-[#82bee2] text-xs rounded min-w-[40px] text-center">
                                {zoomLevel.toFixed(1)}x
                            </div>
                            <button
                                onClick={() => setZoomLevel(prev => Math.min(3, prev * 1.2))}
                                className="w-6 h-6 bg-[#1A325F] text-[#82bee2] rounded-full transition flex items-center justify-center"
                                title="放大"
                            >
                                ＋
                            </button>
                            <button
                                onClick={resetZoomPan}
                                className="px-2 py-1 bg-[#1A325F] text-[#82bee2] text-xs rounded transition"
                                title="重置"
                            >
                                重置
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Modal：切換顯示模式 */}
            {modalOpen && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 animate-in fade-in duration-200"
                    onClick={() => setModalOpen(false)}
                >
                    <div
                        className="bg-[#1A325F] rounded-lg w-72 p-4 relative animate-in zoom-in-95 duration-200"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-md font-semibold text-[#82bee2] mb-3">選擇圖表模式</h3>
                        <ul className="space-y-2">
                            <li>
                                <button
                                    onClick={() => {
                                        setDisplayMode('real');
                                        setModalOpen(false);
                                    }}
                                    className={`w-full text-left px-3 py-2 rounded-md text-xs transition-colors ${displayMode === 'real' ? 'bg-[#82bee2] text-[#0f203e]' : 'text-[#82bee2]'
                                        }`}
                                >
                                    真實價
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => {
                                        setDisplayMode('average');
                                        setModalOpen(false);
                                    }}
                                    className={`w-full text-left px-3 py-2 rounded-md text-xs transition-colors ${displayMode === 'average' ? 'bg-[#82bee2] text-[#0f203e]' : 'text-[#82bee2]'
                                        }`}
                                >
                                    平均價
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => {
                                        setDisplayMode('candlestick');
                                        resetZoomPan();
                                        setModalOpen(false);
                                    }}
                                    className={`w-full text-left px-3 py-2 rounded-md text-xs transition-colors ${displayMode === 'candlestick' ? 'bg-[#82bee2] text-[#0f203e]' : 'text-[#82bee2]'
                                        }`}
                                >
                                    K 線
                                </button>
                            </li>
                        </ul>
                    </div>
                </div>
            )}
        </div>
    );
};

export default StockChart;
