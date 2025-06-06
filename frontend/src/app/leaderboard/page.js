'use client';

import React, { useState, useEffect } from 'react';
import { apiService } from '@/services/apiService';

function RankingItemSkeleton() {
    return (
        <div className="bg-[#1A325F] flex w-11/12 h-14 rounded-2xl py-1 px-2 items-center transition-all duration-300 animate-pulse"></div>
    );
}

function RankingListSkeleton({ title }) {
    return (
        <div className="mb-8">
            <h2 className="text-2xl font-bold text-[#82bee2] mb-4 ml-5">
                {title}
            </h2>
            <div className="flex gap-4 flex-col items-center">
                {[...Array(5)].map((_, index) => (
                    <RankingItemSkeleton key={index} />
                ))}
            </div>
        </div>
    );
}

function RankingItem({ rank, user, isGroup = false }) {
    const getRankIcon = (rank) => {
        return `${rank}.`
    };

    return (
        <div className="bg-[#1A325F] flex w-11/12 rounded-2xl py-1 px-2 items-center transition-all duration-300">
            <div className="flex items-center justify-center w-12 h-12 mr-4">
                <span className="text-[#AFE1F5] font-bold text-lg">
                    {getRankIcon(rank)}
                </span>
            </div>

            <div className="flex-1">
                <h3 className="text-lg font-semibold text-[#AFE1F5]">
                    {isGroup ? user.teamName : user.username}
                </h3>
            </div>
        </div>
    );
}

function RankingList({ title, items, isGroup = false }) {
    return (
        <div className="mb-8">
            <h2 className="text-2xl font-bold text-[#82bee2] mb-4 ml-5">
                {title}
            </h2>
            <div className="flex gap-4 flex-col items-center">
                {items.length > 0 ? (
                    items.map((item, index) => (
                        <RankingItem
                            key={isGroup ? `${item.teamName}-${index}` : `${item.username}-${index}`}
                            rank={index + 1}
                            user={item}
                            isGroup={isGroup}
                        />
                    ))) : (
                    <div className="text-center text-gray-400 py-8">
                        <div>無法取得{isGroup ? '組別' : '個人'}資料</div>
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
            setLeaderboardData(data);

            const groupData = processGroupLeaderboard(data);
            setGroupLeaderboard(groupData);
        } catch (error) {
            console.error('獲取排行榜失敗:', error);
            setError(error.message);

            setLeaderboardData([]);
            setGroupLeaderboard([]);
        } finally {
            setLoading(false);
        }
    };

    const processGroupLeaderboard = (individualData) => {
        const teamMap = new Map();

        individualData.forEach(user => {
            const teamName = user.team || '未分組';
            if (!teamMap.has(teamName)) {
                teamMap.set(teamName, {
                    teamName,
                    members: [],
                    totalPoints: 0,
                    totalStockValue: 0,
                    memberCount: 0
                });
            }

            const team = teamMap.get(teamName);
            team.members.push(user);
            team.totalPoints += user.points;
            team.totalStockValue += user.stockValue || 0;
            team.memberCount++;
        });

        return Array.from(teamMap.values())
            .map(team => ({
                ...team,
                totalValue: team.totalPoints + team.totalStockValue
            }))
            .sort((a, b) => b.totalValue - a.totalValue);
    };

    const refreshData = () => {
        fetchLeaderboard();
    }; useEffect(() => {
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
        <div className="bg-[#0f203e] min-h-screen pb-24">
            <div className="px-4 md:px-8 pt-8">
                <div className="text-center mb-6">
                    <h1 className="text-3xl font-bold text-[#82bee2] mb-2">
                        排行榜
                    </h1>
                </div>

                {error && (
                    <div className="bg-red-500/20 rounded-2xl p-4 mb-6 text-center">
                        <div className="text-red-400 mb-2">資料載入失敗</div>
                        <div className="text-sm text-gray-400">無法連線到伺服器，請重新整理頁面</div>
                    </div>
                )}

                <div className="max-w-6xl mx-auto">
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