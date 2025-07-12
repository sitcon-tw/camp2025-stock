"use client";

import { useState, useEffect, useRef } from "react";
import { getWebPointHistory } from "@/lib/api";
import dayjs from "dayjs";
import { ChevronDown } from "lucide-react";

const PointHistoryCard = ({ token }) => {
    const [pointHistory, setPointHistory] = useState([]);
    const [pointHistoryLimit, setPointHistoryLimit] = useState(100);
    const [pointHistoryLoading, setPointHistoryLoading] = useState(false);
    const [showLimitDropdown, setShowLimitDropdown] = useState(false);
    const limitDropdownRef = useRef(null);

    // 點選外部關閉下拉選單
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (limitDropdownRef.current && !limitDropdownRef.current.contains(event.target)) {
                setShowLimitDropdown(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // 載入點數記錄
    const loadPointHistory = async () => {
        if (!token) return;
        
        setPointHistoryLoading(true);
        try {
            const newPointHistory = await getWebPointHistory(token, pointHistoryLimit);
            setPointHistory(newPointHistory);
        } catch (error) {
            console.error('載入點數記錄失敗:', error);
        } finally {
            setPointHistoryLoading(false);
        }
    };

    // 更改點數記錄顯示筆數
    const changePointHistoryLimit = async (newLimit) => {
        setPointHistoryLimit(newLimit);
        setShowLimitDropdown(false);
        setPointHistoryLoading(true);
        
        try {
            const newPointHistory = await getWebPointHistory(token, newLimit);
            setPointHistory(newPointHistory);
        } catch (error) {
            console.error('載入點數記錄失敗:', error);
        } finally {
            setPointHistoryLoading(false);
        }
    };

    // 初始載入
    useEffect(() => {
        loadPointHistory();
    }, [token, pointHistoryLimit]);

    return (
        <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
            <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-[#92cbf4]">
                    點數紀錄
                </h3>
                
                {/* 筆數選擇器 */}
                <div className="relative" ref={limitDropdownRef}>
                    <button
                        onClick={() => setShowLimitDropdown(!showLimitDropdown)}
                        className="flex items-center gap-2 rounded-lg border border-[#294565] bg-[#0f203e] px-3 py-2 text-sm text-[#92cbf4] transition-colors hover:bg-[#294565]/30"
                    >
                        <span>顯示 {pointHistoryLimit === 999999 ? '全部' : `${pointHistoryLimit} 筆`}</span>
                        <ChevronDown className={`h-4 w-4 transition-transform ${showLimitDropdown ? 'rotate-180' : ''}`} />
                    </button>
                    
                    {/* 下拉選單 */}
                    {showLimitDropdown && (
                        <div className="absolute right-0 top-12 z-10 w-32 rounded-lg border border-[#294565] bg-[#1A325F] py-2 shadow-lg">
                            {[10, 50, 100, 500, 1000].map((limit) => (
                                <button
                                    key={limit}
                                    onClick={() => changePointHistoryLimit(limit)}
                                    className={`w-full px-4 py-2 text-left text-sm transition-colors hover:bg-[#294565]/30 ${
                                        pointHistoryLimit === limit 
                                            ? 'bg-[#469FD2]/20 text-[#469FD2]' 
                                            : 'text-[#92cbf4]'
                                    }`}
                                >
                                    {limit} 筆
                                </button>
                            ))}
                            <button
                                onClick={() => changePointHistoryLimit(999999)}
                                className={`w-full px-4 py-2 text-left text-sm transition-colors hover:bg-[#294565]/30 ${
                                    pointHistoryLimit === 999999 
                                        ? 'bg-[#469FD2]/20 text-[#469FD2]' 
                                        : 'text-[#92cbf4]'
                                }`}
                            >
                                全部
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <div className="grid grid-flow-row gap-4">
                {pointHistoryLoading ? (
                    <div className="flex items-center justify-center py-8">
                        <div className="flex items-center gap-3">
                            <div className="h-5 w-5 animate-spin rounded-full border-2 border-[#92cbf4] border-t-transparent"></div>
                            <span className="text-[#92cbf4]">載入中...</span>
                        </div>
                    </div>
                ) : pointHistory && pointHistory.length > 0 ? (
                    pointHistory.map((i) => {
                        return (
                            <div
                                className="grid grid-cols-5 space-y-1 md:space-y-0 md:space-x-4"
                                key={i.created_at}
                            >
                                <p className="col-span-5 font-mono text-sm md:col-span-1 md:text-base">
                                    {dayjs(i.created_at)
                                        .add(8, "hour")
                                        .format(
                                            "MM/DD HH:mm",
                                        )}
                                </p>
                                <div className="col-span-5 md:col-span-4 md:flex">
                                    <p className="font-bold text-[#92cbf4]">
                                        {i.note}
                                    </p>

                                    <p className="ml-auto w-fit font-mono">
                                        {i.balance_after}{" "}
                                        <span
                                            className={
                                                i.amount < 0
                                                    ? "text-red-400"
                                                    : "text-green-400"
                                            }
                                        >
                                            (
                                            {i.amount > 0 &&
                                                "+"}
                                            {i.amount})
                                        </span>
                                    </p>
                                </div>
                            </div>
                        );
                    })
                ) : (
                    <div className="py-4 text-center text-[#557797]">
                        暫無點數記錄
                    </div>
                )}
            </div>
        </div>
    );
};

export default PointHistoryCard;