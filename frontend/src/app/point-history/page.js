"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getPointHistory } from "@/lib/api";

export default function PointHistoryPage() {
    const router = useRouter();
    const [pointHistory, setPointHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(50);
    const [sortField, setSortField] = useState("created_at");
    const [sortOrder, setSortOrder] = useState("desc");
    const [filterUser, setFilterUser] = useState("");
    const [filterType, setFilterType] = useState("");
    const [originalData, setOriginalData] = useState([]);

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) {
            router.push("/login");
            return;
        }
        fetchPointHistory(token);
    }, [router]);

    const fetchPointHistory = async (token) => {
        try {
            setLoading(true);
            setError(null);
            const data = await getPointHistory(token, 5000);
            setOriginalData(data);
            setPointHistory(data);
        } catch (error) {
            console.error("取得點數紀錄失敗:", error);
            setError(error.message || "無法載入點數紀錄");
            if (error.message.includes("403") || error.message.includes("權限")) {
                setError("權限不足：需要管理員權限才能查看完整點數紀錄");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSort = (field) => {
        const newOrder = sortField === field && sortOrder === "asc" ? "desc" : "asc";
        setSortField(field);
        setSortOrder(newOrder);
        
        const sorted = [...pointHistory].sort((a, b) => {
            let aVal = a[field];
            let bVal = b[field];
            
            if (field === "created_at") {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            } else if (field === "amount") {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            } else if (typeof aVal === "string") {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (newOrder === "asc") {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
        
        setPointHistory(sorted);
        setCurrentPage(1);
    };

    const handleFilter = () => {
        let filtered = [...originalData];
        
        if (filterUser.trim()) {
            filtered = filtered.filter(item => 
                item.username && item.username.toLowerCase().includes(filterUser.toLowerCase())
            );
        }
        
        if (filterType.trim()) {
            filtered = filtered.filter(item => 
                item.note && item.note.toLowerCase().includes(filterType.toLowerCase())
            );
        }
        
        setPointHistory(filtered);
        setCurrentPage(1);
    };

    const clearFilters = () => {
        setFilterUser("");
        setFilterType("");
        setPointHistory(originalData);
        setCurrentPage(1);
    };

    const formatDateTime = (dateString) => {
        return new Date(dateString).toLocaleString('zh-TW', {
            timeZone: 'Asia/Taipei',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    const formatAmount = (amount) => {
        const num = parseFloat(amount) || 0;
        return num >= 0 ? `+${num}` : `${num}`;
    };

    const getAmountColor = (amount) => {
        const num = parseFloat(amount) || 0;
        if (num > 0) return "text-green-400";
        if (num < 0) return "text-red-400";
        return "text-gray-300";
    };

    const getSortIcon = (field) => {
        if (sortField !== field) return "↕️";
        return sortOrder === "asc" ? "↑" : "↓";
    };

    // 分頁邏輯
    const totalPages = Math.ceil(pointHistory.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentItems = pointHistory.slice(startIndex, endIndex);

    const goToPage = (page) => {
        setCurrentPage(Math.max(1, Math.min(page, totalPages)));
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0f203e] p-8">
                <div className="mx-auto max-w-7xl">
                    <div className="mb-6 text-center">
                        <h1 className="text-3xl font-bold text-[#82bee2]">載入中...</h1>
                    </div>
                    <div className="flex justify-center">
                        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-[#82bee2]"></div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-[#0f203e] p-8">
                <div className="mx-auto max-w-7xl">
                    <div className="mb-6 text-center">
                        <h1 className="text-3xl font-bold text-[#82bee2]">完整點數紀錄</h1>
                    </div>
                    <div className="rounded-2xl bg-red-500/20 p-6 text-center">
                        <div className="mb-4 text-lg text-red-400">載入失敗</div>
                        <div className="mb-4 text-gray-300">{error}</div>
                        <button
                            onClick={() => router.push("/leaderboard")}
                            className="rounded-xl bg-[#1A325F] px-4 py-2 text-[#82bee2] hover:bg-[#2A426F]"
                        >
                            返回排行榜
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0f203e] p-8">
            <div className="mx-auto max-w-7xl">
                {/* 標題與返回按鈕 */}
                <div className="mb-6 flex items-center justify-between">
                    <h1 className="text-3xl font-bold text-[#82bee2]">完整點數紀錄</h1>
                    <button
                        onClick={() => router.push("/leaderboard")}
                        className="rounded-xl bg-[#1A325F] px-4 py-2 text-[#82bee2] hover:bg-[#2A426F]"
                    >
                        返回排行榜
                    </button>
                </div>

                {/* 篩選控制項 */}
                <div className="mb-6 rounded-2xl bg-[#1A325F] p-4">
                    <div className="mb-4 flex flex-wrap gap-4">
                        <div className="flex-1 min-w-48">
                            <label className="mb-2 block text-sm text-[#AFE1F5]">
                                使用者名稱
                            </label>
                            <input
                                type="text"
                                value={filterUser}
                                onChange={(e) => setFilterUser(e.target.value)}
                                placeholder="搜尋使用者名稱..."
                                className="w-full rounded-lg bg-[#0f203e] px-3 py-2 text-white"
                            />
                        </div>
                        <div className="flex-1 min-w-48">
                            <label className="mb-2 block text-sm text-[#AFE1F5]">
                                備註類型
                            </label>
                            <input
                                type="text"
                                value={filterType}
                                onChange={(e) => setFilterType(e.target.value)}
                                placeholder="搜尋備註內容..."
                                className="w-full rounded-lg bg-[#0f203e] px-3 py-2 text-white"
                            />
                        </div>
                        <div className="flex-1 min-w-32">
                            <label className="mb-2 block text-sm text-[#AFE1F5]">
                                每頁顯示
                            </label>
                            <select
                                value={itemsPerPage}
                                onChange={(e) => {
                                    setItemsPerPage(parseInt(e.target.value));
                                    setCurrentPage(1);
                                }}
                                className="w-full rounded-lg bg-[#0f203e] px-3 py-2 text-white"
                            >
                                <option value={25}>25</option>
                                <option value={50}>50</option>
                                <option value={100}>100</option>
                                <option value={200}>200</option>
                                <option value={500}>500</option>
                            </select>
                        </div>
                    </div>
                    <div className="flex gap-4">
                        <button
                            onClick={handleFilter}
                            className="rounded-lg bg-[#82bee2] px-4 py-2 text-[#0f203e] font-semibold hover:bg-[#AFE1F5]"
                        >
                            套用篩選
                        </button>
                        <button
                            onClick={clearFilters}
                            className="rounded-lg bg-gray-600 px-4 py-2 text-white hover:bg-gray-500"
                        >
                            清除篩選
                        </button>
                    </div>
                </div>

                {/* 資料統計 */}
                <div className="mb-4 text-sm text-[#AFE1F5]">
                    顯示 {startIndex + 1}-{Math.min(endIndex, pointHistory.length)} 筆，
                    共 {pointHistory.length} 筆紀錄
                    {originalData.length !== pointHistory.length && 
                        ` (從 ${originalData.length} 筆中篩選)`
                    }
                </div>

                {/* 點數紀錄表格 */}
                <div className="rounded-2xl bg-[#1A325F] overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-[#0f203e]">
                                <tr>
                                    <th 
                                        className="px-4 py-3 text-left text-[#82bee2] cursor-pointer hover:bg-[#1A325F]"
                                        onClick={() => handleSort("created_at")}
                                    >
                                        時間 {getSortIcon("created_at")}
                                    </th>
                                    <th 
                                        className="px-4 py-3 text-left text-[#82bee2] cursor-pointer hover:bg-[#1A325F]"
                                        onClick={() => handleSort("username")}
                                    >
                                        使用者 {getSortIcon("username")}
                                    </th>
                                    <th 
                                        className="px-4 py-3 text-left text-[#82bee2] cursor-pointer hover:bg-[#1A325F]"
                                        onClick={() => handleSort("amount")}
                                    >
                                        點數變化 {getSortIcon("amount")}
                                    </th>
                                    <th 
                                        className="px-4 py-3 text-left text-[#82bee2] cursor-pointer hover:bg-[#1A325F]"
                                        onClick={() => handleSort("balance_after")}
                                    >
                                        餘額 {getSortIcon("balance_after")}
                                    </th>
                                    <th 
                                        className="px-4 py-3 text-left text-[#82bee2] cursor-pointer hover:bg-[#1A325F]"
                                        onClick={() => handleSort("note")}
                                    >
                                        備註 {getSortIcon("note")}
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {currentItems.map((item, index) => (
                                    <tr 
                                        key={`${item.created_at}-${item.username}-${index}`}
                                        className="border-t border-[#2A426F] hover:bg-[#2A426F]"
                                    >
                                        <td className="px-4 py-3 text-[#AFE1F5] text-sm">
                                            {formatDateTime(item.created_at)}
                                        </td>
                                        <td className="px-4 py-3 text-[#AFE1F5] font-medium">
                                            {item.username || "未知使用者"}
                                        </td>
                                        <td className={`px-4 py-3 font-semibold ${getAmountColor(item.amount)}`}>
                                            {formatAmount(item.amount)}
                                        </td>
                                        <td className="px-4 py-3 text-[#AFE1F5]">
                                            {item.balance_after || 0}
                                        </td>
                                        <td className="px-4 py-3 text-gray-300 text-sm">
                                            {item.note || "無備註"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* 分頁控制項 */}
                {totalPages > 1 && (
                    <div className="mt-6 flex justify-center items-center gap-2">
                        <button
                            onClick={() => goToPage(1)}
                            disabled={currentPage === 1}
                            className="px-3 py-2 rounded-lg bg-[#1A325F] text-[#82bee2] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#2A426F]"
                        >
                            第一頁
                        </button>
                        <button
                            onClick={() => goToPage(currentPage - 1)}
                            disabled={currentPage === 1}
                            className="px-3 py-2 rounded-lg bg-[#1A325F] text-[#82bee2] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#2A426F]"
                        >
                            上一頁
                        </button>
                        
                        <span className="px-4 py-2 text-[#AFE1F5]">
                            第 {currentPage} 頁，共 {totalPages} 頁
                        </span>
                        
                        <button
                            onClick={() => goToPage(currentPage + 1)}
                            disabled={currentPage === totalPages}
                            className="px-3 py-2 rounded-lg bg-[#1A325F] text-[#82bee2] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#2A426F]"
                        >
                            下一頁
                        </button>
                        <button
                            onClick={() => goToPage(totalPages)}
                            disabled={currentPage === totalPages}
                            className="px-3 py-2 rounded-lg bg-[#1A325F] text-[#82bee2] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#2A426F]"
                        >
                            最後頁
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}