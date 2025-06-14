'use client';

import React from 'react';

const CandlestickChart = ({ data, width = 1000, height = 400, zoomLevel = 1, panOffset = 0 }) => {
    if (!data || data.length === 0) {
        return (
            <div
                className="flex items-center justify-center bg-[#0f203e] rounded-lg"
                style={{ height: height }}
            >
                <div className="text-[#82bee2] text-sm">無資料可顯示</div>
            </div>
        );
    }

    const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

    const margin = isMobile
        ? { top: 10, right: 45, bottom: 30, left: 20 }
        : { top: 15, right: 60, bottom: 40, left: 25 };

    const actualWidth = isMobile ? Math.min(450, window.innerWidth - 20) : width;
    const chartWidth = Math.max(320, actualWidth - margin.left - margin.right);
    const chartHeight = height - margin.top - margin.bottom;

    const allPrices = data.flatMap(d => [
        parseFloat(d.high) || 0,
        parseFloat(d.low) || 0,
        parseFloat(d.open) || 0,
        parseFloat(d.close) || 0
    ]).filter(price => !isNaN(price));

    const minPrice = Math.min(...allPrices) * 0.98;
    const maxPrice = Math.max(...allPrices) * 1.02;
    const priceRange = maxPrice - minPrice;
    const scaledWidth = chartWidth * zoomLevel;
    const candleSpacing = scaledWidth / Math.max(1, data.length - 1);

    const candleWidth = isMobile
        ? Math.max(2, Math.min(8, candleSpacing * 0.6))
        : Math.max(4, Math.min(16, candleSpacing * 0.7));

    const xScale = (index) => {
        const baseX = (index * candleSpacing) + panOffset;
        return baseX;
    };

    const yScale = (price) => {
        const normalizedPrice = parseFloat(price) || 0;
        return chartHeight - ((normalizedPrice - minPrice) / priceRange) * chartHeight;
    };

    return (
        <div className="w-full h-full flex justify-center items-center bg-[#0f203e] rounded-lg overflow-hidden">
            <svg
                width="100%"
                height="100%"
                className="max-w-full h-auto"
                viewBox={`0 0 ${actualWidth} ${height}`}
                preserveAspectRatio="xMidYMid meet"
                style={{ userSelect: 'none', touchAction: 'pan-x pan-y' }}
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

                <g transform={`translate(${margin.left}, ${margin.top})`}>
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

                            const open = parseFloat(d.open) || 0;
                            const close = parseFloat(d.close) || 0;
                            const high = parseFloat(d.high) || 0;
                            const low = parseFloat(d.low) || 0;

                            const bodyTop = yScale(Math.max(open, close));
                            const bodyBottom = yScale(Math.min(open, close));
                            const bodyHeight = Math.max(bodyBottom - bodyTop, 1);
                            const isGreen = close >= open;
                            const color = isGreen ? '#22c55e' : '#ef4444';

                            const strokeWidth = isMobile
                                ? Math.max(0.5, candleWidth * 0.1)
                                : Math.max(1, candleWidth * 0.12);

                            return (
                                <g key={i}>
                                    <line
                                        x1={x}
                                        y1={yScale(high)}
                                        x2={x}
                                        y2={yScale(low)}
                                        stroke={color}
                                        strokeWidth={strokeWidth}
                                        opacity={0.8}
                                    />

                                    <rect
                                        x={x - candleWidth / 2}
                                        y={bodyTop}
                                        width={candleWidth}
                                        height={bodyHeight}
                                        fill={isGreen ? color : 'none'}
                                        stroke={color}
                                        strokeWidth={strokeWidth}
                                        opacity={isGreen ? 0.8 : 1}
                                    />
                                </g>
                            );
                        })}
                    </g>

                    <g className="y-axis">
                        {[0, 0.25, 0.5, 0.75, 1].map(ratio => {
                            const price = minPrice + priceRange * ratio;
                            const y = yScale(price);
                            return (
                                <g key={ratio}>
                                    <text
                                        x={chartWidth + (isMobile ? 5 : 8)}
                                        y={y + 3}
                                        fill="#82bee2"
                                        fontSize={isMobile ? "10" : "11"}
                                        fontFamily="monospace"
                                        fontWeight="400"
                                    >
                                        {Math.round(price)}
                                    </text>
                                </g>
                            );
                        })}
                    </g>

                    <g className="x-axis">
                        {data.map((d, i) => {
                            const shouldShowLabel = isMobile
                                ? i % Math.max(1, Math.floor(data.length / 6)) === 0
                                : i % Math.max(1, Math.floor(data.length / 10)) === 0;

                            if (!shouldShowLabel) return null;

                            const x = xScale(i);
                            if (x < -candleWidth || x > chartWidth + candleWidth) return null;

                            // 格式化時間顯示
                            const formatTime = (timeStr) => {
                                if (!timeStr) return '';
                                try {
                                    const date = new Date(timeStr);
                                    if (isNaN(date.getTime())) {
                                        return timeStr;
                                    }
                                    return date.toLocaleTimeString('zh-TW', {
                                        hour: '2-digit',
                                        minute: '2-digit',
                                        hour12: false,
                                        timeZone: 'Asia/Taipei'
                                    });
                                } catch {
                                    return timeStr;
                                }
                            };

                            return (
                                <g key={`time-${i}`}>
                                    <text
                                        x={x}
                                        y={chartHeight + (isMobile ? 12 : 15)}
                                        fill="#82bee2"
                                        fontSize={isMobile ? "8" : "9"}
                                        fontFamily="monospace"
                                        textAnchor="middle"
                                        opacity={0.8}
                                    >
                                        {formatTime(d.time || d.timestamp || d.date)}
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
                                width={isMobile ? "70" : "85"}
                                height={isMobile ? "18" : "22"}
                                fill="rgba(15, 32, 62, 0.9)"
                                stroke="#82bee2"
                                strokeWidth="0.5"
                                rx="2"
                            />
                            <text
                                x={isMobile ? "8" : "13"}
                                y={isMobile ? "15" : "22"}
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
