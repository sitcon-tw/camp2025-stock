"use client";

import { telegramOAuth } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function TelegramLogin() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [authData, setAuthData] = useState(null);
    const router = useRouter();

    useEffect(() => {
        // 檢查是否已經登入
        const checkUserStatus = async () => {
            const isUser = localStorage.getItem("isUser");
            const token = localStorage.getItem("userToken");

            if (isUser === "true" && token) {
                try {
                    // 驗證 token 是否仍然有效
                    const response = await fetch(
                        `${window.location.origin}/api/web/profile`,
                        {
                            headers: {
                                Authorization: `Bearer ${token}`,
                                "Content-Type": "application/json",
                            },
                        },
                    );

                    if (response.ok) {
                        router.push("/dashboard");
                    } else {
                        // 清除無效的認證資料
                        localStorage.removeItem("isUser");
                        localStorage.removeItem("userToken");
                        localStorage.removeItem("userData");
                        localStorage.removeItem("telegramData");
                    }
                } catch (error) {
                    console.log(
                        "Token validation failed, clearing auth data",
                    );
                    // 清除認證資料
                    localStorage.removeItem("isUser");
                    localStorage.removeItem("userToken");
                    localStorage.removeItem("userData");
                    localStorage.removeItem("telegramData");
                }
            }
        };

        checkUserStatus();

        // 檢查 URL 參數中的 Telegram OAuth 資料
        const urlParams = new URLSearchParams(window.location.search);
        const hash = urlParams.get("hash");

        if (hash) {
            // 從 URL 參數解析 Telegram OAuth 資料
            const authDataFromUrl = {
                id: parseInt(urlParams.get("id")),
                first_name: urlParams.get("first_name"),
                last_name: urlParams.get("last_name"),
                username: urlParams.get("username"),
                photo_url: urlParams.get("photo_url"),
                auth_date: parseInt(urlParams.get("auth_date")),
                hash: hash,
            };

            // 移除 null 值
            Object.keys(authDataFromUrl).forEach((key) => {
                if (
                    authDataFromUrl[key] === null ||
                    authDataFromUrl[key] === "null"
                ) {
                    delete authDataFromUrl[key];
                }
            });

            setAuthData(authDataFromUrl);
            handleTelegramAuth(authDataFromUrl);
        }
    }, [router]);

    const handleTelegramAuth = async (authDataToUse = authData) => {
        if (!authDataToUse) {
            setError("缺少 Telegram 認證資料");
            return;
        }

        setIsLoading(true);
        setError("");

        try {
            const data = await telegramOAuth(authDataToUse);

            if (data.success) {
                // 存認證資訊
                localStorage.setItem("isUser", "true");
                localStorage.setItem("userToken", data.token);
                localStorage.setItem(
                    "userData",
                    JSON.stringify(data.user),
                );
                localStorage.setItem(
                    "telegramData",
                    JSON.stringify(authDataToUse),
                );

                router.push("/dashboard");
            } else {
                setError(data.message || "登入失敗");
            }
        } catch (error) {
            console.error("Telegram OAuth 錯誤:", error);
            setError(error.message || "登入失敗，請檢查網路連線");
        } finally {
            setIsLoading(false);
        }
    };

    const initTelegramWidget = () => {
        const widgetContainer = document.getElementById(
            "telegram-widget-container",
        );
        if (!widgetContainer) return;

        // 如果 Telegram 小工具已存在，先移除
        const existingWidget = document.getElementById(
            "telegram-login-widget",
        );
        if (existingWidget) {
            existingWidget.remove();
        }

        // 移除載入中的 placeholder
        const placeholder =
            widgetContainer.querySelector(".animate-pulse");
        if (placeholder) {
            placeholder.remove();
        }

        // 建立 Telegram 登入小工具
        const telegramLoginWidget = document.createElement("script");
        telegramLoginWidget.id = "telegram-login-widget";
        telegramLoginWidget.src =
            "https://telegram.org/js/telegram-widget.js?22";
        telegramLoginWidget.setAttribute(
            "data-telegram-login",
            "sitconcamp2025bot",
        );
        telegramLoginWidget.setAttribute("data-size", "large");
        telegramLoginWidget.setAttribute(
            "data-auth-url",
            window.location.origin + "/telegram-login",
        );
        telegramLoginWidget.setAttribute(
            "data-request-access",
            "write",
        );

        widgetContainer.appendChild(telegramLoginWidget);
    };

    useEffect(() => {
        // 如果沒有從 URL 參數獲取到認證資料，則顯示 Telegram 小工具
        if (!authData) {
            const timer = setTimeout(() => {
                initTelegramWidget();
            }, 100);

            return () => clearTimeout(timer);
        }
    }, [authData]);

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e] px-4">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#294565] border-t-[#92cbf4]"></div>
                    <p className="text-[#92cbf4]">
                        正在驗證 Telegram 登入...
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
            <div className="w-full max-w-md px-6">
                <div className="mb-12 text-center">
                    <h1 className="text-2xl font-bold tracking-wider text-[#92cbf4]">
                        使用者登入
                    </h1>
                    <p className="mt-2 text-sm text-[#557797]">
                        使用 Telegram 帳號登入系統
                    </p>
                </div>

                <div className="space-y-6">
                    <div className="text-center">
                        <div className="rounded-lg border border-[#294565] bg-[#1a3356] p-4">
                            <div className="text-4xl mb-2">📱</div>
                            <p className="text-sm text-[#92cbf4] mb-4">
                                使用您的 Telegram 帳號登入系統
                            </p>
                            <p className="text-xs text-[#557797] mb-4">
                                點擊下方按鈕開始 Telegram 登入流程
                            </p>

                            <div id="telegram-widget-container" className="flex justify-center">
                                {!authData && (
                                    <div className="animate-pulse space-y-2">
                                        <div className="h-10 bg-[#294565] rounded w-40"></div>
                                        <p className="text-xs text-[#557797]">載入中...</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {error && (
                        <div className="rounded-lg border border-red-500/30 bg-red-900/20 p-3 text-center text-sm text-red-400">
                            {error}
                        </div>
                    )}

                    <div className="rounded-lg border border-[#92cbf4]/20 bg-[#92cbf4]/5 p-3">
                        <p className="text-xs text-center text-[#557797]">
                            登入之前請先使用 Telegram bot 綁定學員帳號
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
