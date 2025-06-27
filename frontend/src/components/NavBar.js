"use client";

import {
    ChartCandlestick,
    CircleQuestionMark,
    House,
    Trophy,
    User,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { twMerge } from "tailwind-merge";

export default function NavBar() {
    const pathname = usePathname();
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        // 檢查登入狀態
        const checkLoginStatus = () => {
            const isUser = localStorage.getItem("isUser");
            const userToken = localStorage.getItem("userToken");
            setIsLoggedIn(isUser === "true" && !!userToken);
        };

        checkLoginStatus();

        // 監聽 storage 變化
        window.addEventListener("storage", checkLoginStatus);

        return () => {
            window.removeEventListener("storage", checkLoginStatus);
        };
    }, []);

    const getIconColor = (path) => {
        return pathname === path
            ? "text-[#4b87cc]"
            : "text-[#82bee2]";
    };
    return (
        <div
            className={twMerge(
                "fixed bottom-4 left-1/2 z-40 flex w-full max-w-[calc(100%-2rem)] -translate-x-1/2 transform items-center justify-between rounded-full border-2 border-[#4f6f97]/20 bg-[#0f203e]/20 px-10 py-4 shadow-lg shadow-black/40 backdrop-blur-md",
                "md:top-1/2 md:left-8 md:h-auto md:w-auto md:max-w-none md:translate-x-0 md:-translate-y-1/2 md:flex-col md:space-y-6 md:rounded-full md:px-4 md:py-6",
            )}
        >
            <Link
                href="/"
                className={twMerge(
                    "h-6 w-6 transition-colors",
                    getIconColor("/"),
                )}
            >
                <House />
            </Link>
            <Link
                href="/status"
                className={twMerge(
                    "h-6 w-6 transition-colors",
                    getIconColor("/status"),
                )}
            >
                <ChartCandlestick />
            </Link>
            <Link
                href="/leaderboard"
                className={twMerge(
                    "h-6 w-6 transition-colors",
                    getIconColor("/leaderboard"),
                )}
            >
                <Trophy />
            </Link>
            <Link
                href="/tutorial"
                className={twMerge(
                    "h-6 w-6 transition-colors",
                    getIconColor("/tutorial"),
                )}
            >
                <CircleQuestionMark />
            </Link>

            {/* 登入/儀表板按鈕 */}
            {isLoggedIn ? (
                <Link
                    href="/dashboard"
                    className={twMerge(
                        "h-6 w-6 transition-colors",
                        getIconColor("/dashboard"),
                    )}
                >
                    <svg
                        width="20"
                        height="20"
                        viewBox="0 0 20 20"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <path
                            d="M10 2C5.58 2 2 5.58 2 10s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 12.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"
                            fill="currentColor"
                        />
                    </svg>
                </Link>
            ) : (
                <Link
                    href="/telegram-login"
                    className={twMerge(
                        "h-6 w-6 transition-colors",
                        getIconColor("/telegram-login"),
                    )}
                >
                    <User />
                </Link>
            )}
        </div>
    );
}
