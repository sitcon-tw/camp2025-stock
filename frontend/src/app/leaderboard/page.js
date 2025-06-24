"use client";

import { apiService } from "@/services/apiService";
import { useEffect, useState } from "react";

function RankingItemSkeleton() {
    return (
        <div className="flex h-18 w-11/12 animate-pulse items-center rounded-2xl bg-[#1A325F] px-2 py-1 transition-all duration-300"></div>
    );
}

function RankingListSkeleton({ title }) {
    return (
        <div className="mb-8">
            <h2 className="mb-4 ml-5 text-2xl font-bold text-[#82bee2]">
                {title}
            </h2>
            <div className="flex flex-col items-center gap-4">
                {[...Array(5)].map((_, index) => (
                    <RankingItemSkeleton key={index} />
                ))}
            </div>
        </div>
    );
}

function RankingItem({ rank, user, isGroup = false }) {
    const getRankIcon = (rank) => {
        return `${rank}.`;
    };

    const formatNumber = (num) => {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + "M";
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + "K";
        }
        return num.toLocaleString();
    };

    return (
        <div className="flex w-11/12 items-center rounded-2xl bg-[#1A325F] px-4 py-3 transition-all duration-300">
            <div className="flex h-12 w-12 items-center justify-center">
                <span className="text-lg font-bold text-[#AFE1F5]">
                    {getRankIcon(rank)}
                </span>
            </div>

            <div className="ml-3 flex-1">
                <h3 className="mb-1 text-lg font-semibold text-[#AFE1F5]">
                    {isGroup ? user.teamName : user.username}
                </h3>
                {isGroup ? (
                    <div className="text-sm text-gray-300">
                        <div className="text-xs text-gray-400">
                            成員數: {user.memberCount || 0}
                        </div>
                    </div>
                ) : (
                    <div className="text-sm text-gray-300">
                        <div>
                            點數: {formatNumber(user.points || 0)}
                        </div>
                        <div>
                            股票價值:{" "}
                            {formatNumber(user.stockValue || 0)}
                        </div>
                    </div>
                )}
            </div>

            <div className="text-right">
                <div className="text-lg font-bold text-[#82bee2]">
                    {isGroup
                        ? formatNumber(user.totalValue || 0)
                        : formatNumber(
                              (user.points || 0) +
                                  (user.stockValue || 0),
                          )}
                </div>
                <div className="text-xs text-gray-400">
                    {isGroup ? "總價值" : "總資產"}
                </div>
            </div>
        </div>
    );
}

function RankingList({ title, items, isGroup = false }) {
    return (
        <div className="mb-8">
            <h2 className="mb-4 ml-5 text-2xl font-bold text-[#82bee2]">
                {title}
            </h2>
            <div className="flex flex-col items-center gap-4">
                {items.length > 0 ? (
                    items.map((item, index) => (
                        <RankingItem
                            key={
                                isGroup
                                    ? `${item.teamName}-${index}`
                                    : `${item.username}-${index}`
                            }
                            rank={index + 1}
                            user={item}
                            isGroup={isGroup}
                        />
                    ))
                ) : (
                    <div className="py-8 text-center text-gray-400">
                        <div>
                            無法取得{isGroup ? "組別" : "個人"}資料
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function Leaderboard() {
    const [leaderboardData, setLeaderboardData] = useState([]);
    const [groupLeaderboard, setGroupLeaderboard] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchLeaderboard = async () => {
        try {
            setLoading(true);
            setError(null);

            const data = await apiService.getLeaderboardData();

            // 對個人資料按總資產排序
            const sortedData = data
                .map((user) => ({
                    ...user,
                    totalAssets:
                        (user.points || 0) + (user.stockValue || 0),
                }))
                .sort((a, b) => b.totalAssets - a.totalAssets);

            setLeaderboardData(sortedData);

            const groupData = processGroupLeaderboard(sortedData);
            setGroupLeaderboard(groupData);
        } catch (error) {
            console.error("獲取排行榜失敗:", error);
            setError(error.message);

            setLeaderboardData([]);
            setGroupLeaderboard([]);
        } finally {
            setLoading(false);
        }
    };

    const processGroupLeaderboard = (individualData) => {
        const teamMap = new Map();

        individualData.forEach((user) => {
            const teamName = user.team || "未分組";
            if (!teamMap.has(teamName)) {
                teamMap.set(teamName, {
                    teamName,
                    members: [],
                    totalPoints: 0,
                    totalStockValue: 0,
                    memberCount: 0,
                });
            }

            const team = teamMap.get(teamName);
            team.members.push(user);
            team.totalPoints += user.points;
            team.totalStockValue += user.stockValue || 0;
            team.memberCount++;
        });

        return Array.from(teamMap.values())
            .map((team) => ({
                ...team,
                totalValue: team.totalPoints + team.totalStockValue,
            }))
            .sort((a, b) => b.totalValue - a.totalValue);
    };

    const refreshData = () => {
        fetchLeaderboard();
    };
    useEffect(() => {
        let isMounted = true;

        const fetchInitialData = async () => {
            if (isMounted) {
                await fetchLeaderboard();
            }
        };

        fetchInitialData();

        return () => {
            isMounted = false;
        };
    }, []);

    return (
        <div className="min-h-screen bg-[#0f203e] pb-24">
            <div className="px-4 pt-8 md:px-8">
                <div className="mb-6 text-center">
                    <h1 className="mb-2 text-3xl font-bold text-[#82bee2]">
                        排行榜
                    </h1>
                </div>

                {error && (
                    <div className="mb-6 rounded-2xl bg-red-500/20 p-4 text-center">
                        <div className="mb-2 text-red-400">
                            資料載入失敗
                        </div>
                        <div className="text-sm text-gray-400">
                            無法連線到伺服器，請重新整理頁面
                        </div>
                    </div>
                )}

                <div className="mx-auto max-w-4xl">
                    {loading ? (
                        <>
                            <RankingListSkeleton title="組排行" />
                            <RankingListSkeleton title="個人排行" />
                        </>
                    ) : (
                        <>
                            <RankingList
                                title="組排行"
                                items={groupLeaderboard}
                                isGroup={true}
                            />

                            <RankingList
                                title="個人排行"
                                items={leaderboardData}
                            />
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
