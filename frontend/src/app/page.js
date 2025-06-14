"use client";

import { getAnnouncements } from "@/lib/api";
import { apiService } from "@/services/apiService";
import { useEffect, useState } from "react";
import { twMerge } from "tailwind-merge";

export default function Home() {
    const [marketStatus, setMarketStatus] = useState(null);
    const [announcements, setAnnouncements] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isModalClosing, setIsModalClosing] = useState(false);

    useEffect(() => {
        let isMounted = true;
        const fetchData = async () => {
            if (!isMounted) return;

            try {
                const [marketData, announcementData] =
                    await Promise.all([
                        apiService.getMarketData(),
                        getAnnouncements(10),
                    ]);

                if (isMounted) {
                    setMarketStatus(marketData);
                    setAnnouncements(announcementData || []);
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

        const now = new Date();
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

    const handleCloseModal = () => {
        setIsModalClosing(true);
        setTimeout(() => {
            setIsModalOpen(false);
            setIsModalClosing(false);
        }, 200); // Match animation duration
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
        <div className="min-h-screen overflow-hidden bg-[#101f3e]">
            <div className="flex h-screen flex-col items-center">
                <h1 className="mt-14 text-center text-4xl font-bold text-[#7BC2E6]">
                    SITCON Camp
                    <br />
                    點數系統
                </h1>

                <div className="mt-10 w-[90%] rounded-xl bg-[#1A325F] p-6">
                    <div className="mb-3 flex items-center justify-between">
                        <div className="w-20"></div>
                        <h2 className="text-center text-2xl font-semibold text-[#AFE1F5]">
                            公告
                        </h2>
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="w-20 rounded-lg bg-[#7BC2E6] px-3 py-1 text-sm font-medium text-[#101f3e] transition-colors hover:bg-[#AFE1F5]"
                        >
                            全部
                        </button>
                    </div>
                    {loading ? (
                        <div className="text-center text-[#AFE1F5]">
                            載入中...
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

                <div className="mt-10 w-[90%] rounded-xl bg-[#1A325F] p-6">
                    <h3 className="mb-4 text-center text-2xl font-semibold text-[#AFE1F5]">
                        關閉交易時間
                    </h3>
                    {loading ? (
                        <div className="text-center text-[#AFE1F5]">
                            載入中...
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

            {/* Modal */}
            {isModalOpen && (
                <div
                    className={twMerge(
                        "fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs",
                        isModalClosing
                            ? "animate-modal-close-bg"
                            : "animate-modal-open-bg",
                    )}
                    onClick={handleCloseModal}
                >
                    <div
                        className={twMerge(
                            "flex max-h-[80vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl bg-[#1A325F] p-6",
                            isModalClosing
                                ? "animate-modal-close"
                                : "animate-modal-open",
                        )}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="mb-4 flex items-center justify-between">
                            <h2 className="text-2xl font-semibold text-[#AFE1F5]">
                                所有公告
                            </h2>
                            <button
                                onClick={handleCloseModal}
                                className="text-2xl font-bold text-[#AFE1F5] hover:text-[#7BC2E6]"
                            >
                                ×
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto">
                            {announcements.length > 0 ? (
                                <div className="space-y-4">
                                    {announcements.map(
                                        (announcement) => (
                                            <div
                                                key={announcement.id}
                                                className="border-b border-[#2A4A7F] pb-4 last:border-b-0"
                                            >
                                                <h3 className="mb-2 text-lg font-semibold text-[#7BC2E6]">
                                                    {
                                                        announcement.title
                                                    }
                                                </h3>
                                                <p className="mb-2 text-[#AFE1F5]">
                                                    {
                                                        announcement.message
                                                    }
                                                </p>
                                                <p className="text-sm text-[#AFE1F5] opacity-70">
                                                    {formatDate(
                                                        announcement.createdAt,
                                                    )}
                                                </p>
                                            </div>
                                        ),
                                    )}
                                </div>
                            ) : (
                                <p className="text-center text-[#AFE1F5]">
                                    暫無公告
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            )}

            <style jsx global>{`
                @keyframes modal-open {
                    from {
                        opacity: 0;
                        transform: scale(0.95);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1);
                    }
                }

                @keyframes modal-close {
                    from {
                        opacity: 1;
                        transform: scale(1);
                    }
                    to {
                        opacity: 0;
                        transform: scale(0.95);
                    }
                }

                @keyframes modal-open-bg {
                    from {
                        opacity: 0;
                        backdrop-filter: blur(0px);
                    }
                    to {
                        opacity: 1;
                        backdrop-filter: blur(4px);
                    }
                }

                @keyframes modal-close-bg {
                    from {
                        opacity: 1;
                        backdrop-filter: blur(4px);
                    }
                    to {
                        opacity: 0;
                        backdrop-filter: blur(0px);
                    }
                }

                .animate-modal-open {
                    animation: modal-open 0.2s ease-out;
                }

                .animate-modal-close {
                    animation: modal-close 0.2s ease-in;
                }

                .animate-modal-open-bg {
                    animation: modal-open-bg 0.2s ease-out;
                }

                .animate-modal-close-bg {
                    animation: modal-close-bg 0.2s ease-in;
                }
            `}</style>
        </div>
    );
}
