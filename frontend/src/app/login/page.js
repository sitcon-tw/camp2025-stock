"use client";

import { adminLogin, checkTelegramAdminStatus } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Login() {
    const [adminCode, setAdminCode] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isTelegramLoading, setIsTelegramLoading] = useState(false);
    const [error, setError] = useState("");
    const [telegramError, setTelegramError] = useState("");
    const [loginMethod, setLoginMethod] = useState("password"); // "password" or "telegram"
    const [telegramUserInfo, setTelegramUserInfo] = useState(null);
    const router = useRouter();
    useEffect(() => {
        const checkAdminStatus = async () => {
            // 檢查傳統管理員 token
            const isAdmin = localStorage.getItem("isAdmin");
            const adminToken = localStorage.getItem("adminToken");
            
            // 檢查 Telegram 使用者 token
            const userToken = localStorage.getItem("userToken");
            const isUser = localStorage.getItem("isUser");

            // 優先檢查管理員 token
            if (isAdmin === "true" && adminToken) {
                try {
                    const response = await fetch(
                        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/admin/stats`,
                        {
                            headers: {
                                Authorization: `Bearer ${adminToken}`,
                                "Content-Type": "application/json",
                            },
                        },
                    );

                    if (response.ok) {
                        router.push("/admin");
                        return;
                    } else if (response.status === 401) {
                        localStorage.removeItem("isAdmin");
                        localStorage.removeItem("adminToken");
                        localStorage.removeItem("adminCode");
                    }
                } catch (error) {
                    console.error("驗證管理員 token 失敗:", error);
                    localStorage.removeItem("isAdmin");
                    localStorage.removeItem("adminToken");
                    localStorage.removeItem("adminCode");
                }
            }

            // 檢查 Telegram 使用者是否有管理員權限
            if (isUser === "true" && userToken) {
                try {
                    const permissionData = await checkTelegramAdminStatus(userToken);
                    if (permissionData.role === "admin") {
                        // Telegram 使用者有管理員權限，直接導向管理員頁面
                        localStorage.setItem("isAdmin", "true");
                        localStorage.setItem("adminToken", userToken);
                        router.push("/admin");
                        return;
                    }
                } catch (error) {
                    console.error("檢查 Telegram 管理員權限失敗:", error);
                }
            }
        };

        checkAdminStatus();
    }, [router]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        if (adminCode.trim() === "") {
            setError("請輸入管理員密碼");
            setIsLoading(false);
            return;
        }
        try {
            const data = await adminLogin(adminCode);

            // 存認證資訊
            localStorage.setItem("isAdmin", "true");
            localStorage.setItem("adminToken", data.token);
            localStorage.setItem("adminCode", adminCode);

            router.push("/admin");
        } catch (error) {
            console.error("登入錯誤:", error);
            setError(error.message || "登入失敗，請檢查網路連線");
        } finally {
            setIsLoading(false);
        }
    };

    // 檢查 Telegram 使用者狀態
    useEffect(() => {
        if (loginMethod === "telegram") {
            const checkTelegramUser = async () => {
                const userToken = localStorage.getItem("userToken");
                const isUser = localStorage.getItem("isUser");
                
                if (isUser && userToken) {
                    try {
                        const permissionData = await checkTelegramAdminStatus(userToken);
                        setTelegramUserInfo(permissionData);
                        setTelegramError(""); // 清除之前的錯誤
                    } catch (error) {
                        console.error("檢查 Telegram 使用者資訊失敗:", error);
                        setTelegramUserInfo(null);
                        setTelegramError("無法檢查 Telegram 使用者狀態");
                    }
                } else {
                    setTelegramUserInfo(null);
                    setTelegramError("");
                }
            };
            
            checkTelegramUser();
        } else {
            // 重置 Telegram 相關狀態
            setTelegramUserInfo(null);
            setTelegramError("");
        }
    }, [loginMethod]);

    const handleTelegramLogin = async () => {
        setIsTelegramLoading(true);
        setTelegramError("");

        try {
            // 檢查是否已有 Telegram 登入
            const userToken = localStorage.getItem("userToken");
            const isUser = localStorage.getItem("isUser");

            if (!isUser || !userToken) {
                setTelegramError("請先使用 Telegram 登入系統");
                setIsTelegramLoading(false);
                return;
            }

            // 檢查目前 Telegram 使用者是否有管理員權限
            const permissionData = await checkTelegramAdminStatus(userToken);
            
            if (permissionData.role === "admin") {
                // 設置管理員狀態
                localStorage.setItem("isAdmin", "true");
                localStorage.setItem("adminToken", userToken);
                
                router.push("/admin");
            } else {
                setTelegramError(`您的角色是 ${permissionData.role}，需要管理員權限才能存取管理員介面`);
            }
        } catch (error) {
            console.error("Telegram 登入錯誤:", error);
            setTelegramError("無法驗證管理員權限，請檢查您的 Telegram 登入狀態");
        } finally {
            setIsTelegramLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
            <div className="w-full max-w-md px-6">
                <div className="mb-12 text-center">
                    <h1 className="text-2xl font-bold tracking-wider text-[#92cbf4]">
                        管理員介面
                    </h1>
                    <p className="mt-2 text-sm text-[#557797]">
                        選擇登入方式
                    </p>
                </div>

                {/* 登入方法選擇 */}
                <div className="mb-6">
                    <div className="flex rounded-lg border border-[#294565] bg-[#1a3356] p-1">
                        <button
                            onClick={() => {
                                setLoginMethod("password");
                                setError("");
                                setTelegramError("");
                            }}
                            className={`flex-1 rounded-md py-2 px-3 text-sm font-medium transition-colors ${
                                loginMethod === "password"
                                    ? "bg-[#81c0e7] text-[#092e58]"
                                    : "text-[#92cbf4] hover:text-white"
                            }`}
                        >
                            🔑 密碼登入
                        </button>
                        <button
                            onClick={() => {
                                setLoginMethod("telegram");
                                setError("");
                                setTelegramError("");
                            }}
                            className={`flex-1 rounded-md py-2 px-3 text-sm font-medium transition-colors ${
                                loginMethod === "telegram"
                                    ? "bg-[#81c0e7] text-[#092e58]"
                                    : "text-[#92cbf4] hover:text-white"
                            }`}
                        >
                            📱 Telegram
                        </button>
                    </div>
                </div>

                <div className="space-y-6">
                    {loginMethod === "password" ? (
                        // 密碼登入表單
                        <>
                            <div className="text-left">
                                <label className="mb-4 block text-sm font-medium text-[#557797]">
                                    管理員密碼
                                </label>
                                <input
                                    type="password"
                                    value={adminCode}
                                    onChange={(e) => setAdminCode(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter") {
                                            handleSubmit(e);
                                        }
                                    }}
                                    className="w-full rounded-lg border-2 border-[#294565] bg-transparent px-4 py-3 text-white placeholder-slate-400 transition-colors duration-200 focus:border-cyan-400 focus:outline-none"
                                    placeholder="輸入管理員密碼"
                                    disabled={isLoading}
                                />
                            </div>

                            {error && (
                                <div className="rounded-lg border border-red-500/30 bg-red-900/20 p-3 text-center text-sm text-red-400">
                                    {error}
                                </div>
                            )}

                            <button
                                onClick={handleSubmit}
                                disabled={isLoading}
                                className="text-md w-full rounded-xl bg-[#81c0e7] py-3 font-bold text-[#092e58] transition-colors duration-200 hover:bg-[#70b3d9] disabled:cursor-not-allowed disabled:bg-gray-500"
                            >
                                {isLoading ? "登入中..." : "登入"}
                            </button>
                        </>
                    ) : (
                        // Telegram 登入表單
                        <>
                            <div className="text-center">
                                <div className="mb-4 rounded-lg border border-[#294565] bg-[#1a3356] p-4">
                                    <div className="text-4xl mb-2">📱</div>
                                    <p className="text-sm text-[#92cbf4] mb-2">
                                        使用您的 Telegram 帳號登入管理員介面
                                    </p>
                                    <p className="text-xs text-[#557797]">
                                        需要先完成 Telegram 登入且擁有管理員權限
                                    </p>
                                </div>
                            </div>

                            {/* Telegram 使用者狀態顯示 */}
                            {telegramUserInfo && (
                                <div className={`rounded-lg border p-3 text-sm ${
                                    telegramUserInfo.role === "admin" 
                                        ? "border-green-500/30 bg-green-900/20 text-green-400"
                                        : "border-yellow-500/30 bg-yellow-900/20 text-yellow-400"
                                }`}>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="font-medium">
                                                {telegramUserInfo.role === "admin" ? "✅ 已檢測到管理員權限" : "⚠️ 目前角色"}
                                            </p>
                                            <p className="text-xs opacity-75">
                                                角色: {telegramUserInfo.role}
                                            </p>
                                        </div>
                                        <div className="text-lg">
                                            {telegramUserInfo.role === "admin" ? "🔑" : "👤"}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {telegramError && (
                                <div className="rounded-lg border border-red-500/30 bg-red-900/20 p-3 text-center text-sm text-red-400">
                                    {telegramError}
                                </div>
                            )}

                            <button
                                onClick={handleTelegramLogin}
                                disabled={isTelegramLoading || (telegramUserInfo && telegramUserInfo.role !== "admin")}
                                className={`text-md w-full rounded-xl py-3 font-bold transition-colors duration-200 ${
                                    telegramUserInfo?.role === "admin"
                                        ? "bg-green-600 text-white hover:bg-green-700"
                                        : telegramUserInfo && telegramUserInfo.role !== "admin"
                                        ? "bg-gray-400 text-gray-700 cursor-not-allowed"
                                        : "bg-[#81c0e7] text-[#092e58] hover:bg-[#70b3d9]"
                                } disabled:cursor-not-allowed disabled:opacity-75`}
                            >
                                {isTelegramLoading ? "驗證中..." : 
                                 telegramUserInfo?.role === "admin" ? "以管理員身份登入" :
                                 telegramUserInfo ? `無法登入 (角色: ${telegramUserInfo.role})` :
                                 "檢查 Telegram 登入狀態"}
                            </button>

                            <div className="text-center">
                                <button
                                    onClick={() => router.push("/telegram-login")}
                                    className="text-sm text-[#81c0e7] hover:text-[#70b3d9] transition-colors"
                                >
                                    還沒有 Telegram 登入？點此登入
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
