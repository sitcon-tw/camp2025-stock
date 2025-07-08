import { useState, useEffect } from "react";
import { getPendingOrders, triggerManualMatching, getPriceLimitInfo } from "@/lib/api";

/**
 * 等待撮合訂單查看器組件
 * 顯示所有等待撮合的股票訂單
 */
export const PendingOrdersViewer = ({ token }) => {
    const [orders, setOrders] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [limit, setLimit] = useState(100);
    const [autoRefresh, setAutoRefresh] = useState(false);
    const [lastUpdate, setLastUpdate] = useState(null);
    const [matchingInProgress, setMatchingInProgress] = useState(false);
    const [showPriceLimitInfo, setShowPriceLimitInfo] = useState(false);
    const [priceLimitInfo, setPriceLimitInfo] = useState(null);

    // 獲取等待撮合的訂單
    const fetchPendingOrders = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const result = await getPendingOrders(token, limit);
            
            if (result.ok) {
                setOrders(result.orders);
                setStats(result.stats);
                setLastUpdate(new Date());
            } else {
                setError("獲取訂單失敗");
            }
        } catch (error) {
            console.error("Failed to fetch pending orders:", error);
            setError(error.message || "獲取訂單失敗");
        } finally {
            setLoading(false);
        }
    };

    // 手動觸發撮合
    const handleManualMatching = async () => {
        try {
            setMatchingInProgress(true);
            setError(null);
            
            const result = await triggerManualMatching(token);
            
            if (result.ok) {
                // 撮合成功後，等待一下再刷新數據
                setTimeout(() => {
                    fetchPendingOrders();
                }, 1000);
            }
        } catch (error) {
            console.error("Manual matching failed:", error);
            setError(`手動撮合失敗: ${error.message}`);
        } finally {
            setMatchingInProgress(false);
        }
    };

    // 查詢價格限制資訊
    const checkPriceLimit = async (testPrice = 14.0) => {
        try {
            const result = await getPriceLimitInfo(token, testPrice);
            if (result.ok) {
                setPriceLimitInfo(result);
                setShowPriceLimitInfo(true);
            }
        } catch (error) {
            console.error("Failed to get price limit info:", error);
            setError(`查詢價格限制失敗: ${error.message}`);
        }
    };

    // 初次載入
    useEffect(() => {
        if (token) {
            fetchPendingOrders();
        }
    }, [token, limit]);

    // 自動刷新
    useEffect(() => {
        let interval;
        if (autoRefresh && token) {
            interval = setInterval(fetchPendingOrders, 10000); // 每10秒刷新一次
        }
        return () => {
            if (interval) {
                clearInterval(interval);
            }
        };
    }, [autoRefresh, token, limit]);

    // 格式化時間
    const formatTime = (timeString) => {
        if (!timeString) return 'N/A';
        try {
            const date = new Date(timeString);
            return date.toLocaleString('zh-TW', {
                timeZone: 'Asia/Taipei',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (e) {
            return timeString;
        }
    };

    // 格式化訂單類型
    const formatOrderType = (type) => {
        const typeMap = {
            'market': '市價單',
            'limit': '限價單'
        };
        return typeMap[type] || type;
    };

    // 格式化訂單狀態
    const formatOrderStatus = (status) => {
        const statusMap = {
            'pending': '等待撮合',
            'partial': '部分成交',
            'pending_limit': '等待限價'
        };
        return statusMap[status] || status;
    };

    // 格式化買賣方向
    const formatSide = (side) => {
        return side === 'buy' ? '買入' : '賣出';
    };

    // 獲取狀態顏色
    const getStatusColor = (status) => {
        const colorMap = {
            'pending': 'text-yellow-400',
            'partial': 'text-blue-400',
            'pending_limit': 'text-orange-400'
        };
        return colorMap[status] || 'text-gray-400';
    };

    // 獲取買賣方向顏色
    const getSideColor = (side) => {
        return side === 'buy' ? 'text-green-400' : 'text-red-400';
    };

    if (loading && orders.length === 0) {
        return (
            <div className="flex items-center justify-center py-8">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                <span className="ml-3 text-[#92cbf4]">載入中...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* 控制面板 */}
            <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-4">
                <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-xl font-bold text-[#92cbf4]">等待撮合訂單</h2>
                    <div className="flex items-center space-x-4">
                        {/* 自動刷新開關 */}
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={autoRefresh}
                                onChange={(e) => setAutoRefresh(e.target.checked)}
                                className="rounded border-[#294565] bg-[#0f203e] text-[#469FD2] focus:ring-2 focus:ring-[#469FD2]"
                            />
                            <span className="text-sm text-[#7BC2E6]">自動刷新</span>
                        </label>

                        {/* 筆數限制 */}
                        <div className="flex items-center space-x-2">
                            <label className="text-sm text-[#7BC2E6]">顯示筆數:</label>
                            <select
                                value={limit}
                                onChange={(e) => setLimit(parseInt(e.target.value))}
                                className="rounded border border-[#294565] bg-[#0f203e] px-2 py-1 text-sm text-white"
                            >
                                <option value={50}>50</option>
                                <option value={100}>100</option>
                                <option value={200}>200</option>
                                <option value={500}>500</option>
                            </select>
                        </div>

                        {/* 手動刷新按鈕 */}
                        <button
                            onClick={fetchPendingOrders}
                            disabled={loading}
                            className="rounded bg-[#469FD2] px-4 py-2 text-sm text-white hover:bg-[#357AB8] disabled:opacity-50"
                        >
                            {loading ? "刷新中..." : "刷新"}
                        </button>

                        {/* 手動撮合按鈕 */}
                        <button
                            onClick={handleManualMatching}
                            disabled={matchingInProgress || loading}
                            className="rounded bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
                            title="立即執行一次訂單撮合"
                        >
                            {matchingInProgress ? "撮合中..." : "手動撮合"}
                        </button>

                        {/* 價格限制診斷按鈕 */}
                        <button
                            onClick={() => checkPriceLimit(14)}
                            className="rounded bg-orange-600 px-4 py-2 text-sm text-white hover:bg-orange-700"
                            title="檢查14點價格是否受限制"
                        >
                            檢查限制
                        </button>
                    </div>
                </div>

                {/* 統計資訊 */}
                {stats && (
                    <div className="mb-4 grid grid-cols-2 gap-4 md:grid-cols-4">
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3 text-center">
                            <div className="text-2xl font-bold text-[#92cbf4]">{stats.total_orders}</div>
                            <div className="text-sm text-[#7BC2E6]">總訂單數</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3 text-center">
                            <div className="text-2xl font-bold text-yellow-400">{stats.status_breakdown.pending.count}</div>
                            <div className="text-sm text-[#7BC2E6]">等待撮合</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3 text-center">
                            <div className="text-2xl font-bold text-blue-400">{stats.status_breakdown.partial.count}</div>
                            <div className="text-sm text-[#7BC2E6]">部分成交</div>
                        </div>
                        <div className="rounded border border-[#294565] bg-[#0f203e] p-3 text-center">
                            <div className="text-2xl font-bold text-orange-400">{stats.status_breakdown.pending_limit.count}</div>
                            <div className="text-sm text-[#7BC2E6]">等待限價</div>
                        </div>
                    </div>
                )}

                {/* 最後更新時間 */}
                {lastUpdate && (
                    <div className="text-xs text-gray-400">
                        最後更新：{formatTime(lastUpdate.toISOString())}
                        {autoRefresh && <span className="ml-2 text-green-400">• 自動刷新開啟</span>}
                    </div>
                )}
            </div>

            {/* 錯誤提示 */}
            {error && (
                <div className="rounded-lg border border-red-500/30 bg-red-600/20 p-4">
                    <div className="flex items-center space-x-2">
                        <span className="text-red-400">⚠️</span>
                        <span className="text-red-300">{error}</span>
                    </div>
                </div>
            )}

            {/* 價格限制資訊 */}
            {showPriceLimitInfo && priceLimitInfo && (
                <div className="rounded-lg border border-orange-500/30 bg-orange-600/20 p-4">
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <h3 className="mb-2 text-lg font-semibold text-orange-400">
                                價格限制診斷：{priceLimitInfo.test_price} 點
                            </h3>
                            <div className="space-y-2 text-sm text-orange-200">
                                <div>
                                    <span className="font-medium">
                                        是否可交易：
                                        <span className={priceLimitInfo.within_limit ? "text-green-400" : "text-red-400"}>
                                            {priceLimitInfo.within_limit ? "✅ 是" : "❌ 否"}
                                        </span>
                                    </span>
                                </div>
                                {priceLimitInfo.limit_info && (
                                    <>
                                        <div>基準價格：{priceLimitInfo.limit_info.reference_price} 點</div>
                                        <div>漲跌限制：{priceLimitInfo.limit_info.limit_percent}%</div>
                                        <div>
                                            可交易範圍：{priceLimitInfo.limit_info.min_price.toFixed(2)} ~ {priceLimitInfo.limit_info.max_price.toFixed(2)} 點
                                        </div>
                                        <div>上漲上限：{priceLimitInfo.limit_info.max_price.toFixed(2)} 點</div>
                                        <div>下跌下限：{priceLimitInfo.limit_info.min_price.toFixed(2)} 點</div>
                                    </>
                                )}
                            </div>
                        </div>
                        <button
                            onClick={() => setShowPriceLimitInfo(false)}
                            className="ml-4 text-orange-300 hover:text-orange-100"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}

            {/* 訂單列表 */}
            <div className="rounded-lg border border-[#294565] bg-[#1A325F] shadow">
                {orders.length === 0 && !loading ? (
                    <div className="p-8 text-center">
                        <div className="text-4xl text-gray-500 mb-4">📋</div>
                        <p className="text-[#7BC2E6]">目前沒有等待撮合的訂單</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-[#294565] bg-[#0f203e]">
                                    <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">訂單ID</th>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">使用者</th>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">隊伍</th>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">方向</th>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">類型</th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-[#7BC2E6]">價格</th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-[#7BC2E6]">數量</th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-[#7BC2E6]">原始數量</th>
                                    <th className="px-4 py-3 text-center text-sm font-medium text-[#7BC2E6]">狀態</th>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">建立時間</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orders.map((order, index) => (
                                    <tr 
                                        key={order._id} 
                                        className={`border-b border-[#294565] ${index % 2 === 0 ? 'bg-[#1A325F]' : 'bg-[#0f203e]'} hover:bg-[#294565] transition-colors`}
                                    >
                                        <td className="px-4 py-3 text-sm font-mono text-white">
                                            {order.order_id || order._id.slice(-8)}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-white">
                                            {order.username || 'N/A'}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-[#7BC2E6]">
                                            {order.user_team || '-'}
                                        </td>
                                        <td className={`px-4 py-3 text-sm font-semibold ${getSideColor(order.side)}`}>
                                            {formatSide(order.side)}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-[#7BC2E6]">
                                            {formatOrderType(order.order_type)}
                                        </td>
                                        <td className="px-4 py-3 text-right text-sm text-white">
                                            {order.price ? `${order.price} 點` : '市價'}
                                        </td>
                                        <td className="px-4 py-3 text-right text-sm font-semibold text-white">
                                            {order.quantity?.toLocaleString() || 0}
                                        </td>
                                        <td className="px-4 py-3 text-right text-sm text-[#7BC2E6]">
                                            {order.original_quantity?.toLocaleString() || order.quantity?.toLocaleString() || 0}
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            <span className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${getStatusColor(order.status)}`}>
                                                {formatOrderStatus(order.status)}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-[#7BC2E6]">
                                            {formatTime(order.created_at)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* 顯示更多提示 */}
            {stats && stats.returned_count < stats.total_orders && (
                <div className="rounded-lg border border-[#469FD2] bg-[#0f203e] p-3 text-center">
                    <p className="text-sm text-[#7BC2E6]">
                        顯示了 {stats.returned_count} / {stats.total_orders} 筆訂單
                        {stats.returned_count < stats.total_orders && (
                            <span className="ml-2 text-[#469FD2]">• 調整顯示筆數以查看更多</span>
                        )}
                    </p>
                </div>
            )}
        </div>
    );
};

export default PendingOrdersViewer;