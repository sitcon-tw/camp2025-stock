import { useState, useEffect } from "react";
import { getPointHistory } from "@/lib/api";
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

export const PointHistory = ({ token }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchHistory = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await getPointHistory(token, 1000);
            setHistory(data);
        } catch (error) {
            console.error("Failed to fetch point history:", error);
            setError(error.message || "獲取點數紀錄失敗");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (token) {
            fetchHistory();
        }
    }, [token]);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">載入點數紀錄中...</p>
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
                        <h2 className="text-2xl font-bold text-[#92cbf4]">點數紀錄</h2>
                        <p className="text-[#7BC2E6]">查看所有使用者的點數交易紀錄</p>
                    </div>
                    <button
                        onClick={fetchHistory}
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
                    {history.length === 0 ? (
                        <div className="p-8 text-center">
                            <div className="text-4xl text-gray-500 mb-4">📜</div>
                            <p className="text-[#7BC2E6]">沒有點數紀錄</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-[#294565] bg-[#0f203e]">
                                        <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">時間</th>
                                        <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">使用者</th>
                                        <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">類型</th>
                                        <th className="px-4 py-3 text-right text-sm font-medium text-[#7BC2E6]">數量</th>
                                        <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">備註</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {history.map((entry, index) => (
                                        <tr 
                                            key={entry._id || index}
                                            className={`border-b border-[#294565] ${index % 2 === 0 ? 'bg-[#1A325F]' : 'bg-[#0f203e]'} hover:bg-[#294565] transition-colors`}
                                        >
                                            <td className="px-4 py-3 text-sm text-white">{formatTimeUTC8(entry.created_at)}</td>
                                            <td className="px-4 py-3 text-sm text-white">{entry.user_name || entry.user_id}</td>
                                            <td className="px-4 py-3 text-sm text-white">{entry.type}</td>
                                            <td className="px-4 py-3 text-right text-sm font-semibold text-green-400">{entry.amount}</td>
                                            <td className="px-4 py-3 text-sm text-white">{entry.note}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </PermissionGuard>
    );
};

export default PointHistory;
