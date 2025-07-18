import { Inter, Roboto_Mono } from "next/font/google";
import "./globals.css";

import { NavBar } from "@/components/ui";
import { DataCacheProvider } from "@/contexts/DataCacheContext";
import { twMerge } from "tailwind-merge";

const inter = Inter({
    variable: "--font-inter",
    subsets: ["latin"],
    fallback: ["LiHei Pro", "黑體-繁", "微軟正黑體"],
});

const robotoMono = Roboto_Mono({
    variable: "--font-roboto-mono",
    subsets: ["latin"],
});

export const metadata = {
    title: "SITCON Camp 2025 點數系統",
    description: "這裡可以查看排行榜、股票資訊、排行榜等公開資料",
    manifest: "/manifest.json",
    appleWebApp: {
        capable: true,
        statusBarStyle: "default",
        title: "SITCON Camp 2025 點數系統",
    },
    other: {
        "mobile-web-app-capable": "yes",
        "apple-mobile-web-app-capable": "yes",
        "apple-mobile-web-app-status-bar-style": "black-translucent",
        "apple-mobile-web-app-title": "SITCON Camp 2025 點數系統",
        "application-name": "SITCON Camp 2025 點數系統",
        "msapplication-TileColor": "#565A70",
        "msapplication-TileImage": "/icons/icon-144x144.png",
        "theme-color": "#565A70",
    },
};

export default function RootLayout({ children }) {
    return (
        <html lang="zh-TW" suppressHydrationWarning>
            <head>
                <title>SITCON Camp 2025 點數系統</title>

                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"
                />
                <link rel="manifest" href="/manifest.json" />
                <meta name="theme-color" content="#0f203e" />
                <link
                    rel="icon"
                    href="/icons/favicon.png"
                    type="image/x-icon"
                    sizes="16x16"
                ></link>
                <meta
                    name="apple-mobile-web-app-capable"
                    content="yes"
                />
                <meta
                    name="apple-mobile-web-app-status-bar-style"
                    content="black-translucent"
                />
                <meta
                    name="apple-mobile-web-app-title"
                    content="SITCON Camp 2025 點數系統"
                />
                <link
                    rel="apple-touch-icon"
                    href="/icons/icon-152x152.png"
                />
                <link
                    rel="apple-touch-icon"
                    sizes="152x152"
                    href="/icons/icon-152x152.png"
                />
                <link
                    rel="apple-touch-icon"
                    sizes="192x192"
                    href="/icons/icon-192x192.png"
                />
                <meta
                    name="msapplication-TileImage"
                    content="/icons/icon-144x144.png"
                />
                <meta
                    name="msapplication-TileColor"
                    content="#0f203e"
                />
            </head>
            <body
                className={twMerge(
                    inter.variable,
                    robotoMono.variable,
                    "min-h-screen bg-[#0f203e]",
                )}
            >
                <DataCacheProvider>
                    <div className="w-full bg-[#0f203e]">
                        {children}
                    </div>
                    <NavBar />
                </DataCacheProvider>
            </body>
        </html>
    );
}
