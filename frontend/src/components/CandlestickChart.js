'use client';

import React from 'react';

const CandlestickChart = ({ data, width = 1000, height = 200, zoomLevel = 1, panOffset = 0 }) => {
    if (!data || data.length === 0) {
        return (
            <div
                className="flex items-center justify-center bg-[#1a2e4a] rounded-lg"
                style={{ height: height }}
            >
                <div className="text-[#82bee2] text-sm">無 K 線資料可顯示</div>
            </div>
        );
    }

    const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
    const margin = isMobile
        ? { top: 10, right: 35, bottom: 10, left: 20 }
        : { top: 15, right: 50, bottom: 15, left: 25 };

    // 計算實際繪圖區寬高 (放大圖表)
    const actualWidth = isMobile ? Math.min(450, window.innerWidth - 20) : width;
    const chartWidth = Math.max(320, actualWidth - margin.left - margin.right);
    const chartHeight = height - margin.top - margin.bottom;

    // 計算價格範圍，並稍微擴大以避免 K 線碰到邊框
    const prices = data.flatMap(d => [d.high, d.low, d.open, d.close]);
    const minPrice = Math.min(...prices) * 0.995;
    const maxPrice = Math.max(...prices) * 1.005;
    const priceRange = maxPrice - minPrice;    // 計算縮放
    const scaledWidth = chartWidth * zoomLevel;
    const candleWidth = isMobile
        ? Math.max(3, Math.min(12, (scaledWidth / data.length) * 0.8))
        : Math.max(6, Math.min(20, (scaledWidth / data.length) * 0.8));
    const xScale = (index) => ((index / (data.length - 1)) * scaledWidth) + panOffset;
    const yScale = (price) => chartHeight - ((price - minPrice) / priceRange) * chartHeight;

    return (
        <div className="w-full h-full flex justify-center items-center bg-[#1a2e4a] rounded-lg overflow-hidden">
            <svg
                width="100%"
                height="100%"
                className="max-w-full h-auto touch-pan-x touch-pan-y"
                viewBox={`0 0 ${actualWidth} ${height}`}
                preserveAspectRatio="xMidYMid meet"
                style={{ userSelect: 'none' }}
            >
                <defs>
                    <linearGradient id="gridGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style={{ stopColor: '#82bee2', stopOpacity: 0.1 }} />
                        <stop offset="100%" style={{ stopColor: '#82bee2', stopOpacity: 0.05 }} />
                    </linearGradient>
                    <clipPath id="chartClip">
                        <rect x="0" y="0" width={chartWidth} height={chartHeight} />
                    </clipPath>
                </defs>

                <g transform={`translate(${margin.left}, ${margin.top})`}>                    {/* 簡化的網格線 (只顯示主要線條) */}
                    <g className="grid-lines">
                        {(isMobile ? [0.5] : [0.25, 0.75]).map(ratio => {
                            const y = yScale(minPrice + priceRange * ratio);
                            return (
                                <line
                                    key={ratio}
                                    x1={0}
                                    y1={y}
                                    x2={chartWidth}
                                    y2={y}
                                    stroke="#82bee2"
                                    strokeOpacity={0.1}
                                    strokeWidth={0.5}
                                />
                            );
                        })}
                    </g>

                    <g className="candlesticks" clipPath="url(#chartClip)">
                        {data.map((d, i) => {
                            const x = xScale(i);
                            if (x < -candleWidth || x > chartWidth + candleWidth) return null;

                            const bodyTop = yScale(Math.max(d.open, d.close));
                            const bodyBottom = yScale(Math.min(d.open, d.close));
                            const bodyHeight = Math.max(bodyBottom - bodyTop, 1);
                            const isGreen = d.close >= d.open;
                            const color = isGreen ? '#22c55e' : '#ef4444'; const strokeWidth = isMobile
                                ? Math.max(1, candleWidth * 0.08)
                                : Math.max(1.5, candleWidth * 0.1);

                            return (
                                <g key={i}>
                                    {/* 上下影線 */}
                                    <line
                                        x1={x}
                                        y1={yScale(d.high)}
                                        x2={x}
                                        y2={yScale(d.low)}
                                        stroke={color}
                                        strokeWidth={strokeWidth}
                                    />
                                    {/* K 線實體 */}
                                    <rect
                                        x={x - candleWidth / 2}
                                        y={bodyTop}
                                        width={candleWidth}
                                        height={bodyHeight}
                                        fill={isGreen ? color : 'none'}
                                        stroke={color}
                                        strokeWidth={strokeWidth}
                                    />
                                </g>
                            );
                        })}
                    </g>
                    <g className="y-axis">
                        {[0, 0.5, 1].map(ratio => {
                            const price = minPrice + priceRange * ratio;
                            const y = yScale(price);
                            return (
                                <g key={ratio}>
                                    <text
                                        x={chartWidth + (isMobile ? 8 : 12)}
                                        y={y + 4}
                                        fill="#82bee2"
                                        fontSize={isMobile ? "11" : "12"}
                                        fontFamily="monospace"
                                        fontWeight="500"
                                    >
                                        {Math.round(price)}
                                    </text>
                                </g>
                            );
                        })}
                    </g>

                    {(zoomLevel !== 1 || panOffset !== 0) && (
                        <g className="zoom-indicator">
                            <rect
                                x={isMobile ? "5" : "10"}
                                y={isMobile ? "5" : "10"}
                                width={isMobile ? "80" : "100"}
                                height={isMobile ? "20" : "25"}
                                fill="rgba(26, 46, 74, 0.9)"
                                stroke="#82bee2"
                                strokeWidth="1"
                                rx="3"
                            />
                            <text
                                x={isMobile ? "10" : "15"}
                                y={isMobile ? "17" : "25"}
                                fill="#82bee2"
                                fontSize={isMobile ? "8" : "9"}
                                fontFamily="monospace"
                            >
                                縮放: {zoomLevel.toFixed(1)}x
                            </text>
                        </g>
                    )}
                </g>
            </svg>
        </div>
    );
};

export default CandlestickChart;
