"use client";

import { useEffect } from "react";

export default function CommunityLayout({ children }) {
    useEffect(() => {
        // 隱藏 NavBar
        const style = document.createElement('style');
        style.textContent = `
            #navbar {
                display: none !important;
            }
        `;
        document.head.appendChild(style);
        
        // 清理函數
        return () => {
            try {
                document.head.removeChild(style);
            } catch (e) {
                // 忽略清理錯誤
            }
        };
    }, []);

    return (
        <div className="w-full bg-[#0f203e]">
            {children}
        </div>
    );
}