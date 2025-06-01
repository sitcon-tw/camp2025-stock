'use client';

import React, { useState, useEffect } from 'react';

// 排行榜項目組件
function RankingItem({ rank, user, isGroup = false }) {
    const totalValue = user.points + (user.stockValue || 0);
    const getRankIcon = (rank) => {
        switch (rank) {
            case 1: return '🥇';
            case 2: return '🥈';
            case 3: return '🥉';
            default: return `${rank}.`;
        }
    };

    const formatValue = (value) => {
        if (value >= 10000) {
            return `${(value / 10000).toFixed(1)}萬`;
        }
        return value.toLocaleString();
    };

    return (
        <div className={`bg-gradient-to-r ${
            rank <= 3 
                ? 'from-[#1a2e4a] to-[#2a4e6a] border-[#82bee2]/30' 
                : 'from-[#19325e] to-[#1a2e4a] border-[#82bee2]/20'
        } flex w-full max-w-4xl rounded-xl p-4 items-center border transition-all duration-300 hover:border-[#82bee2]/50 hover:shadow-lg`}>
            <div className="flex items-center justify-center w-12 h-12 mr-4">
                <span className={`${rank <= 3 ? 'text-2xl' : 'text-[#82bee2] font-bold text-lg'}`}>
                    {getRankIcon(rank)}
                </span>
            </div>
            
            <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-semibold text-[#82bee2]">
                        {user.username}
                    </h3>
                    {!isGroup && user.team && (
                        <span className="bg-[#82bee2]/20 text-[#82bee2] px-2 py-1 rounded-full text-xs">
                            {user.team}
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span>點數: <span className="text-yellow-400">{formatValue(user.points)}</span></span>
                    <span>股票價值: <span className="text-green-400">{formatValue(user.stockValue || 0)}</span></span>
                    <span className="font-semibold">總價值: <span className="text-[#82bee2]">{formatValue(totalValue)}</span></span>
                </div>
            </div>
            
            <div className="text-right">
                <div className="text-xl font-bold text-[#82bee2]">
                    {formatValue(totalValue)}
                </div>
                <div className="text-xs text-gray-400">總資產</div>
            </div>
        </div>
    );
}

// 組排行組件
function GroupRankingItem({ rank, group }) {
    const getRankIcon = (rank) => {
        switch (rank) {
            case 1: return '🥇';
            case 2: return '🥈';
            case 3: return '🥉';
            default: return `${rank}.`;
        }
    };

    const formatValue = (value) => {
        if (value >= 10000) {
            return `${(value / 10000).toFixed(1)}萬`;
        }
        return value.toLocaleString();
    };

    return (
        <div className={`bg-gradient-to-r ${
            rank <= 3 
                ? 'from-[#1a2e4a] to-[#2a4e6a] border-[#82bee2]/30' 
                : 'from-[#19325e] to-[#1a2e4a] border-[#82bee2]/20'
        } flex w-full max-w-4xl rounded-xl p-4 items-center border transition-all duration-300 hover:border-[#82bee2]/50 hover:shadow-lg`}>
            <div className="flex items-center justify-center w-12 h-12 mr-4">
                <span className={`${rank <= 3 ? 'text-2xl' : 'text-[#82bee2] font-bold text-lg'}`}>
                    {getRankIcon(rank)}
                </span>
            </div>
            
            <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-semibold text-[#82bee2]">
                        {group.teamName}
                    </h3>
                    <span className="bg-[#82bee2]/20 text-[#82bee2] px-2 py-1 rounded-full text-xs">
                        {group.memberCount} 成員
                    </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span>總點數: <span className="text-yellow-400">{formatValue(group.totalPoints)}</span></span>
                    <span>股票價值: <span className="text-green-400">{formatValue(group.totalStockValue)}</span></span>
                    <span>平均: <span className="text-cyan-400">{formatValue(Math.round(group.totalValue / group.memberCount))}</span></span>
                </div>
            </div>
            
            <div className="text-right">
                <div className="text-xl font-bold text-[#82bee2]">
                    {formatValue(group.totalValue)}
                </div>
                <div className="text-xs text-gray-400">總資產</div>
            </div>
        </div>
    );
}

// 排行榜列表組件
function RankingList({ title, items, isGroup = false, loading = false }) {
    if (loading) {
        return (
            <div className="mb-8">
                <h2 className="text-xl font-bold text-[#82bee2] mb-4 text-center">
                    {title}
                </h2>
                <div className="flex flex-col gap-4 items-center">
                    {[...Array(5)].map((_, index) => (
                        <div key={index} className="bg-[#19325e] w-full max-w-4xl rounded-xl p-4 animate-pulse">
                            <div className="flex items-center">
                                <div className="w-12 h-12 bg-[#82bee2]/20 rounded mr-4"></div>
                                <div className="flex-1">
                                    <div className="h-4 bg-[#82bee2]/20 rounded mb-2 w-1/3"></div>
                                    <div className="h-3 bg-[#82bee2]/10 rounded w-2/3"></div>
                                </div>
                                <div className="w-16 h-6 bg-[#82bee2]/20 rounded"></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="mb-8">
            <h2 className="text-xl font-bold text-[#82bee2] mb-4 text-center">
                {title} ({items.length} {isGroup ? '組' : '人'})
            </h2>
            <div className="flex gap-4 flex-col items-center">
                {items.length > 0 ? (
                    items.map((item, index) => (
                        isGroup ? (
                            <GroupRankingItem
                                key={`${item.teamName}-${index}`}
                                rank={index + 1}
                                group={item}
                            />
                        ) : (
                            <RankingItem
                                key={`${item.username}-${index}`}
                                rank={index + 1}
                                user={item}
                            />
                        )
                    ))
                ) : (
                    <div className="text-center text-gray-400 py-8">
                        <div className="text-4xl mb-4">📊</div>
                        <div>目前還沒有{isGroup ? '組別' : '個人'}資料</div>
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
    const [activeTab, setActiveTab] = useState('individual'); // 'individual' or 'group'
    const [lastUpdated, setLastUpdated] = useState(new Date());

    // 獲取排行榜資料
    const fetchLeaderboard = async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/leaderboard`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setLeaderboardData(data);
            
            // 處理組別排行榜
            const groupData = processGroupLeaderboard(data);
            setGroupLeaderboard(groupData);
            
            setLastUpdated(new Date());
        } catch (error) {
            console.error('獲取排行榜失敗:', error);
            setError(error.message);
            
            // 如果 API 失敗，使用模擬資料
            const mockData = generateMockData();
            setLeaderboardData(mockData.individual);
            setGroupLeaderboard(mockData.group);
        } finally {
            setLoading(false);
        }
    };

    // 處理組別排行榜
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

    // 生成模擬資料（當 API 不可用時）
    const generateMockData = () => {
        const mockIndividual = [
            { username: '張小明', team: '第一組', points: 15000, stockValue: 8500 },
            { username: '李小華', team: '第二組', points: 14200, stockValue: 8800 },
            { username: '王小美', team: '第一組', points: 13800, stockValue: 8200 },
            { username: '陳小強', team: '第三組', points: 13500, stockValue: 7900 },
            { username: '林小雨', team: '第二組', points: 13200, stockValue: 7600 },
            { username: '黃小龍', team: '第三組', points: 12800, stockValue: 7200 },
            { username: '劉小芳', team: '第一組', points: 12500, stockValue: 6800 },
            { username: '趙小剛', team: '第二組', points: 12200, stockValue: 6500 },
        ];

        const mockGroup = [
            { teamName: '第一組', memberCount: 3, totalPoints: 41300, totalStockValue: 23500, totalValue: 64800 },
            { teamName: '第二組', memberCount: 3, totalPoints: 39600, totalStockValue: 22900, totalValue: 62500 },
            { teamName: '第三組', memberCount: 2, totalPoints: 26300, totalStockValue: 15100, totalValue: 41400 },
        ];

        return { individual: mockIndividual, group: mockGroup };
    };

    // 重新整理資料
    const refreshData = () => {
        fetchLeaderboard();
    };

    // 初始載入
    useEffect(() => {
        fetchLeaderboard();
        
        // 設置自動刷新（每30秒）
        const interval = setInterval(() => {
            fetchLeaderboard();
        }, 30000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="bg-[#0f203e] min-h-screen pb-24">
            <div className="px-4 md:px-8 pt-8">
                {/* 標題區域 */}
                <div className="text-center mb-6">
                    <h1 className="text-3xl font-bold text-[#82bee2] mb-2">
                        🏆 SITCON Camp 2025 排行榜
                    </h1>
                    <div className="flex items-center justify-center gap-4 text-sm text-gray-400">
                        <span>最後更新: {lastUpdated.toLocaleTimeString()}</span>
                        <button
                            onClick={refreshData}
                            disabled={loading}
                            className="flex items-center gap-1 text-[#82bee2] hover:text-white transition-colors disabled:opacity-50"
                        >
                            <span className={loading ? 'animate-spin' : ''}>🔄</span>
                            重新整理
                        </button>
                    </div>
                </div>

                {/* 分頁切換 */}
                <div className="flex justify-center mb-6">
                    <div className="bg-[#1a2e4a] rounded-lg p-1 flex">
                        <button
                            onClick={() => setActiveTab('individual')}
                            className={`px-6 py-2 rounded-md transition-all duration-300 ${
                                activeTab === 'individual'
                                    ? 'bg-[#82bee2] text-[#0f203e] font-semibold'
                                    : 'text-[#82bee2] hover:bg-[#82bee2]/10'
                            }`}
                        >
                            個人排行
                        </button>
                        <button
                            onClick={() => setActiveTab('group')}
                            className={`px-6 py-2 rounded-md transition-all duration-300 ${
                                activeTab === 'group'
                                    ? 'bg-[#82bee2] text-[#0f203e] font-semibold'
                                    : 'text-[#82bee2] hover:bg-[#82bee2]/10'
                            }`}
                        >
                            組別排行
                        </button>
                    </div>
                </div>

                {/* 錯誤提示 */}
                {error && (
                    <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4 mb-6 text-center">
                        <div className="text-red-400 mb-2">⚠️ 資料載入失敗</div>
                        <div className="text-sm text-gray-400">正在顯示模擬資料</div>
                    </div>
                )}

                {/* 排行榜內容 */}
                <div className="max-w-6xl mx-auto">
                    {activeTab === 'individual' ? (
                        <RankingList 
                            title="個人排行榜" 
                            items={leaderboardData} 
                            loading={loading}
                        />
                    ) : (
                        <RankingList 
                            title="組別排行榜" 
                            items={groupLeaderboard} 
                            isGroup={true}
                            loading={loading}
                        />
                    )}
                </div>

                {/* 統計資訊 */}
                {!loading && (
                    <div className="bg-[#1a2e4a] rounded-lg p-6 mt-8 max-w-4xl mx-auto">
                        <h3 className="text-[#82bee2] font-semibold mb-4 text-center">📊 統計資訊</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                            <div>
                                <div className="text-2xl font-bold text-[#82bee2]">
                                    {leaderboardData.length}
                                </div>
                                <div className="text-sm text-gray-400">參與者</div>
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-yellow-400">
                                    {leaderboardData.reduce((sum, user) => sum + user.points, 0).toLocaleString()}
                                </div>
                                <div className="text-sm text-gray-400">總點數</div>
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-green-400">
                                    {leaderboardData.reduce((sum, user) => sum + (user.stockValue || 0), 0).toLocaleString()}
                                </div>
                                <div className="text-sm text-gray-400">股票總值</div>
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-cyan-400">
                                    {groupLeaderboard.length}
                                </div>
                                <div className="text-sm text-gray-400">參與組別</div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}