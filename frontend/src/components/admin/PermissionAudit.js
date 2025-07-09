import { useState, useEffect } from "react";
import { getPointHistory, getTrades } from "@/lib/api";
import { Clock, User, Activity, AlertCircle, Search, Filter, Download } from "lucide-react";

/**
 * 系統審計日誌 - 類似 Discord 的伺服器審計日誌
 * 記錄和顯示系統中的所有重要操作
 */
export const PermissionAudit = ({ token }) => {
    const [auditData, setAuditData] = useState({
        pointLogs: [],
        escrowLogs: [],
        tradeLogs: [],
        systemEvents: [],
        combinedLogs: [],
    });
    const [loading, setLoading] = useState(true);
    const [selectedTab, setSelectedTab] = useState("all");
    const [filters, setFilters] = useState({
        dateRange: "today",
        actionType: "all",
        userId: "",
        searchTerm: "",
    });
    const [pagination, setPagination] = useState({
        currentPage: 1,
        pageSize: 50,
        totalPages: 1,
    });

    useEffect(() => {
        fetchAuditData();
    }, [token, filters]);

    const fetchAuditData = async () => {
        try {
            setLoading(true);
            
            // 並行獲取不同類型的日誌數據
            const [pointHistoryResponse, transactionResponse] = await Promise.all([
                getPointHistory(token).catch(err => ({ point_logs: [] })),
                getTrades(token).catch(err => ({ trades: [] })),
            ]);

            // 處理點數日誌
            const pointLogs = (pointHistoryResponse.point_logs || []).map(log => ({
                id: `point_${log.user_id}_${log.created_at}`,
                timestamp: log.created_at,
                type: "point_operation",
                action: log.type,
                user_id: log.user_id,
                details: {
                    amount: log.amount,
                    balance_after: log.balance_after,
                    note: log.note,
                },
                icon: "💰",
                color: "text-green-400",
            }));

            // 處理交易日誌
            const tradeLogs = (transactionResponse.trades || []).map(trade => ({
                id: `trade_${trade.id}`,
                timestamp: trade.timestamp,
                type: "trade_operation",
                action: "TRADE",
                user_id: trade.buyer_id || trade.seller_id,
                details: {
                    price: trade.price,
                    quantity: trade.quantity,
                    total_value: trade.total_value,
                    buyer_id: trade.buyer_id,
                    seller_id: trade.seller_id,
                },
                icon: "📊",
                color: "text-blue-400",
            }));

            // 模擬系統事件（基於已知的系統操作）
            const systemEvents = generateSystemEvents();

            // 合併所有日誌
            const combinedLogs = [...pointLogs, ...tradeLogs, ...systemEvents]
                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                .slice(0, 1000); // 限制最多1000條記錄

            setAuditData({
                pointLogs,
                tradeLogs,
                systemEvents,
                combinedLogs: applyFilters(combinedLogs),
            });

            // 更新分頁
            const filteredLogs = applyFilters(combinedLogs);
            setPagination(prev => ({
                ...prev,
                totalPages: Math.ceil(filteredLogs.length / prev.pageSize),
            }));

        } catch (error) {
            console.error("Failed to fetch audit data:", error);
        } finally {
            setLoading(false);
        }
    };

    const generateSystemEvents = () => {
        // 模擬系統事件，實際應從後端獲取
        const now = new Date();
        const events = [];
        
        // 模擬市場開閉事件
        const marketEvents = [
            { action: "market_open", note: "市場開啟", time: -30 },
            { action: "market_close", note: "市場關閉", time: -60 },
            { action: "system_maintenance", note: "系統維護", time: -120 },
        ];

        marketEvents.forEach((event, index) => {
            events.push({
                id: `system_${index}`,
                timestamp: new Date(now.getTime() + event.time * 60000).toISOString(),
                type: "system_operation",
                action: event.action,
                user_id: "system",
                details: {
                    note: event.note,
                    automated: true,
                },
                icon: "🖥️",
                color: "text-purple-400",
            });
        });

        return events;
    };

    const applyFilters = (logs) => {
        let filtered = logs;

        // 日期範圍過濾
        if (filters.dateRange !== "all") {
            const now = new Date();
            let startDate = new Date();
            
            switch (filters.dateRange) {
                case "today":
                    startDate.setHours(0, 0, 0, 0);
                    break;
                case "week":
                    startDate.setDate(now.getDate() - 7);
                    break;
                case "month":
                    startDate.setMonth(now.getMonth() - 1);
                    break;
            }
            
            filtered = filtered.filter(log => 
                new Date(log.timestamp) >= startDate
            );
        }

        // 操作類型過濾
        if (filters.actionType !== "all") {
            filtered = filtered.filter(log => log.type === filters.actionType);
        }

        // 用戶ID過濾
        if (filters.userId) {
            filtered = filtered.filter(log => 
                log.user_id && log.user_id.toLowerCase().includes(filters.userId.toLowerCase())
            );
        }

        // 搜索過濾
        if (filters.searchTerm) {
            const searchTerm = filters.searchTerm.toLowerCase();
            filtered = filtered.filter(log => 
                log.action.toLowerCase().includes(searchTerm) ||
                (log.details.note && log.details.note.toLowerCase().includes(searchTerm)) ||
                (log.user_id && log.user_id.toLowerCase().includes(searchTerm))
            );
        }

        return filtered;
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString('zh-TW', {
            timeZone: 'Asia/Taipei',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    };

    const formatActionName = (action) => {
        const actionMap = {
            "TRANSFER_IN": "轉入點數",
            "TRANSFER_OUT": "轉出點數",
            "ADMIN_GIVE": "管理員給予",
            "ADMIN_DEDUCT": "管理員扣除",
            "QR_REDEEM": "QR碼兌換",
            "TRADE": "股票交易",
            "TRADE_BUY": "購買股票",
            "TRADE_SELL": "出售股票",
            "market_open": "市場開啟",
            "market_close": "市場關閉",
            "system_maintenance": "系統維護",
            "ORDER_CREATE": "建立訂單",
            "ORDER_CANCEL": "取消訂單",
            "ORDER_MATCH": "訂單撮合",
        };
        return actionMap[action] || action;
    };

    const getActionColor = (type, action) => {
        const colorMap = {
            "point_operation": "text-green-400",
            "trade_operation": "text-blue-400", 
            "system_operation": "text-purple-400",
            "admin_operation": "text-orange-400",
            "user_operation": "text-cyan-400",
        };
        return colorMap[type] || "text-gray-400";
    };

    const getPaginatedLogs = () => {
        const startIndex = (pagination.currentPage - 1) * pagination.pageSize;
        const endIndex = startIndex + pagination.pageSize;
        return auditData.combinedLogs.slice(startIndex, endIndex);
    };

    // 審計日誌項目組件
    const AuditLogItem = ({ log }) => {
        const [expanded, setExpanded] = useState(false);

        return (
            <div className="bg-[#0f203e] border border-[#294565] rounded-lg p-4 hover:bg-[#1A325F] transition-colors">
                <div className="flex items-start space-x-3">
                    {/* 圖示 */}
                    <div className="flex-shrink-0 w-8 h-8 bg-[#294565] rounded-full flex items-center justify-center text-sm">
                        {log.icon}
                    </div>

                    {/* 主要內容 */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                                <span className={`font-medium ${getActionColor(log.type, log.action)}`}>
                                    {formatActionName(log.action)}
                                </span>
                                {log.user_id && log.user_id !== "system" && (
                                    <span className="text-[#7BC2E6] text-sm">
                                        by {log.user_id}
                                    </span>
                                )}
                            </div>
                            <div className="flex items-center space-x-2">
                                <span className="text-[#557797] text-sm">
                                    {formatTimestamp(log.timestamp)}
                                </span>
                                {Object.keys(log.details || {}).length > 0 && (
                                    <button
                                        onClick={() => setExpanded(!expanded)}
                                        className="text-[#7BC2E6] hover:text-[#92cbf4] text-sm"
                                    >
                                        {expanded ? "收起" : "詳情"}
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* 基本信息 */}
                        <div className="mt-1 text-sm text-[#7BC2E6]">
                            {log.type === "point_operation" && (
                                <span>
                                    {log.details.amount > 0 ? "+" : ""}{log.details.amount} 點數
                                    {log.details.balance_after && ` (餘額: ${log.details.balance_after})`}
                                </span>
                            )}
                            {log.type === "trade_operation" && (
                                <span>
                                    {log.details.quantity} 股 @ {log.details.price} 點數
                                    {log.details.total_value && ` (總價: ${log.details.total_value})`}
                                </span>
                            )}
                            {log.type === "system_operation" && (
                                <span>{log.details.note}</span>
                            )}
                        </div>

                        {/* 詳細信息 */}
                        {expanded && (
                            <div className="mt-3 p-3 bg-[#294565] rounded border border-[#3A5A7E]">
                                <h4 className="text-sm font-medium text-[#92cbf4] mb-2">詳細資訊</h4>
                                <div className="space-y-1">
                                    {Object.entries(log.details || {}).map(([key, value]) => (
                                        <div key={key} className="flex justify-between text-sm">
                                            <span className="text-[#7BC2E6]">{key}:</span>
                                            <span className="text-[#92cbf4]">
                                                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">載入審計日誌中...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-[#1A325F] rounded-lg shadow-lg border border-[#294565]">
            {/* 頁面標題 */}
            <div className="border-b border-[#294565] px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Activity className="h-6 w-6 text-[#92cbf4]" />
                        <h2 className="text-xl font-bold text-[#92cbf4]">審計日誌</h2>
                        <span className="text-sm text-[#7BC2E6]">
                            共 {auditData.combinedLogs.length} 條記錄
                        </span>
                    </div>
                    <button
                        onClick={fetchAuditData}
                        className="flex items-center space-x-2 bg-[#469FD2] text-white px-4 py-2 rounded hover:bg-[#5BAEE3] transition-colors"
                    >
                        <Clock className="h-4 w-4" />
                        <span>刷新</span>
                    </button>
                </div>
            </div>

            {/* 篩選器 */}
            <div className="border-b border-[#294565] px-6 py-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* 日期範圍篩選 */}
                    <div>
                        <label className="block text-sm font-medium text-[#7BC2E6] mb-1">
                            時間範圍
                        </label>
                        <select
                            value={filters.dateRange}
                            onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
                            className="w-full bg-[#0f203e] border border-[#294565] rounded px-3 py-2 text-[#92cbf4] focus:outline-none focus:ring-2 focus:ring-[#469FD2]"
                        >
                            <option value="all">全部時間</option>
                            <option value="today">今天</option>
                            <option value="week">過去7天</option>
                            <option value="month">過去30天</option>
                        </select>
                    </div>

                    {/* 操作類型篩選 */}
                    <div>
                        <label className="block text-sm font-medium text-[#7BC2E6] mb-1">
                            操作類型
                        </label>
                        <select
                            value={filters.actionType}
                            onChange={(e) => setFilters(prev => ({ ...prev, actionType: e.target.value }))}
                            className="w-full bg-[#0f203e] border border-[#294565] rounded px-3 py-2 text-[#92cbf4] focus:outline-none focus:ring-2 focus:ring-[#469FD2]"
                        >
                            <option value="all">全部類型</option>
                            <option value="point_operation">點數操作</option>
                            <option value="trade_operation">交易操作</option>
                            <option value="system_operation">系統操作</option>
                            <option value="admin_operation">管理員操作</option>
                        </select>
                    </div>

                    {/* 用戶篩選 */}
                    <div>
                        <label className="block text-sm font-medium text-[#7BC2E6] mb-1">
                            用戶ID
                        </label>
                        <input
                            type="text"
                            value={filters.userId}
                            onChange={(e) => setFilters(prev => ({ ...prev, userId: e.target.value }))}
                            placeholder="搜索用戶..."
                            className="w-full bg-[#0f203e] border border-[#294565] rounded px-3 py-2 text-[#92cbf4] placeholder-[#557797] focus:outline-none focus:ring-2 focus:ring-[#469FD2]"
                        />
                    </div>

                    {/* 搜索框 */}
                    <div>
                        <label className="block text-sm font-medium text-[#7BC2E6] mb-1">
                            搜索
                        </label>
                        <div className="relative">
                            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#557797]" />
                            <input
                                type="text"
                                value={filters.searchTerm}
                                onChange={(e) => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
                                placeholder="搜索操作..."
                                className="w-full bg-[#0f203e] border border-[#294565] rounded pl-10 pr-3 py-2 text-[#92cbf4] placeholder-[#557797] focus:outline-none focus:ring-2 focus:ring-[#469FD2]"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* 審計日誌列表 */}
            <div className="p-6">
                {auditData.combinedLogs.length === 0 ? (
                    <div className="text-center py-12">
                        <AlertCircle className="h-12 w-12 text-[#557797] mx-auto mb-4" />
                        <p className="text-[#7BC2E6] text-lg">沒有找到符合條件的日誌記錄</p>
                        <p className="text-[#557797] text-sm mt-2">
                            請嘗試調整篩選條件或刷新頁面
                        </p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {getPaginatedLogs().map((log) => (
                            <AuditLogItem key={log.id} log={log} />
                        ))}
                    </div>
                )}

                {/* 分頁 */}
                {auditData.combinedLogs.length > 0 && (
                    <div className="mt-6 flex items-center justify-between">
                        <div className="text-sm text-[#7BC2E6]">
                            顯示 {(pagination.currentPage - 1) * pagination.pageSize + 1} - {Math.min(pagination.currentPage * pagination.pageSize, auditData.combinedLogs.length)} 條，共 {auditData.combinedLogs.length} 條記錄
                        </div>
                        <div className="flex space-x-2">
                            <button
                                onClick={() => setPagination(prev => ({ ...prev, currentPage: Math.max(1, prev.currentPage - 1) }))}
                                disabled={pagination.currentPage === 1}
                                className="px-3 py-1 bg-[#0f203e] border border-[#294565] rounded text-[#92cbf4] hover:bg-[#294565] disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                上一頁
                            </button>
                            <span className="px-3 py-1 text-[#7BC2E6]">
                                {pagination.currentPage} / {pagination.totalPages}
                            </span>
                            <button
                                onClick={() => setPagination(prev => ({ ...prev, currentPage: Math.min(prev.totalPages, prev.currentPage + 1) }))}
                                disabled={pagination.currentPage === pagination.totalPages}
                                className="px-3 py-1 bg-[#0f203e] border border-[#294565] rounded text-[#92cbf4] hover:bg-[#294565] disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                下一頁
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PermissionAudit;