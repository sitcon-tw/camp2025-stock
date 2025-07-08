"use client";

import botAvatar from "@/assets/uwu.svg";
import { Modal } from "@/components/ui";
import { TradingHoursVisualizer } from "@/components/trading";
import useModal from "@/hooks/useModal";
import { getAnnouncements, getTradingHours } from "@/lib/api";
import { apiService } from "@/services/apiService";
import Image from "next/image";
import { useEffect, useState } from "react";

export default function Home() {
    const [marketStatus, setMarketStatus] = useState(null);
    const [announcements, setAnnouncements] = useState([]);
    const [tradingHours, setTradingHours] = useState(null);
    const [loading, setLoading] = useState(true);

    const announcementModal = useModal();

    useEffect(() => {
        let isMounted = true;
        const fetchData = async () => {
            if (!isMounted) return;

            try {
                const [marketData, announcementData, tradingHoursData] =
                    await Promise.all([
                        apiService.getMarketData(),
                        getAnnouncements(10),
                        getTradingHours(),
                    ]);

                if (isMounted) {
                    setMarketStatus(marketData);
                    setAnnouncements(announcementData || []);
                    setTradingHours(tradingHoursData || null);
                }
            } catch (error) {
                console.error("獲取資料失敗:", error);
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        fetchData();

        return () => {
            isMounted = false;
        };
    }, []);

    const getClosedTradingTimes = () => {
        if (
            !marketStatus?.openTime ||
            marketStatus.openTime.length === 0
        ) {
            return [{ start: "00:00", end: "23:59" }];
        }

        const closedTimes = [];

        // 將時間戳轉換為今天的時間
        const openTimes = marketStatus.openTime
            .map((slot) => {
                const startDate = new Date(slot.start * 1000);
                const endDate = new Date(slot.end * 1000);
                return {
                    start: startDate.toTimeString().slice(0, 5),
                    end: endDate.toTimeString().slice(0, 5),
                    startDate,
                    endDate,
                };
            })
            .filter((slot) => {
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                const tomorrow = new Date(today);
                tomorrow.setDate(tomorrow.getDate() + 1);

                return (
                    slot.startDate >= today &&
                    slot.startDate < tomorrow
                );
            })
            .sort((a, b) => a.start.localeCompare(b.start));

        if (openTimes.length === 0) {
            return [{ start: "00:00", end: "23:59" }];
        }

        if (openTimes[0].start !== "00:00") {
            closedTimes.push({
                start: "00:00",
                end: openTimes[0].start,
            });
        }

        for (let i = 0; i < openTimes.length - 1; i++) {
            if (openTimes[i].end !== openTimes[i + 1].start) {
                closedTimes.push({
                    start: openTimes[i].end,
                    end: openTimes[i + 1].start,
                });
            }
        }

        const lastOpenTime = openTimes[openTimes.length - 1];
        if (lastOpenTime.end !== "23:59") {
            closedTimes.push({
                start: lastOpenTime.end,
                end: "23:59",
            });
        }

        return closedTimes.slice(0, 5);
    };

    const latestAnnouncement =
        announcements.length > 0 ? announcements[0] : null;

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleString("zh-TW", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    return (
        <div className="flex min-h-dvh place-items-center justify-center overflow-hidden bg-[#101f3e] py-8 px-8 pb-20">
            <div className="flex flex-col items-center">
                <Image
                    src={botAvatar}
                    alt="喵券機頭貼"
                    className="mb-6 aspect-auto h-30 bg-transparent"
                />
                <h1 className="text-center text-4xl font-bold text-[#7BC2E6]">
                    SITCON Camp 喵券機
                </h1>

                <div className="mt-10 w-[95%] max-w-lg rounded-xl bg-[#1A325F] p-6">
                    <div className="mb-3 flex items-center justify-between">
                        <div className="w-20"></div>
                        <h2 className="text-center text-2xl font-semibold text-[#AFE1F5]">
                            公告
                        </h2>
                        <button
                            onClick={announcementModal.openModal}
                            className="w-20 rounded-lg bg-[#7BC2E6] px-3 py-1 text-sm font-medium text-[#101f3e] transition-colors hover:bg-[#AFE1F5]"
                        >
                            全部
                        </button>
                    </div>
                    {loading ? (
                        <div>
                            <div className="h-24 w-full animate-pulse rounded bg-[#7BC2E6]/50"></div>
                        </div>
                    ) : latestAnnouncement ? (
                        <div>
                            <h3 className="mb-2 text-lg font-semibold text-[#7BC2E6]">
                                {latestAnnouncement.title}
                            </h3>
                            <p className="text-md mb-2 text-[#AFE1F5]">
                                {latestAnnouncement.message}
                            </p>
                            <p className="text-sm text-[#AFE1F5] opacity-70">
                                {formatDate(
                                    latestAnnouncement.createdAt,
                                )}
                            </p>
                        </div>
                    ) : (
                        <p className="text-md text-[#AFE1F5]">
                            暫無公告
                        </p>
                    )}
                </div>

                {/* 交易時間可視化 */}
                <div className="mt-10 w-[95%] max-w-lg rounded-xl bg-[#1A325F] p-6">
                    <h3 className="mb-4 text-center text-2xl font-semibold text-[#AFE1F5]">
                        交易時間概覽
                    </h3>
                    {loading ? (
                        <div className="animate-pulse">
                            <div className="h-8 w-full rounded bg-[#7BC2E6]/50 mb-2"></div>
                            <div className="h-20 w-full rounded bg-[#7BC2E6]/30"></div>
                        </div>
                    ) : (
                        <TradingHoursVisualizer tradingHours={tradingHours} />
                    )}
                </div>

                <div className="mt-10 w-[95%] max-w-lg rounded-xl bg-[#1A325F] p-6">
                    <h3 className="mb-4 text-center text-2xl font-semibold text-[#AFE1F5]">
                        關閉交易時間
                    </h3>
                    {loading ? (
                        <div>
                            <div className="h-8 w-full animate-pulse rounded bg-[#7BC2E6]/50"></div>
                        </div>
                    ) : (
                        <div className="space-y-1 text-center text-lg font-bold text-[#AFE1F5]">
                            {getClosedTradingTimes().length > 0 ? (
                                getClosedTradingTimes().map(
                                    (timeSlot, index) => (
                                        <p key={index}>
                                            {timeSlot.start} ~{" "}
                                            {timeSlot.end}
                                        </p>
                                    ),
                                )
                            ) : (
                                <p>今日無關閉交易時間</p>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* 公告 Modal */}
            <Modal
                isOpen={announcementModal.isOpen}
                isClosing={announcementModal.isClosing}
                onClose={announcementModal.closeModal}
                title="所有公告"
                size="2xl"
            >
                {announcements.length > 0 ? (
                    <div className="space-y-4">
                        {announcements.map((announcement) => (
                            <div
                                key={announcement.id}
                                className="border-b border-[#2A4A7F] pb-4 last:border-b-0"
                            >
                                <h3 className="mb-2 text-lg font-semibold text-[#7BC2E6]">
                                    {announcement.title}
                                </h3>
                                <p className="mb-2 text-[#AFE1F5]">
                                    {announcement.message}
                                </p>
                                <p className="text-sm text-[#AFE1F5] opacity-70">
                                    {formatDate(
                                        announcement.createdAt,
                                    )}
                                </p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-center text-[#AFE1F5]">
                        暫無公告
                    </p>
                )}
            </Modal>
        </div>
    );
}
