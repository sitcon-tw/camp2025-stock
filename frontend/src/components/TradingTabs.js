"use client";

import { apiService } from "@/services/apiService";
import { useEffect, useState } from "react";
import { twMerge } from "tailwind-merge";

const TradingTabs = ({ activeTab: propActiveTab }) => {
    const [activeTab, setActiveTab] = useState(
        propActiveTab || "orderbook",
    );
    const [orderbookData, setOrderbookData] = useState({
        sells: [],
        buys: [],
    });
    const [tradeHistory, setTradeHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null); // 新增請求控制

    const fetchData = async () => {
        try {
            setLoading(true);

            // 同時抓五檔和交易記錄
            const [depthData, tradesData] = await Promise.all([
                apiService.getOrderBookData(),
                apiService.getTradeHistory(20),
            ]);

            setOrderbookData({
                sells: depthData.sell || [],
                buys: depthData.buy || [],
            });

            setTradeHistory(tradesData || []);

            setError(null);
        } catch (err) {
            console.error("獲取交易資料失敗:", err);
            setError("無法獲取交易資料");

            setOrderbookData({
                sells: [],
                buys: [],
            });

            setTradeHistory([]);
        } finally {
            setLoading(false);
        }
    };
    useEffect(() => {
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
    }, []);
    const OrderBookTab = () => {
        // 計算待買賣總數量
        const totalBuyQuantity = orderbookData.buys.reduce(
            (sum, order) => sum + (order?.quantity || 0),
            0,
        );
        const totalSellQuantity = orderbookData.sells.reduce(
            (sum, order) => sum + (order?.quantity || 0),
            0,
        );

        return (
            <div className="space-y-4">
                {loading && (
                    <div className="py-8 text-center text-[#82bee2]">
                        載入中...
                    </div>
                )}

                {error && (
                    <div className="py-2 text-center text-sm text-red-400">
                        {error}
                    </div>
                )}

                {!loading && (
                    <>
                        {/* 表頭 */}
                        <div className="text-md mb-2 grid grid-cols-4 border-b border-[#469FD2] pb-2 text-white">
                            <div className="text-center">
                                (
                                {totalBuyQuantity
                                    .toString()
                                    .padStart(2, "0")}
                                )
                            </div>
                            <div className="text-center">買價</div>
                            <div className="text-center">賣價</div>
                            <div className="text-center">
                                (
                                {totalSellQuantity
                                    .toString()
                                    .padStart(2, "0")}
                                )
                            </div>
                        </div>

                        {/* 五檔資料 */}
                        <div className="space-y-0">
                            {Array.from({ length: 5 }, (_, index) => {
                                const buyOrder =
                                    orderbookData.buys[index];
                                const sellOrder =
                                    orderbookData.sells[4 - index];

                                return (
                                    <div
                                        key={index}
                                        className="border-b border-[#469FD2]/30 last:border-b-0"
                                    >
                                        <div className="text-md grid grid-cols-4 gap-2 p-1 hover:bg-[#1a325f]/50">
                                            <div className="text-center font-mono text-white">
                                                {buyOrder
                                                    ? buyOrder.quantity.toLocaleString()
                                                    : "-"}
                                            </div>

                                            <div className="text-center font-mono text-white">
                                                {buyOrder
                                                    ? Math.round(
                                                          buyOrder.price,
                                                      )
                                                    : "-"}
                                            </div>

                                            <div className="text-center font-mono text-white">
                                                {" "}
                                                {sellOrder
                                                    ? Math.round(
                                                          sellOrder.price,
                                                      )
                                                    : "-"}
                                            </div>

                                            <div className="text-center font-mono text-white">
                                                {sellOrder
                                                    ? sellOrder.quantity.toLocaleString()
                                                    : "-"}
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

            // make UTC+8 Asia/Taipei
            date.setHours(date.getHours() + 8);

            const month = date.getMonth() + 1;
            const day = date.getDate();
            const hours = date.getHours().toString().padStart(2, "0");
            const minutes = date
                .getMinutes()
                .toString()
                .padStart(2, "0");
            const seconds = date
                .getSeconds()
                .toString()
                .padStart(2, "0");
            return `${month}/${day} ${hours}:${minutes}:${seconds}`;
        };

        // 計算漲跌
        const calculateChange = (currentPrice, index) => {
            if (index >= tradeHistory.length - 1) return 0;
            const prevPrice = tradeHistory[index + 1].price;
            return currentPrice - prevPrice;
        };

        return (
            <div
                className={twMerge(
                    "space-y-1",
                    isFixedMode && "flex h-full flex-col",
                )}
            >
                {loading && (
                    <div className="py-8 text-center text-[#82bee2]">
                        載入中...
                    </div>
                )}

                {error && (
                    <div className="py-2 text-center text-sm text-red-400">
                        {error}
                    </div>
                )}

                {!loading && (
                    <>
                        {/* 表頭 */}
                        <div className="text-md grid flex-shrink-0 grid-cols-5 gap-1 border-b border-[#469FD2] pb-1 text-white">
                            <div className="col-span-2 text-center">
                                時間
                            </div>
                            <div className="text-center">價格</div>
                            <div className="text-center">數量</div>
                            <div className="text-center">漲跌</div>
                        </div>

                        {/* 交易記錄 */}
                        <div
                            className={twMerge(
                                "space-y-0",
                                isFixedMode &&
                                    "flex-1 overflow-y-auto",
                            )}
                        >
                            {tradeHistory.map((trade, index) => {
                                const change = calculateChange(
                                    trade.price,
                                    index,
                                );
                                return (
                                    <div
                                        key={index}
                                        className="border-b border-[#469FD2]/30 last:border-b-0"
                                    >
                                        <div className="text-md grid grid-cols-5 gap-1 px-1 py-1 hover:bg-[#1a325f]/50">
                                            <div className="col-span-2 text-center font-mono whitespace-nowrap text-white">
                                                {formatTime(
                                                    trade.timestamp,
                                                )}
                                            </div>
                                            <div className="text-center font-mono text-white">
                                                {Math.round(
                                                    trade.price,
                                                )}
                                            </div>
                                            <div className="text-center font-mono text-white">
                                                {trade.quantity.toLocaleString()}
                                            </div>
                                            <div
                                                className={twMerge(
                                                    "text-center font-mono font-semibold",
                                                    change > 0
                                                        ? "text-red-400"
                                                        : change < 0
                                                          ? "text-green-400"
                                                          : "text-gray-400",
                                                )}
                                            >
                                                {change > 0
                                                    ? "+"
                                                    : ""}
                                                {change !== 0
                                                    ? Math.round(
                                                          change,
                                                      )
                                                    : "-"}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                            {tradeHistory.length === 0 &&
                                !loading && (
                                    <div className="py-8 text-center text-gray-400">
                                        暫無交易記錄
                                    </div>
                                )}
                        </div>
                    </>
                )}
            </div>
        );
    };

    // 判斷是否為固定模式（桌面版使用）
    const isFixedMode = propActiveTab !== undefined;

    return (
        <div
            className={twMerge(
                "flex flex-col",
                isFixedMode
                    ? activeTab === "orderbook"
                        ? "h-[250px]"
                        : "h-full flex-1"
                    : "h-[310px]",
            )}
        >
            {/* 標籤頁 - 只在非固定模式顯示 */}
            {!isFixedMode && (
                <div className="relative z-10 flex">
                    <button
                        onClick={() => setActiveTab("orderbook")}
                        className={twMerge(
                            "relative w-1/2 rounded-t-2xl px-6 py-2 text-sm font-medium text-[#AFE1F5]",
                            activeTab === "orderbook"
                                ? "bg-[#1a325f]"
                                : "bg-[#14274b]",
                        )}
                    >
                        五檔報價
                    </button>
                    <button
                        onClick={() => setActiveTab("history")}
                        className={twMerge(
                            "relative w-1/2 rounded-t-2xl px-6 py-2 text-sm font-medium text-[#AFE1F5]",
                            activeTab === "history"
                                ? "bg-[#1a325f]"
                                : "bg-[#14274b]",
                        )}
                    >
                        交易紀錄
                    </button>
                </div>
            )}

            {/* 固定模式的標題 */}
            {isFixedMode && (
                <div className="relative z-10 flex">
                    <div className="relative w-full rounded-t-2xl bg-[#1a325f] px-6 py-2 text-sm font-medium text-[#AFE1F5]">
                        {activeTab === "orderbook"
                            ? "五檔報價"
                            : "交易紀錄"}
                    </div>
                </div>
            )}

            {/* 內容區 */}
            <div
                className={twMerge(
                    "flex-1 bg-[#1a325f] p-2",
                    isFixedMode && activeTab === "orderbook"
                        ? "overflow-hidden"
                        : "overflow-y-auto",
                    isFixedMode
                        ? "rounded-t-none rounded-b-2xl"
                        : "rounded-tr-none rounded-b-2xl",
                )}
            >
                {activeTab === "orderbook" ? (
                    <OrderBookTab />
                ) : (
                    <TradeHistoryTab />
                )}
            </div>
        </div>
    );
};

export default TradingTabs;
