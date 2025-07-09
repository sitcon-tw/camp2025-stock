'use client';

import { useState, useEffect } from 'react';
import { getPriceSummary, getMarketPriceInfo, getTransferFeeConfigPublic, API_BASE_URL } from '@/lib/api';

export default function TutorialPage() {
    const [marketData, setMarketData] = useState({
        ipoPrice: 20,
        tradingLimit: 20,
        transferFeeRate: 10,
        transferMinFee: 1,
        ipoSharesRemaining: null,
        loading: true
    });

    useEffect(() => {
        const fetchMarketData = async () => {
            try {
                // 獲取價格摘要（包含漲跌限制）
                const priceData = await getPriceSummary();

                // 獲取 IPO 狀態
                const ipoResponse = await fetch(`${API_BASE_URL}/api/ipo/status`);
                const ipoData = await ipoResponse.json();

                // 嘗試獲取市場價格資訊
                let marketInfo = null;
                try {
                    marketInfo = await getMarketPriceInfo();
                } catch (error) {
                    console.warn('Failed to fetch market price info:', error);
                }

                // 獲取轉帳手續費設定
                let feeConfig = { feeRate: 10, minFee: 1 };
                try {
                    feeConfig = await getTransferFeeConfigPublic();
                } catch (error) {
                    console.warn('Failed to fetch transfer fee config:', error);
                }

                setMarketData({
                    ipoPrice: ipoData?.initialPrice || 20,
                    tradingLimit: priceData.limitPercent ? (priceData.limitPercent / 100) : 20,
                    transferFeeRate: feeConfig.feeRate || 10,
                    transferMinFee: feeConfig.minFee || 1,
                    ipoSharesRemaining: ipoData?.sharesRemaining,
                    loading: false
                });
            } catch (error) {
                console.error('Failed to fetch market data:', error);
                setMarketData(prev => ({ ...prev, loading: false }));
            }
        };

        fetchMarketData();
    }, []);
    if (marketData.loading) {
        return (
            <div className="min-h-screen bg-[#0f203e] pb-32">
                <div className="container mx-auto max-w-4xl px-8 py-8">
                    <h1 className="mb-8 text-center text-3xl font-bold text-[#82bee2]">
                        📈 SITC 股市交易指南
                    </h1>
                    <div className="text-center text-white">
                        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
                        <p className="mt-4">載入市場資料中...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0f203e] pb-32">
            <div className="container mx-auto max-w-4xl px-8 py-8">
                <h1 className="mb-8 text-center text-3xl font-bold text-[#82bee2]">
                    📈 SITC 股市交易指南
                </h1>

                <div className="mb-8 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="text-md text-white">
                        歡迎來到 SITCON Camp 的 SITC
                        模擬股市！你可以使用「營隊點數」來體驗
                        投資的樂趣，就算你從沒碰過股票也沒關係！
                    </p>
                </div>

                <div className="mb-8 rounded-lg bg-[#0d2543] border border-[#82bee2] p-4">
                    <h3 className="mb-3 text-lg font-semibold text-[#82bee2]">
                        📊 目前系統設定
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-white">
                        <div>
                            <span className="text-[#a8d4f0]">IPO 價格：</span>
                            {marketData.ipoPrice} 點/股
                        </div>
                        <div>
                            <span className="text-[#a8d4f0]">漲跌限制：</span>
                            {marketData.tradingLimit}%
                        </div>
                        <div>
                            <span className="text-[#a8d4f0]">轉帳手續費：</span>
                            {marketData.transferFeeRate}%（最低 {marketData.transferMinFee} 點）
                        </div>
                        {marketData.ipoSharesRemaining !== null && (
                            <div>
                                <span className="text-[#a8d4f0]">IPO 剩餘：</span>
                                {marketData.ipoSharesRemaining.toLocaleString()} 股
                            </div>
                        )}
                    </div>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    TL;DR
                </h2>
                <ul className="mb-8 list-disc pl-6 text-white">
                    <li>低買高賣。</li>
                    <li>點少的輸，點多的贏。</li>
                </ul>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🧩 基本玩法總覽
                </h2>
                <div className="mb-8 overflow-x-auto">
                    <table className="w-full overflow-hidden">
                        <thead className="border-b border-[#82bee2] [&>tr>th]:bg-[#19325e] [&>tr>th:not(:last-child)]:border-r [&>tr>th:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <th className="rounded-tl-xl px-4 py-2 text-left text-[#82bee2]">
                                    項目
                                </th>
                                <th className="rounded-tr-xl px-4 py-2 text-left text-[#82bee2]">
                                    說明
                                </th>
                            </tr>
                        </thead>
                        <tbody className="[&>tr:not(:last-child)>td]:border-b [&>tr:not(:last-child)>td]:border-[#82bee2] [&>tr>td]:bg-[#1a2e4a] [&>tr>td:not(:last-child)]:border-r [&>tr>td:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    交易單位
                                </td>
                                <td className="px-4 py-2 text-white">
                                    使用「營隊點數」購買或賣出「SITC
                                    股票」
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    操作方式
                                </td>
                                <td className="px-4 py-2 text-white">
                                    所有買賣都用 Telegram bot
                                    下指令完成
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    資訊查詢
                                </td>
                                <td className="px-4 py-2 text-white">
                                    用網頁查詢目前價格、交易紀錄等資訊
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    交易時間
                                </td>
                                <td className="px-4 py-2 text-white">
                                    只在指定時段能交易（如活動時可能會禁止）
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    圈存系統
                                </td>
                                <td className="px-4 py-2 text-white">
                                    交易時自動預留資金，防止超支和重複消費
                                </td>
                            </tr>
                            <tr>
                                <td className="rounded-bl-xl px-4 py-2 text-white">
                                    點數排行榜
                                </td>
                                <td className="rounded-br-xl px-4 py-2 text-white">
                                    以組別或個人為單位，可將股票換算點數
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    📱 操作流程總覽
                </h2>
                <div className="mb-6 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="font-semibold text-[#82bee2]">
                        此網站可以買賣股票，其他遊戲和轉帳請透過 Telegram Bot 完成！
                    </p>
                </div>

                <p className="mb-6 text-white">你可以選擇：</p>
                <ol className="mb-8 list-decimal pl-6 text-white">
                    <li>
                        即時交易（市價單） →
                        直接成交（人家想賣多少就用多少買）
                    </li>
                    <li>
                        掛單交易（限價單） →
                        等待有人來成交（等到你要的價格）
                    </li>
                </ol>

                <div className="mb-8 rounded-lg bg-[#0d2543] border border-[#82bee2] p-6">
                    <h3 className="mb-4 text-xl font-semibold text-[#82bee2]">
                        ⚡ 即時成交機制說明
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <h4 className="mb-2 font-semibold text-[#a8d4f0]">市價單即時成交：</h4>
                            <ul className="list-disc pl-6 text-white space-y-1">
                                <li><strong>市價買單</strong>：優先與最低價賣單配對，若無賣單則從 IPO 以 {marketData.loading ? '...' : marketData.ipoPrice} 點/股購買</li>
                                <li><strong>市價賣單</strong>：優先與最高價買單配對，若無買單則拒絕交易</li>
                                <li>成交立即執行，無需等待</li>
                                <li><span className="text-red-400">⚠️ 限制</span>：市價買單在無賣單且 IPO 售完時會失敗</li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="mb-2 font-semibold text-[#a8d4f0]">限價單可能即時成交：</h4>
                            <ul className="list-disc pl-6 text-white space-y-1">
                                <li><strong>限價買單</strong>：當有賣單價格 ≤ 你的買價時，透過撮合系統立即成交</li>
                                <li><strong>限價賣單</strong>：當有買單價格 ≥ 你的賣價時，透過撮合系統立即成交</li>
                                <li>撮合系統每 60 秒執行一次，或在下單後觸發</li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="mb-2 font-semibold text-[#a8d4f0]">IPO 回補機制：</h4>
                            <ul className="list-disc pl-6 text-white space-y-1">
                                <li>當市場缺乏賣單時，市價買單可從系統 IPO 購買</li>
                                <li>IPO 價格為 {marketData.loading ? '...' : marketData.ipoPrice} 點/股，提供市場流動性</li>
                                <li><span className="text-yellow-400">⚠️ IPO 股數有限</span>，售完後市價買單會失敗</li>
                                <li>IPO 在五檔報價中會顯示為系統賣單</li>
                                <li>管理員可動態調整 IPO 剩餘股數和價格</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🛒 如何「買股票」？
                </h2>

                <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                    ✅ 即時買（市價買入）
                </h3>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /stock
                    </code>
                </div>
                <div className="mb-6">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>
                            使用 /stock
                            指令進入交易介面，選擇市價買入。
                        </li>
                        <li>用當下市場「賣一價」直接買入，若無賣單則從 IPO 以 {marketData.loading ? '...' : marketData.ipoPrice} 點/股購買。</li>
                        <li>
                            系統會顯示「你花了多少點數，買了幾張」。
                        </li>
                        <li><span className="text-[#ffd700]">立即成交</span>：無需等待撮合時間。</li>
                        <li><span className="text-red-400">⚠️ 注意</span>：若市場無賣單且 IPO 股份售完，市價買單會失敗。</li>
                    </ul>
                </div>

                <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                    ✅ 掛單買（限價掛單）
                </h3>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /stock
                    </code>
                </div>
                <div className="mb-8">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>
                            使用 /stock
                            指令進入交易介面，選擇限價掛單買入。
                        </li>
                        <li>掛在市場等人賣給你。</li>
                        <li>
                            只有當「有人的賣價 ≤
                            你的買價」時才會成交。
                        </li>
                        <li><span className="text-[#ffd700]">可能即時成交</span>：若有符合條件的賣單，透過撮合系統立即配對。</li>
                    </ul>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    💰 如何「賣股票」？
                </h2>

                <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                    ✅ 即時賣（市價賣出）
                </h3>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /stock
                    </code>
                </div>
                <div className="mb-6">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>
                            使用 /stock
                            指令進入交易介面，選擇市價賣出。
                        </li>
                        <li>以當下市場「買一價」賣出。</li>
                        <li>越多競爭者願意買，價格越好。</li>
                        <li><span className="text-[#ffd700]">立即成交</span>：若有買單則立即配對，無買單則拒絕交易。</li>
                    </ul>
                </div>

                <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                    ✅ 掛單賣（限價掛單）
                </h3>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /stock
                    </code>
                </div>
                <div className="mb-8">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>
                            使用 /stock
                            指令進入交易介面，選擇限價掛單賣出。
                        </li>
                        <li>掛單等待市場出價。</li>
                        <li>
                            只有當「有人的買價 ≥
                            你的賣價」時才會成交。
                        </li>
                        <li><span className="text-[#ffd700]">可能即時成交</span>：若有符合條件的買單，透過撮合系統立即配對。</li>
                    </ul>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    💸 如何「轉帳」？
                </h2>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /transfer
                    </code>
                </div>
                <div className="mb-8">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>可以轉點數給其他人。</li>
                        <li>會抽取 {marketData.loading ? '...' : marketData.transferFeeRate}% 手續費（最低 {marketData.loading ? '...' : marketData.transferMinFee} 點）。</li>
                    </ul>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🔒 圈存系統說明
                </h2>
                <div className="mb-8 rounded-lg bg-[#0d2543] border border-[#82bee2] p-6">
                    <div className="mb-4">
                        <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                            💰 什麼是圈存？
                        </h3>
                        <p className="text-white mb-4">
                            圈存是一種資金預留機制，類似銀行的資金凍結功能。當你進行需要花費點數的操作時，
                            系統會先「圈存」（預留）相應的資金，確保交易安全進行。
                        </p>
                        
                        <h4 className="mb-2 font-semibold text-[#a8d4f0]">圈存會在以下情況發生：</h4>
                        <ul className="list-disc pl-6 text-white space-y-1 mb-4">
                            <li><strong>股票掛單</strong>：下限價買單時，會圈存最大可能的購買成本</li>
                            <li><strong>市價單</strong>：下市價買單時，會預估並圈存購買成本</li>
                            <li><strong>PvP 對戰</strong>：發起挑戰時，會圈存挑戰金額</li>
                            <li><strong>點數轉帳</strong>：轉帳時，會圈存轉帳金額加上手續費</li>
                        </ul>
                    </div>

                    <div className="mb-4">
                        <h4 className="mb-2 font-semibold text-[#a8d4f0]">雙餘額系統：</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-white">
                            <div className="bg-[#1a2e4a] p-4 rounded-lg">
                                <h5 className="font-semibold text-green-400 mb-2">可用點數</h5>
                                <p className="text-sm">可以自由使用的點數，用於新的交易和轉帳</p>
                            </div>
                            <div className="bg-[#1a2e4a] p-4 rounded-lg">
                                <h5 className="font-semibold text-yellow-400 mb-2">圈存金額</h5>
                                <p className="text-sm">已預留但尚未消費的點數，正在等待交易完成</p>
                            </div>
                        </div>
                        <div className="mt-3 p-3 bg-[#1a2e4a] rounded-lg">
                            <p className="text-sm text-[#a8d4f0]">
                                <strong>總餘額 = 可用點數 + 圈存金額</strong>
                            </p>
                            <p className="text-xs text-[#557797] mt-1">
                                這代表你實際擁有的所有點數
                            </p>
                        </div>
                    </div>

                    <div className="mb-4">
                        <h4 className="mb-2 font-semibold text-[#a8d4f0]">圈存的好處：</h4>
                        <ul className="list-disc pl-6 text-white space-y-1">
                            <li><strong>防止超支</strong>：確保你不會花費超過擁有的點數</li>
                            <li><strong>交易安全</strong>：避免同時進行多筆交易導致的資金不足</li>
                            <li><strong>自動管理</strong>：交易完成後自動扣除，取消後自動退回</li>
                            <li><strong>透明化</strong>：可隨時查看圈存詳情和交易狀態</li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="mb-2 font-semibold text-[#a8d4f0]">如何查看圈存詳情：</h4>
                        <ol className="list-decimal pl-6 text-white space-y-1">
                            <li>在個人資料頁面，可以看到圈存金額（黃色顯示）</li>
                            <li>點擊「查看詳情」按鈕，可以看到所有圈存記錄</li>
                            <li>每筆圈存都會顯示類型、金額、時間和狀態</li>
                            <li>狀態包括：處理中、已完成、已取消</li>
                        </ol>
                    </div>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🔍 如何「查看小隊點數」？
                </h2>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /point
                    </code>
                </div>
                <div className="mb-8">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>查看自己小隊的總點數。</li>
                    </ul>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    📊 如何查詢市場價格？
                </h2>
                <p className="mb-4 text-white">網頁會顯示：</p>
                <div className="mb-8 overflow-x-auto">
                    <table className="w-full overflow-hidden">
                        <thead className="border-b border-[#82bee2] [&>tr>th]:bg-[#19325e] [&>tr>th:not(:last-child)]:border-r [&>tr>th:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <th className="rounded-tl-xl px-4 py-2 text-left text-[#82bee2]">
                                    項目
                                </th>
                                <th className="rounded-tr-xl px-4 py-2 text-left text-[#82bee2]">
                                    說明
                                </th>
                            </tr>
                        </thead>
                        <tbody className="[&>tr:not(:last-child)>td]:border-b [&>tr:not(:last-child)>td]:border-[#82bee2] [&>tr>td]:bg-[#1a2e4a] [&>tr>td:not(:last-child)]:border-r [&>tr>td:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    買一價 / 賣一價
                                </td>
                                <td className="px-4 py-2 text-white">
                                    市場目前最高買價 / 最低賣價
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    即時價格
                                </td>
                                <td className="px-4 py-2 text-white">
                                    最新成交價格
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    今日漲跌
                                </td>
                                <td className="px-4 py-2 text-white">
                                    與開盤價相比的變動
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    今日最低 / 最高
                                </td>
                                <td className="px-4 py-2 text-white">
                                    單日內波動範圍
                                </td>
                            </tr>
                            <tr>
                                <td className="rounded-bl-xl px-4 py-2 text-white">
                                    最近成交紀錄
                                </td>
                                <td className="rounded-br-xl px-4 py-2 text-white">
                                    顯示價格與成交時間
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🕒 交易時間？
                </h2>
                <p className="mb-8 text-white">
                    每天限定時段可交易，可在網站首頁查看。管理員也可手動開關市場。
                </p>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    📊 漲跌限制機制
                </h2>
                <div className="mb-8 rounded-lg bg-[#0d2543] border border-[#82bee2] p-6">
                    <div className="space-y-4">
                        <div>
                            <h4 className="mb-2 font-semibold text-[#a8d4f0]">價格限制：</h4>
                            <ul className="list-disc pl-6 text-white space-y-1">
                                <li>預設漲跌限制為 <strong>{marketData.loading ? '...' : marketData.tradingLimit}%</strong>（{marketData.loading ? '...' : marketData.tradingLimit * 100} basis points）</li>
                                <li>基準價格基於最近成交價格計算</li>
                                <li>超出限制的訂單會暫停，狀態變為 <span className="text-yellow-400">"pending_limit"</span></li>
                                <li>當價格回到允許範圍內時，訂單會自動重新啟用</li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="mb-2 font-semibold text-[#a8d4f0]">撮合頻率：</h4>
                            <ul className="list-disc pl-6 text-white space-y-1">
                                <li>自動撮合：每 60 秒執行一次</li>
                                <li>觸發撮合：下單後立即嘗試撮合</li>
                                <li>管理員可手動觸發撮合</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🏆 排行榜怎麼算？
                </h2>
                <p className="mb-4 text-white">
                    想知道你現在是營隊的投資之神嗎？排行榜幫你算清楚！
                </p>

                <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                    排行榜會顯示兩種資產總值：
                </h3>
                <div className="mb-8 overflow-x-auto">
                    <table className="w-full overflow-hidden">
                        <thead className="border-b border-[#82bee2] [&>tr>th]:bg-[#19325e] [&>tr>th:not(:last-child)]:border-r [&>tr>th:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <th className="rounded-tl-xl px-4 py-2 text-left text-[#82bee2]">
                                    類型
                                </th>
                                <th className="rounded-tr-xl px-4 py-2 text-left text-[#82bee2]">
                                    說明
                                </th>
                            </tr>
                        </thead>
                        <tbody className="[&>tr:not(:last-child)>td]:border-b [&>tr:not(:last-child)>td]:border-[#82bee2] [&>tr>td]:bg-[#1a2e4a] [&>tr>td:not(:last-child)]:border-r [&>tr>td:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    評價資產
                                </td>
                                <td className="px-4 py-2 text-white">
                                    總餘額（可用點數+圈存金額）+ 股票市值（用當下價格估算）
                                </td>
                            </tr>
                            <tr>
                                <td className="rounded-bl-xl px-4 py-2 text-white">
                                    現金資產
                                </td>
                                <td className="rounded-br-xl px-4 py-2 text-white">
                                    只看總餘額（可用點數+圈存金額，未賣股票不算）
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🧠 常見問題（FAQ）
                </h2>

                <div className="space-y-6">
                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 如果我買不到怎麼辦？
                        </h3>
                        <p className="text-white">
                            可能的原因：價格太低、市場無賣單且 IPO 售完，或流動性不足。請改用市價單或調整掛單價格。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 股票價格怎麼決定？
                        </h3>
                        <p className="text-white">看你要賣多少錢。</p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 如果今天沒人跟我成交，怎麼辦？
                        </h3>
                        <p className="text-white">
                            掛著等，或是取消再下其他價格。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 股票有分紅嗎？
                        </h3>
                        <p className="text-white">沒有。</p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 我可以轉點數給別人嗎？
                        </h3>
                        <p className="text-white">
                            可以。使用 /transfer 指令，會抽取 {marketData.loading ? '...' : marketData.transferFeeRate}%
                            手續費（最低 {marketData.loading ? '...' : marketData.transferMinFee} 點）。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 如果掛單之後我沒點數了怎麼辦？
                        </h3>
                        <p className="text-white">會自動取消。</p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 即時股價如何計算？
                        </h3>
                        <p className="text-white">
                            顯示價格為最新成交價，平均價格為最近 5 筆成交的平均值。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓
                            我只要開一個很高的單是不是股價就上去了？
                        </h3>
                        <p className="text-white">
                            對。但前提是有人要買。
                        </p>
                        <p className="text-white">
                            如果你持有的股票很多的話確實容易控制股價。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 什麼是 IPO？
                        </h3>
                        <p className="text-white">
                            IPO 是系統初次公開發行，當市場沒有賣單時，市價買單會自動從 IPO 以 {marketData.loading ? '...' : marketData.ipoPrice} 點/股購買。
                        </p>
                        <p className="text-white">
                            <span className="text-yellow-400">注意：</span>IPO 股數有限，售完後只能透過限價單與其他玩家交易。
                        </p>
                        {!marketData.loading && marketData.ipoSharesRemaining !== null && (
                            <p className="text-white">
                                <span className="text-blue-400">目前 IPO 剩餘：</span>{marketData.ipoSharesRemaining.toLocaleString()} 股
                            </p>
                        )}
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 為什麼我的訂單沒有立即成交？
                        </h3>
                        <p className="text-white">
                            可能原因：
                        </p>
                        <ul className="list-disc pl-6 text-white">
                            <li>限價單價格不符合市場條件</li>
                            <li>訂單超出漲跌限制被暫停（狀態：pending_limit）</li>
                            <li>市場流動性不足</li>
                            <li>系統正在等待下次撮合週期（最長 60 秒）</li>
                        </ul>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 什麼是部分成交？
                        </h3>
                        <p className="text-white">
                            當你的訂單數量大於市場可供應量時，會發生部分成交。
                        </p>
                        <p className="text-white">
                            例如：你想買 100 股，但市場只有 60 股可賣，你會先買到 60 股，剩下 40 股繼續掛單等待。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 如何取消掛單？
                        </h3>
                        <p className="text-white">
                            使用 Telegram Bot 的取消功能，或透過 /stock 指令查看並取消待成交的訂單。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 什麼是圈存？為什麼我的點數變少了？
                        </h3>
                        <p className="text-white mb-2">
                            圈存是資金預留機制，當你下單、轉帳或參與 PvP 時，系統會先「圈存」相應金額，確保交易安全。
                        </p>
                        <p className="text-white mb-2">
                            你的總資產沒有減少，只是分為「可用點數」和「圈存金額」兩部分：
                        </p>
                        <ul className="list-disc pl-6 text-white space-y-1">
                            <li><span className="text-green-400">可用點數</span>：可以立即使用的資金</li>
                            <li><span className="text-yellow-400">圈存金額</span>：已預留給進行中交易的資金</li>
                            <li>交易完成後會自動扣除圈存，取消時會退回可用餘額</li>
                        </ul>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 圈存的錢什麼時候會退回？
                        </h3>
                        <p className="text-white">
                            圈存會在以下情況自動處理：
                        </p>
                        <ul className="list-disc pl-6 text-white space-y-1">
                            <li><strong>交易成交</strong>：圈存金額轉為實際消費，多餘部分退回</li>
                            <li><strong>訂單取消</strong>：全額退回到可用餘額</li>
                            <li><strong>PvP 完成</strong>：根據結果扣除或退回</li>
                            <li><strong>轉帳完成</strong>：扣除實際轉帳金額和手續費</li>
                        </ul>
                    </div>
                </div>

                {/* <div className="mt-8 overflow-hidden rounded-xl bg-[#1a2e4a] p-3">
                    <blockquote className="text-center text-lg text-[#82bee2] italic">
                        最大的秘密，就是票多的贏、票少的輸。 -韓國瑜
                    </blockquote>
                </div> */}
            </div>
        </div>
    );
}
