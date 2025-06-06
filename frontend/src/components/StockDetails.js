'use client';

import React from 'react';

const StockDetails = ({ stockData = {} }) => {
    const {
        currentPrice = 70,
        changePercent = 20,
        changeAmount = 11.67,
        openPrice = 58.33,
        highPrice = 75,
        lowPrice = 55,
        volume = 1250000,
        turnover = 87500000,
        marketCap = 8750000000,
        peRatio = 15.8,
        pbRatio = 2.1,
        eps = 4.43,
        dividend = 1.20,
        dividendYield = 1.71,
        previousClose = 58.33,
        weekHigh52 = 82.50,
        weekLow52 = 35.20,
        avgVolume = 980000,
        beta = 1.15,
        rsi = 65.4,
        macd = 2.35
    } = stockData;

    const isPositive = changePercent > 0;

    const formatNumber = (num) => {
        if (num >= 1e9) return Math.round(num / 1e9) + 'B';
        if (num >= 1e6) return Math.round(num / 1e6) + 'M';
        if (num >= 1e3) return Math.round(num / 1e3) + 'K';
        return Math.round(num).toLocaleString();
    };

    const DetailCard = ({ title, value, subValue, isPrice = false, isChange = false }) => (
        <div className="bg-[#1a2e4a] rounded-lg p-4 border border-[#82bee2]/10">
            <h3 className="text-[#82bee2] text-sm mb-2">{title}</h3>
            <div className="flex flex-col">
                <span className={`text-lg font-bold ${isChange ? (isPositive ? 'text-red-400' : 'text-green-400') : 'text-white'
                    }`}>
                    {value}
                </span>
                {subValue && (
                    <span className="text-gray-400 text-sm">{subValue}</span>
                )}
            </div>
        </div>
    );

    return (
        <div className="space-y-6">
            {/* 價格概覽 */}
            <div>
                <h2 className="text-[#82bee2] text-xl font-bold mb-4">價格資訊</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <DetailCard
                        title="目前價格"
                        value={Math.round(currentPrice)}
                        isPrice={true}
                    />
                    <DetailCard
                        title="漲跌幅"
                        value={`${isPositive ? '+' : ''}${changePercent.toFixed(1)}%`}
                        subValue={`${isPositive ? '+' : ''}${Math.round(changeAmount)}`}
                        isChange={true}
                    />
                    <DetailCard
                        title="開盤價"
                        value={Math.round(openPrice)}
                        isPrice={true}
                    />
                    <DetailCard
                        title="成交量"
                        value={formatNumber(volume)}
                        subValue="股"
                    />
                </div>
            </div>

            {/* 價格區間 */}
            <div>
                <h2 className="text-[#82bee2] text-xl font-bold mb-4">價格區間</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <DetailCard
                        title="最高價"
                        value={Math.round(highPrice)}
                        isPrice={true}
                    />
                    <DetailCard
                        title="最低價"
                        value={Math.round(lowPrice)}
                        isPrice={true}
                    />
                    <DetailCard
                        title="52週最高"
                        value={Math.round(weekHigh52)}
                        isPrice={true}
                    />
                    <DetailCard
                        title="52週最低"
                        value={Math.round(weekLow52)}
                        isPrice={true}
                    />
                </div>
            </div>

            {/* 成交資訊 */}
            <div>
                <h2 className="text-[#82bee2] text-xl font-bold mb-4">成交資訊</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <DetailCard
                        title="成交金額"
                        value={formatNumber(turnover)}
                        subValue="元"
                    />
                    <DetailCard
                        title="平均成交量"
                        value={formatNumber(avgVolume)}
                        subValue="股"
                    />          <DetailCard
                        title="前收盤價"
                        value={Math.round(previousClose)}
                        isPrice={true}
                    />
                </div>
            </div>

            {/* 財務指標 */}
            <div>
                <h2 className="text-[#82bee2] text-xl font-bold mb-4">財務指標</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                    <DetailCard
                        title="市值"
                        value={formatNumber(marketCap)}
                        subValue="元"
                    />
                    <DetailCard
                        title="本益比"
                        value={peRatio.toFixed(1)}
                        subValue="倍"
                    />
                    <DetailCard
                        title="股價淨值比"
                        value={pbRatio.toFixed(1)}
                        subValue="倍"
                    />          <DetailCard
                        title="每股盈餘"
                        value={eps.toFixed(1)}
                        subValue="元"
                    />
                    <DetailCard
                        title="股利"
                        value={dividend.toFixed(1)}
                        subValue="元"
                    />          <DetailCard
                        title="殖利率"
                        value={`${dividendYield.toFixed(1)}%`}
                    />
                </div>
            </div>

            {/* 技術指標 */}
            <div>
                <h2 className="text-[#82bee2] text-xl font-bold mb-4">技術分析</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                    <DetailCard
                        title="5日均線"
                        value={Math.round(currentPrice * 0.98)}
                        isPrice={true}
                    />
                    <DetailCard
                        title="10日均線"
                        value={Math.round(currentPrice * 0.95)}
                        isPrice={true}
                    />
                    <DetailCard
                        title="20日均線"
                        value={Math.round(currentPrice * 0.92)}
                        isPrice={true}
                    />
                    <DetailCard
                        title="60日均線"
                        value={Math.round(currentPrice * 0.88)}
                        isPrice={true}
                    />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <DetailCard
                        title="RSI (14天)"
                        value={rsi.toFixed(1)}
                        subValue={rsi > 70 ? "超買" : rsi < 30 ? "超賣" : "中性"}
                    />          <DetailCard
                        title="MACD"
                        value={macd.toFixed(1)}
                        subValue={macd > 0 ? "多頭" : "空頭"}
                    />
                    <DetailCard
                        title="Beta 係數"
                        value={beta.toFixed(1)}
                        subValue={beta > 1 ? "高波動" : "低波動"}
                    />
                </div>
            </div>
        </div>
    );
};

export default StockDetails;
