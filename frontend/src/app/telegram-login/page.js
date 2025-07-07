"use client";

import { telegramOAuth } from "@/lib/api";
import { Info } from "lucide-react";
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
        <div className="flex min-h-screen items-center justify-center bg-[#0f203e] p-4">
            <div className="w-full max-w-sm">
                {/* Main Login Card */}
                <div className="rounded-2xl border border-[#294565] bg-[#1A325F] p-6 shadow-xl">
                    <div className="mb-6 text-center">
                        <div className="bg-opacity-10 mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#92cbf4]/30 text-xl">
                            👋
                        </div>
                        <h2 className="mb-1 text-lg font-semibold text-[#92cbf4]">
                            Telegram 帳號登入
                        </h2>
                        <p className="text-sm text-[#557797]">
                            用你的 Telegram 帳號登入 SITCON Camp 2025
                            點數系統
                        </p>
                    </div>

                    {/* Login Widget Container */}
                    <div className="mb-4 rounded-xl bg-[#0f203e] p-4">
                        <div
                            id="telegram-widget-container"
                            className="flex justify-center"
                        >
                            {!authData && (
                                <div className="animate-pulse text-center">
                                    <div className="mb-2 h-12 w-48 rounded-lg bg-[#294565]"></div>
                                    <p className="text-xs text-[#557797]">
                                        載入登入按鈕...
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Error Display */}
                    {error && (
                        <div className="bg-opacity-10 border-opacity-30 mb-4 rounded-lg border border-red-500 bg-red-500 p-3">
                            <div className="flex items-start space-x-2">
                                <svg
                                    className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-400"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                >
                                    <path
                                        fillRule="evenodd"
                                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                                <p className="text-sm text-red-300">
                                    {error}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Info Notice */}
                    <div className="border-opacity-10 rounded-lg border border-[#92cbf4] bg-[#0f203e] p-3 text-[#92cbf4]">
                        <div className="flex items-center justify-center space-x-2">
                            <Info className="h-4 w-4" />
                            <p className="text-xs">
                                登入之前需要先用喵券機機器人註冊帳號
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
