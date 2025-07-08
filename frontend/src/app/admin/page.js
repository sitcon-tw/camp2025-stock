"use client";

import { AdminDashboard, PermissionAudit, SystemConfig, PendingOrdersViewer, MembersList, TransactionHistory } from "@/components/admin";
import { PermissionProvider, usePermissionContext } from "@/contexts/PermissionContext";
import { debugAuth } from "@/utils/debugAuth";
import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

/**
 * Inner component that handles permission checks
 * This must be inside PermissionProvider to access context
 */
function AdminPageContent({ activeTab, setActiveTab, adminToken, router }) {
    const { permissions, role, loading: permissionLoading, error } = usePermissionContext();

    // 權限錯誤
    if (error) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="max-w-md rounded-lg border border-red-500/30 bg-red-600/20 p-8 shadow-lg">
                    <div className="text-center">
                        <div className="mb-4 text-4xl text-red-400">⚠️</div>
                        <h2 className="mb-2 text-xl font-bold text-red-400">權限驗證失敗</h2>
                        <p className="mb-2 text-red-300">{error}</p>
                        <p className="mb-4 text-sm text-red-300">
                            這可能是由於：
                            <br />• Token 已過期
                            <br />• 權限設定問題
                            <br />• 後端服務連線異常
                        </p>
                        <div className="space-y-3">
                            <button
                                onClick={() => window.location.reload()}
                                className="w-full rounded bg-[#469FD2] px-6 py-2 text-white hover:bg-[#357AB8]"
                            >
                                重新載入頁面
                            </button>
                            <button
                                onClick={() => debugAuth()}
                                className="w-full rounded bg-[#294565] px-6 py-2 text-sm text-[#92cbf4] hover:bg-[#1A325F]"
                            >
                                顯示調試資訊 (請查看控制台)
                            </button>
                            <button
                                onClick={() => {
                                    localStorage.removeItem("isAdmin");
                                    localStorage.removeItem("adminToken");
                                    localStorage.removeItem("isUser");
                                    localStorage.removeItem("userToken");
                                    localStorage.removeItem("userData");
                                    localStorage.removeItem("telegramData");
                                    window.location.href = "/login";
                                }}
                                className="w-full rounded bg-red-600 px-6 py-2 text-white hover:bg-red-700"
                            >
                                重新登入
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // 載入中狀態
    if (permissionLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">載入權限中...</p>
                </div>
            </div>
        );
    }

    // 檢查是否有管理權限
    const hasManagementAccess = role && ["admin", "point_manager", "announcer"].includes(role);

    if (!hasManagementAccess) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="max-w-md rounded-lg border border-yellow-500/30 bg-yellow-600/20 p-8 shadow-lg">
                    <div className="text-center">
                        <div className="mb-4 text-4xl text-yellow-400">🚫</div>
                        <h2 className="mb-2 text-xl font-bold text-yellow-400">權限不足</h2>
                        <p className="mb-2 text-yellow-300">您的角色是：{role || "未知"}</p>
                        <p className="mb-4 text-yellow-300">需要管理相關權限才能存取此頁面</p>
                        <p className="mb-4 text-sm text-yellow-300">
                            允許的角色：admin、point_manager、announcer
                        </p>
                        <button
                            onClick={() => router.push("/dashboard")}
                            className="rounded bg-yellow-600 px-6 py-2 text-white hover:bg-yellow-700"
                        >
                            返回儀表板
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0f203e] pb-20">
            {/* 頁面標題和用戶資訊 */}
            <div className="border-b border-[#294565] bg-[#1A325F] shadow">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between py-6">
                        <div>
                            <h1 className="mb-2 text-3xl font-bold text-[#92cbf4]">管理員控制台</h1>
                            <p className="text-[#557797]">
                                角色：{role} | 權限數量：{permissions ? permissions.length : 0}
                            </p>
                        </div>
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={() => {
                                    localStorage.removeItem("isAdmin");
                                    localStorage.removeItem("adminToken");
                                    localStorage.removeItem("isUser");
                                    localStorage.removeItem("userToken");
                                    localStorage.removeItem("userData");
                                    localStorage.removeItem("telegramData");
                                    window.location.href = "/login";
                                }}
                            >
                                <LogOut className="h-5 w-5 text-[#92cbf4] transition-colors hover:text-red-700" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* 導航頁簽 */}
            <div className="mx-auto mt-6 max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="border-b border-[#294565]">
                    <nav className="flex space-x-8">
                        {[
                            { id: "dashboard", label: "功能面板" },
                            { id: "members", label: "所有成員" },
                            { id: "pending-orders", label: "等待撮合訂單" },
                            { id: "transactions", label: "交易紀錄" },
                            { id: "config", label: "系統設定" },
                            { id: "audit", label: "權限審查" },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center space-x-2 border-b-2 px-1 py-4 text-sm font-medium ${
                                    activeTab === tab.id
                                        ? "border-[#469FD2] text-[#92cbf4]"
                                        : "border-transparent text-[#557797] hover:text-[#92cbf4]"
                                }`}
                            >
                                <span>{tab.label}</span>
                            </button>
                        ))}
                    </nav>
                </div>
            </div>

            {/* 主要內容區域 */}
            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {activeTab === "dashboard" && <AdminDashboard token={adminToken} />}
                {activeTab === "members" && <MembersList token={adminToken} />}
                {activeTab === "pending-orders" && <PendingOrdersViewer token={adminToken} />}
                {activeTab === "transactions" && <TransactionHistory token={adminToken} />}
                {activeTab === "config" && <SystemConfig token={adminToken} />}
                {activeTab === "audit" && <PermissionAudit token={adminToken} />}
            </div>
        </div>
    );
}

/**
 * 增強版管理員頁面
 * 使用權限驅動的 UI 控制系統
 */
export default function EnhancedAdminPage() {
    const router = useRouter();
    const [adminToken, setAdminToken] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState("dashboard");

    // Remove direct usePermissions call - will be handled by PermissionProvider

    // 檢查登入狀態和權限
    useEffect(() => {
        const checkAuthAndPermissions = async () => {
            console.log("=== ADMIN PAGE AUTH CHECK ===");

            // === 路徑1: 檢查傳統管理員登入 (早期系統) ===
            const isAdminStored = localStorage.getItem("isAdmin");
            const adminToken = localStorage.getItem("adminToken");

            if (isAdminStored && adminToken) {
                console.log("Legacy admin login detected");

                // 檢查 admin token 內容
                try {
                    const tokenParts = adminToken.split(".");
                    if (tokenParts.length === 3) {
                        const payload = JSON.parse(
                            atob(tokenParts[1]),
                        );
                        console.log("Admin token payload:", payload);
                    }
                } catch (e) {
                    console.error("Failed to parse admin token:", e);
                }

                // 直接設定 token，不驗證 getSystemStats
                // 因為後端可能已經改為 RBAC 驗證，讓 usePermissions hook 處理
                console.log(
                    "Setting admin token, will validate via usePermissions hook",
                );
                setAdminToken(adminToken);
                setLoading(false);
                return;
            }

            // === 路徑2: 檢查 Telegram 登入 (新系統) ===
            const isUser = localStorage.getItem("isUser");
            const userToken = localStorage.getItem("userToken");
            const telegramData = localStorage.getItem("telegramData");

            if (isUser && userToken && telegramData) {
                console.log("Telegram login detected");
                try {
                    setAdminToken(userToken);
                    console.log(
                        "Telegram user token set, will check permissions via RBAC",
                    );
                    // 權限檢查會在 usePermissions hook 中處理
                } catch (error) {
                    console.error(
                        "Telegram user validation failed:",
                        error,
                    );
                    router.push("/login");
                } finally {
                    setLoading(false);
                }
                return;
            }

            // === 沒有任何登入 ===
            console.log(
                "No valid login found, redirecting to login page",
            );
            router.push("/login");
        };

        checkAuthAndPermissions();
    }, [router]);

    // 載入中狀態 - only check authentication loading, not permission loading
    if (loading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">載入中...</p>
                </div>
            </div>
        );
    }

    return (
        <PermissionProvider token={adminToken}>
            <AdminPageContent
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                adminToken={adminToken}
                router={router}
            />
        </PermissionProvider>
    );
}
