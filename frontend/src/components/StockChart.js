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
import { apiService } from '@/services/apiService';
import CandlestickChart from './CandlestickChart';

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

const BackgroundColorPlugin = {
    id: 'custom_canvas_background_color',
    beforeDraw: (chart) => {
        const ctx = chart.ctx;
        ctx.save();
        ctx.globalCompositeOperation = 'destination-over';
        ctx.fillStyle = '#0f203e';
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
    const [displayMode, setDisplayMode] = useState('real');
    const [zoomLevel, setZoomLevel] = useState(3);
    const [panOffset, setPanOffset] = useState(0);
    const chartRef = useRef(null);
    const isDragging = useRef(false);
    const lastMouseX = useRef(0);

    const [modalOpen, setModalOpen] = useState(false);
    const [isModalClosing, setIsModalClosing] = useState(false);

    const fetchingRef = useRef(false);
    const lastFetchTimeRef = useRef(0);

    useEffect(() => {
        if (displayMode === 'candlestick') {
            setZoomLevel(1);
        } else {
            setZoomLevel(3);
        }
    }, [displayMode]); useEffect(() => {
        let isMounted = true;

        const fetchHistoricalData = async () => {
            const now = Date.now();

            // 避免重複 fetch
            if (fetchingRef.current) {
                return;
            }

            if (!isMounted) return; try {
                fetchingRef.current = true;
                setLoading(true);
                const historicalData = await apiService.getHistoricalData(24);

                if (!isMounted) return;

                if (historicalData && historicalData.length > 0) {
                    const realPriceData = historicalData.map(item => item.price);
                    const labels = historicalData.map(item => {
                        const date = new Date(item.timestamp);

                        // time zone asia/taipei
                        date.setHours(date.getHours() + 8);

                        return date.toLocaleTimeString('zh-TW', {
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                    });

                    setChartData({ data: realPriceData, labels });

                    const candlesticks = [];
                    for (let i = 0; i < historicalData.length; i += 4) {
                        const chunk = historicalData.slice(i, i + 4);
                        if (chunk.length > 0) {
                            const open = chunk[0].price;
                            const close = chunk[chunk.length - 1].price;
                            const high = Math.max(...chunk.map(d => d.price));
                            const low = Math.min(...chunk.map(d => d.price));

                            let datetime = new Date(chunk[0].timestamp);
                            datetime.setHours(datetime.getHours() + 8); // 時區調整

                            candlesticks.push({
                                open,
                                high,
                                low,
                                close,
                                timestamp: chunk[0].timestamp,
                                time: datetime
                            });
                        }
                    }
                    setCandlestickData(candlesticks);

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
                    });

                    if (candlesticks.length > 0) {
                        const chartWidth = 1200;
                        const scaledWidth = chartWidth * 1;
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
                lastFetchTimeRef.current = now;
            } catch (err) {
                console.error('獲取歷史資料失敗:', err);
                if (isMounted) {
                    setError('無法獲取歷史資料');
                    setChartData({ data: [], labels: [] });
                    setCandlestickData([]);
                    setAverageData({ data: [], labels: [] });
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
                fetchingRef.current = false;
            }
        };

        fetchHistoricalData();

        return () => {
            isMounted = false;
        };
    }, []);

    const handleMouseDown = (e) => {
        e.preventDefault();
        isDragging.current = true;
        lastMouseX.current = e.clientX || (e.touches && e.touches[0].clientX);
    };

    const handleMouseMove = (e) => {
        if (!isDragging.current) return;
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
        e.preventDefault();
        const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
        setZoomLevel(prev => Math.max(0.5, Math.min(10, prev * zoomFactor)));
    };

    const handleTouchStart = (e) => {
        if (e.touches.length === 1) {
            isDragging.current = true;
            lastMouseX.current = e.touches[0].clientX;
        }
    };

    const handleTouchMove = (e) => {
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
        const defaultZoom = displayMode === 'candlestick' ? 1 : 3;
        setZoomLevel(defaultZoom);

        if (candlestickData.length > 0) {
            const chartWidth = 1200;
            const scaledWidth = chartWidth * defaultZoom;
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

    const getCurrentData = () => {
        switch (displayMode) {
            case 'real':
                return chartData;
            case 'average':
                return averageData;
            default:
                return chartData;
        }
    };

    // 這邊會根據當天的漲或跌來決定圖表的顏色
    // 上漲紅色 下跌或沒變化綠色 (暫時)
    const lineColor = changePercent > 0 ? '#ef4444' : '#22c55e';
    const gradientColor = changePercent > 0
        ? 'rgba(239, 68, 68, 0.2)'
        : 'rgba(34, 197, 94, 0.2)';

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
            custom_canvas_background_color: {}
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
                min: displayMode !== 'candlestick' ? Math.max(0, getCurrentData().labels.length - Math.floor(getCurrentData().labels.length / zoomLevel)) : undefined,
                max: displayMode !== 'candlestick' ? getCurrentData().labels.length - 1 : undefined,
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

    if (loading) {
        return (
            <div className="relative w-full bg-[#0f203e] rounded-lg">
                <div className="flex justify-end mb-2 w-full">
                    <div className="px-3 py-1 bg-[#1A325F]/50 rounded-2xl text-xs">
                        <div className="w-8 h-3 bg-[#82bee2]/20 rounded animate-pulse"></div>
                    </div>
                </div>
                <div className="w-full h-full flex flex-col justify-center items-center rounded-lg overflow-hidden">
                    <div className="h-48 md:h-52 mb-2 w-full flex items-center justify-center bg-[#0f203e] rounded-lg">
                        <div className="flex flex-col items-center space-y-3">
                            <div className="text-[#82bee2] text-sm">載入圖表中...</div>
                        </div>
                    </div>
                    <div className="flex flex-col space-y-2 pb-2">
                        <div className="flex justify-center items-center space-x-2">
                            <div className="w-16 h-6 bg-[#1A325F]/50 rounded animate-pulse"></div>
                            <div className="w-6 h-6 bg-[#1A325F]/50 rounded-full animate-pulse"></div>
                            <div className="w-10 h-6 bg-[#1A325F]/50 rounded animate-pulse"></div>
                            <div className="w-6 h-6 bg-[#1A325F]/50 rounded-full animate-pulse"></div>
                            <div className="w-12 h-6 bg-[#1A325F]/50 rounded animate-pulse"></div>
                        </div>
                    </div>
                </div>
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

    const handleCloseModal = () => {
        setIsModalClosing(true);
        setTimeout(() => {
            setModalOpen(false);
            setIsModalClosing(false);
        }, 200); // Match animation duration
    };

    const handleModeSelect = (mode) => {
        setDisplayMode(mode);
        if (mode === 'candlestick') {
            resetZoomPan();
        }
        handleCloseModal();
    };

    return (
        <div className="relative w-full bg-[#0f203e] rounded-lg">
            <div className="flex justify-end mb-2 w-full">
                <button
                    onClick={() => setModalOpen(true)}
                    className="px-3 py-1 bg-[#1A325F] text-[#AFE1F5] rounded-2xl text-xs font-medium hover:bg-[#2A4F7F] transition-colors ml-auto"
                >
                    檢視
                </button>
            </div>
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
                            style={{ touchAction: 'pan-x pan-y' }}>
                            <CandlestickChart
                                data={candlestickData}
                                width={1200}
                                height={200}
                                zoomLevel={zoomLevel}
                                panOffset={panOffset}
                                changePercent={changePercent}
                                loading={loading}
                            />
                        </div>) : (
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
                            style={{ touchAction: 'pan-x pan-y' }}
                        >
                            <Line options={options} data={data} ref={chartRef} />
                        </div>
                    )}
                </div>
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
                            onClick={() => setZoomLevel(prev => Math.min(10, prev * 1.2))}
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
            </div>

            {modalOpen && (
                <div
                    className={`fixed inset-0 z-50 flex items-center justify-center bg-black/70 ${isModalClosing ? 'animate-modal-close-bg' : 'animate-modal-open-bg'}`}
                    onClick={handleCloseModal}
                >
                    <div
                        className={`bg-[#1A325F] rounded-lg w-72 p-4 relative ${isModalClosing ? 'animate-modal-close' : 'animate-modal-open'}`}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-xl font-semibold text-[#82bee2] mb-3">選擇圖表模式</h3>
                        <ul className="space-y-2">
                            <li>
                                <button
                                    onClick={() => handleModeSelect('real')}
                                    className={`w-full text-left px-3 py-2 rounded-md text-md transition-colors ${displayMode === 'real' ? 'bg-[#82bee2] text-[#0f203e]' : 'text-[#82bee2]'}`}
                                >
                                    真實價
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => handleModeSelect('average')}
                                    className={`w-full text-left px-3 py-2 rounded-md text-md transition-colors ${displayMode === 'average' ? 'bg-[#82bee2] text-[#0f203e]' : 'text-[#82bee2]'}`}
                                >
                                    平均價
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => handleModeSelect('candlestick')}
                                    className={`w-full text-left px-3 py-2 rounded-md text-md transition-colors ${displayMode === 'candlestick' ? 'bg-[#82bee2] text-[#0f203e]' : 'text-[#82bee2]'}`}
                                >
                                    K 線
                                </button>
                            </li>
                        </ul>
                    </div>
                </div>
            )}

            <style jsx global>{`
                @keyframes modal-open {
                    from {
                        opacity: 0;
                        transform: scale(0.95);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1);
                    }
                }
                
                @keyframes modal-close {
                    from {
                        opacity: 1;
                        transform: scale(1);
                    }
                    to {
                        opacity: 0;
                        transform: scale(0.95);
                    }
                }
                
                @keyframes modal-open-bg {
                    from {
                        opacity: 0;
                    }
                    to {
                        opacity: 1;
                    }
                }
                
                @keyframes modal-close-bg {
                    from {
                        opacity: 1;
                    }
                    to {
                        opacity: 0;
                    }
                }
                
                .animate-modal-open {
                    animation: modal-open 0.2s ease-out;
                }
                
                .animate-modal-close {
                    animation: modal-close 0.2s ease-in;
                }
                
                .animate-modal-open-bg {
                    animation: modal-open-bg 0.2s ease-out;
                }
                
                .animate-modal-close-bg {
                    animation: modal-close-bg 0.2s ease-in;
                }
            `}</style>
        </div>
    );
};

export default StockChart;
