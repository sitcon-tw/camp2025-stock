"use client";

import { useState, useRef } from "react";
import dayjs from "dayjs";
import { twMerge } from "tailwind-merge";
import Modal from "../ui/Modal";

const HistoricalOrdersCard = ({ 
    orderHistory, 
    canCancelOrder, 
    cancelingOrders,
    openCancelModal,
    cancelSuccess,
    cancelError 
}) => {
    return (
        <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
            <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                股票購買紀錄
            </h3>

            {/* 取消訂單的通知訊息 */}
            {cancelSuccess && (
                <div className="mb-4 rounded-xl border border-green-500/30 bg-green-600/20 p-3">
                    <p className="text-sm text-green-400">
                        ✅ {cancelSuccess}
                    </p>
                </div>
            )}
            {cancelError && (
                <div className="mb-4 rounded-xl border border-red-500/30 bg-red-600/20 p-3">
                    <p className="text-sm text-red-400">
                        ❌ {cancelError}
                    </p>
                </div>
            )}

            <div className="grid grid-flow-row gap-4">
                {orderHistory && orderHistory.length > 0 ? (
                    orderHistory.map((i) => {
                        const isCancellable = canCancelOrder(i);
                        const orderId =
                            i._id ||
                            i.id ||
                            i.order_id ||
                            i.orderId ||
                            i["$oid"];
                        const isCancelling = cancelingOrders.has(orderId);

                        return (
                            <div
                                className="rounded-xl border border-[#294565] bg-[#0f203e] p-4"
                                key={orderId || i.created_at}
                            >
                                {/* 訂單基本資訊 */}
                                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                                    <p className="font-mono text-sm text-[#92cbf4]">
                                        {dayjs(i.created_at)
                                            .add(8, "hour")
                                            .format("MM/DD HH:mm")}
                                    </p>
                                    <div className="flex items-center gap-2">
                                        <span
                                            className={twMerge(
                                                "rounded px-2 py-1 text-xs font-semibold",
                                                i.side === "sell"
                                                    ? "bg-green-600/20 text-green-400"
                                                    : "bg-red-600/20 text-red-400",
                                            )}
                                        >
                                            {i.side === "sell" ? "賣出" : "買入"}
                                        </span>
                                        <span className="rounded bg-[#294565] px-2 py-1 text-xs text-[#92cbf4]">
                                            {i.order_type === "market"
                                                ? "市價單"
                                                : "限價單"}
                                        </span>
                                    </div>
                                </div>

                                {/* Debug訊息 - 可以在生產環境中移除 */}
                                {process.env.NODE_ENV === "development" && (
                                    <div className="mb-2 rounded bg-gray-800 p-2 text-xs">
                                        <details>
                                            <summary className="cursor-pointer text-gray-400">
                                                Debug：訂單物件結構
                                            </summary>
                                            <pre className="mt-1 overflow-auto text-gray-300">
                                                {JSON.stringify(i, null, 2)}
                                            </pre>
                                        </details>
                                    </div>
                                )}

                                {/* 訂單狀態和詳情 */}
                                <div className="mb-3">
                                    <p className="font-bold text-[#92cbf4]">
                                        {i.status === "filled"
                                            ? `✅ 已成交${i.price ? ` → ${i.price}元` : ""}`
                                            : i.status === "cancelled"
                                              ? "❌ 已取消"
                                              : i.status === "pending_limit"
                                                ? "⏳ 等待中 (限制)"
                                                : i.status === "partial" ||
                                                    i.status === "pending"
                                                  ? i.filled_quantity > 0
                                                      ? `🔄 部分成交 (${i.filled_quantity}/${i.quantity} 股已成交@${i.filled_price ?? i.price}元，剩餘${i.quantity - i.filled_quantity}股等待)`
                                                      : "⏳ 等待成交"
                                                  : i.status}
                                    </p>

                                    {/* 訂單詳情 */}
                                    <div className="mt-2 grid grid-cols-2 gap-4 text-sm text-[#557797] md:grid-cols-3">
                                        <div>
                                            <span>數量：</span>
                                            <span className="text-white">
                                                {i.quantity} 股
                                            </span>
                                        </div>
                                        {i.price && (
                                            <div>
                                                <span>價格：</span>
                                                <span className="text-white">
                                                    {i.price} 元
                                                </span>
                                            </div>
                                        )}
                                        {i.filled_quantity > 0 && (
                                            <div>
                                                <span>已成交：</span>
                                                <span className="text-green-400">
                                                    {i.filled_quantity} 股
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* 取消按鈕 */}
                                {isCancellable && (
                                    <div className="flex justify-end">
                                        <button
                                            onClick={() =>
                                                openCancelModal(
                                                    i,
                                                    i.order_type,
                                                    i.quantity - (i.filled_quantity || 0),
                                                )
                                            }
                                            disabled={isCancelling}
                                            className={twMerge(
                                                "rounded-xl px-3 py-1 text-sm font-medium transition-colors",
                                                isCancelling
                                                    ? "cursor-not-allowed bg-gray-600/50 text-gray-400"
                                                    : "border border-red-500/30 bg-red-600/20 text-red-400 hover:bg-red-600/30",
                                            )}
                                        >
                                            {isCancelling ? "取消中..." : "取消訂單"}
                                        </button>
                                    </div>
                                )}
                            </div>
                        );
                    })
                ) : (
                    <div className="py-4 text-center text-[#557797]">
                        暫無股票交易記錄
                    </div>
                )}
            </div>
        </div>
    );
};

export default HistoricalOrdersCard;