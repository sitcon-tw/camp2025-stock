"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { getAllPointHistory } from "@/lib/api";

export default function PointsHistoryDBMSPage() {
    const router = useRouter();
    const [pointHistory, setPointHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(100);
    const [sortField, setSortField] = useState("created_at");
    const [sortOrder, setSortOrder] = useState("desc");
    
    // 搜尋和篩選狀態
    const [searchTerm, setSearchTerm] = useState("");
    const [filterType, setFilterType] = useState("");
    const [filterUser, setFilterUser] = useState("");
    const [filterDateFrom, setFilterDateFrom] = useState("");
    const [filterDateTo, setFilterDateTo] = useState("");
    const [filterAmountMin, setFilterAmountMin] = useState("");
    const [filterAmountMax, setFilterAmountMax] = useState("");

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
            const data = await getAllPointHistory(token, 5000);
            setPointHistory(data);
        } catch (error) {
            console.error("取得點數紀錄失敗:", error);
            setError(error.message || "無法載入點數紀錄");
        } finally {
            setLoading(false);
        }
    };

    // 篩選和搜尋邏輯
    const filteredData = useMemo(() => {
        return pointHistory.filter(record => {
            // 文字搜尋 (搜尋用戶名稱、備註、轉帳對象)
            const searchMatch = !searchTerm || 
                record.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                record.note?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                record.transfer_partner?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                record.transaction_id?.toLowerCase().includes(searchTerm.toLowerCase());

            // 類型篩選
            const typeMatch = !filterType || record.type === filterType;

            // 用戶篩選
            const userMatch = !filterUser || record.user_name?.toLowerCase().includes(filterUser.toLowerCase());

            // 日期範圍篩選
            const recordDate = new Date(record.created_at);
            const dateFromMatch = !filterDateFrom || recordDate >= new Date(filterDateFrom);
            const dateToMatch = !filterDateTo || recordDate <= new Date(filterDateTo + "T23:59:59");

            // 金額範圍篩選
            const amountMinMatch = !filterAmountMin || record.amount >= parseInt(filterAmountMin);
            const amountMaxMatch = !filterAmountMax || record.amount <= parseInt(filterAmountMax);

            return searchMatch && typeMatch && userMatch && dateFromMatch && dateToMatch && amountMinMatch && amountMaxMatch;
        });
    }, [pointHistory, searchTerm, filterType, filterUser, filterDateFrom, filterDateTo, filterAmountMin, filterAmountMax]);

    // 排序邏輯
    const sortedData = useMemo(() => {
        return [...filteredData].sort((a, b) => {
            let aValue = a[sortField];
            let bValue = b[sortField];

            // 處理日期排序
            if (sortField === "created_at") {
                aValue = new Date(aValue);
                bValue = new Date(bValue);
            }

            // 處理數字排序
            if (sortField === "amount" || sortField === "balance_after") {
                aValue = Number(aValue);
                bValue = Number(bValue);
            }

            // 處理字串排序
            if (typeof aValue === "string" && typeof bValue === "string") {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }

            if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
            if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
            return 0;
        });
    }, [filteredData, sortField, sortOrder]);

    // 分頁邏輯
    const totalPages = Math.ceil(sortedData.length / itemsPerPage);
    const paginatedData = sortedData.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    const handleSort = (field) => {
        if (sortField === field) {
            setSortOrder(sortOrder === "asc" ? "desc" : "asc");
        } else {
            setSortField(field);
            setSortOrder("asc");
        }
        setCurrentPage(1);
    };

    const clearFilters = () => {
        setSearchTerm("");
        setFilterType("");
        setFilterUser("");
        setFilterDateFrom("");
        setFilterDateTo("");
        setFilterAmountMin("");
        setFilterAmountMax("");
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
        return amount >= 0 ? `+${amount.toLocaleString()}` : amount.toLocaleString();
    };

    const getTypeDisplay = (type) => {
        const typeMap = {
            'transfer_in': '收到轉帳',
            'transfer_out': '發送轉帳',
            'arcade_deduct': '遊戲廳扣款',
            'arcade_win': '遊戲廳獲勝',
            'qr_redeem': 'QR碼兌換',
            'trading_buy': '股票購買',
            'trading_sell': '股票出售',
            'system_adjustment': '系統調整',
            'initial_points': '初始點數'
        };
        return typeMap[type] || type;
    };

    const getTypeColor = (type) => {
        const colorMap = {
            'transfer_in': 'text-green-600',
            'transfer_out': 'text-red-600',
            'arcade_deduct': 'text-red-500',
            'arcade_win': 'text-green-500',
            'qr_redeem': 'text-blue-600',
            'trading_buy': 'text-purple-600',
            'trading_sell': 'text-indigo-600',
            'system_adjustment': 'text-yellow-600',
            'initial_points': 'text-gray-600'
        };
        return colorMap[type] || 'text-gray-500';
    };

    // 取得所有類型選項
    const allTypes = [...new Set(pointHistory.map(record => record.type))];

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
                    <p className="mt-4 text-xl text-gray-600">載入點數紀錄中...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full mx-4">
                    <div className="text-red-500 text-center mb-4">
                        <svg className="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold text-center mb-4">載入失敗</h2>
                    <p className="text-gray-600 text-center mb-6">{error}</p>
                    <div className="flex gap-4">
                        <button
                            onClick={() => window.location.reload()}
                            className="flex-1 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                        >
                            重新載入
                        </button>
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="flex-1 bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                        >
                            返回首頁
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">點數紀錄 DBMS</h1>
                    <p className="text-gray-600">查詢、篩選、排序所有點數變動紀錄</p>
                    <div className="mt-4 flex items-center gap-4 text-sm text-gray-500">
                        <span>總計 {pointHistory.length} 筆紀錄</span>
                        <span>•</span>
                        <span>篩選後 {filteredData.length} 筆</span>
                        <span>•</span>
                        <span>第 {currentPage} / {totalPages} 頁</span>
                    </div>
                </div>

                {/* 篩選控制區 */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        {/* 文字搜尋 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">搜尋</label>
                            <input
                                type="text"
                                placeholder="用戶名稱、備註、交易ID..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* 類型篩選 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">交易類型</label>
                            <select
                                value={filterType}
                                onChange={(e) => setFilterType(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">所有類型</option>
                                {allTypes.map(type => (
                                    <option key={type} value={type}>{getTypeDisplay(type)}</option>
                                ))}
                            </select>
                        </div>

                        {/* 用戶篩選 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">用戶名稱</label>
                            <input
                                type="text"
                                placeholder="篩選特定用戶..."
                                value={filterUser}
                                onChange={(e) => setFilterUser(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* 每頁筆數 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">每頁筆數</label>
                            <select
                                value={itemsPerPage}
                                onChange={(e) => {
                                    setItemsPerPage(Number(e.target.value));
                                    setCurrentPage(1);
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value={25}>25</option>
                                <option value={50}>50</option>
                                <option value={100}>100</option>
                                <option value={200}>200</option>
                                <option value={500}>500</option>
                            </select>
                        </div>

                        {/* 日期範圍 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">開始日期</label>
                            <input
                                type="date"
                                value={filterDateFrom}
                                onChange={(e) => setFilterDateFrom(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">結束日期</label>
                            <input
                                type="date"
                                value={filterDateTo}
                                onChange={(e) => setFilterDateTo(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* 金額範圍 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">最小金額</label>
                            <input
                                type="number"
                                placeholder="最小金額"
                                value={filterAmountMin}
                                onChange={(e) => setFilterAmountMin(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">最大金額</label>
                            <input
                                type="number"
                                placeholder="最大金額"
                                value={filterAmountMax}
                                onChange={(e) => setFilterAmountMax(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    {/* 操作按鈕 */}
                    <div className="flex gap-4">
                        <button
                            onClick={clearFilters}
                            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
                        >
                            清除篩選
                        </button>
                        <button
                            onClick={() => {
                                const token = localStorage.getItem("token");
                                if (token) fetchPointHistory(token);
                            }}
                            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                        >
                            重新載入
                        </button>
                    </div>
                </div>

                {/* 資料表格 */}
                <div className="bg-white rounded-lg shadow-md overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th 
                                        onClick={() => handleSort("created_at")}
                                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    >
                                        時間 {sortField === "created_at" && (sortOrder === "asc" ? "↑" : "↓")}
                                    </th>
                                    <th 
                                        onClick={() => handleSort("user_name")}
                                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    >
                                        用戶 {sortField === "user_name" && (sortOrder === "asc" ? "↑" : "↓")}
                                    </th>
                                    <th 
                                        onClick={() => handleSort("type")}
                                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    >
                                        類型 {sortField === "type" && (sortOrder === "asc" ? "↑" : "↓")}
                                    </th>
                                    <th 
                                        onClick={() => handleSort("amount")}
                                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    >
                                        金額 {sortField === "amount" && (sortOrder === "asc" ? "↑" : "↓")}
                                    </th>
                                    <th 
                                        onClick={() => handleSort("balance_after")}
                                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                    >
                                        餘額 {sortField === "balance_after" && (sortOrder === "asc" ? "↑" : "↓")}
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        轉帳對象
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        備註
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        交易ID
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {paginatedData.map((record, index) => (
                                    <tr key={`${record.user_id}-${record.created_at}-${index}`} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {formatDateTime(record.created_at)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {record.user_name}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`text-sm font-medium ${getTypeColor(record.type)}`}>
                                                {getTypeDisplay(record.type)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                                            <span className={record.amount >= 0 ? 'text-green-600' : 'text-red-600'}>
                                                {formatAmount(record.amount)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                                            {record.balance_after?.toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {record.transfer_partner && (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                    {record.transfer_partner}
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title={record.note}>
                                            {record.note}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                                            {record.transaction_id && (
                                                <span className="text-xs">
                                                    {record.transaction_id.substring(0, 8)}...
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* 分頁控制 */}
                    {totalPages > 1 && (
                        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                            <div className="flex-1 flex justify-between sm:hidden">
                                <button
                                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                    disabled={currentPage === 1}
                                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                                >
                                    上一頁
                                </button>
                                <button
                                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                    disabled={currentPage === totalPages}
                                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                                >
                                    下一頁
                                </button>
                            </div>
                            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                                <div>
                                    <p className="text-sm text-gray-700">
                                        顯示第 <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span> 到{" "}
                                        <span className="font-medium">{Math.min(currentPage * itemsPerPage, sortedData.length)}</span> 筆，
                                        共 <span className="font-medium">{sortedData.length}</span> 筆
                                    </p>
                                </div>
                                <div>
                                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                                        <button
                                            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                            disabled={currentPage === 1}
                                            className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                                        >
                                            上一頁
                                        </button>
                                        
                                        {/* 頁碼按鈕 */}
                                        {Array.from({ length: Math.min(10, totalPages) }, (_, i) => {
                                            const page = i + 1;
                                            return (
                                                <button
                                                    key={page}
                                                    onClick={() => setCurrentPage(page)}
                                                    className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                                        currentPage === page
                                                            ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                                                    }`}
                                                >
                                                    {page}
                                                </button>
                                            );
                                        })}
                                        
                                        <button
                                            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                            disabled={currentPage === totalPages}
                                            className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                                        >
                                            下一頁
                                        </button>
                                    </nav>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}