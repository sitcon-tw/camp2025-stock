"use client";

import useModal from "@/hooks/useModal";
import { apiService } from "@/services/apiService";
import {
    CategoryScale,
    Chart as ChartJS,
    Filler,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    TimeScale,
    Title,
    Tooltip,
} from "chart.js";
import "chartjs-adapter-date-fns";
import { useEffect, useRef, useState } from "react";
import { Line } from "react-chartjs-2";
import { twMerge } from "tailwind-merge";
import KLineChart from "./KLineChart";
import { Modal } from "../ui";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    TimeScale,
    Title,
    Tooltip,
    Legend,
    Filler,
);

const BackgroundColorPlugin = {
    id: "custom_canvas_background_color",
    beforeDraw: (chart) => {
        const ctx = chart.ctx;
        ctx.save();
        ctx.globalCompositeOperation = "destination-over";
        ctx.fillStyle = "#0f203e";
        ctx.fillRect(0, 0, chart.width, chart.height);
        ctx.restore();
    },
};
ChartJS.register(BackgroundColorPlugin);

const StockChart = ({ currentPrice = 20.0, changePercent = 0 }) => {
    const [chartData, setChartData] = useState({
        data: [],
        labels: [],
    });
    const [candlestickData, setCandlestickData] = useState([]);
    const [averageData, setAverageData] = useState({
        data: [],
        labels: [],
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [displayMode, setDisplayMode] = useState("candlestick");
    const [zoomLevel, setZoomLevel] = useState(1);
    const [panOffset, setPanOffset] = useState(0);
    const chartRef = useRef(null);
    const isDragging = useRef(false);
    const lastMouseX = useRef(0);

    // 日期區間選擇功能
    const [dateRangeMode, setDateRangeMode] = useState(false);
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");

    const chartModeModal = useModal();
    const dateRangeModal = useModal();

    const fetchingRef = useRef(false);
    const lastFetchTimeRef = useRef(0);

    useEffect(() => {
        if (displayMode === "candlestick") {
            setZoomLevel(1);
        } else {
            setZoomLevel(1);
        }
    }, [displayMode]);
    useEffect(() => {
        let isMounted = true;

        const fetchHistoricalData = async () => {
            while (isMounted) {
                if (fetchingRef.current) {
                    await new Promise((resolve) =>
                        setTimeout(resolve, 1000),
                    );
                    console.log("Skipping");
                    continue;
                }

                fetchingRef.current = true;
                setLoading(true);

                try {
                    const now = Date.now();
                    let historicalData;
                    
                    if (dateRangeMode && startDate && endDate) {
                        // 使用日期區間模式
                        historicalData = await apiService.getHistoricalDataByDateRange(startDate, endDate);
                    } else {
                        // 使用原有的小時數模式
                        historicalData = await apiService.getHistoricalData(24);
                    }

                    if (!isMounted) break;

                    if (historicalData && historicalData.length > 0) {
                        const realPriceData = historicalData.map(
                            (item) => item.price,
                        );
                        const labels = historicalData.map((item) => {
                            const date = new Date(item.timestamp);
                            // Convert to UTC+8 timezone
                            const utc8Date = new Date(date.getTime() + (8 * 60 * 60 * 1000));
                            return utc8Date.toLocaleTimeString("zh-TW", {
                                hour: "2-digit",
                                minute: "2-digit",
                                hour12: false
                            });
                        });

                        setChartData({ data: realPriceData, labels });

                        const candlesticks = [];
                        for (
                            let i = 0;
                            i < historicalData.length;
                            i += 4
                        ) {
                            const chunk = historicalData.slice(
                                i,
                                i + 4,
                            );
                            if (chunk.length > 0) {
                                const open = chunk[0].price;
                                const close =
                                    chunk[chunk.length - 1].price;
                                const high = Math.max(
                                    ...chunk.map((d) => d.price),
                                );
                                const low = Math.min(
                                    ...chunk.map((d) => d.price),
                                );

                                candlesticks.push({
                                    open,
                                    high,
                                    low,
                                    close,
                                    timestamp: new Date(chunk[0].timestamp).getTime(),
                                    volume: chunk.reduce((sum, d) => sum + (d.volume || 0), 0)
                                });
                            }
                        }
                        setCandlestickData(candlesticks);

                        const period = 5;
                        const movingAverages = [];
                        for (
                            let i = period - 1;
                            i < realPriceData.length;
                            i++
                        ) {
                            const sum = realPriceData
                                .slice(i - period + 1, i + 1)
                                .reduce((a, b) => a + b, 0);
                            movingAverages.push(sum / period);
                        }
                        setAverageData({
                            data: movingAverages,
                            labels: labels.slice(period - 1),
                        });

                        if (candlesticks.length > 0) {
                            const chartWidth = 1200;
                            const scaledWidth = chartWidth * 1;
                            const visibleCandles = Math.floor(
                                chartWidth / 20,
                            );
                            if (
                                candlesticks.length > visibleCandles
                            ) {
                                const totalWidth =
                                    (candlesticks.length - 1) *
                                    (scaledWidth /
                                        (candlesticks.length - 1));
                                const offsetToShowLast = -(
                                    totalWidth -
                                    chartWidth +
                                    100
                                );
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
                    console.error("獲取歷史資料失敗:", err);
                    if (isMounted) {
                        setError("無法獲取歷史資料");
                        setChartData({ data: [], labels: [] });
                        setCandlestickData([]);
                        setAverageData({ data: [], labels: [] });
                    }
                } finally {
                    if (isMounted) setLoading(false);
                    fetchingRef.current = false;
                }

                // 在日期區間模式下，不需要定期刷新
                if (!dateRangeMode) {
                    await new Promise((resolve) =>
                        setTimeout(resolve, 15_000),
                    );
                } else {
                    break; // 日期區間模式只執行一次
                }
            }
        };

        fetchHistoricalData();

        return () => {
            isMounted = false;
        };
    }, [dateRangeMode, startDate, endDate]);

    const handleMouseDown = (e) => {
        e.preventDefault();
        isDragging.current = true;
        lastMouseX.current =
            e.clientX || (e.touches && e.touches[0].clientX);
    };

    const handleMouseMove = (e) => {
        if (!isDragging.current) return;
        e.preventDefault();
        const clientX =
            e.clientX || (e.touches && e.touches[0].clientX);
        const deltaX = clientX - lastMouseX.current;
        const maxOffset = getCurrentData().labels.length * zoomLevel * 10;
        const minOffset = -maxOffset;
        setPanOffset((prev) => Math.max(minOffset, Math.min(maxOffset, prev + deltaX * 2)));
        lastMouseX.current = clientX;
    };

    const handleMouseUp = () => {
        isDragging.current = false;
    };

    const handleWheel = (e) => {
        e.preventDefault();
        const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
        setZoomLevel((prev) =>
            Math.max(0.5, Math.min(10, prev * zoomFactor)),
        );
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
            const maxOffset = getCurrentData().labels.length * zoomLevel * 10;
            const minOffset = -maxOffset;
            setPanOffset((prev) => Math.max(minOffset, Math.min(maxOffset, prev + deltaX * 2.5)));
            lastMouseX.current = e.touches[0].clientX;
        }
    };

    const handleTouchEnd = () => {
        isDragging.current = false;
    };

    const resetZoomPan = () => {
        // const defaultZoom = displayMode === 'candlestick' ? 1 : 3;
        const defaultZoom = 1;
        setZoomLevel(defaultZoom);

        if (candlestickData.length > 0) {
            const chartWidth = 1200;
            const scaledWidth = chartWidth * defaultZoom;
            const visibleCandles = Math.floor(chartWidth / 20);
            if (candlestickData.length > visibleCandles) {
                const totalWidth =
                    (candlestickData.length - 1) *
                    (scaledWidth / (candlestickData.length - 1));
                const offsetToShowLast = -(
                    totalWidth -
                    chartWidth +
                    100
                );
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
            case "real":
                return chartData;
            case "average":
                return averageData;
            default:
                return chartData;
        }
    };

    // 計算漲跌幅和顏色邏輯
    const calculateColorLogic = () => {
        if (dateRangeMode && chartData.data.length > 0) {
            // 日期區間模式：比較區間內第一個和最後一個價格
            const firstPrice = chartData.data[0];
            const lastPrice = chartData.data[chartData.data.length - 1];
            const change = lastPrice - firstPrice;
            const changePercent = firstPrice > 0 ? (change / firstPrice) * 100 : 0;
            
            return {
                changePercent,
                lineColor: changePercent > 0 ? "#ef4444" : "#22c55e",
                gradientColor: changePercent > 0 
                    ? "rgba(239, 68, 68, 0.2)" 
                    : "rgba(34, 197, 94, 0.2)"
            };
        } else {
            // 即時模式：使用傳入的 changePercent (基於當天開盤價)
            return {
                changePercent,
                lineColor: changePercent > 0 ? "#ef4444" : "#22c55e",
                gradientColor: changePercent > 0 
                    ? "rgba(239, 68, 68, 0.2)" 
                    : "rgba(34, 197, 94, 0.2)"
            };
        }
    };

    const colorLogic = calculateColorLogic();
    const lineColor = colorLogic.lineColor;
    const gradientColor = colorLogic.gradientColor;

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                mode: "index",
                intersect: false,
                backgroundColor: "rgba(15, 32, 62, 0.9)",
                titleColor: "#82bee2",
                bodyColor: "#ffffff",
                borderColor: "#82bee2",
                borderWidth: 1,
                callbacks: {
                    title: (context) => `時間：${context[0].label}`,
                    label: (context) =>
                        `價格：${Math.round(context.parsed.y)}`,
                },
            },
            custom_canvas_background_color: {},
        },
        interaction: {
            mode: "nearest",
            axis: "x",
            intersect: false,
        },
        scales: {
            x: {
                display: false,
                grid: { display: false },
                min:
                    displayMode !== "candlestick"
                        ? Math.max(
                              0,
                              Math.floor(-panOffset / (zoomLevel * 10)) +
                                  getCurrentData().labels.length -
                                  Math.floor(
                                      getCurrentData().labels.length /
                                          zoomLevel,
                                  ),
                          )
                        : undefined,
                max:
                    displayMode !== "candlestick"
                        ? Math.floor(-panOffset / (zoomLevel * 10)) +
                          getCurrentData().labels.length - 1
                        : undefined,
            },
            y: {
                display: true,
                position: "right",
                grid: {
                    color: "rgba(130, 190, 226, 0.1)",
                },
                ticks: {
                    color: "#82bee2",
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
                label: displayMode === "average" ? "平均價" : "價格",
                data: getCurrentData().data,
                borderColor: lineColor,
                backgroundColor: (context) => {
                    const chart = context.chart;
                    const { ctx, chartArea } = chart;
                    if (!chartArea) return null;
                    const gradient = ctx.createLinearGradient(
                        0,
                        chartArea.top,
                        0,
                        chartArea.bottom,
                    );
                    gradient.addColorStop(0, gradientColor);
                    gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
                    return gradient;
                },
                fill: true,
                pointBackgroundColor: lineColor,
                pointBorderColor: "#0f203e",
                pointBorderWidth: 2,
            },
        ],
    };

    if (loading) {
        return (
            <div className="flex h-full w-full flex-col rounded-lg bg-[#0f203e]">
                <div className="mb-2 flex w-full justify-end">
                    <div className="rounded-2xl bg-[#1A325F]/50 px-3 py-1 text-xs">
                        <div className="h-3 w-8 animate-pulse rounded bg-[#82bee2]/20"></div>
                    </div>
                </div>
                <div className="flex w-full flex-1 flex-col items-center justify-center overflow-hidden" style={{ minHeight: '350px' }}>
                    <div className="mb-2 flex w-full grow items-center justify-center rounded-lg bg-[#0f203e]">
                        <div className="text-sm text-[#82bee2]">
                            載入圖表中...
                        </div>
                    </div>
                    <div className="flex flex-col space-y-2 pb-2">
                        <div className="flex items-center justify-center space-x-2">
                            <div className="h-6 w-16 animate-pulse rounded bg-[#1A325F]/50"></div>
                            <div className="h-6 w-6 animate-pulse rounded-full bg-[#1A325F]/50"></div>
                            <div className="h-6 w-10 animate-pulse rounded bg-[#1A325F]/50"></div>
                            <div className="h-6 w-6 animate-pulse rounded-full bg-[#1A325F]/50"></div>
                            <div className="h-6 w-12 animate-pulse rounded bg-[#1A325F]/50"></div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex w-full items-center justify-center rounded-lg bg-[#0f203e] h-full" style={{ minHeight: '350px' }}>
                <div className="text-sm text-red-400">{error}</div>
            </div>
        );
    }

    const handleModeSelect = (mode) => {
        setDisplayMode(mode);
        resetZoomPan();
        chartModeModal.closeModal();
    };

    // 處理日期區間選擇
    const handleDateRangeSubmit = () => {
        if (!startDate || !endDate) {
            alert("請選擇開始和結束日期");
            return;
        }
        
        if (new Date(startDate) > new Date(endDate)) {
            alert("開始日期不能晚於結束日期");
            return;
        }
        
        // 檢查日期範圍是否超過30天
        const daysDiff = Math.ceil((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24));
        if (daysDiff > 30) {
            alert("日期範圍不能超過30天");
            return;
        }
        
        setDateRangeMode(true);
        dateRangeModal.closeModal();
    };

    // 重置為小時模式
    const resetToHourMode = () => {
        setDateRangeMode(false);
        setStartDate("");
        setEndDate("");
    };

    // 快速日期選擇
    const setQuickDateRange = (days) => {
        const today = new Date();
        const startDate = new Date(today);
        startDate.setDate(today.getDate() - days);
        
        setStartDate(startDate.toISOString().split('T')[0]);
        setEndDate(today.toISOString().split('T')[0]);
    };

    return (
        <div className="relative flex h-full w-full flex-col rounded-lg bg-[#0f203e]">
            <div className="mb-2 flex w-full flex-shrink-0 justify-between">
                <div className="flex items-center space-x-2">
                    {dateRangeMode && (
                        <div className="flex items-center space-x-2">
                            <span className="text-xs text-[#AFE1F5]">
                                {startDate} ~ {endDate}
                            </span>
                            {chartData.data.length > 0 && (
                                <span className={`text-xs font-medium ${
                                    colorLogic.changePercent > 0 ? 'text-red-400' : 
                                    colorLogic.changePercent < 0 ? 'text-green-400' : 'text-gray-400'
                                }`}>
                                    {colorLogic.changePercent > 0 ? '+' : ''}
                                    {colorLogic.changePercent.toFixed(2)}%
                                </span>
                            )}
                            <button
                                onClick={resetToHourMode}
                                className="rounded-2xl bg-[#1A325F] px-2 py-1 text-xs font-medium text-[#AFE1F5] transition-colors hover:bg-[#2A4F7F]"
                            >
                                重置
                            </button>
                        </div>
                    )}
                </div>
                <div className="flex space-x-2">
                    <button
                        onClick={dateRangeModal.openModal}
                        className="rounded-2xl bg-[#1A325F] px-3 py-1 text-xs font-medium text-[#AFE1F5] transition-colors hover:bg-[#2A4F7F]"
                    >
                        日期區間
                    </button>
                    <button
                        onClick={chartModeModal.openModal}
                        className="rounded-2xl bg-[#1A325F] px-3 py-1 text-xs font-medium text-[#AFE1F5] transition-colors hover:bg-[#2A4F7F]"
                    >
                        檢視
                    </button>
                </div>
            </div>
            <div className="flex h-full w-full flex-col items-center justify-center overflow-hidden rounded-lg">
                <div className="mb-2 w-full flex-1" style={{ minHeight: '350px' }}>
                    {displayMode === "candlestick" ? (
                        <div className="h-full">
                            <KLineChart
                                data={candlestickData}
                                width={1200}
                                height={400}
                                changePercent={changePercent}
                                loading={loading}
                            />
                        </div>
                    ) : (
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
                            style={{ touchAction: "pan-x pan-y" }}
                        >
                            <Line
                                options={options}
                                data={data}
                                ref={chartRef}
                                height={400}
                            />
                        </div>
                    )}
                </div>
                {displayMode !== "candlestick" && (
                    <div className="flex flex-shrink-0 flex-col space-y-2 pb-2">
                        <div className="flex items-center justify-center space-x-2">
                            <button
                                onClick={() =>
                                    setZoomLevel((prev) =>
                                        Math.max(0.5, prev * 0.8),
                                    )
                                }
                                className="flex h-6 w-6 items-center justify-center rounded-full bg-[#1A325F] text-[#82bee2] transition"
                                title="縮小"
                            >
                                –
                            </button>
                            <div className="min-w-[40px] rounded px-1 py-1 text-center text-xs text-[#82bee2]">
                                {Math.round(
                                    zoomLevel.toFixed(1) * 100,
                                )}
                                %
                            </div>
                            <button
                                onClick={() =>
                                    setZoomLevel((prev) =>
                                        Math.min(10, prev * 1.2),
                                    )
                                }
                                className="flex h-6 w-6 items-center justify-center rounded-full bg-[#1A325F] text-[#82bee2] transition"
                                title="放大"
                            >
                                ＋
                            </button>
                            <button
                                onClick={resetZoomPan}
                                className="rounded bg-[#1A325F] px-2 py-1 text-xs text-[#82bee2] transition"
                                title="重置"
                            >
                                重置
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* 日期區間選擇 Modal */}
            <Modal
                isOpen={dateRangeModal.isOpen}
                isClosing={dateRangeModal.isClosing}
                onClose={dateRangeModal.closeModal}
                title="選擇日期區間"
                size="md"
                className="w-96"
            >
                <div className="space-y-4">
                    {/* 快速選擇按鈕 */}
                    <div>
                        <label className="block text-sm font-medium text-[#82bee2] mb-2">
                            快速選擇
                        </label>
                        <div className="flex space-x-2">
                            <button
                                onClick={() => setQuickDateRange(7)}
                                className="px-3 py-1 text-xs rounded bg-[#1A325F] text-[#AFE1F5] hover:bg-[#2A4F7F] transition-colors"
                            >
                                最近7天
                            </button>
                            <button
                                onClick={() => setQuickDateRange(14)}
                                className="px-3 py-1 text-xs rounded bg-[#1A325F] text-[#AFE1F5] hover:bg-[#2A4F7F] transition-colors"
                            >
                                最近14天
                            </button>
                            <button
                                onClick={() => setQuickDateRange(30)}
                                className="px-3 py-1 text-xs rounded bg-[#1A325F] text-[#AFE1F5] hover:bg-[#2A4F7F] transition-colors"
                            >
                                最近30天
                            </button>
                        </div>
                    </div>

                    {/* 日期選擇 */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-[#82bee2] mb-1">
                                開始日期
                            </label>
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="w-full px-3 py-2 bg-[#1A325F] text-[#AFE1F5] border border-[#82bee2]/20 rounded focus:border-[#82bee2] focus:outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-[#82bee2] mb-1">
                                結束日期
                            </label>
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="w-full px-3 py-2 bg-[#1A325F] text-[#AFE1F5] border border-[#82bee2]/20 rounded focus:border-[#82bee2] focus:outline-none"
                            />
                        </div>
                    </div>

                    {/* 說明文字 */}
                    <div className="text-xs text-[#AFE1F5]/70">
                        <p>• 最多可查詢30天的歷史資料</p>
                        <p>• 開始日期不能晚於結束日期</p>
                    </div>

                    {/* 操作按鈕 */}
                    <div className="flex justify-end space-x-2">
                        <button
                            onClick={dateRangeModal.closeModal}
                            className="px-4 py-2 text-sm bg-[#1A325F] text-[#AFE1F5] rounded hover:bg-[#2A4F7F] transition-colors"
                        >
                            取消
                        </button>
                        <button
                            onClick={handleDateRangeSubmit}
                            className="px-4 py-2 text-sm bg-[#82bee2] text-[#0f203e] rounded hover:bg-[#82bee2]/80 transition-colors"
                        >
                            確定
                        </button>
                    </div>
                </div>
            </Modal>

            {/* 圖表模式選擇 Modal */}
            <Modal
                isOpen={chartModeModal.isOpen}
                isClosing={chartModeModal.isClosing}
                onClose={chartModeModal.closeModal}
                title="選擇圖表模式"
                size="sm"
                className="w-72"
            >
                <ul className="space-y-2">
                    <li>
                        <button
                            onClick={() => handleModeSelect("real")}
                            className={twMerge(
                                "text-md w-full rounded-md px-3 py-2 text-left transition-colors hover:bg-[#82bee2]/70",
                                displayMode === "real"
                                    ? "bg-[#82bee2] text-[#0f203e]"
                                    : "text-[#82bee2]",
                            )}
                        >
                            真實價
                        </button>
                    </li>
                    <li>
                        <button
                            onClick={() =>
                                handleModeSelect("average")
                            }
                            className={twMerge(
                                "text-md w-full rounded-md px-3 py-2 text-left transition-colors hover:bg-[#82bee2]/70",
                                displayMode === "average"
                                    ? "bg-[#82bee2] text-[#0f203e]"
                                    : "text-[#82bee2]",
                            )}
                        >
                            平均價
                        </button>
                    </li>
                    <li>
                        <button
                            onClick={() =>
                                handleModeSelect("candlestick")
                            }
                            className={twMerge(
                                "text-md w-full rounded-md px-3 py-2 text-left transition-colors hover:bg-[#82bee2]/70",
                                displayMode === "candlestick"
                                    ? "bg-[#82bee2] text-[#0f203e]"
                                    : "text-[#82bee2]",
                            )}
                        >
                            K 線
                        </button>
                    </li>
                </ul>
            </Modal>
        </div>
    );
};

export default StockChart;
