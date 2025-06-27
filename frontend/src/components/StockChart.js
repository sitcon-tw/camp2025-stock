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
    Title,
    Tooltip,
} from "chart.js";
import { useEffect, useRef, useState } from "react";
import { Line } from "react-chartjs-2";
import { twMerge } from "tailwind-merge";
import CandlestickChart from "./CandlestickChart";
import Modal from "./Modal";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
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
    const [displayMode, setDisplayMode] = useState("real");
    const [zoomLevel, setZoomLevel] = useState(1);
    const [panOffset, setPanOffset] = useState(0);
    const chartRef = useRef(null);
    const isDragging = useRef(false);
    const lastMouseX = useRef(0);

    const chartModeModal = useModal();

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
            const now = Date.now();

            // 避免重複 fetch
            if (fetchingRef.current) {
                return;
            }

            if (!isMounted) return;
            try {
                fetchingRef.current = true;
                setLoading(true);
                const historicalData =
                    await apiService.getHistoricalData(24);

                if (!isMounted) return;

                if (historicalData && historicalData.length > 0) {
                    const realPriceData = historicalData.map(
                        (item) => item.price,
                    );
                    const labels = historicalData.map((item) => {
                        const date = new Date(item.timestamp);

                        // time zone asia/taipei
                        date.setHours(date.getHours() + 8);

                        return date.toLocaleTimeString("zh-TW", {
                            hour: "2-digit",
                            minute: "2-digit",
                        });
                    });

                    setChartData({ data: realPriceData, labels });

                    const candlesticks = [];
                    for (
                        let i = 0;
                        i < historicalData.length;
                        i += 4
                    ) {
                        const chunk = historicalData.slice(i, i + 4);
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

                            let datetime = new Date(
                                chunk[0].timestamp,
                            );
                            datetime.setHours(
                                datetime.getHours() + 8,
                            ); // 時區調整

                            candlesticks.push({
                                open,
                                high,
                                low,
                                close,
                                timestamp: chunk[0].timestamp,
                                time: datetime,
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
                        if (candlesticks.length > visibleCandles) {
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
        lastMouseX.current =
            e.clientX || (e.touches && e.touches[0].clientX);
    };

    const handleMouseMove = (e) => {
        if (!isDragging.current) return;
        e.preventDefault();
        const clientX =
            e.clientX || (e.touches && e.touches[0].clientX);
        const deltaX = clientX - lastMouseX.current;
        setPanOffset((prev) => prev + deltaX * 0.5);
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
            setPanOffset((prev) => prev + deltaX * 0.8);
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

    // 這邊會根據當天的漲或跌來決定圖表的顏色
    // 上漲紅色 下跌或沒變化綠色 (暫時)
    const lineColor = changePercent > 0 ? "#ef4444" : "#22c55e";
    const gradientColor =
        changePercent > 0
            ? "rgba(239, 68, 68, 0.2)"
            : "rgba(34, 197, 94, 0.2)";

    const options = {
        responsive: true,
        maintainAspectRatio: false,
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
                              getCurrentData().labels.length -
                                  Math.floor(
                                      getCurrentData().labels.length /
                                          zoomLevel,
                                  ),
                          )
                        : undefined,
                max:
                    displayMode !== "candlestick"
                        ? getCurrentData().labels.length - 1
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
                <div className="flex min-h-[400px] w-full grow flex-col items-center justify-center overflow-hidden">
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
            <div className="flex h-48 w-full items-center justify-center rounded-lg bg-[#0f203e] md:h-56">
                <div className="text-sm text-red-400">{error}</div>
            </div>
        );
    }

    const handleModeSelect = (mode) => {
        setDisplayMode(mode);
        if (mode === "candlestick") {
            resetZoomPan();
        }
        chartModeModal.closeModal();
    };

    return (
        <div className="relative flex h-full w-full flex-col rounded-lg bg-[#0f203e]">
            <div className="mb-2 flex w-full flex-shrink-0 justify-end">
                <button
                    onClick={chartModeModal.openModal}
                    className="ml-auto rounded-2xl bg-[#1A325F] px-3 py-1 text-xs font-medium text-[#AFE1F5] transition-colors hover:bg-[#2A4F7F]"
                >
                    檢視
                </button>
            </div>
            <div className="flex h-full w-full flex-col items-center justify-center overflow-hidden rounded-lg">
                <div className="md:min-h-none mb-2 min-h-[400px] w-full flex-1">
                    {displayMode === "candlestick" ? (
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
                            <CandlestickChart
                                data={candlestickData}
                                width={1200}
                                height={400}
                                zoomLevel={zoomLevel}
                                panOffset={panOffset}
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
                            {Math.round(zoomLevel.toFixed(1) * 100)}%
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
            </div>

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
