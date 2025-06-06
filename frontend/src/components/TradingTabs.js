'use client';

import React, { useState, useEffect } from 'react';
import { apiService } from '@/services/apiService';

const TradingTabs = ({ currentPrice = 20.0 }) => {
    const [activeTab, setActiveTab] = useState('orderbook');
    const [orderbookData, setOrderbookData] = useState({
        sells: [],
        buys: []
    });
    const [tradeHistory, setTradeHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);    // 添加請求控制
    const [lastFetchTime, setLastFetchTime] = useState(0);
    const MIN_FETCH_INTERVAL = 5000; // 5秒最小間隔

    const fetchData = async () => {
        try {
            setLoading(true);

            // 同時抓五檔和交易記錄
            const [depthData, tradesData] = await Promise.all([
                apiService.getOrderBookData(),
                apiService.getTradeHistory(20)
            ]);

            setOrderbookData({
                sells: depthData.sell || [],
                buys: depthData.buy || []
            });

            setTradeHistory(tradesData || []);

            setError(null);
        } catch (err) {
            console.error('獲取交易資料失敗:', err);
            setError('無法獲取交易資料');

            setOrderbookData({
                sells: [],
                buys: []
            });

            setTradeHistory([]);
        } finally {
            setLoading(false);
        }
    }; useEffect(() => {
        let isMounted = true;

        const fetchInitialData = async () => {
            if (isMounted) {
                await fetchData();
            }
        };

        fetchInitialData();

        return () => {
            isMounted = false;
        };
    }, []); const OrderBookTab = () => {
        // 計算待買賣總數量
        const totalBuyQuantity = orderbookData.buys.reduce((sum, order) => sum + (order?.quantity || 0), 0);
        const totalSellQuantity = orderbookData.sells.reduce((sum, order) => sum + (order?.quantity || 0), 0);

        return (
            <div className="space-y-4">
                {loading && (
                    <div className="text-center text-[#82bee2] py-8">載入中...</div>
                )}

                {error && (
                    <div className="text-center text-red-400 text-sm py-2">{error}</div>
                )}

                {!loading && (
                    <>
                        {/* 表頭 */}
                        <div className="grid grid-cols-4 text-md text-white pb-2 border-b border-[#469FD2] mb-2">
                            <div className="text-center">({totalBuyQuantity.toString().padStart(2, '0')})</div>
                            <div className="text-center">買價</div>
                            <div className="text-center">賣價</div>
                            <div className="text-center">({totalSellQuantity.toString().padStart(2, '0')})</div>
                        </div>

                        {/* 五檔資料 */}
                        <div className="space-y-0">
                            {Array.from({ length: 5 }, (_, index) => {
                                const buyOrder = orderbookData.buys[index];
                                const sellOrder = orderbookData.sells[4 - index];

                                return (
                                    <div key={index} className="border-b border-[#469FD2]/30 last:border-b-0">
                                        <div className="grid grid-cols-4 gap-2 text-md hover:bg-[#1a325f]/50 p-1">
                                            <div className="text-white text-center font-mono">
                                                {buyOrder ? buyOrder.quantity.toLocaleString() : '-'}
                                            </div>

                                            <div className="text-white text-center font-mono">
                                                {buyOrder ? Math.round(buyOrder.price) : '-'}
                                            </div>

                                            <div className="text-white text-center font-mono">                            {sellOrder ? Math.round(sellOrder.price) : '-'}
                                            </div>

                                            <div className="text-white text-center font-mono">
                                                {sellOrder ? sellOrder.quantity.toLocaleString() : '-'}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </>
                )}
            </div>
        );
    };

    const TradeHistoryTab = () => {
        // 時間格式化
        const formatTime = (timestamp) => {
            const date = new Date(timestamp);
            const month = date.getMonth() + 1;
            const day = date.getDate();
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            const seconds = date.getSeconds().toString().padStart(2, '0');
            return `${month}/${day} ${hours}:${minutes}:${seconds}`;
        };

        // 計算漲跌
        const calculateChange = (currentPrice, index) => {
            if (index >= tradeHistory.length - 1) return 0;
            const prevPrice = tradeHistory[index + 1].price;
            return currentPrice - prevPrice;
        };

        return (
            <div className="space-y-1">
                {loading && (
                    <div className="text-center text-[#82bee2] py-8">載入中...</div>
                )}

                {error && (
                    <div className="text-center text-red-400 text-sm py-2">{error}</div>
                )}

                {!loading && (
                    <>
                        {/* 表頭 */}
                        <div className="grid grid-cols-5 gap-1 text-md text-white pb-1 border-b border-[#469FD2]">
                            <div className="text-center col-span-2">時間</div>
                            <div className="text-center">價格</div>
                            <div className="text-center">數量</div>
                            <div className="text-center">漲跌</div>
                        </div>

                        {/* 交易記錄 */}
                        <div className="space-y-0">
                            {tradeHistory.map((trade, index) => {
                                const change = calculateChange(trade.price, index);
                                return (
                                    <div key={index} className="border-b border-[#469FD2]/30 last:border-b-0">
                                        <div className="grid grid-cols-5 gap-1 text-md hover:bg-[#1a325f]/50 py-1 px-1">
                                            <div className="text-white font-mono text-center col-span-2 whitespace-nowrap">
                                                {formatTime(trade.timestamp)}
                                            </div>
                                            <div className="text-white font-mono text-center">
                                                {Math.round(trade.price)}
                                            </div>
                                            <div className="text-white text-center font-mono">
                                                {trade.quantity.toLocaleString()}
                                            </div>
                                            <div className={`text-center font-mono font-semibold ${change > 0 ? 'text-red-400' : change < 0 ? 'text-green-400' : 'text-gray-400'}`}>
                                                {change > 0 ? '+' : ''}{change !== 0 ? Math.round(change) : '-'}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                            {tradeHistory.length === 0 && !loading && (
                                <div className="text-center text-gray-400 py-8">暫無交易記錄</div>
                            )}
                        </div>
                    </>
                )}
            </div>
        );
    };

    return (
        <div className="h-[310px] flex flex-col">
            {/* 標籤頁 */}
            <div className="flex relative z-10">
                <button
                    onClick={() => setActiveTab('orderbook')}
                    className={`w-1/2 px-6 py-2 text-[#AFE1F5] text-sm font-medium relative rounded-t-2xl ${activeTab === 'orderbook'
                        ? 'bg-[#1a325f]'
                        : 'bg-[#14274b]'
                        }`}
                >
                    五檔報價
                </button>
                <button
                    onClick={() => setActiveTab('history')}
                    className={`w-1/2 px-6 py-2 text-[#AFE1F5] text-sm font-medium relative rounded-t-2xl ${activeTab === 'history'
                        ? 'bg-[#1a325f]'
                        : 'bg-[#14274b]'
                        }`}
                >
                    交易紀錄
                </button>
            </div>

            {/* 內容區 */}
            <div className="bg-[#1a325f] p-2 rounded-b-2xl rounded-tr-none flex-1 overflow-y-auto">
                {activeTab === 'orderbook' ? <OrderBookTab /> : <TradeHistoryTab />}
            </div>
        </div>
    );
};

export default TradingTabs;
