"use client";

import { useState, useEffect } from "react";

export default function UpdateBanner() {
    const [timeLeft, setTimeLeft] = useState(5);
    const [isUpdating, setIsUpdating] = useState(false);

    useEffect(() => {
        const interval = setInterval(() => {
            setTimeLeft((prevTime) => {
                if (prevTime <= 1) {
                    // 模擬更新過程
                    setIsUpdating(true);
                    setTimeout(() => {
                        setIsUpdating(false);
                    }, 800);
                    return 5; // 改為5秒更新週期
                }
                return prevTime - 1;
            });
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="w-full bg-gradient-to-r from-[#1A325F] via-[#294565] to-[#0f203e] px-4 py-1.5 text-center text-xs text-white shadow-sm border-b border-[#294565] absolute top-0 left-0">
            <div className="flex items-center justify-center space-x-2">
                {isUpdating ? (
                    <>
                        <svg className="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle 
                                className="opacity-25" 
                                cx="12" 
                                cy="12" 
                                r="10" 
                                stroke="currentColor" 
                                strokeWidth="4"
                            />
                            <path 
                                className="opacity-75" 
                                fill="currentColor" 
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                        </svg>
                        <span className="font-medium">🔄 資料更新中</span>
                    </>
                ) : (
                    <>
                        <div className="flex items-center space-x-1">
                            <div className="h-2 w-2 animate-pulse rounded-full bg-green-300"></div>
                            <span className="text-green-100">即時更新</span>
                        </div>
                        <span className="text-white/80">|</span>
                        <span>
                            下次更新: <span className="font-mono font-semibold text-yellow-200">{timeLeft}s</span>
                        </span>
                    </>
                )}
            </div>
        </div>
    );
}