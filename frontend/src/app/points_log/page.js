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
    const [mergeTransfers, setMergeTransfers] = useState(false);

    useEffect(() => {
        // 優先順序：token > userToken > adminToken
        const token = localStorage.getItem("token") || 
                     localStorage.getItem("userToken") || 
                     localStorage.getItem("adminToken");
        
        if (!token) {
            setError("請先登入以查看點數紀錄");
            setLoading(false);
            return;
        }
        fetchPointHistory(token);
    }, [router]);

    const fetchPointHistory = async (token) => {
        try {
            setLoading(true);
            setError(null);
            console.log("開始載入所有點數紀錄（無限制）...");
            
            const startTime = Date.now();
            
            // 不設定 limit，載入所有資料
            const data = await getAllPointHistory(token, null);
            
            const loadTime = Date.now() - startTime;
            console.log(`成功載入 ${data?.length || 0} 筆點數紀錄，耗時 ${loadTime}ms`);
            setPointHistory(data || []);
            
            // 效能提示
            if (data && data.length > 100000) {
                console.warn(`載入了 ${data.length} 筆大量資料，可能影響頁面效能`);
            }
            
            if (data && data.length > 500000) {
                setError(`已載入 ${data.length} 筆記錄，資料量極大，建議使用篩選功能`);
            }
            
        } catch (error) {
            console.error("取得點數紀錄失敗:", error);
            setError(error.message || "無法載入點數紀錄");
        } finally {
            setLoading(false);
        }
    };

    // 處理轉帳合併邏輯
    const processedData = useMemo(() => {
        if (!mergeTransfers) {
            return pointHistory;
        }

        // 合併轉帳記錄
        const merged = [];
        const processedTransactionIds = new Set();

        for (const record of pointHistory) {
            if (record.type === 'transfer_out' || record.type === 'transfer_in') {
                // 如果已經處理過這個交易ID，跳過
                if (processedTransactionIds.has(record.transaction_id)) {
                    continue;
                }

                // 尋找配對的轉帳記錄
                const pairedRecord = pointHistory.find(r => 
                    r.transaction_id === record.transaction_id && 
                    r.user_id !== record.user_id &&
                    ((record.type === 'transfer_out' && r.type === 'transfer_in') ||
                     (record.type === 'transfer_in' && r.type === 'transfer_out'))
                );

                if (pairedRecord) {
                    // 創建合併記錄
                    const senderRecord = record.type === 'transfer_out' ? record : pairedRecord;
                    const receiverRecord = record.type === 'transfer_in' ? record : pairedRecord;
                    
                    // 從發送者的備註中提取實際轉帳金額和手續費
                    const transferAmount = Math.abs(receiverRecord.amount);
                    const fee = Math.abs(senderRecord.amount) - transferAmount;

                    const mergedRecord = {
                        ...record,
                        type: 'transfer_merged',
                        user_name: `${senderRecord.user_name} → ${receiverRecord.user_name}`,
                        amount: transferAmount,
                        note: `轉帳：${transferAmount} 點 ${fee > 0 ? `(手續費 ${fee} 點)` : ''}`,
                        transfer_partner: `${senderRecord.user_name} → ${receiverRecord.user_name}`,
                        balance_after: null, // 合併記錄不顯示餘額
                        created_at: Math.min(new Date(senderRecord.created_at), new Date(receiverRecord.created_at)),
                        sender_data: senderRecord,
                        receiver_data: receiverRecord,
                        transfer_fee: fee
                    };

                    merged.push(mergedRecord);
                    processedTransactionIds.add(record.transaction_id);
                } else {
                    // 沒有找到配對記錄，保持原樣
                    merged.push(record);
                }
            } else {
                // 非轉帳記錄，直接加入
                merged.push(record);
            }
        }

        return merged;
    }, [pointHistory, mergeTransfers]);

    // 篩選和搜尋邏輯
    const filteredData = useMemo(() => {
        return processedData.filter(record => {
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
    }, [processedData, searchTerm, filterType, filterUser, filterDateFrom, filterDateTo, filterAmountMin, filterAmountMax]);

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

    const exportToCSV = () => {
        // 準備 CSV 資料
        const headers = [
            '時間',
            '用戶名稱', 
            '交易類型',
            '金額',
            '餘額',
            '轉帳對象',
            '備註',
            '交易ID'
        ];

        // 轉換資料為 CSV 格式
        const csvData = filteredData.map(record => [
            formatDateTime(record.created_at),
            record.user_name || '',
            getTypeDisplay(record.type),
            record.amount || 0,
            record.balance_after !== null ? record.balance_after : '',
            record.transfer_partner || '',
            record.note || '',
            record.transaction_id || ''
        ]);

        // 建立 CSV 內容
        const csvContent = [
            headers.join(','),
            ...csvData.map(row => 
                row.map(field => {
                    // 處理包含逗號、引號或換行的欄位
                    const fieldStr = String(field);
                    if (fieldStr.includes(',') || fieldStr.includes('"') || fieldStr.includes('\n')) {
                        return `"${fieldStr.replace(/"/g, '""')}"`;
                    }
                    return fieldStr;
                }).join(',')
            )
        ].join('\n');

        // 建立並下載檔案
        const blob = new Blob(['\uFEFF' + csvContent], { 
            type: 'text/csv;charset=utf-8;' 
        });
        const link = document.createElement('a');
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-');
        const filename = `點數紀錄_${timestamp}.csv`;
        
        if (navigator.msSaveBlob) {
            // IE 10+
            navigator.msSaveBlob(blob, filename);
        } else {
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
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
            'transfer_merged': '轉帳交易',
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
            'transfer_in': 'text-green-400',
            'transfer_out': 'text-red-400',
            'transfer_merged': 'text-[#469FD2]',
            'arcade_deduct': 'text-red-400',
            'arcade_win': 'text-green-400',
            'qr_redeem': 'text-[#92cbf4]',
            'trading_buy': 'text-purple-400',
            'trading_sell': 'text-indigo-400',
            'system_adjustment': 'text-yellow-400',
            'initial_points': 'text-[#557797]'
        };
        return colorMap[type] || 'text-[#557797]';
    };

    // 取得所有類型選項
    const allTypes = [...new Set(processedData.map(record => record.type))];

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0f203e] flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-32 w-32 border-4 border-[#92cbf4] border-t-transparent mx-auto"></div>
                    <p className="mt-4 text-xl text-[#92cbf4]">載入點數紀錄中...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-[#0f203e] flex items-center justify-center">
                <div className="bg-[#1A325F] border border-[#294565] p-8 rounded-xl shadow-lg max-w-md w-full mx-4">
                    <div className="text-red-400 text-center mb-4">
                        <svg className="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold text-center mb-4 text-[#92cbf4]">載入失敗</h2>
                    <p className="text-[#557797] text-center mb-6">{error}</p>
                    <div className="flex gap-4">
                        <button
                            onClick={() => window.location.reload()}
                            className="flex-1 bg-[#469FD2] text-white px-4 py-2 rounded-xl hover:bg-[#357AB8] transition-colors"
                        >
                            重新載入
                        </button>
                        <button
                            onClick={() => window.open('/dashboard', '_blank')}
                            className="flex-1 border border-[#294565] bg-[#1A325F] text-[#92cbf4] px-4 py-2 rounded-xl hover:bg-[#294565] transition-colors"
                        >
                            前往 Dashboard
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0f203e] py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-[#92cbf4] mb-2">點數紀錄 DBMS</h1>
                    <p className="text-[#557797]">查詢、篩選、排序所有點數變動紀錄</p>
                    <div className="mt-4 flex items-center gap-4 text-sm text-[#557797]">
                        <span>總計 {pointHistory.length} 筆紀錄</span>
                        <span>•</span>
                        <span>處理後 {processedData.length} 筆</span>
                        <span>•</span>
                        <span>篩選後 {filteredData.length} 筆</span>
                        <span>•</span>
                        <span>第 {currentPage} / {totalPages} 頁</span>
                    </div>
                </div>

                {/* 篩選控制區 */}
                <div className="bg-[#1A325F] border border-[#294565] rounded-xl shadow-lg p-6 mb-6">
                    {/* 轉帳合併選項 */}
                    <div className="mb-4 flex items-center">
                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                checked={mergeTransfers}
                                onChange={(e) => setMergeTransfers(e.target.checked)}
                                className="h-4 w-4 text-[#469FD2] focus:ring-[#469FD2] border-[#294565] rounded bg-[#0f203e]"
                            />
                            <span className="ml-2 text-sm font-medium text-[#92cbf4]">
                                合併轉帳記錄 
                                <span className="text-[#557797] font-normal">
                                    (將 transfer_in 和 transfer_out 合併為單一轉帳交易)
                                </span>
                            </span>
                        </label>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        {/* 文字搜尋 */}
                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-1">搜尋</label>
                            <input
                                type="text"
                                placeholder="用戶名稱、備註、交易ID..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full px-3 py-2 border border-[#294565] bg-[#0f203e] text-white rounded-xl focus:outline-none focus:border-[#469FD2] placeholder-[#557797]"
                            />
                        </div>

                        {/* 類型篩選 */}
                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-1">交易類型</label>
                            <select
                                value={filterType}
                                onChange={(e) => setFilterType(e.target.value)}
                                className="w-full px-3 py-2 border border-[#294565] bg-[#0f203e] text-white rounded-xl focus:outline-none focus:border-[#469FD2]"
                            >
                                <option value="">所有類型</option>
                                {allTypes.map(type => (
                                    <option key={type} value={type}>{getTypeDisplay(type)}</option>
                                ))}
                            </select>
                        </div>

                        {/* 用戶篩選 */}
                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-1">用戶名稱</label>
                            <input
                                type="text"
                                placeholder="篩選特定用戶..."
                                value={filterUser}
                                onChange={(e) => setFilterUser(e.target.value)}
                                className="w-full px-3 py-2 border border-[#294565] bg-[#0f203e] text-white rounded-xl focus:outline-none focus:border-[#469FD2] placeholder-[#557797]"
                            />
                        </div>

                        {/* 每頁筆數 */}
                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-1">每頁筆數</label>
                            <select
                                value={itemsPerPage}
                                onChange={(e) => {
                                    setItemsPerPage(Number(e.target.value));
                                    setCurrentPage(1);
                                }}
                                className="w-full px-3 py-2 border border-[#294565] bg-[#0f203e] text-white rounded-xl focus:outline-none focus:border-[#469FD2]"
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
                            <label className="block text-sm font-medium text-[#92cbf4] mb-1">開始日期</label>
                            <input
                                type="date"
                                value={filterDateFrom}
                                onChange={(e) => setFilterDateFrom(e.target.value)}
                                className="w-full px-3 py-2 border border-[#294565] bg-[#0f203e] text-white rounded-xl focus:outline-none focus:border-[#469FD2]"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-1">結束日期</label>
                            <input
                                type="date"
                                value={filterDateTo}
                                onChange={(e) => setFilterDateTo(e.target.value)}
                                className="w-full px-3 py-2 border border-[#294565] bg-[#0f203e] text-white rounded-xl focus:outline-none focus:border-[#469FD2]"
                            />
                        </div>

                        {/* 金額範圍 */}
                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-1">最小金額</label>
                            <input
                                type="number"
                                placeholder="最小金額"
                                value={filterAmountMin}
                                onChange={(e) => setFilterAmountMin(e.target.value)}
                                className="w-full px-3 py-2 border border-[#294565] bg-[#0f203e] text-white rounded-xl focus:outline-none focus:border-[#469FD2] placeholder-[#557797]"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-1">最大金額</label>
                            <input
                                type="number"
                                placeholder="最大金額"
                                value={filterAmountMax}
                                onChange={(e) => setFilterAmountMax(e.target.value)}
                                className="w-full px-3 py-2 border border-[#294565] bg-[#0f203e] text-white rounded-xl focus:outline-none focus:border-[#469FD2] placeholder-[#557797]"
                            />
                        </div>
                    </div>

                    {/* 操作按鈕 */}
                    <div className="flex gap-4 flex-wrap">
                        <button
                            onClick={clearFilters}
                            className="px-4 py-2 border border-[#294565] bg-[#1A325F] text-[#92cbf4] rounded-xl hover:bg-[#294565] transition-colors"
                        >
                            清除篩選
                        </button>
                        <button
                            onClick={() => {
                                const token = localStorage.getItem("token") || 
                                             localStorage.getItem("userToken") || 
                                             localStorage.getItem("adminToken");
                                if (token) {
                                    console.log("手動重新載入所有點數紀錄");
                                    fetchPointHistory(token);
                                }
                            }}
                            className="px-4 py-2 bg-[#469FD2] text-white rounded-xl hover:bg-[#357AB8] transition-colors"
                        >
                            重新載入（全部）
                        </button>
                        <button
                            onClick={exportToCSV}
                            className="px-4 py-2 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors flex items-center gap-2"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            匯出 CSV ({filteredData.length} 筆)
                        </button>
                    </div>
                </div>

                {/* 資料表格 */}
                <div className="bg-[#1A325F] border border-[#294565] rounded-xl shadow-lg overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-[#294565]">
                            <thead className="bg-[#0f203e]">
                                <tr>
                                    <th 
                                        onClick={() => handleSort("created_at")}
                                        className="px-6 py-3 text-left text-xs font-medium text-[#92cbf4] uppercase tracking-wider cursor-pointer hover:bg-[#294565] transition-colors select-none"
                                    >
                                        <div className="flex items-center space-x-1">
                                            <span>時間</span>
                                            <div className="flex flex-col">
                                                <svg className={`w-3 h-3 ${sortField === "created_at" && sortOrder === "asc" ? "text-[#469FD2]" : "text-[#557797]"}`} fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
                                                </svg>
                                                <svg className={`w-3 h-3 ${sortField === "created_at" && sortOrder === "desc" ? "text-[#469FD2]" : "text-[#557797]"}`} fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                                </svg>
                                            </div>
                                        </div>
                                    </th>
                                    <th 
                                        onClick={() => handleSort("user_name")}
                                        className="px-6 py-3 text-left text-xs font-medium text-[#92cbf4] uppercase tracking-wider cursor-pointer hover:bg-[#294565] transition-colors select-none"
                                    >
                                        <div className="flex items-center space-x-1">
                                            <span>用戶</span>
                                            <div className="flex flex-col">
                                                <svg className={`w-3 h-3 ${sortField === "user_name" && sortOrder === "asc" ? "text-[#469FD2]" : "text-[#557797]"}`} fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
                                                </svg>
                                                <svg className={`w-3 h-3 ${sortField === "user_name" && sortOrder === "desc" ? "text-[#469FD2]" : "text-[#557797]"}`} fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                                </svg>
                                            </div>
                                        </div>
                                    </th>
                                    <th 
                                        onClick={() => handleSort("type")}
                                        className="px-6 py-3 text-left text-xs font-medium text-[#92cbf4] uppercase tracking-wider cursor-pointer hover:bg-[#294565] transition-colors select-none"
                                    >
                                        <div className="flex items-center space-x-1">
                                            <span>類型</span>
                                            <div className="flex flex-col">
                                                <svg className={`w-3 h-3 ${sortField === "type" && sortOrder === "asc" ? "text-[#469FD2]" : "text-[#557797]"}`} fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
                                                </svg>
                                                <svg className={`w-3 h-3 ${sortField === "type" && sortOrder === "desc" ? "text-[#469FD2]" : "text-[#557797]"}`} fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                                </svg>
                                            </div>
                                        </div>
                                    </th>
                                    <th 
                                        onClick={() => handleSort("amount")}
                                        className="px-6 py-3 text-left text-xs font-medium text-[#92cbf4] uppercase tracking-wider cursor-pointer hover:bg-[#294565] transition-colors select-none"
                                    >
                                        <div className="flex items-center space-x-1">
                                            <span>金額</span>
                                            <div className="flex flex-col">
                                                <svg className={`w-3 h-3 ${sortField === "amount" && sortOrder === "asc" ? "text-[#469FD2]" : "text-[#557797]"}`} fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
                                                </svg>
                                                <svg className={`w-3 h-3 ${sortField === "amount" && sortOrder === "desc" ? "text-[#469FD2]" : "text-[#557797]"}`} fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                                </svg>
                                            </div>
                                        </div>
                                    </th>
                                    <th 
                                        onClick={() => handleSort("balance_after")}
                                        className="px-6 py-3 text-left text-xs font-medium text-[#92cbf4] uppercase tracking-wider cursor-pointer hover:bg-[#294565] transition-colors select-none"
                                    >
                                        <div className="flex items-center space-x-1">
                                            <span>餘額</span>
                                            <div className="flex flex-col">
                                                <svg className={`w-3 h-3 ${sortField === "balance_after" && sortOrder === "asc" ? "text-[#469FD2]" : "text-[#557797]"}`} fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
                                                </svg>
                                                <svg className={`w-3 h-3 ${sortField === "balance_after" && sortOrder === "desc" ? "text-[#469FD2]" : "text-[#557797]"}`} fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                                </svg>
                                            </div>
                                        </div>
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-[#92cbf4] uppercase tracking-wider">
                                        轉帳對象
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-[#92cbf4] uppercase tracking-wider">
                                        備註
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-[#92cbf4] uppercase tracking-wider">
                                        交易ID
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-[#1A325F] divide-y divide-[#294565]">
                                {paginatedData.map((record, index) => (
                                    <tr key={`${record.user_id}-${record.created_at}-${index}`} className="hover:bg-[#294565] transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                                            {formatDateTime(record.created_at)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[#92cbf4]">
                                            {record.user_name}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`text-sm font-medium ${getTypeColor(record.type)}`}>
                                                {getTypeDisplay(record.type)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                                            <span className={record.amount >= 0 ? 'text-green-400' : 'text-red-400'}>
                                                {formatAmount(record.amount)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-white">
                                            {record.balance_after !== null ? record.balance_after?.toLocaleString() : '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                                            {record.transfer_partner && (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#469FD2] text-white">
                                                    {record.transfer_partner}
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-[#557797] max-w-xs truncate" title={record.note}>
                                            {record.note}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[#557797] font-mono">
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
                        <div className="bg-[#1A325F] px-4 py-3 flex items-center justify-between border-t border-[#294565] sm:px-6">
                            <div className="flex-1 flex justify-between sm:hidden">
                                <button
                                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                    disabled={currentPage === 1}
                                    className="relative inline-flex items-center px-4 py-2 border border-[#294565] text-sm font-medium rounded-xl text-[#92cbf4] bg-[#1A325F] hover:bg-[#294565] disabled:opacity-50 transition-colors"
                                >
                                    上一頁
                                </button>
                                <button
                                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                    disabled={currentPage === totalPages}
                                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-[#294565] text-sm font-medium rounded-xl text-[#92cbf4] bg-[#1A325F] hover:bg-[#294565] disabled:opacity-50 transition-colors"
                                >
                                    下一頁
                                </button>
                            </div>
                            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                                <div>
                                    <p className="text-sm text-[#557797]">
                                        顯示第 <span className="font-medium text-[#92cbf4]">{(currentPage - 1) * itemsPerPage + 1}</span> 到{" "}
                                        <span className="font-medium text-[#92cbf4]">{Math.min(currentPage * itemsPerPage, sortedData.length)}</span> 筆，
                                        共 <span className="font-medium text-[#92cbf4]">{sortedData.length}</span> 筆
                                    </p>
                                </div>
                                <div>
                                    <nav className="relative z-0 inline-flex rounded-xl shadow-sm -space-x-px">
                                        <button
                                            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                            disabled={currentPage === 1}
                                            className="relative inline-flex items-center px-2 py-2 rounded-l-xl border border-[#294565] bg-[#1A325F] text-sm font-medium text-[#92cbf4] hover:bg-[#294565] disabled:opacity-50 transition-colors"
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
                                                    className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium transition-colors ${
                                                        currentPage === page
                                                            ? 'z-10 bg-[#469FD2] border-[#469FD2] text-white'
                                                            : 'bg-[#1A325F] border-[#294565] text-[#92cbf4] hover:bg-[#294565]'
                                                    }`}
                                                >
                                                    {page}
                                                </button>
                                            );
                                        })}
                                        
                                        <button
                                            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                            disabled={currentPage === totalPages}
                                            className="relative inline-flex items-center px-2 py-2 rounded-r-xl border border-[#294565] bg-[#1A325F] text-sm font-medium text-[#92cbf4] hover:bg-[#294565] disabled:opacity-50 transition-colors"
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