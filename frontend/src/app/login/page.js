"use client";

import { adminLogin } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Login() {
    const [adminCode, setAdminCode] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();
    useEffect(() => {
        const checkAdminStatus = async () => {
            const isAdmin = localStorage.getItem("isAdmin");
            const token = localStorage.getItem("adminToken");

            if (isAdmin === "true" && token) {
                // 看 token 有沒有效
                try {
                    const response = await fetch(
                        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/admin/stats`,
                        {
                            headers: {
                                Authorization: `Bearer ${token}`,
                                "Content-Type": "application/json",
                            },
                        },
                    );

                    if (response.ok) {
                        router.push("/admin");
                    } else if (response.status === 401) {
                        // 清除 localStorage
                        localStorage.removeItem("isAdmin");
                        localStorage.removeItem("adminToken");
                        localStorage.removeItem("adminCode");
                    }
                } catch (error) {
                    console.error("驗證 token 失敗:", error);
                    // 網路錯誤時也清除 token
                    localStorage.removeItem("isAdmin");
                    localStorage.removeItem("adminToken");
                    localStorage.removeItem("adminCode");
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

    return (
        <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
            <div className="w-full max-w-sm px-6">
                <div className="mb-12 text-center">
                    <h1 className="text-2xl font-bold tracking-wider text-[#92cbf4]">
                        管理員介面
                    </h1>
                </div>

                <div className="space-y-6">
                    <div className="text-left">
                        <label className="mb-4 block text-sm font-medium text-[#557797]">
                            管理員密碼
                        </label>

                        <input
                            type="password"
                            value={adminCode}
                            onChange={(e) =>
                                setAdminCode(e.target.value)
                            }
                            onKeyPress={(e) => {
                                if (e.key === "Enter") {
                                    handleSubmit(e);
                                }
                            }}
                            className="w-full rounded-lg border-2 border-[#294565] bg-transparent px-4 py-3 text-white placeholder-slate-400 transition-colors duration-200 focus:border-cyan-400 focus:outline-none"
                            placeholder=""
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
                </div>
            </div>
        </div>
    );
}
