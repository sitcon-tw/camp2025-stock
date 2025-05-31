'use client';

import React from 'react';

// Fallback K-line chart using Canvas or simplified library
const CandlestickChart = ({ data, width = 800, height = 400 }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center bg-[#1a2e4a] rounded-lg" style={{ height: height }}>
        <div className="text-[#82bee2]">無數據可顯示</div>
      </div>
    );
  }

  // Simple K-line visualization using SVG
  const margin = { top: 20, right: 70, bottom: 30, left: 50 };
  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;

  // Calculate price range
  const prices = data.flatMap(d => [d.high, d.low, d.open, d.close]);
  const minPrice = Math.min(...prices) * 0.98;
  const maxPrice = Math.max(...prices) * 1.02;
  const priceRange = maxPrice - minPrice;

  // Scale functions
  const xScale = (index) => (index / (data.length - 1)) * chartWidth;
  const yScale = (price) => chartHeight - ((price - minPrice) / priceRange) * chartHeight;

  return (
    <div className="bg-[#1a2e4a] rounded-lg p-4">
      <svg width={width} height={height}>
        <g transform={`translate(${margin.left}, ${margin.top})`}>
          {/* Candlesticks */}
          {data.map((d, i) => {
            const x = xScale(i);
            const bodyTop = yScale(Math.max(d.open, d.close));
            const bodyBottom = yScale(Math.min(d.open, d.close));
            const bodyHeight = bodyBottom - bodyTop;
            const isGreen = d.close <= d.open;
            const color = isGreen ? '#22c55e' : '#ef4444';
            
            return (
              <g key={i}>
                {/* High-Low line */}
                <line
                  x1={x}
                  y1={yScale(d.high)}
                  x2={x}
                  y2={yScale(d.low)}
                  stroke={color}
                  strokeWidth={1}
                />
                {/* Body */}
                <rect
                  x={x - 3}
                  y={bodyTop}
                  width={6}
                  height={Math.max(bodyHeight, 1)}
                  fill={isGreen ? color : 'none'}
                  stroke={color}
                  strokeWidth={1}
                />
              </g>
            );
          })}
          
          {/* Y-axis */}
          <g transform={`translate(${chartWidth}, 0)`}>
            {[0, 0.25, 0.5, 0.75, 1].map(ratio => {
              const price = minPrice + (priceRange * ratio);
              const y = yScale(price);
              return (
                <g key={ratio}>
                  <line x1={0} y1={y} x2={5} y2={y} stroke="#82bee2" />
                  <text x={10} y={y + 4} fill="#82bee2" fontSize="12">
                    ${price.toFixed(2)}
                  </text>
                </g>
              );
            })}
          </g>
          
          {/* X-axis */}
          <g transform={`translate(0, ${chartHeight})`}>
            {data.filter((_, i) => i % Math.ceil(data.length / 6) === 0).map((d, i) => {
              const originalIndex = i * Math.ceil(data.length / 6);
              const x = xScale(originalIndex);
              return (
                <g key={i}>
                  <line x1={x} y1={0} x2={x} y2={5} stroke="#82bee2" />
                  <text x={x} y={20} fill="#82bee2" fontSize="10" textAnchor="middle">
                    {new Date(d.date).toLocaleDateString()}
                  </text>
                </g>
              );
            })}
          </g>
        </g>
      </svg>
    </div>
  );
};

export default CandlestickChart;
