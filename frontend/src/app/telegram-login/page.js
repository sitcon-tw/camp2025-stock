"use client";

import { telegramOAuth } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Image from "next/image";
import loginSvg from "@/assets/undraw_authentication_tbfc.svg";

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
                    const response = await fetch(`${window.location.origin}/api/web/profile`, {
                        headers: {
                            Authorization: `Bearer ${token}`,
                            "Content-Type": "application/json",
                        },
                    });
                    
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
                    console.log("Token validation failed, clearing auth data");
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
        const placeholder = widgetContainer.querySelector('.animate-pulse');
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
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">
                        正在驗證 Telegram 登入...
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-[#0f203e] px-4">
            <div className="w-full max-w-md">
                <div className="mb-12 text-center">
                    <div className="mb-8 flex justify-center">
                        <Image
                            src={loginSvg}
                            alt="登入圖示"
                            className="h-32 w-auto"
                        />
                    </div>
                    <h1 className="mb-4 text-2xl font-bold tracking-wider text-[#92cbf4]">
                        使用者登入
                    </h1>
                    <p className="text-sm text-[#557797]">
                        使用您的 Telegram
                        帳號登入來進行交易
                    </p>
                </div>

                <div className="space-y-6">
                    {error && (
                        <div className="rounded-lg border border-red-500/30 bg-red-900/20 p-3 text-center text-sm text-red-400">
                            {error}
                        </div>
                    )}

                    {!authData && (
                        <div className="text-center">
                            <div className="mb-6">
                                <p className="mb-4 text-sm text-[#557797]">
                                    點選下方按鈕使用 Telegram 登入
                                </p>
                                <div
                                    id="telegram-widget-container"
                                    className="flex justify-center min-h-[52px] items-center"
                                >
                                    <div className="animate-pulse rounded-lg bg-[#1A325F] px-6 py-3 text-sm text-[#557797]">
                                        載入中...
                                    </div>
                                </div>
                            </div>

                            <div className="mt-8 border-t border-[#294565] pt-6">
                                <p className="text-xs text-[#557797]">
                                    首次使用請先透過 Telegram Bot
                                    註冊帳號
                                </p>
                            </div>
                        </div>
                    )}

                    {authData && (
                        <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-4">
                            <p className="mb-2 text-sm text-[#92cbf4]">
                                檢測到 Telegram 認證資料
                            </p>
                            <p className="text-xs text-[#557797]">
                                使用者: {authData.first_name}{" "}
                                {authData.last_name}
                                {authData.username &&
                                    ` (@${authData.username})`}
                            </p>
                        </div>
                    )}
                </div>

                <div className="mt-8 text-center">
                    <button
                        onClick={() => router.push("/")}
                        className="text-sm text-[#557797] transition-colors duration-200 hover:text-[#92cbf4]"
                    >
                        ← 返回首頁
                    </button>
                </div>
            </div>
        </div>
    );
}
