"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getSystemStats } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";
import { PermissionProvider } from "@/contexts/PermissionContext";
import { AdminDashboard } from "@/components/AdminDashboard";
import { PermissionAudit } from "@/components/PermissionAudit";

/**
 * 增強版管理員頁面
 * 使用權限驅動的 UI 控制系統
 */
export default function EnhancedAdminPage() {
    const router = useRouter();
    const [adminToken, setAdminToken] = useState(null);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState("dashboard");
    
    // 使用權限 Hook
    const { permissions, role, loading: permissionLoading, isAdmin, error } = usePermissions(adminToken);

    // 檢查登入狀態和權限
    useEffect(() => {
        const checkAuthAndPermissions = async () => {
            const isAdminStored = localStorage.getItem("isAdmin");
            const token = localStorage.getItem("adminToken");

            if (!isAdminStored || !token) {
                router.push("/login");
                return;
            }

            try {
                // 驗證 token 有效性
                await getSystemStats(token);
                setAdminToken(token);
                setIsLoggedIn(true);
            } catch (error) {
                console.error("Token validation failed:", error);
                localStorage.removeItem("isAdmin");
                localStorage.removeItem("adminToken");
                router.push("/login");
            } finally {
                setLoading(false);
            }
        };

        checkAuthAndPermissions();
    }, [router]);

    // 載入中狀態
    if (loading || permissionLoading) {
        return (
            <div className="min-h-screen bg-gray-100 flex items-center justify-center">
                <div className="bg-white p-8 rounded-lg shadow-lg">
                    <div className="flex items-center space-x-4">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        <span className="text-lg text-gray-600">載入中...</span>
                    </div>
                </div>
            </div>
        );
    }

    // 權限錯誤
    if (error) {
        return (
            <div className="min-h-screen bg-gray-100 flex items-center justify-center">
                <div className="bg-red-50 border border-red-200 p-8 rounded-lg shadow-lg max-w-md">
                    <div className="text-center">
                        <div className="text-red-600 text-4xl mb-4">⚠️</div>
                        <h2 className="text-xl font-bold text-red-800 mb-2">權限驗證失敗</h2>
                        <p className="text-red-700 mb-4">{error}</p>
                        <button
                            onClick={() => {
                                localStorage.removeItem("isAdmin");
                                localStorage.removeItem("adminToken");
                                router.push("/login");
                            }}
                            className="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700"
                        >
                            重新登入
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // 非管理員用戶
    if (!isAdmin()) {
        return (
            <div className="min-h-screen bg-gray-100 flex items-center justify-center">
                <div className="bg-yellow-50 border border-yellow-200 p-8 rounded-lg shadow-lg max-w-md">
                    <div className="text-center">
                        <div className="text-yellow-600 text-4xl mb-4">🚫</div>
                        <h2 className="text-xl font-bold text-yellow-800 mb-2">權限不足</h2>
                        <p className="text-yellow-700 mb-2">您的角色是：{role}</p>
                        <p className="text-yellow-700 mb-4">需要管理員權限才能存取此頁面</p>
                        <button
                            onClick={() => router.push("/dashboard")}
                            className="bg-yellow-600 text-white px-6 py-2 rounded hover:bg-yellow-700"
                        >
                            返回儀表板
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <PermissionProvider token={adminToken}>
            <div className="min-h-screen bg-gray-100">
                {/* 頁面標題和用戶資訊 */}
                <div className="bg-white shadow">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex justify-between items-center py-6">
                            <div>
                                <h1 className="text-3xl font-bold text-gray-900">管理員控制台</h1>
                                <p className="text-gray-600">
                                    角色：{role} | 權限數量：{permissions.length}
                                </p>
                            </div>
                            <div className="flex items-center space-x-4">
                                <div className="text-sm text-gray-500">
                                    {new Date().toLocaleString()}
                                </div>
                                <button
                                    onClick={() => {
                                        localStorage.removeItem("isAdmin");
                                        localStorage.removeItem("adminToken");
                                        router.push("/login");
                                    }}
                                    className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
                                >
                                    登出
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 導航頁簽 */}
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
                    <div className="border-b border-gray-200">
                        <nav className="flex space-x-8">
                            {[
                                { id: "dashboard", label: "功能面板", icon: "🏠" },
                                { id: "audit", label: "權限審查", icon: "🔍" },
                            ].map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                                        activeTab === tab.id
                                            ? "border-blue-500 text-blue-600"
                                            : "border-transparent text-gray-500 hover:text-gray-700"
                                    }`}
                                >
                                    <span>{tab.icon}</span>
                                    <span>{tab.label}</span>
                                </button>
                            ))}
                        </nav>
                    </div>
                </div>

                {/* 主要內容區域 */}
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {activeTab === "dashboard" && (
                        <AdminDashboard token={adminToken} />
                    )}
                    {activeTab === "audit" && (
                        <PermissionAudit token={adminToken} />
                    )}
                </div>

                {/* 頁腳資訊 */}
                <div className="bg-gray-50 border-t border-gray-200 mt-12">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                        <div className="text-center text-sm text-gray-500">
                            <p>權限驅動的管理系統 | 基於 RBAC 安全架構</p>
                            <p className="mt-1">
                                目前擁有權限：
                                {permissions.slice(0, 3).join(", ")}
                                {permissions.length > 3 && ` 等 ${permissions.length} 項`}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </PermissionProvider>
    );
}

/**
 * 使用說明：
 * 
 * 1. 將此文件重命名為 page.js 以替換原有的管理員頁面
 * 2. 或者在原有頁面中引入權限檢查邏輯
 * 3. 確保所有管理員功能都有對應的權限檢查
 * 
 * 主要改進：
 * - 使用 usePermissions Hook 進行權限驗證
 * - 實施權限驅動的 UI 控制
 * - 加入權限審查工具
 * - 提供清晰的錯誤處理和用戶反饋
 */