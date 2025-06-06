import React, { useState, useEffect } from 'react'
import { apiService } from '@/services/apiService'

export default function HeaderBar() {
    const [priceData, setPriceData] = useState({
        currentPrice: 0,
        changePercent: 0,
        loading: true
    });

    const [marketStatus, setMarketStatus] = useState({
        isOpen: false,
        loading: true
    });

    const fetchPriceData = async () => {
        try {
            const data = await apiService.getPriceData();

            if (data) {
                const changePercentNum = parseFloat(data.changePercent?.replace('%', '') || '0');

                setPriceData({
                    currentPrice: data.lastPrice || 0,
                    changePercent: changePercentNum,
                    loading: false
                });
            }
        } catch (error) {
            console.error('獲取價格資料失敗:', error);
            setPriceData({
                currentPrice: 0,
                changePercent: 0,
                loading: false
            });
        }
    };

    const fetchMarketStatus = async () => {
        try {
            const data = await apiService.getMarketData();

            if (data) {
                setMarketStatus({
                    isOpen: data.isOpen,
                    loading: false
                });
            }
        } catch (error) {
            console.error('獲取市場狀態失敗:', error);
            setMarketStatus({
                isOpen: false,
                loading: false
            });
        }
    }; useEffect(() => {
        let isMounted = true;

        const fetchInitialData = async () => {
            if (isMounted) {
                await Promise.all([fetchPriceData(), fetchMarketStatus()]);
            }
        };

        fetchInitialData();

        return () => {
            isMounted = false;
        };
    }, []);

    const { currentPrice, changePercent, loading } = priceData;
    const isPositive = changePercent > 0;
    const isNegative = changePercent < 0;

    return (
        <div id="header" className="flex justify-between items-center pt-10">
            <div>
                <h1 className="font-bold text-5xl text-[#82bee2] mx-auto mb-2">
                    SITC
                </h1>

                <h1 className="font-bold text-lg text-[#82bee2] mx-auto mt-4">
                    SITCON Camp • 點
                </h1>
            </div>

            <div className="flex flex-col justify-center items-end mb-auto">
                {loading ? (
                    <div className="animate-pulse">
                        <div className="h-8 w-16 bg-[#82bee2]/20 rounded mb-2"></div>
                        <div className="h-6 w-12 bg-[#82bee2]/20 rounded mb-2"></div>
                    </div>
                ) : (
                    <>
                        <h1 className="text-[#82bee2] text-3xl font-bold">
                            {Math.round(currentPrice)}
                        </h1>
                        <h1 className={`mt-1 font-semibold ${isPositive
                            ? "text-[#D55E74]"
                            : isNegative
                                ? "text-green-500"
                                : "text-gray-500"}`}>
                            <span className='text-xs'>{isPositive ? "▲ " : isNegative ? "▼ " : ""}</span>
                            {Math.abs(changePercent).toFixed(1)}% (今天)
                        </h1>
                    </>
                )}

                {/* 動態市場狀態 */}
                <div className="flex items-center space-x-2 mt-1">
                    {marketStatus.loading ? (
                        <div className="animate-pulse">
                            <div className="h-4 w-16 bg-[#82bee2]/20 rounded"></div>
                        </div>
                    ) : (
                        <>
                            <div className={`w-2 h-2 rounded-full ${marketStatus.isOpen ? 'bg-green-400' : 'bg-red-400'}`}></div>
                            <h1 className={`text-md font-bold ${marketStatus.isOpen ? 'text-green-400' : 'text-red-400'}`}>
                                {marketStatus.isOpen ? '開放交易' : '交易關閉'}
                            </h1>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
