'use client';

import { useState, useEffect } from 'react';
import { getMarketStatus } from '@/lib/api';

export default function Home() {
    const [marketStatus, setMarketStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMarketStatus = async () => {
            try {
                const data = await getMarketStatus();
                setMarketStatus(data);
            } catch (error) {
                console.error('獲取市場狀態失敗:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchMarketStatus();

        const interval = setInterval(fetchMarketStatus, 60000);

        return () => clearInterval(interval);
    }, []);
    const getClosedTradingTimes = () => {
        if (!marketStatus?.openTime || marketStatus.openTime.length === 0) {
            return [{ start: '00:00', end: '23:59' }];
        }

        const now = new Date();
        const closedTimes = [];

        // 將時間戳轉換為今天的時間
        const openTimes = marketStatus.openTime
            .map(slot => {
                const startDate = new Date(slot.start * 1000);
                const endDate = new Date(slot.end * 1000);
                return {
                    start: startDate.toTimeString().slice(0, 5),
                    end: endDate.toTimeString().slice(0, 5),
                    startDate,
                    endDate
                };
            })
            .filter(slot => {
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                const tomorrow = new Date(today);
                tomorrow.setDate(tomorrow.getDate() + 1);

                return slot.startDate >= today && slot.startDate < tomorrow;
            })
            .sort((a, b) => a.start.localeCompare(b.start));

        if (openTimes.length === 0) {
            return [{ start: '00:00', end: '23:59' }];
        }

        if (openTimes[0].start !== '00:00') {
            closedTimes.push({
                start: '00:00',
                end: openTimes[0].start
            });
        }

        for (let i = 0; i < openTimes.length - 1; i++) {
            if (openTimes[i].end !== openTimes[i + 1].start) {
                closedTimes.push({
                    start: openTimes[i].end,
                    end: openTimes[i + 1].start
                });
            }
        }

        const lastOpenTime = openTimes[openTimes.length - 1];
        if (lastOpenTime.end !== '23:59') {
            closedTimes.push({
                start: lastOpenTime.end,
                end: '23:59'
            });
        }

        return closedTimes.slice(0, 5);
    };
    return (
        <div className="min-h-screen bg-[#101f3e] overflow-hidden">
            <div className="flex flex-col items-center h-screen">
                <h1 className="text-4xl font-bold text-[#7BC2E6] mt-14 text-center">SITCON Camp<br />點數系統</h1>

                <div className="bg-[#1A325F] p-6 rounded-xl mt-10 w-[90%]">
                    <h2 className="text-2xl font-semibold text-[#AFE1F5] mb-3 text-center">公告</h2>
                    <p className="text-[#AFE1F5] text-md">
                        別墅裡面唱k，水池裡面銀龍魚。我送阿叔茶具，他研墨下筆直接給我四個字，大展鴻圖。
                    </p>
                </div>
                <div className="bg-[#1A325F] p-6 rounded-xl mt-10 w-[90%]">
                    <h3 className="text-2xl font-semibold text-[#AFE1F5] mb-4 text-center">關閉交易時間</h3>
                    {loading ? (
                        <div className="text-[#AFE1F5] text-center">載入中...</div>
                    ) : (<div className="space-y-1 text-[#AFE1F5] text-lg font-bold">
                        {getClosedTradingTimes().length > 0 ? (
                            getClosedTradingTimes().map((timeSlot, index) => (
                                <p key={index}>
                                    {timeSlot.start} ~ {timeSlot.end}
                                </p>
                            ))
                        ) : (
                            <p>今日無關閉交易時間</p>
                        )}
                    </div>
                    )}
                </div>
            </div>
        </div>
    );
}