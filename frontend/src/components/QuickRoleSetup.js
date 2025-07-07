import { useState } from "react";
import { updateUserRole } from "@/lib/api";
import { ROLES } from "@/contexts/PermissionContext";
import { formatRoleName } from "@/utils/permissionHelper";

/**
 * 快速角色設定設定
 * 提供管理員快速設定其他管理員的功能
 */
export const QuickRoleSetup = ({ token }) => {
    const [username, setUsername] = useState("");
    const [selectedRole, setSelectedRole] = useState("point_manager");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleQuickSetup = async (e) => {
        e.preventDefault();
        
        if (!username.trim()) {
            setResult({ success: false, message: "請輸入使用者名稱" });
            return;
        }

        try {
            setLoading(true);
            setResult(null);

            // 由於後端 API 需要 user_id，我們需要先透過其他 API 取得 user_id
            // 這裡假設使用 username 作為 user_id（根據實際情況調整）
            const response = await updateUserRole(
                token, 
                username.trim(), 
                selectedRole,
                `快速設定：提升為${formatRoleName(selectedRole)}`
            );

            if (response.success) {
                setResult({
                    success: true,
                    message: `成功將 ${username} 設定為 ${formatRoleName(selectedRole)}`
                });
                setUsername("");
            } else {
                setResult({
                    success: false,
                    message: response.message || "設定失敗"
                });
            }
        } catch (error) {
            console.error("快速角色設定失敗:", error);
            setResult({
                success: false,
                message: error.message || "設定過程發生錯誤"
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-[#1A325F] p-6 rounded-lg shadow border border-[#294565]">
            <div className="mb-4">
                <h3 className="text-lg font-semibold text-[#92cbf4] mb-2">
                    🚀 快速角色設定
                </h3>
                <p className="text-sm text-[#557797]">
                    快速將使用者提升為管理員角色，適用於初始系統設定
                </p>
            </div>

            <form onSubmit={handleQuickSetup} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* 使用者名稱輸入 */}
                    <div>
                        <label className="block text-sm font-medium text-[#92cbf4] mb-2">
                            使用者名稱 / ID
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="輸入使用者名稱或 ID"
                            className="w-full px-3 py-2 bg-[#0f203e] border border-[#294565] rounded-md text-white placeholder-[#557797] focus:outline-none focus:ring-2 focus:ring-[#469FD2]"
                            disabled={loading}
                        />
                    </div>

                    {/* 角色選擇 */}
                    <div>
                        <label className="block text-sm font-medium text-[#92cbf4] mb-2">
                            目標角色
                        </label>
                        <select
                            value={selectedRole}
                            onChange={(e) => setSelectedRole(e.target.value)}
                            className="w-full px-3 py-2 bg-[#0f203e] border border-[#294565] rounded-md text-white focus:outline-none focus:ring-2 focus:ring-[#469FD2]"
                            disabled={loading}
                        >
                            <option value="point_manager">點數管理員</option>
                            <option value="announcer">公告員</option>
                            <option value="admin">管理員</option>
                        </select>
                    </div>
                </div>

                {/* 角色說明 */}
                <div className="p-3 bg-[#0f203e] border border-[#294565] rounded text-sm">
                    <p className="text-[#557797]">
                        <strong>{formatRoleName(selectedRole)}：</strong>
                        {selectedRole === "point_manager" && "可以發放點數給使用者、查看所有使用者資料"}
                        {selectedRole === "announcer" && "可以發布系統公告、查看所有使用者資料"}
                        {selectedRole === "admin" && "擁有完整的系統管理權限，包含所有功能"}
                    </p>
                </div>

                {/* 結果顯示 */}
                {result && (
                    <div className={`p-3 rounded text-sm ${
                        result.success 
                            ? "bg-green-600/20 border border-green-500/30 text-green-400"
                            : "bg-red-600/20 border border-red-500/30 text-red-400"
                    }`}>
                        {result.message}
                    </div>
                )}

                {/* 提交按鈕 */}
                <button
                    type="submit"
                    disabled={loading || !username.trim()}
                    className="w-full bg-[#469FD2] text-white py-2 px-4 rounded-md hover:bg-[#357AB8] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? "設定中..." : `設定為${formatRoleName(selectedRole)}`}
                </button>
            </form>

            {/* 使用提示 */}
            <div className="mt-4 p-3 bg-yellow-600/20 border border-yellow-500/30 rounded text-sm">
                <p className="text-yellow-400">
                    <strong>💡 使用提示：</strong>
                </p>
                <ul className="list-disc list-inside text-yellow-300 mt-1 space-y-1">
                    <li>請確保輸入正確的使用者名稱或 ID</li>
                    <li>使用者需要先通過 Telegram 完成註冊</li>
                    <li>角色變更會立即生效，使用者下次登入時即可使用新權限</li>
                    <li>建議先設定幾個點數管理員和公告員，再設定其他管理員</li>
                </ul>
            </div>
        </div>
    );
};

export default QuickRoleSetup;