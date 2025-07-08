import { useState, useEffect } from "react";
import { getAllStudents } from "@/lib/api";
import { PermissionGuard } from "./PermissionGuard";
import { PERMISSIONS } from "@/contexts/PermissionContext";

/**
 * 強制格式化時間為 UTC+8
 */
const formatTimeUTC8 = (dateString, options = {}) => {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        // 強制加 8 小時轉換為 UTC+8
        const utc8Date = new Date(date.getTime() + (8 * 60 * 60 * 1000));
        
        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            ...options
        };
        
        return utc8Date.toLocaleString('zh-TW', defaultOptions);
    } catch (error) {
        return 'N/A';
    }
};

/**
 * 簡短時間格式（月日時分）
 */
const formatShortTimeUTC8 = (dateString) => {
    return formatTimeUTC8(dateString, {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
};

/**
 * 所有成員名單組件
 * 顯示所有註冊成員的詳細資料
 */
export const MembersList = ({ token }) => {
    const [members, setMembers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [sortBy, setSortBy] = useState("username");
    const [sortOrder, setSortOrder] = useState("asc");
    const [selectedMember, setSelectedMember] = useState(null);
    const [showDebugInfo, setShowDebugInfo] = useState(false);

    // 獲取所有成員資料
    const fetchMembers = async () => {
        try {
            setLoading(true);
            setError(null);
            
            // 獲取完整的學員資料（包含資產資訊）
            const studentsData = await getAllStudents(token);
            
            if (Array.isArray(studentsData)) {
                // 將資料格式化為組件期望的格式
                const formattedData = studentsData.map(student => ({
                    user_id: student.id,
                    username: student.name,
                    team: student.team,
                    telegram_id: student.telegram_id,
                    telegram_nickname: student.telegram_nickname,
                    enabled: student.enabled,
                    created_at: student.created_at,
                    updated_at: student.updated_at,
                    points: student.points || 0,
                    stock_amount: student.stock_amount || 0,
                    total_value: student.total_value || 0,
                    // 添加 debug 資訊
                    is_active: student.enabled,
                    last_login: student.updated_at // 使用 updated_at 作為最後活動時間的代理
                }));
                
                setMembers(formattedData);
            } else {
                setError("獲取成員資料失敗");
            }
        } catch (error) {
            console.error("Failed to fetch members:", error);
            setError(error.message || "獲取成員資料失敗");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (token) {
            fetchMembers();
        }
    }, [token]);

    // 過濾和排序成員
    const filteredMembers = members
        .filter(member => 
            member.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            member.team?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            member.telegram_id?.toString().includes(searchTerm)
        )
        .sort((a, b) => {
            let aValue = a[sortBy] || "";
            let bValue = b[sortBy] || "";
            
            // 數字類型特殊處理
            if (["points", "stock_amount", "total_value"].includes(sortBy)) {
                aValue = parseFloat(aValue) || 0;
                bValue = parseFloat(bValue) || 0;
            }
            
            if (sortOrder === "asc") {
                return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
            } else {
                return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
            }
        });

    // 排序處理
    const handleSort = (field) => {
        if (sortBy === field) {
            setSortOrder(sortOrder === "asc" ? "desc" : "asc");
        } else {
            setSortBy(field);
            setSortOrder("asc");
        }
    };

    // 格式化數值
    const formatNumber = (value) => {
        return (value || 0).toLocaleString();
    };

    // 獲取排序箭頭
    const getSortIcon = (field) => {
        if (sortBy !== field) return "⇅";
        return sortOrder === "asc" ? "▲" : "▼";
    };

    // 強制格式化時間為 UTC+8
    const formatTimeUTC8 = (dateString, options = {}) => {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            // 強制加 8 小時轉換為 UTC+8
            const utc8Date = new Date(date.getTime() + (8 * 60 * 60 * 1000));
            
            const defaultOptions = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
                ...options
            };
            
            return utc8Date.toLocaleString('zh-TW', defaultOptions);
        } catch (error) {
            return 'N/A';
        }
    };

    // 簡短時間格式（月日時分）
    const formatShortTimeUTC8 = (dateString) => {
        return formatTimeUTC8(dateString, {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">載入成員資料中...</p>
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
                {/* 標題和搜尋 */}
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-[#92cbf4]">所有成員名單</h2>
                        <p className="text-[#7BC2E6]">查看所有註冊成員的詳細資料</p>
                    </div>
                    <button
                        onClick={fetchMembers}
                        disabled={loading}
                        className="rounded bg-[#469FD2] px-4 py-2 text-white hover:bg-[#357AB8] disabled:opacity-50"
                    >
                        {loading ? "更新中..." : "更新"}
                    </button>
                </div>

                {/* 搜尋和統計 */}
                <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-4">
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-4 space-y-3 lg:space-y-0">
                        <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
                            <input
                                type="text"
                                placeholder="搜尋成員名稱、隊伍或Telegram ID..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full sm:w-80 rounded border border-[#294565] bg-[#0f203e] px-3 py-2 text-white placeholder-gray-400 focus:border-[#469FD2] focus:outline-none"
                            />
                            <div className="text-sm text-[#7BC2E6] whitespace-nowrap">
                                顯示 {filteredMembers.length} / {members.length} 位成員
                            </div>
                        </div>
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={showDebugInfo}
                                onChange={(e) => setShowDebugInfo(e.target.checked)}
                                className="rounded border-[#294565] bg-[#0f203e] text-[#469FD2] focus:ring-2 focus:ring-[#469FD2]"
                            />
                            <span className="text-sm text-[#7BC2E6]">Debug模式</span>
                        </label>
                    </div>

                    {/* 統計摘要 */}
                    {members.length > 0 && (
                        <div className="grid grid-cols-2 gap-2 sm:gap-4 md:grid-cols-4">
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-2 sm:p-3 text-center">
                                <div className="text-lg sm:text-xl font-bold text-[#92cbf4]">{members.length}</div>
                                <div className="text-xs sm:text-sm text-[#7BC2E6]">總成員數</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-2 sm:p-3 text-center">
                                <div className="text-lg sm:text-xl font-bold text-green-400">
                                    {formatNumber(members.reduce((sum, m) => sum + (m.points || 0), 0))}
                                </div>
                                <div className="text-xs sm:text-sm text-[#7BC2E6]">總點數</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-2 sm:p-3 text-center">
                                <div className="text-lg sm:text-xl font-bold text-blue-400">
                                    {formatNumber(members.reduce((sum, m) => sum + (m.stock_amount || 0), 0))}
                                </div>
                                <div className="text-xs sm:text-sm text-[#7BC2E6]">總持股數</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-2 sm:p-3 text-center">
                                <div className="text-lg sm:text-xl font-bold text-yellow-400">
                                    {new Set(members.map(m => m.team).filter(Boolean)).size}
                                </div>
                                <div className="text-xs sm:text-sm text-[#7BC2E6]">隊伍數</div>
                            </div>
                        </div>
                    )}
                </div>

                {/* 錯誤提示 */}
                {error && (
                    <div className="rounded-lg border border-red-500/30 bg-red-600/20 p-4">
                        <div className="flex items-center space-x-2">
                            <span className="text-red-400">!</span>
                            <span className="text-red-300">{error}</span>
                        </div>
                    </div>
                )}

                {/* 成員列表 */}
                <div className="rounded-lg border border-[#294565] bg-[#1A325F] shadow">
                    {filteredMembers.length === 0 ? (
                        <div className="p-8 text-center">
                            <div className="text-4xl text-gray-500 mb-4">👤</div>
                            <p className="text-[#7BC2E6]">
                                {searchTerm ? "沒有找到符合條件的成員" : "沒有成員資料"}
                            </p>
                        </div>
                    ) : (
                        <>
                            {/* 桌面版表格 */}
                            <div className="hidden lg:block overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-[#294565] bg-[#0f203e]">
                                            <th 
                                                className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6] cursor-pointer hover:text-[#92cbf4]"
                                                onClick={() => handleSort("username")}
                                            >
                                                成員名稱 {getSortIcon("username")}
                                            </th>
                                            <th 
                                                className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6] cursor-pointer hover:text-[#92cbf4]"
                                                onClick={() => handleSort("team")}
                                            >
                                                隊伍 {getSortIcon("team")}
                                            </th>
                                            <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">Telegram</th>
                                            <th 
                                                className="px-4 py-3 text-right text-sm font-medium text-[#7BC2E6] cursor-pointer hover:text-[#92cbf4]"
                                                onClick={() => handleSort("points")}
                                            >
                                                點數 {getSortIcon("points")}
                                            </th>
                                            <th 
                                                className="px-4 py-3 text-right text-sm font-medium text-[#7BC2E6] cursor-pointer hover:text-[#92cbf4]"
                                                onClick={() => handleSort("stock_amount")}
                                            >
                                                持股數 {getSortIcon("stock_amount")}
                                            </th>
                                            <th 
                                                className="px-4 py-3 text-right text-sm font-medium text-[#7BC2E6] cursor-pointer hover:text-[#92cbf4]"
                                                onClick={() => handleSort("total_value")}
                                            >
                                                總資產 {getSortIcon("total_value")}
                                            </th>
                                            {showDebugInfo && (
                                                <>
                                                    <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">狀態</th>
                                                    <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">註冊時間</th>
                                                    <th className="px-4 py-3 text-left text-sm font-medium text-[#7BC2E6]">最後活動</th>
                                                </>
                                            )}
                                            <th className="px-4 py-3 text-center text-sm font-medium text-[#7BC2E6]">操作</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredMembers.map((member, index) => (
                                            <tr 
                                                key={member.user_id || index}
                                                className={`border-b border-[#294565] ${index % 2 === 0 ? 'bg-[#1A325F]' : 'bg-[#0f203e]'} hover:bg-[#294565] transition-colors`}
                                            >
                                                <td className="px-4 py-3 text-sm text-white">
                                                    <div className="font-medium">{member.username || 'N/A'}</div>
                                                    {member.user_id && (
                                                        <div className="text-xs text-gray-400">ID: {member.user_id}</div>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-sm text-[#7BC2E6]">
                                                    {member.team || '-'}
                                                </td>
                                                <td className="px-4 py-3 text-sm">
                                                    {member.telegram_id ? (
                                                        <div>
                                                            <div className="text-white">{member.telegram_id}</div>
                                                            {member.telegram_nickname && (
                                                                <div className="text-xs text-gray-400">@{member.telegram_nickname}</div>
                                                            )}
                                                        </div>
                                                    ) : (
                                                        <span className="text-gray-400">未連結</span>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm font-semibold text-green-400">
                                                    {formatNumber(member.points)}
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm font-semibold text-blue-400">
                                                    {formatNumber(member.stock_amount)}
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm font-semibold text-yellow-400">
                                                    {formatNumber(member.total_value)}
                                                </td>
                                                {showDebugInfo && (
                                                    <>
                                                        <td className="px-4 py-3 text-sm">
                                                            <div className="space-y-1">
                                                                <div className={`inline-block px-2 py-1 rounded text-xs ${
                                                                    member.is_active !== false ? 'bg-green-600 text-green-100' : 'bg-red-600 text-red-100'
                                                                }`}>
                                                                    {member.is_active !== false ? '啟用' : '停用'}
                                                                </div>
                                                                {member.enabled !== undefined && (
                                                                    <div className={`inline-block px-2 py-1 rounded text-xs ml-1 ${
                                                                        member.enabled ? 'bg-blue-600 text-blue-100' : 'bg-gray-600 text-gray-100'
                                                                    }`}>
                                                                        {member.enabled ? '已驗證' : '未驗證'}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </td>
                                                        <td className="px-4 py-3 text-xs text-gray-400">
                                                            {formatShortTimeUTC8(member.created_at)}
                                                        </td>
                                                        <td className="px-4 py-3 text-xs text-gray-400">
                                                            {formatShortTimeUTC8(member.last_login || member.updated_at)}
                                                        </td>
                                                    </>
                                                )}
                                                <td className="px-4 py-3 text-center">
                                                    <button
                                                        onClick={() => setSelectedMember(member)}
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
                            
                            {/* 手機版卡片式佈局 */}
                            <div className="lg:hidden space-y-3 p-4">
                                {filteredMembers.map((member, index) => (
                                    <div 
                                        key={member.user_id || index}
                                        className="rounded-lg border border-[#294565] bg-[#0f203e] p-4 space-y-3"
                                    >
                                        {/* 成員基本資訊 */}
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="font-medium text-white text-base">{member.username || 'N/A'}</div>
                                                <div className="text-sm text-[#7BC2E6] mt-1">
                                                    {member.team || '未設定隊伍'}
                                                </div>
                                                {member.user_id && (
                                                    <div className="text-xs text-gray-400 mt-1">ID: {member.user_id}</div>
                                                )}
                                            </div>
                                            <button
                                                onClick={() => setSelectedMember(member)}
                                                className="rounded bg-[#469FD2] px-3 py-1.5 text-xs text-white hover:bg-[#357AB8] ml-3"
                                            >
                                                詳細
                                            </button>
                                        </div>
                                        
                                        {/* 資產資訊 */}
                                        <div className="grid grid-cols-3 gap-2">
                                            <div className="text-center">
                                                <div className="text-sm font-semibold text-green-400">
                                                    {formatNumber(member.points)}
                                                </div>
                                                <div className="text-xs text-[#7BC2E6]">點數</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-sm font-semibold text-blue-400">
                                                    {formatNumber(member.stock_amount)}
                                                </div>
                                                <div className="text-xs text-[#7BC2E6]">持股</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-sm font-semibold text-yellow-400">
                                                    {formatNumber(member.total_value)}
                                                </div>
                                                <div className="text-xs text-[#7BC2E6]">總資產</div>
                                            </div>
                                        </div>
                                        
                                        {/* Telegram 資訊 */}
                                        {member.telegram_id && (
                                            <div className="text-sm">
                                                <span className="text-[#7BC2E6]">Telegram: </span>
                                                <span className="text-white">{member.telegram_id}</span>
                                                {member.telegram_nickname && (
                                                    <span className="text-gray-400"> (@{member.telegram_nickname})</span>
                                                )}
                                            </div>
                                        )}
                                        
                                        {/* Debug 資訊 */}
                                        {showDebugInfo && (
                                            <div className="border-t border-[#294565] pt-3 space-y-2">
                                                <div className="flex flex-wrap gap-2">
                                                    <div className={`inline-block px-2 py-1 rounded text-xs ${
                                                        member.is_active !== false ? 'bg-green-600 text-green-100' : 'bg-red-600 text-red-100'
                                                    }`}>
                                                        {member.is_active !== false ? '啟用' : '停用'}
                                                    </div>
                                                    {member.enabled !== undefined && (
                                                        <div className={`inline-block px-2 py-1 rounded text-xs ${
                                                            member.enabled ? 'bg-blue-600 text-blue-100' : 'bg-gray-600 text-gray-100'
                                                        }`}>
                                                            {member.enabled ? '已驗證' : '未驗證'}
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="text-xs text-gray-400">
                                                    <div>註冊: {formatShortTimeUTC8(member.created_at)}</div>
                                                    <div>活動: {formatShortTimeUTC8(member.last_login || member.updated_at)}</div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>

                {/* 成員詳細資料彈窗 */}
                {selectedMember && (
                    <MemberDetailModal 
                        member={selectedMember} 
                        showDebugInfo={showDebugInfo}
                        onClose={() => setSelectedMember(null)} 
                    />
                )}
            </div>
        </PermissionGuard>
    );
};

/**
 * 成員詳細資料彈窗組件
 */
const MemberDetailModal = ({ member, showDebugInfo, onClose }) => {
    // 處理 ESC 鍵關閉
    const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
            onClose();
        }
    };

    // 處理背景點擊關閉
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
            <div className="max-w-4xl w-full my-4 sm:my-8 rounded-lg border border-[#294565] bg-[#1A325F] shadow-xl max-h-[95vh] sm:max-h-[90vh] flex flex-col">
                <div className="flex items-center justify-between p-4 sm:p-6 border-b border-[#294565]">
                    <h3 className="text-lg sm:text-xl font-bold text-[#92cbf4]">成員詳細資料</h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors text-lg sm:text-xl"
                    >
                        ×
                    </button>
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
                    {/* 基本資料 */}
                    <div>
                        <h4 className="text-base sm:text-lg font-semibold text-[#7BC2E6] mb-3">基本資料</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="text-sm text-[#7BC2E6]">使用者名稱</div>
                                <div className="text-white font-medium break-words">{member.username || 'N/A'}</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="text-sm text-[#7BC2E6]">使用者ID</div>
                                <div className="text-white font-mono text-sm break-all">{member.user_id || 'N/A'}</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="text-sm text-[#7BC2E6]">隊伍</div>
                                <div className="text-white font-medium break-words">{member.team || '未設定'}</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="text-sm text-[#7BC2E6]">Telegram ID</div>
                                <div className="text-white font-mono text-sm break-all">{member.telegram_id || '未連結'}</div>
                            </div>
                        </div>
                    </div>

                    {/* 資產資料 */}
                    <div>
                        <h4 className="text-base sm:text-lg font-semibold text-[#7BC2E6] mb-3">資產資料</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3 sm:p-4 text-center">
                                <div className="text-lg sm:text-2xl font-bold text-green-400">
                                    {(member.points || 0).toLocaleString()}
                                </div>
                                <div className="text-sm text-[#7BC2E6]">持有點數</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3 sm:p-4 text-center">
                                <div className="text-lg sm:text-2xl font-bold text-blue-400">
                                    {(member.stock_amount || 0).toLocaleString()}
                                </div>
                                <div className="text-sm text-[#7BC2E6]">持股數量</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3 sm:p-4 text-center">
                                <div className="text-lg sm:text-2xl font-bold text-yellow-400">
                                    {(member.total_value || 0).toLocaleString()}
                                </div>
                                <div className="text-sm text-[#7BC2E6]">總資產價值</div>
                            </div>
                        </div>
                    </div>

                    {/* 其他資訊 */}
                    {(member.telegram_nickname || member.created_at || member.last_login) && (
                        <div>
                            <h4 className="text-base sm:text-lg font-semibold text-[#7BC2E6] mb-3">其他資訊</h4>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                                {member.telegram_nickname && (
                                    <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                        <div className="text-sm text-[#7BC2E6]">Telegram 暱稱</div>
                                        <div className="text-white break-words">@{member.telegram_nickname}</div>
                                    </div>
                                )}
                                {member.created_at && (
                                    <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                        <div className="text-sm text-[#7BC2E6]">註冊時間</div>
                                        <div className="text-white text-sm">{formatTimeUTC8(member.created_at)}</div>
                                    </div>
                                )}
                                {member.last_login && (
                                    <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                        <div className="text-sm text-[#7BC2E6]">最後登入</div>
                                        <div className="text-white text-sm">{formatTimeUTC8(member.last_login)}</div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Debug 資訊 */}
                    {showDebugInfo && (
                        <div>
                            <h4 className="text-base sm:text-lg font-semibold text-yellow-400 mb-3">🔧 Debug 資訊</h4>
                            <div className="space-y-3 sm:space-y-4">
                                {/* 帳號狀態 */}
                                <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                    <div className="text-sm text-[#7BC2E6] mb-2">帳號狀態</div>
                                    <div className="flex flex-wrap gap-2">
                                        <div className={`inline-block px-2 py-1 rounded text-xs ${
                                            member.is_active !== false ? 'bg-green-600 text-green-100' : 'bg-red-600 text-red-100'
                                        }`}>
                                            {member.is_active !== false ? '啟用' : '停用'}
                                        </div>
                                        {member.enabled !== undefined && (
                                            <div className={`inline-block px-2 py-1 rounded text-xs ${
                                                member.enabled ? 'bg-blue-600 text-blue-100' : 'bg-gray-600 text-gray-100'
                                            }`}>
                                                {member.enabled ? '已驗證' : '未驗證'}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* 內部 ID */}
                                <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                    <div className="text-sm text-[#7BC2E6]">內部 ID</div>
                                    <div className="text-white font-mono text-sm break-all">{member.user_id || 'N/A'}</div>
                                </div>

                                {/* 資料庫記錄 */}
                                <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                    <div className="text-sm text-[#7BC2E6] mb-2">資料庫記錄</div>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                                        <div>
                                            <div className="text-gray-400">建立時間</div>
                                            <div className="text-white">
                                                {formatTimeUTC8(member.created_at)}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-gray-400">最後更新</div>
                                            <div className="text-white">
                                                {formatTimeUTC8(member.updated_at)}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* 原始資料 */}
                                <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                    <div className="text-sm text-[#7BC2E6] mb-2">原始資料 (JSON)</div>
                                    <pre className="text-xs text-gray-300 whitespace-pre-wrap overflow-auto max-h-32 sm:max-h-48 bg-black p-2 rounded border">
                                        {JSON.stringify(member, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        </div>
                    )}
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

export default MembersList;