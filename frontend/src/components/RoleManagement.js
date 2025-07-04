import { useState, useEffect } from "react";
import { 
    getUserPermissionSummaries, 
    updateUserRole, 
    getAvailableRoles,
    getUserAssets 
} from "@/lib/api";
import { PERMISSIONS, ROLES } from "@/contexts/PermissionContext";
import { formatRoleName, formatPermissionName } from "@/utils/permissionHelper";

/**
 * 角色管理組件
 * 管理員可以查看和修改使用者角色
 */
export const RoleManagement = ({ token }) => {
    const [users, setUsers] = useState([]);
    const [filteredUsers, setFilteredUsers] = useState([]);
    const [availableRoles, setAvailableRoles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState({});
    const [searchTerm, setSearchTerm] = useState("");
    const [roleFilter, setRoleFilter] = useState("all");
    const [selectedUser, setSelectedUser] = useState(null);
    const [roleChangeModal, setRoleChangeModal] = useState({ show: false, user: null });
    const [notification, setNotification] = useState({ show: false, message: "", type: "info" });

    // 載入使用者列表和可用角色
    useEffect(() => {
        loadUsersAndRoles();
    }, [token]);

    // 搜尋和篩選使用者
    useEffect(() => {
        let filtered = users;
        
        // 文字搜尋
        if (searchTerm) {
            filtered = filtered.filter(user => 
                user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                user.user_id.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }
        
        // 角色篩選
        if (roleFilter !== "all") {
            filtered = filtered.filter(user => user.role === roleFilter);
        }
        
        setFilteredUsers(filtered);
    }, [users, searchTerm, roleFilter]);

    const loadUsersAndRoles = async () => {
        try {
            setLoading(true);
            const [usersResponse, rolesResponse] = await Promise.all([
                getUserPermissionSummaries(token),
                getAvailableRoles(token)
            ]);
            
            setUsers(usersResponse || []);
            setAvailableRoles(rolesResponse.available_roles || []);
        } catch (error) {
            console.error("載入使用者和角色失敗:", error);
            showNotification("載入資料失敗: " + error.message, "error");
        } finally {
            setLoading(false);
        }
    };

    const showNotification = (message, type = "info") => {
        setNotification({ show: true, message, type });
        setTimeout(() => setNotification({ show: false, message: "", type: "info" }), 5000);
    };

    const handleRoleChange = async (userId, newRole, reason = "") => {
        try {
            setUpdating(prev => ({ ...prev, [userId]: true }));
            
            const response = await updateUserRole(token, userId, newRole, reason);
            
            if (response.success) {
                // 更新本地使用者列表
                setUsers(prev => prev.map(user => 
                    user.user_id === userId 
                        ? { ...user, role: newRole }
                        : user
                ));
                
                showNotification(
                    `成功將使用者角色更新為 ${formatRoleName(newRole)}`, 
                    "success"
                );
            } else {
                showNotification(`角色更新失敗: ${response.message}`, "error");
            }
        } catch (error) {
            console.error("更新角色失敗:", error);
            showNotification(`角色更新失敗: ${error.message}`, "error");
        } finally {
            setUpdating(prev => ({ ...prev, [userId]: false }));
            setRoleChangeModal({ show: false, user: null });
        }
    };

    const openRoleChangeModal = (user) => {
        setRoleChangeModal({ show: true, user });
    };

    const getRoleColor = (role) => {
        const colors = {
            student: "bg-gray-100 text-gray-800",
            point_manager: "bg-blue-100 text-blue-800",
            announcer: "bg-purple-100 text-purple-800",
            admin: "bg-red-100 text-red-800"
        };
        return colors[role] || "bg-gray-100 text-gray-800";
    };

    const getPermissionBadges = (user) => {
        const badges = [];
        if (user.can_give_points) badges.push("發放點數");
        if (user.can_create_announcement) badges.push("發布公告");
        if (user.can_manage_system) badges.push("系統管理");
        return badges;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-lg text-gray-600">載入使用者資料中...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* 通知 */}
            {notification.show && (
                <div className={`p-4 rounded-lg border ${
                    notification.type === "success" 
                        ? "bg-green-50 border-green-200 text-green-800"
                        : notification.type === "error"
                        ? "bg-red-50 border-red-200 text-red-800"
                        : "bg-blue-50 border-blue-200 text-blue-800"
                }`}>
                    {notification.message}
                </div>
            )}

            {/* 標題和統計 */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">角色管理</h2>
                    <p className="text-gray-600">管理使用者角色和權限</p>
                </div>
                <div className="text-sm text-gray-500">
                    總共 {users.length} 個使用者，顯示 {filteredUsers.length} 個
                </div>
            </div>

            {/* 搜尋和篩選 */}
            <div className="bg-white p-4 rounded-lg shadow space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* 搜尋框 */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            搜尋使用者
                        </label>
                        <input
                            type="text"
                            placeholder="輸入使用者名稱或 ID"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* 角色篩選 */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            篩選角色
                        </label>
                        <select
                            value={roleFilter}
                            onChange={(e) => setRoleFilter(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">所有角色</option>
                            <option value="student">學員</option>
                            <option value="point_manager">點數管理員</option>
                            <option value="announcer">公告員</option>
                            <option value="admin">管理員</option>
                        </select>
                    </div>
                </div>

                {/* 快速統計 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.values(ROLES).map(role => {
                        const count = users.filter(user => user.role === role).length;
                        return (
                            <div key={role} className="text-center p-3 bg-gray-50 rounded">
                                <div className="text-lg font-bold text-gray-900">{count}</div>
                                <div className="text-sm text-gray-600">{formatRoleName(role)}</div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* 使用者列表 */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    使用者
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    角色
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    權限
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    操作
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {filteredUsers.map((user) => (
                                <tr key={user.user_id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div>
                                            <div className="text-sm font-medium text-gray-900">
                                                {user.username}
                                            </div>
                                            <div className="text-sm text-gray-500">
                                                ID: {user.user_id}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(user.role)}`}>
                                            {formatRoleName(user.role)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-wrap gap-1">
                                            {getPermissionBadges(user).map((badge, index) => (
                                                <span key={index} className="inline-flex px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                                                    {badge}
                                                </span>
                                            ))}
                                            {getPermissionBadges(user).length === 0 && (
                                                <span className="text-xs text-gray-500">基本權限</span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <button
                                            onClick={() => openRoleChangeModal(user)}
                                            disabled={updating[user.user_id]}
                                            className="text-blue-600 hover:text-blue-900 disabled:opacity-50"
                                        >
                                            {updating[user.user_id] ? "更新中..." : "變更角色"}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {filteredUsers.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                        找不到符合條件的使用者
                    </div>
                )}
            </div>

            {/* 角色變更模態框 */}
            {roleChangeModal.show && (
                <RoleChangeModal
                    user={roleChangeModal.user}
                    availableRoles={availableRoles}
                    onConfirm={handleRoleChange}
                    onCancel={() => setRoleChangeModal({ show: false, user: null })}
                />
            )}
        </div>
    );
};

/**
 * 角色變更模態框
 */
const RoleChangeModal = ({ user, availableRoles, onConfirm, onCancel }) => {
    const [selectedRole, setSelectedRole] = useState(user?.role || "student");
    const [reason, setReason] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        
        try {
            await onConfirm(user.user_id, selectedRole, reason);
        } finally {
            setLoading(false);
        }
    };

    const getRoleDescription = (role) => {
        const descriptions = {
            student: "基本使用者權限：查看個人資料、股票交易、轉帳點數",
            point_manager: "點數管理權限：包含基本權限 + 發放點數、查看所有使用者",
            announcer: "公告管理權限：包含基本權限 + 發布公告、查看所有使用者", 
            admin: "完整管理員權限：包含所有系統功能和管理權限"
        };
        return descriptions[role] || "";
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    變更使用者角色
                </h3>
                
                <div className="mb-4 p-3 bg-gray-50 rounded">
                    <p className="text-sm text-gray-600">使用者：</p>
                    <p className="font-medium">{user?.username}</p>
                    <p className="text-xs text-gray-500">ID: {user?.user_id}</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            選擇新角色
                        </label>
                        <select
                            value={selectedRole}
                            onChange={(e) => setSelectedRole(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                        >
                            {Object.values(ROLES).map(role => (
                                <option key={role} value={role}>
                                    {formatRoleName(role)}
                                </option>
                            ))}
                        </select>
                        
                        {selectedRole && (
                            <p className="mt-2 text-xs text-gray-600">
                                {getRoleDescription(selectedRole)}
                            </p>
                        )}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            變更原因 (選填)
                        </label>
                        <textarea
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            placeholder="請說明變更角色的原因..."
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={3}
                        />
                    </div>

                    <div className="flex justify-end space-x-3">
                        <button
                            type="button"
                            onClick={onCancel}
                            className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
                            disabled={loading}
                        >
                            取消
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                            disabled={loading || selectedRole === user?.role}
                        >
                            {loading ? "更新中..." : "確認變更"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default RoleManagement;