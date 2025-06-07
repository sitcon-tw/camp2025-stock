'use client';

import { useState, useEffect } from 'react';
import { apiService } from '@/services/apiService';
import { getAnnouncements } from '@/lib/api';

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
                const [marketData, announcementData] = await Promise.all([
                    apiService.getMarketData(),
                    getAnnouncements(10)
                ]);

                if (isMounted) {
                    setMarketStatus(marketData);
                    setAnnouncements(announcementData || []);
                }
            } catch (error) {
                console.error('獲取資料失敗:', error);
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

    const handleCloseModal = () => {
        setIsModalClosing(true);
        setTimeout(() => {
            setIsModalOpen(false);
            setIsModalClosing(false);
        }, 200); // Match animation duration
    };

    const latestAnnouncement = announcements.length > 0 ? announcements[0] : null;

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="min-h-screen bg-[#101f3e] overflow-hidden">
            <div className="flex flex-col items-center h-screen">
                <h1 className="text-4xl font-bold text-[#7BC2E6] mt-14 text-center">SITCON Camp<br />點數系統</h1>

                <div className="bg-[#1A325F] p-6 rounded-xl mt-10 w-[90%]">
                    <div className="flex justify-between items-center mb-3">
                        <div className="w-20"></div>
                        <h2 className="text-2xl font-semibold text-[#AFE1F5] text-center">公告</h2>
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="bg-[#7BC2E6] text-[#101f3e] px-3 py-1 rounded-lg text-sm font-medium hover:bg-[#AFE1F5] transition-colors w-20"
                        >
                            全部
                        </button>
                    </div>
                    {loading ? (
                        <div className="text-[#AFE1F5] text-center">載入中...</div>
                    ) : latestAnnouncement ? (
                        <div>
                            <h3 className="text-lg font-semibold text-[#7BC2E6] mb-2">{latestAnnouncement.title}</h3>
                            <p className="text-[#AFE1F5] text-md mb-2">{latestAnnouncement.message}</p>
                            <p className="text-[#AFE1F5] text-sm opacity-70">{formatDate(latestAnnouncement.createdAt)}</p>
                        </div>
                    ) : (
                        <p className="text-[#AFE1F5] text-md">暫無公告</p>
                    )}
                </div>

                <div className="bg-[#1A325F] p-6 rounded-xl mt-10 w-[90%]">
                    <h3 className="text-2xl font-semibold text-[#AFE1F5] mb-4 text-center">關閉交易時間</h3>
                    {loading ? (
                        <div className="text-[#AFE1F5] text-center">載入中...</div>
                    ) : (<div className="space-y-1 text-[#AFE1F5] text-lg font-bold text-center">
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

            {/* Modal */}
            {isModalOpen && (
                <div
                    className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 ${isModalClosing ? 'animate-modal-close-bg' : 'animate-modal-open-bg'}`}
                    onClick={handleCloseModal}
                >
                    <div
                        className={`bg-[#1A325F] rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col ${isModalClosing ? 'animate-modal-close' : 'animate-modal-open'}`}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-2xl font-semibold text-[#AFE1F5]">所有公告</h2>
                            <button
                                onClick={handleCloseModal}
                                className="text-[#AFE1F5] hover:text-[#7BC2E6] text-2xl font-bold"
                            >
                                ×
                            </button>
                        </div>

                        <div className="overflow-y-auto flex-1">
                            {announcements.length > 0 ? (
                                <div className="space-y-4">
                                    {announcements.map((announcement) => (
                                        <div key={announcement.id} className="border-b border-[#2A4A7F] pb-4 last:border-b-0">
                                            <h3 className="text-lg font-semibold text-[#7BC2E6] mb-2">{announcement.title}</h3>
                                            <p className="text-[#AFE1F5] mb-2">{announcement.message}</p>
                                            <p className="text-[#AFE1F5] text-sm opacity-70">{formatDate(announcement.createdAt)}</p>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-[#AFE1F5] text-center">暫無公告</p>
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
                    }
                    to {
                        opacity: 1;
                    }
                }
                
                @keyframes modal-close-bg {
                    from {
                        opacity: 1;
                    }
                    to {
                        opacity: 0;
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