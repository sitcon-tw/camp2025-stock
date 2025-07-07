"use client";

import { apiService } from "@/services/apiService";
import { useEffect, useState } from "react";
import { twMerge } from "tailwind-merge";

export default function HeaderBar() {
    const [priceData, setPriceData] = useState({
        currentPrice: 0,
        changePercent: 0,
        loading: true,
    });

    const [marketStatus, setMarketStatus] = useState({
        isOpen: false,
        loading: true,
    });

    const fetchPriceData = async () => {
        try {
            const data = await apiService.getPriceData();

            if (data) {
                const changePercentNum = parseFloat(
                    data.changePercent?.replace("%", "") || "0",
                );

                setPriceData({
                    currentPrice: data.lastPrice || 0,
                    averagePrice: data.averagePrice || 0,
                    changePercent: changePercentNum,
                    loading: false,
                });
            }
        } catch (error) {
            console.error("獲取價格資料失敗:", error);
            setPriceData({
                currentPrice: 0,
                changePercent: 0,
                loading: false,
            });
        }
    };

    const fetchMarketStatus = async () => {
        try {
            const data = await apiService.getMarketData();

            if (data) {
                setMarketStatus({
                    isOpen: data.isOpen,
                    loading: false,
                });
            }
        } catch (error) {
            console.error("獲取市場狀態失敗:", error);
            setMarketStatus({
                isOpen: false,
                loading: false,
            });
        }
    };
    useEffect(() => {
        let isMounted = true;

        const fetchInitialData = async () => {
            while (isMounted) {
                await Promise.all([
                    fetchPriceData(),
                    fetchMarketStatus(),
                ]);

                await new Promise((resolve) =>
                    setTimeout(resolve, 15_000),
                );
            }
        };

        fetchInitialData();

        return () => {
            isMounted = false;
        };
    }, []);

    const { currentPrice, changePercent, loading, averagePrice } =
        priceData;
    const isPositive = changePercent > 0;
    const isNegative = changePercent < 0;

    return (
        <div
            id="header"
            className="flex items-center justify-between pt-10"
        >
            <div>
                <h1 className="mx-auto mb-2 text-5xl font-bold text-[#82bee2]">
                    SITC
                </h1>

                <h1 className="mx-auto mt-4 text-lg font-bold text-[#82bee2]">
                    SITCON Camp • 點
                </h1>
            </div>

            <div className="mb-auto flex flex-col items-end justify-center">
                {loading ? (
                    <div className="animate-pulse">
                        <div className="mb-2 h-8 w-16 rounded bg-[#82bee2]/20"></div>
                        <div className="mb-2 h-6 w-12 rounded bg-[#82bee2]/20"></div>
                    </div>
                ) : (
                    <>
                        <div className="flex items-end gap-2">
                            <h1 className="text-sm font-bold text-[#82bee2]">
                                目前
                            </h1>
                            <h1 className="text-3xl font-bold text-[#82bee2]">
                                {Math.round(currentPrice)}
                            </h1>
                            <h1 className="text-sm font-bold text-[#82bee2]">
                                平均
                            </h1>
                            <h1 className="text-3xl font-bold text-[#82bee2]">
                                {Math.round(averagePrice)}
                            </h1>
                        </div>
                        <h1
                            className={twMerge(
                                "mt-1 font-semibold",
                                isPositive
                                    ? "text-[#D55E74]"
                                    : isNegative
                                      ? "text-green-500"
                                      : "text-gray-500",
                            )}
                        >
                            <span className="text-xs">
                                {isPositive
                                    ? "▲ "
                                    : isNegative
                                      ? "▼ "
                                      : ""}
                            </span>
                            {Math.abs(changePercent).toFixed(1)}%
                            (今天)
                        </h1>
                    </>
                )}

                {/* 動態市場狀態 */}
                <div className="mt-1 flex items-center space-x-2">
                    {marketStatus.loading ? (
                        <div className="animate-pulse">
                            <div className="h-4 w-16 rounded bg-[#82bee2]/20"></div>
                        </div>
                    ) : (
                        <>
                            <div
                                className={twMerge(
                                    "h-2 w-2 rounded-full",
                                    marketStatus.isOpen
                                        ? "bg-green-400"
                                        : "bg-red-400",
                                )}
                            ></div>
                            <h1
                                className={twMerge(
                                    "text-md font-bold",
                                    marketStatus.isOpen
                                        ? "text-green-400"
                                        : "text-red-400",
                                )}
                            >
                                {marketStatus.isOpen
                                    ? "開放交易"
                                    : "交易關閉"}
                            </h1>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
