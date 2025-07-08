
import { useState, useEffect } from "react";
import { getTrades } from "@/lib/api";
import { PermissionGuard } from "./PermissionGuard";
import { PERMISSIONS } from "@/contexts/PermissionContext";

const formatTimeUTC8 = (dateString, options = {}) => {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        const utc8Date = new Date(date.getTime() + (8 * 60 * 60 * 1000));
        
        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
            ...options
        };
        
        return utc8Date.toLocaleString('zh-TW', defaultOptions);
    } catch (error) {
        return 'N/A';
    }
};

export const TransactionHistory = ({ token }) => {
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedTransaction, setSelectedTransaction] = useState(null);

    const fetchTransactions = async () => {
        try {
            setLoading(true);
            setError(null);
            const trades = await getTrades(token, 1000); // Fetch a large number of trades
            setTransactions(trades);
        } catch (error) {
            console.error("Failed to fetch transactions:", error);
            setError(error.message || "獲取交易紀錄失敗");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (token) {
            fetchTransactions();
        }
    }, [token]);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">載入交易紀錄中...</p>
                </div>
            </div>
        );
    }

    return (
        <PermissionGuard
            requiredPermission={PERMISSIONS.VIEW_ALL_USERS}
            token={token}
        >
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-[#92cbf4]">交易紀錄</h2>
                        <p className="text-[#7BC2E6]">查看所有使用者的交易紀錄</p>
                    </div>
                    <button
                        onClick={fetchTransactions}
                        disabled={loading}
                        className="rounded bg-[#469FD2] px-4 py-2 text-white hover:bg-[#357AB8] disabled:opacity-50"
                    >
                        {loading ? "更新中..." : "更新"}
                    </button>
                </div>

                {error && (
                    <div className="rounded-lg border border-red-500/30 bg-red-600/20 p-4">
                        <div className="flex items-center space-x-2">
                            <span className="text-red-400">!</span>
                            <span className="text-red-300">{error}</span>
                        </div>
                    </div>
                )}

                <div className="rounded-lg border border-[#294565] bg-[#1A325F] shadow">
                    {transactions.length === 0 ? (
                        <div className="p-8 text-center">
                            <div className="text-4xl text-gray-500 mb-4">📜</div>
                            <p className="text-[#7BC2E6]">沒有交易紀錄</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-[#294565] bg-[#0f203e]">
                                        <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">時間</th>
                                        <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">買方</th>
                                        <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">賣方</th>
                                        <th className="px-4 py-3 text-right text-sm font-medium text-[#7BC2E6]">價格</th>
                                        <th className="px-4 py-3 text-right text-sm font-medium text-[#7BC2E6]">數量</th>
                                        <th className="px-4 py-3 text-center text-sm font-medium text-[#7BC2E6]">操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {transactions.map((trade, index) => (
                                        <tr 
                                            key={trade.id || index}
                                            className={`border-b border-[#294565] ${index % 2 === 0 ? 'bg-[#1A325F]' : 'bg-[#0f203e]'} hover:bg-[#294565] transition-colors`}
                                        >
                                            <td className="px-4 py-3 text-sm text-white">{formatTimeUTC8(trade.timestamp)}</td>
                                            <td className="px-4 py-3 text-sm text-white">{trade.buyer_username}</td>
                                            <td className="px-4 py-3 text-sm text-white">{trade.seller_username}</td>
                                            <td className="px-4 py-3 text-right text-sm font-semibold text-green-400">{trade.price}</td>
                                            <td className="px-4 py-3 text-right text-sm font-semibold text-blue-400">{trade.amount}</td>
                                            <td className="px-4 py-3 text-center">
                                                <button
                                                    onClick={() => setSelectedTransaction(trade)}
                                                    className="rounded bg-[#469FD2] px-3 py-1 text-xs text-white hover:bg-[#357AB8]"
                                                >
                                                    詳細
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {selectedTransaction && (
                    <TransactionDetailModal 
                        transaction={selectedTransaction} 
                        onClose={() => setSelectedTransaction(null)} 
                    />
                )}
            </div>
        </PermissionGuard>
    );
};

const TransactionDetailModal = ({ transaction, onClose }) => {
    const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
            onClose();
        }
    };

    const handleBackdropClick = (e) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-2 sm:p-4 overflow-y-auto"
            onClick={handleBackdropClick}
            onKeyDown={handleKeyDown}
            tabIndex={-1}
        >
            <div className="max-w-2xl w-full my-4 sm:my-8 rounded-lg border border-[#294565] bg-[#1A325F] shadow-xl max-h-[95vh] sm:max-h-[90vh] flex flex-col">
                <div className="flex items-center justify-between p-4 sm:p-6 border-b border-[#294565]">
                    <h3 className="text-lg sm:text-xl font-bold text-[#92cbf4]">交易詳細資料</h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors text-lg sm:text-xl"
                    >
                        ×
                    </button>
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                            <div className="text-sm text-[#7BC2E6]">交易ID</div>
                            <div className="text-white font-mono text-sm break-all">{transaction.id}</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                            <div className="text-sm text-[#7BC2E6]">時間</div>
                            <div className="text-white text-sm">{formatTimeUTC8(transaction.timestamp)}</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                            <div className="text-sm text-[#7BC2E6]">買方</div>
                            <div className="text-white font-medium">{transaction.buyer_username}</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                            <div className="text-sm text-[#7BC2E6]">賣方</div>
                            <div className="text-white font-medium">{transaction.seller_username}</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                            <div className="text-sm text-[#7BC2E6]">成交價格</div>
                            <div className="text-lg font-semibold text-green-400">{transaction.price}</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                            <div className="text-sm text-[#7BC2E6]">成交數量</div>
                            <div className="text-lg font-semibold text-blue-400">{transaction.amount}</div>
                        </div>
                    </div>
                </div>

                <div className="flex-shrink-0 flex justify-end p-4 sm:p-6 border-t border-[#294565]">
                    <button
                        onClick={onClose}
                        className="rounded bg-[#469FD2] px-4 sm:px-6 py-2 text-white hover:bg-[#357AB8]"
                    >
                        關閉
                    </button>
                </div>
            </div>
        </div>
    );
};

export default TransactionHistory;
