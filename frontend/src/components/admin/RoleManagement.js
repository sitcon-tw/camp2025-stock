import { ROLES } from "@/contexts/PermissionContext";
import {
    getAvailableRoles,
    getUserPermissionSummaries,
    updateUserRole,
} from "@/lib/api";
import { formatRoleName } from "@/utils/permissionHelper";
import { useEffect, useState } from "react";
import { Modal } from "../ui";

/**
 * 角色管理設定
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
    const [roleChangeModal, setRoleChangeModal] = useState({
        show: false,
        user: null,
    });
    const [notification, setNotification] = useState({
        show: false,
        message: "",
        type: "info",
    });

    // 載入使用者列表和可用角色
    useEffect(() => {
        loadUsersAndRoles();
    }, [token]);

    // 搜尋和篩選使用者
    useEffect(() => {
        let filtered = users;

        // 文字搜尋
        if (searchTerm) {
            filtered = filtered.filter(
                (user) =>
                    user.username
                        .toLowerCase()
                        .includes(searchTerm.toLowerCase()) ||
                    user.user_id
                        .toLowerCase()
                        .includes(searchTerm.toLowerCase()),
            );
        }

        // 角色篩選
        if (roleFilter !== "all") {
            filtered = filtered.filter(
                (user) => user.role === roleFilter,
            );
        }

        setFilteredUsers(filtered);
    }, [users, searchTerm, roleFilter]);

    const loadUsersAndRoles = async () => {
        try {
            setLoading(true);
            const [usersResponse, rolesResponse] = await Promise.all([
                getUserPermissionSummaries(token),
                getAvailableRoles(token),
            ]);

            setUsers(usersResponse || []);
            setAvailableRoles(rolesResponse.available_roles || []);
        } catch (error) {
            console.error("載入使用者和角色失敗:", error);

            // 改善錯誤訊息處理
            let errorMessage = "載入資料失敗";

            if (error.status === 422) {
                errorMessage =
                    "無法載入使用者資料，請確保已登入 Telegram 並綁定帳號";
            } else if (
                error.message &&
                typeof error.message === "string"
            ) {
                errorMessage = `載入資料失敗: ${error.message}`;
            } else if (error.status) {
                errorMessage = `載入資料失敗: HTTP ${error.status}`;
            }

            showNotification(errorMessage, "error");
        } finally {
            setLoading(false);
        }
    };

    const showNotification = (message, type = "info") => {
        setNotification({ show: true, message, type });
        setTimeout(
            () =>
                setNotification({
                    show: false,
                    message: "",
                    type: "info",
                }),
            5000,
        );
    };

    const handleRoleChange = async (userId, newRole, reason = "") => {
        try {
            setUpdating((prev) => ({ ...prev, [userId]: true }));

            const response = await updateUserRole(
                token,
                userId,
                newRole,
                reason,
            );

            if (response.success) {
                // 重新載入使用者列表以確保權限資料同步
                await loadUsersAndRoles();

                showNotification(
                    `成功將使用者角色更新為 ${formatRoleName(newRole)}`,
                    "success",
                );
            } else {
                showNotification(
                    `角色更新失敗: ${response.message}`,
                    "error",
                );
            }
        } catch (error) {
            console.error("更新角色失敗:", error);

            // 改善錯誤訊息處理
            let errorMessage = "角色更新失敗";

            if (error.status === 422) {
                errorMessage =
                    "角色更新失敗，請確保已登入 Telegram 並綁定帳號";
            } else if (
                error.message &&
                typeof error.message === "string"
            ) {
                errorMessage = `角色更新失敗: ${error.message}`;
            } else if (error.status) {
                errorMessage = `角色更新失敗: HTTP ${error.status}`;
            }

            showNotification(errorMessage, "error");
        } finally {
            setUpdating((prev) => ({ ...prev, [userId]: false }));
            setRoleChangeModal({ show: false, user: null });
        }
    };

    const openRoleChangeModal = (user) => {
        setRoleChangeModal({ show: true, user });
    };

    const getRoleColor = (role) => {
        const colors = {
            student:
                "bg-blue-600/20 text-blue-400 border border-blue-500/30",
            qrcode_manager:
                "bg-cyan-600/20 text-cyan-400 border border-cyan-500/30",
            point_manager:
                "bg-yellow-600/20 text-yellow-400 border border-yellow-500/30",
            qr_point_manager:
                "bg-orange-600/20 text-orange-400 border border-orange-500/30",
            announcer:
                "bg-purple-600/20 text-purple-400 border border-purple-500/30",
            admin: "bg-red-600/20 text-red-400 border border-red-500/30",
        };
        return (
            colors[role] ||
            "bg-blue-600/20 text-blue-400 border border-blue-500/30"
        );
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
                <div className="text-lg text-[#557797]">
                    載入使用者資料中...
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* 通知 */}
            {notification.show && (
                <div
                    className={`rounded-lg border p-4 ${
                        notification.type === "success"
                            ? "border-green-500/30 bg-green-600/20 text-green-400"
                            : notification.type === "error"
                              ? "border-red-500/30 bg-red-600/20 text-red-400"
                              : "border-blue-500/30 bg-blue-600/20 text-blue-400"
                    }`}
                >
                    {notification.message}
                </div>
            )}

            {/* 標題和統計 */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-[#92cbf4]">
                        角色管理
                    </h2>
                    <p className="text-[#557797]">
                        管理使用者角色和權限
                    </p>
                </div>
                <div className="text-sm text-[#557797]">
                    總共 {users.length} 個使用者，顯示{" "}
                    {filteredUsers.length} 個
                </div>
            </div>

            {/* 搜尋和篩選 */}
            <div className="space-y-4 rounded-lg border border-[#294565] bg-[#1A325F] p-4 shadow">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    {/* 搜尋框 */}
                    <div>
                        <label className="mb-2 block text-sm font-medium text-[#92cbf4]">
                            搜尋使用者
                        </label>
                        <input
                            type="text"
                            placeholder="輸入使用者名稱或 ID"
                            value={searchTerm}
                            onChange={(e) =>
                                setSearchTerm(e.target.value)
                            }
                            className="w-full rounded-md border border-[#294565] bg-[#0f203e] px-3 py-2 text-white placeholder-[#557797] focus:ring-2 focus:ring-[#469FD2] focus:outline-none"
                        />
                    </div>

                    {/* 角色篩選 */}
                    <div>
                        <label className="mb-2 block text-sm font-medium text-[#92cbf4]">
                            篩選角色
                        </label>
                        <select
                            value={roleFilter}
                            onChange={(e) =>
                                setRoleFilter(e.target.value)
                            }
                            className="w-full rounded-md border border-[#294565] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-[#469FD2] focus:outline-none"
                        >
                            <option value="all">所有角色</option>
                            {Object.values(ROLES).map((role) => (
                                <option key={role} value={role}>
                                    {formatRoleName(role)}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* 快速統計 */}
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                    {Object.values(ROLES).map((role) => {
                        const count = users.filter(
                            (user) => user.role === role,
                        ).length;
                        return (
                            <div
                                key={role}
                                className="rounded border border-[#294565] bg-[#0f203e] p-3 text-center"
                            >
                                <div className="text-lg font-bold text-[#92cbf4]">
                                    {count}
                                </div>
                                <div className="text-sm text-[#557797]">
                                    {formatRoleName(role)}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* 使用者列表 */}
            <div className="overflow-hidden rounded-lg border border-[#294565] bg-[#1A325F] shadow">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-[#294565]">
                        <thead className="bg-[#0f203e]">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-[#92cbf4] uppercase">
                                    使用者
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-[#92cbf4] uppercase">
                                    角色
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-[#92cbf4] uppercase">
                                    權限
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-[#92cbf4] uppercase">
                                    操作
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#294565] bg-[#1A325F]">
                            {filteredUsers.map((user) => (
                                <tr
                                    key={user.user_id}
                                    className="hover:bg-[#0f203e]"
                                >
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div>
                                            <div className="text-sm font-medium text-[#92cbf4]">
                                                {user.username}
                                            </div>
                                            <div className="text-sm text-[#557797]">
                                                ID: {user.user_id}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span
                                            className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getRoleColor(user.role)}`}
                                        >
                                            {formatRoleName(
                                                user.role,
                                            )}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-wrap gap-1">
                                            {getPermissionBadges(
                                                user,
                                            ).map((badge, index) => (
                                                <span
                                                    key={index}
                                                    className="inline-flex rounded border border-green-500/30 bg-green-600/20 px-2 py-1 text-xs text-green-400"
                                                >
                                                    {badge}
                                                </span>
                                            ))}
                                            {getPermissionBadges(user)
                                                .length === 0 && (
                                                <span className="text-xs text-[#557797]">
                                                    基本權限
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm font-medium whitespace-nowrap">
                                        <button
                                            onClick={() =>
                                                openRoleChangeModal(
                                                    user,
                                                )
                                            }
                                            disabled={
                                                updating[user.user_id]
                                            }
                                            className="text-[#469FD2] hover:text-[#92cbf4] disabled:opacity-50"
                                        >
                                            {updating[user.user_id]
                                                ? "更新中..."
                                                : "變更角色"}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {filteredUsers.length === 0 && (
                    <div className="py-8 text-center text-[#557797]">
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
                    onCancel={() =>
                        setRoleChangeModal({
                            show: false,
                            user: null,
                        })
                    }
                />
            )}
        </div>
    );
};

/**
 * 角色變更模態框
 */
const RoleChangeModal = ({
    user,
    availableRoles,
    onConfirm,
    onCancel,
}) => {
    const [selectedRole, setSelectedRole] = useState(
        user?.role || "student",
    );
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
            student:
                "基本使用者權限：查看個人資料、股票交易、轉帳點數",
            qrcode_manager:
                "QR Code管理權限：包含基本權限 + 生成QR Code",
            point_manager:
                "點數管理權限：包含基本權限 + 發放點數、查看所有使用者",
            qr_point_manager:
                "QR碼與點數管理權限：包含基本權限 + 生成QR Code、發放點數、查看所有使用者",
            announcer:
                "公告管理權限：包含基本權限 + 發布公告、查看所有使用者",
            admin: "完整管理員權限：包含所有系統功能和管理權限",
        };
        return descriptions[role] || "";
    };

    return (
        <Modal
            isOpen={true}
            onClose={onCancel}
            title="變更使用者角色"
            size="md"
        >
            <div className="mb-4 rounded border border-[#294565] bg-[#0f203e] p-3">
                <p className="text-sm text-[#557797]">使用者：</p>
                <p className="font-medium text-white">
                    {user?.username}
                </p>
                <p className="text-xs text-[#557797]">
                    ID: {user?.user_id}
                </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="mb-2 block text-sm font-medium text-[#92cbf4]">
                        選擇新角色
                    </label>
                    <select
                        value={selectedRole}
                        onChange={(e) =>
                            setSelectedRole(e.target.value)
                        }
                        className="w-full rounded-md border border-[#294565] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-[#469FD2] focus:outline-none"
                        required
                    >
                        {Object.values(ROLES).map((role) => (
                            <option key={role} value={role}>
                                {formatRoleName(role)}
                            </option>
                        ))}
                    </select>

                    {selectedRole && (
                        <p className="mt-2 text-xs text-[#557797]">
                            {getRoleDescription(selectedRole)}
                        </p>
                    )}
                </div>

                <div>
                    <label className="mb-2 block text-sm font-medium text-[#92cbf4]">
                        變更原因 (選填)
                    </label>
                    <textarea
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder="請說明變更角色的原因..."
                        className="w-full rounded-md border border-[#294565] bg-[#0f203e] px-3 py-2 text-white placeholder-[#557797] focus:ring-2 focus:ring-[#469FD2] focus:outline-none"
                        rows={3}
                    />
                </div>

                <div className="flex justify-end space-x-3">
                    <button
                        type="button"
                        onClick={onCancel}
                        className="rounded bg-[#294565] px-4 py-2 text-[#92cbf4] hover:bg-[#1A325F]"
                        disabled={loading}
                    >
                        取消
                    </button>
                    <button
                        type="submit"
                        className="rounded bg-[#469FD2] px-4 py-2 text-white hover:bg-[#357AB8] disabled:opacity-50"
                        disabled={
                            loading || selectedRole === user?.role
                        }
                    >
                        {loading ? "更新中..." : "確認變更"}
                    </button>
                </div>
            </form>
        </Modal>
    );
};

export default RoleManagement;
