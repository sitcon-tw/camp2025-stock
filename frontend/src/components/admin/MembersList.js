import { useState, useEffect } from "react";
import { getUserAssets } from "@/lib/api";
import { PermissionGuard } from "./PermissionGuard";
import { PERMISSIONS } from "@/contexts/PermissionContext";

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

    // 獲取所有成員數據
    const fetchMembers = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const result = await getUserAssets(token);
            
            if (Array.isArray(result)) {
                setMembers(result);
            } else {
                setError("獲取成員數據失敗");
            }
        } catch (error) {
            console.error("Failed to fetch members:", error);
            setError(error.message || "獲取成員數據失敗");
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
        if (sortBy !== field) return "↕️";
        return sortOrder === "asc" ? "↑" : "↓";
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">載入成員數據中...</p>
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
                        {loading ? "刷新中..." : "刷新"}
                    </button>
                </div>

                {/* 搜尋和統計 */}
                <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-4">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-4">
                            <input
                                type="text"
                                placeholder="搜尋成員名稱、隊伍或Telegram ID..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-80 rounded border border-[#294565] bg-[#0f203e] px-3 py-2 text-white placeholder-gray-400 focus:border-[#469FD2] focus:outline-none"
                            />
                            <div className="text-sm text-[#7BC2E6]">
                                顯示 {filteredMembers.length} / {members.length} 位成員
                            </div>
                        </div>
                    </div>

                    {/* 統計摘要 */}
                    {members.length > 0 && (
                        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3 text-center">
                                <div className="text-xl font-bold text-[#92cbf4]">{members.length}</div>
                                <div className="text-sm text-[#7BC2E6]">總成員數</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3 text-center">
                                <div className="text-xl font-bold text-green-400">
                                    {formatNumber(members.reduce((sum, m) => sum + (m.points || 0), 0))}
                                </div>
                                <div className="text-sm text-[#7BC2E6]">總點數</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3 text-center">
                                <div className="text-xl font-bold text-blue-400">
                                    {formatNumber(members.reduce((sum, m) => sum + (m.stock_amount || 0), 0))}
                                </div>
                                <div className="text-sm text-[#7BC2E6]">總持股數</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3 text-center">
                                <div className="text-xl font-bold text-yellow-400">
                                    {new Set(members.map(m => m.team).filter(Boolean)).size}
                                </div>
                                <div className="text-sm text-[#7BC2E6]">隊伍數</div>
                            </div>
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

                {/* 成員列表 */}
                <div className="rounded-lg border border-[#294565] bg-[#1A325F] shadow">
                    {filteredMembers.length === 0 ? (
                        <div className="p-8 text-center">
                            <div className="text-4xl text-gray-500 mb-4">👥</div>
                            <p className="text-[#7BC2E6]">
                                {searchTerm ? "沒有找到符合條件的成員" : "沒有成員數據"}
                            </p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
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
                    )}
                </div>

                {/* 成員詳細資料彈窗 */}
                {selectedMember && (
                    <MemberDetailModal 
                        member={selectedMember} 
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
const MemberDetailModal = ({ member, onClose }) => {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="max-w-2xl w-full mx-4 rounded-lg border border-[#294565] bg-[#1A325F] shadow-xl">
                <div className="flex items-center justify-between p-6 border-b border-[#294565]">
                    <h3 className="text-xl font-bold text-[#92cbf4]">成員詳細資料</h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        ✕
                    </button>
                </div>
                
                <div className="p-6 space-y-6">
                    {/* 基本資料 */}
                    <div>
                        <h4 className="text-lg font-semibold text-[#7BC2E6] mb-3">基本資料</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="text-sm text-[#7BC2E6]">使用者名稱</div>
                                <div className="text-white font-medium">{member.username || 'N/A'}</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="text-sm text-[#7BC2E6]">使用者ID</div>
                                <div className="text-white font-mono">{member.user_id || 'N/A'}</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="text-sm text-[#7BC2E6]">隊伍</div>
                                <div className="text-white font-medium">{member.team || '未設定'}</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                <div className="text-sm text-[#7BC2E6]">Telegram ID</div>
                                <div className="text-white font-mono">{member.telegram_id || '未連結'}</div>
                            </div>
                        </div>
                    </div>

                    {/* 資產資料 */}
                    <div>
                        <h4 className="text-lg font-semibold text-[#7BC2E6] mb-3">資產資料</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-4 text-center">
                                <div className="text-2xl font-bold text-green-400">
                                    {(member.points || 0).toLocaleString()}
                                </div>
                                <div className="text-sm text-[#7BC2E6]">持有點數</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-4 text-center">
                                <div className="text-2xl font-bold text-blue-400">
                                    {(member.stock_amount || 0).toLocaleString()}
                                </div>
                                <div className="text-sm text-[#7BC2E6]">持股數量</div>
                            </div>
                            <div className="rounded border border-[#294565] bg-[#0f203e] p-4 text-center">
                                <div className="text-2xl font-bold text-yellow-400">
                                    {(member.total_value || 0).toLocaleString()}
                                </div>
                                <div className="text-sm text-[#7BC2E6]">總資產價值</div>
                            </div>
                        </div>
                    </div>

                    {/* 其他資訊 */}
                    {(member.telegram_nickname || member.created_at || member.last_login) && (
                        <div>
                            <h4 className="text-lg font-semibold text-[#7BC2E6] mb-3">其他資訊</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {member.telegram_nickname && (
                                    <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                        <div className="text-sm text-[#7BC2E6]">Telegram 暱稱</div>
                                        <div className="text-white">@{member.telegram_nickname}</div>
                                    </div>
                                )}
                                {member.created_at && (
                                    <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                        <div className="text-sm text-[#7BC2E6]">註冊時間</div>
                                        <div className="text-white">{new Date(member.created_at).toLocaleString('zh-TW')}</div>
                                    </div>
                                )}
                                {member.last_login && (
                                    <div className="rounded border border-[#294565] bg-[#0f203e] p-3">
                                        <div className="text-sm text-[#7BC2E6]">最後登入</div>
                                        <div className="text-white">{new Date(member.last_login).toLocaleString('zh-TW')}</div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex justify-end p-6 border-t border-[#294565]">
                    <button
                        onClick={onClose}
                        className="rounded bg-[#469FD2] px-6 py-2 text-white hover:bg-[#357AB8]"
                    >
                        關閉
                    </button>
                </div>
            </div>
        </div>
    );
};

export default MembersList;