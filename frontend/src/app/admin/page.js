'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
    getUserAssets,
    getSystemStats,
    givePoints,
    setTradingLimit,
    updateMarketTimes,
    createAnnouncement,
    getStudents,
    getTeams,
    getMarketStatus,
    getTradingHours,
    resetAllData,
    forceSettlement,
    getIpoStatus,
    resetIpo,
    updateIpo,
    executeCallAuction,
    getIpoDefaults,
    updateIpoDefaults
} from '@/lib/api';

export default function AdminPage() {
    const router = useRouter();

    const [adminToken, setAdminToken] = useState(null);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [notification, setNotification] = useState({ show: false, message: '', type: 'info' });

    // loading state
    const [givePointsLoading, setGivePointsLoading] = useState(false);
    const [tradingLimitLoading, setTradingLimitLoading] = useState(false);
    const [marketTimesLoading, setMarketTimesLoading] = useState(false);
    const [announcementLoading, setAnnouncementLoading] = useState(false);
    const [resetLoading, setResetLoading] = useState(false);
    const [userAssetsLoading, setUserAssetsLoading] = useState(false);
    const [forceSettlementLoading, setForceSettlementLoading] = useState(false);

    const [givePointsForm, setGivePointsForm] = useState({
        type: 'user',
        username: ''
    });

    const [tradingLimitPercent, setTradingLimitPercent] = useState(10);
    const [marketTimes, setMarketTimes] = useState([]);
    const [userAssets, setUserAssets] = useState([]);
    const [systemStats, setSystemStats] = useState(null);
    const [userSearchTerm, setUserSearchTerm] = useState('');
    const [announcementForm, setAnnouncementForm] = useState({
        title: '',
        message: '',
        broadcast: true
    });

    // 學員跟小隊列表
    const [students, setStudents] = useState([]); const [teams, setTeams] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);

    // 市場狀態
    const [marketStatus, setMarketStatus] = useState(null);

    // IPO 管理狀態
    const [ipoStatus, setIpoStatus] = useState(null);
    const [ipoLoading, setIpoLoading] = useState(false);
    const [showIpoUpdateModal, setShowIpoUpdateModal] = useState(false);
    const [ipoUpdateForm, setIpoUpdateForm] = useState({
        sharesRemaining: '',
        initialPrice: ''
    });

    // 集合競價狀態
    const [callAuctionLoading, setCallAuctionLoading] = useState(false);
    const [showCallAuctionModal, setShowCallAuctionModal] = useState(false);
    const [callAuctionResult, setCallAuctionResult] = useState(null);

    // IPO 預設配置狀態
    const [ipoDefaults, setIpoDefaults] = useState(null);
    const [showIpoDefaultsModal, setShowIpoDefaultsModal] = useState(false);
    const [ipoDefaultsForm, setIpoDefaultsForm] = useState({
        defaultInitialShares: '',
        defaultInitialPrice: ''
    });
    const [ipoDefaultsLoading, setIpoDefaultsLoading] = useState(false);

    // 新增時間 Modal
    const [showAddTimeModal, setShowAddTimeModal] = useState(false);
    const [newTimeForm, setNewTimeForm] = useState({
        start: '7:00',
        end: '9:00'
    });

    // Danger Zone 
    const [showResetConfirmModal, setShowResetConfirmModal] = useState(false);
    const [showResetResultModal, setShowResetResultModal] = useState(false);
    const [resetResult, setResetResult] = useState(null);
    const [showSettlementConfirmModal, setShowSettlementConfirmModal] = useState(false);
    const [showSettlementResultModal, setShowSettlementResultModal] = useState(false);
    const [settlementResult, setSettlementResult] = useState(null);
    const showNotification = (message, type = 'info') => {
        setNotification({ show: true, message, type });
        setTimeout(() => {
            setNotification({ show: false, message: '', type: 'info' });
        }, 3000);
    };

    // 處理 401 錯誤的統一函數
    const handle401Error = () => {
        localStorage.removeItem('isAdmin');
        localStorage.removeItem('adminToken');
        localStorage.removeItem('adminCode');
        setIsLoggedIn(false);
        setAdminToken(null);
        router.push('/login');
    };

    // 統一的錯誤處理函數
    const handleApiError = (error, context = '') => {
        console.error(`${context}錯誤:`, error);
        if (error.status === 401) {
            handle401Error();
            showNotification('登入已過期，請重新登入', 'error');
        } else {
            showNotification(`${context}失敗: ${error.message}`, 'error');
        }
    };
    
    // 檢查登入狀態
    useEffect(() => {
        let isMounted = true;

        const checkAuthAndInitialize = async () => {
            const isAdmin = localStorage.getItem('isAdmin');
            const token = localStorage.getItem('adminToken');

            if (!isAdmin || !token) {
                router.push('/login');
                return;
            }

            if (!isMounted) return;

            try {
                // 先測試 token 是否有效
                await getSystemStats(token);

                // Token 有效，設置狀態並初始化數據
                setAdminToken(token);
                setIsLoggedIn(true);

                if (isMounted) {
                    fetchUserAssets(token);
                    fetchSystemStats(token);
                    fetchStudents(token);
                    fetchTeams(token);
                    fetchMarketStatus();
                    fetchTradingHours();
                    fetchIpoStatus(token);
                    fetchIpoDefaults(token);
                }
            } catch (error) {
                if (error.status === 401) {
                    handle401Error();
                } else {
                    console.error('初始化失敗:', error);
                    router.push('/login');
                }
            }
        };

        checkAuthAndInitialize();

        return () => {
            isMounted = false;
        };
    }, [router]);
    
    // 管理員登出
    const handleLogout = () => {
        setIsLoggedIn(false);
        setAdminToken(null);
        localStorage.removeItem('isAdmin');
        localStorage.removeItem('adminToken');
        localStorage.removeItem('adminCode');
        setUserAssets([]);
        setSystemStats(null);
        router.push('/login');
    };
    
    // 撈學員的資料
    const fetchUserAssets = async (token, searchUser = null) => {
        try {
            setUserAssetsLoading(true);
            const data = await getUserAssets(token, searchUser);
            setUserAssets(data);
        } catch (error) {
            handleApiError(error, '獲取使用者資產');
        } finally {
            setUserAssetsLoading(false);
        }
    };

    // 確定後端狀態
    const fetchSystemStats = async (token) => {
        try {
            const data = await getSystemStats(token);
            setSystemStats(data);
        } catch (error) {
            handleApiError(error, '獲取系統統計');
        }
    };

    // 撈學員列表
    const fetchStudents = async (token) => {
        try {
            const data = await getStudents(token);
            setStudents(data);
        } catch (error) {
            handleApiError(error, '獲取學生列表');
        }
    };

    // 撈小隊列表
    const fetchTeams = async (token) => {
        try {
            const data = await getTeams(token);
            setTeams(data);
        } catch (error) {
            handleApiError(error, '獲取團隊列表');
        }
    };

    // 撈市場狀態
    const fetchMarketStatus = async () => {
        try {
            const data = await getMarketStatus();
            setMarketStatus(data);
        } catch (error) {
            console.error('獲取市場狀態失敗:', error);
        }
    };

    // 撈交易時間
    const fetchTradingHours = async () => {
        try {
            const data = await getTradingHours();
            if (data.tradingHours && data.tradingHours.length > 0) {
                const formattedTimes = data.tradingHours.map(slot => {
                    const startDate = new Date(slot.start * 1000);
                    const endDate = new Date(slot.end * 1000);
                    return {
                        start: startDate.toTimeString().slice(0, 5), // 轉 HH:MM Format
                        end: endDate.toTimeString().slice(0, 5),
                        favorite: false
                    };
                });
                setMarketTimes(formattedTimes);
            }
        } catch (error) {
            console.error('獲取交易時間失敗:', error);
        }
    };

    // 撈IPO狀態
    const fetchIpoStatus = async (token) => {
        try {
            setIpoLoading(true);
            const data = await getIpoStatus(token);
            setIpoStatus(data);
        } catch (error) {
            handleApiError(error, '獲取IPO狀態');
        } finally {
            setIpoLoading(false);
        }
    };

    // 撈IPO預設配置
    const fetchIpoDefaults = async (token) => {
        try {
            setIpoDefaultsLoading(true);
            const data = await getIpoDefaults(token);
            setIpoDefaults(data);
        } catch (error) {
            handleApiError(error, '獲取IPO預設配置');
        } finally {
            setIpoDefaultsLoading(false);
        }
    };

    // 更新IPO
    const handleIpoUpdate = async () => {
        try {
            setIpoLoading(true);
            
            const sharesRemaining = ipoUpdateForm.sharesRemaining !== '' ? parseInt(ipoUpdateForm.sharesRemaining) : null;
            const initialPrice = ipoUpdateForm.initialPrice !== '' ? parseInt(ipoUpdateForm.initialPrice) : null;
            
            const result = await updateIpo(adminToken, sharesRemaining, initialPrice);
            
            showNotification(result.message, 'success');
            setShowIpoUpdateModal(false);
            setIpoUpdateForm({ sharesRemaining: '', initialPrice: '' });
            
            // 重新取得IPO狀態
            await fetchIpoStatus(adminToken);
        } catch (error) {
            handleApiError(error, 'IPO更新');
        } finally {
            setIpoLoading(false);
        }
    };

    // 重置IPO
    const handleIpoReset = async () => {
        try {
            setIpoLoading(true);
            const result = await resetIpo(adminToken);
            showNotification(result.message, 'success');
            await fetchIpoStatus(adminToken);
        } catch (error) {
            handleApiError(error, 'IPO重置');
        } finally {
            setIpoLoading(false);
        }
    };

    // 更新IPO預設配置
    const handleIpoDefaultsUpdate = async () => {
        try {
            setIpoDefaultsLoading(true);
            
            const defaultShares = ipoDefaultsForm.defaultInitialShares !== '' ? parseInt(ipoDefaultsForm.defaultInitialShares) : null;
            const defaultPrice = ipoDefaultsForm.defaultInitialPrice !== '' ? parseInt(ipoDefaultsForm.defaultInitialPrice) : null;
            
            const result = await updateIpoDefaults(adminToken, defaultShares, defaultPrice);
            
            showNotification(result.message, 'success');
            setShowIpoDefaultsModal(false);
            setIpoDefaultsForm({ defaultInitialShares: '', defaultInitialPrice: '' });
            
            // 重新取得IPO預設配置
            await fetchIpoDefaults(adminToken);
        } catch (error) {
            handleApiError(error, 'IPO預設配置更新');
        } finally {
            setIpoDefaultsLoading(false);
        }
    };

    // 執行集合競價
    const handleCallAuction = async () => {
        try {
            setCallAuctionLoading(true);
            const result = await executeCallAuction(adminToken);
            
            // 儲存結果供顯示
            setCallAuctionResult(result);
            setShowCallAuctionModal(true);
            
            if (result.ok) {
                let message = result.message;
                
                // 如果有詳細統計，添加到通知中
                if (result.order_stats) {
                    const stats = result.order_stats;
                    const totalBuy = (stats.pending_buy || 0) + (stats.limit_buy || 0);
                    const totalSell = (stats.pending_sell || 0) + (stats.limit_sell || 0);
                    message += ` (處理了 ${totalBuy} 張買單、${totalSell} 張賣單)`;
                }
                
                showNotification(message, 'success');
            } else {
                let errorMessage = result.message || '集合競價執行失敗';
                
                // 如果有統計信息，添加到錯誤消息中
                if (result.order_stats) {
                    const stats = result.order_stats;
                    const totalPending = (stats.pending_buy || 0) + (stats.pending_sell || 0);
                    const totalLimit = (stats.limit_buy || 0) + (stats.limit_sell || 0);
                    if (totalPending > 0 || totalLimit > 0) {
                        errorMessage += ` (目前有 ${totalPending} 張待撮合訂單、${totalLimit} 張限制等待訂單)`;
                    }
                }
                
                showNotification(errorMessage, 'error');
            }
        } catch (error) {
            handleApiError(error, '集合競價執行');
        } finally {
            setCallAuctionLoading(false);
        }
    };

    // 搜尋建議
    const handleUsernameChange = (value) => {
        setGivePointsForm({
            ...givePointsForm,
            username: value
        });

        if (value.trim() === '') {
            setSuggestions([]);
            setShowSuggestions(false);
            return;
        }

        let filteredSuggestions = [];

        if (givePointsForm.type === 'user') {

            // 查學員
            filteredSuggestions = students
                .filter(student =>
                    student.username.toLowerCase().includes(value.toLowerCase())
                )
                .map(student => ({
                    value: student.username,
                    label: `${student.username} (${student.team})`,
                    type: 'user'
                }));
        } else {
            // 查小隊
            filteredSuggestions = teams
                .filter(team =>
                    team.name.toLowerCase().includes(value.toLowerCase())
                )
                .map(team => ({
                    value: team.name,
                    label: `${team.name} (${team.member_count || 0}人)`,
                    type: 'group'
                }));
        }

        setSuggestions(filteredSuggestions.slice(0, 5));
        setShowSuggestions(filteredSuggestions.length > 0);
    };

    const selectSuggestion = (suggestion) => {
        setGivePointsForm({
            ...givePointsForm,
            username: suggestion.value
        });
        setShowSuggestions(false);
        setSuggestions([]);
    }; const handleGivePoints = async () => {
        setGivePointsLoading(true);
        try {
            await givePoints(
                adminToken,
                givePointsForm.username,
                givePointsForm.type,
                parseInt(givePointsForm.amount)
            );
            showNotification('點數發放成功！', 'success');
            await fetchSystemStats(adminToken);
            setGivePointsForm({
                type: givePointsForm.type,
                username: '',
                amount: ''
            });

            setSuggestions([]);
            setShowSuggestions(false);
        } catch (error) {
            handleApiError(error, '發放點數');
        }
        setGivePointsLoading(false);
    };

    const handleSetTradingLimit = async () => {
        setTradingLimitLoading(true);
        try {
            await setTradingLimit(adminToken, parseFloat(tradingLimitPercent));
            showNotification('交易限制設定成功！', 'success');
        } catch (error) {
            handleApiError(error, '設定交易限制');
        }
        setTradingLimitLoading(false);
    };

    // 時間管理 Modal
    const openAddTimeModal = () => {
        setNewTimeForm({ start: '7:00', end: '9:00' });
        setShowAddTimeModal(true);
    };

    const closeAddTimeModal = () => {
        setShowAddTimeModal(false);
        setNewTimeForm({ start: '7:00', end: '9:00' });
    };

    const handleAddNewTime = () => {
        setMarketTimes([...marketTimes, { ...newTimeForm, favorite: false }]);
        closeAddTimeModal();
    };

    const removeMarketTime = (index) => {
        const newTimes = marketTimes.filter((_, i) => i !== index);
        setMarketTimes(newTimes);
    }; const saveMarketTimes = async () => {
        setMarketTimesLoading(true);
        try {
            const openTime = marketTimes.map(time => {
                const today = new Date();
                const startTime = new Date(today.toDateString() + ' ' + time.start);
                const endTime = new Date(today.toDateString() + ' ' + time.end);

                return {
                    start: Math.floor(startTime.getTime() / 1000),
                    end: Math.floor(endTime.getTime() / 1000)
                };
            });

            await updateMarketTimes(adminToken, openTime);
            showNotification('市場時間設定成功！', 'success');
        } catch (error) {
            handleApiError(error, '設定市場時間');
        }
        setMarketTimesLoading(false);
    };

    // 查學員
    const handleUserSearch = () => {
        if (adminToken) {
            fetchUserAssets(adminToken, userSearchTerm.trim() || null);
        }
    };    // 發布公告
    const handleCreateAnnouncement = async () => {
        if (!announcementForm.title.trim() || !announcementForm.message.trim()) {
            showNotification('請填寫公告標題和內容', 'error');
            return;
        }

        setAnnouncementLoading(true);
        try {
            await createAnnouncement(
                adminToken,
                announcementForm.title,
                announcementForm.message,
                announcementForm.broadcast
            );

            showNotification('公告發布成功！', 'success');
            setAnnouncementForm({
                title: '',
                message: '',
                broadcast: true
            });
        } catch (error) {
            handleApiError(error, '發布公告');
        }
        setAnnouncementLoading(false);
    };

    // Danger Zone 相關函數
    const openResetConfirmModal = () => {
        setShowResetConfirmModal(true);
    };

    const closeResetConfirmModal = () => {
        setShowResetConfirmModal(false);
    };

    const closeResetResultModal = () => {
        setShowResetResultModal(false);
        setResetResult(null);
    };

    const openSettlementConfirmModal = () => {
        setShowSettlementConfirmModal(true);
    };

    const closeSettlementConfirmModal = () => {
        setShowSettlementConfirmModal(false);
    };

    const closeSettlementResultModal = () => {
        setShowSettlementResultModal(false);
        setSettlementResult(null);
    };

    const handleResetAllData = async () => {
        setResetLoading(true);
        setShowResetConfirmModal(false);
        
        try {
            const result = await resetAllData(adminToken);
            setResetResult(result);
            setShowResetResultModal(true);
            showNotification('資料重置完成', 'success');
        } catch (error) {
            handleApiError(error, '重置資料');
        }
        setResetLoading(false);
    };

    const handleForceSettlement = async () => {
        setForceSettlementLoading(true);
        setShowSettlementConfirmModal(false);
        
        try {
            const result = await forceSettlement(adminToken);
            setSettlementResult(result);
            setShowSettlementResultModal(true);
            showNotification('強制結算完成！', 'success');
            
            // 重新獲取統計數據
            await fetchSystemStats(adminToken);
            await fetchUserAssets(adminToken);
        } catch (error) {
            handleApiError(error, '強制結算');
        }
        setForceSettlementLoading(false);
    };

    // 未登入時顯示載入畫面
    if (!isLoggedIn) {
        return (
            <div className="min-h-screen bg-[#0f203e] flex items-center justify-center">
                <div className="text-center">
                    <div className="h-12 w-12 animate-spin rounded-full border-4 border-white border-t-transparent mx-auto mb-4"></div>
                    <p className="text-white">正在檢查登入狀態...</p>
                </div>
            </div>
        );
    } return (
        <div className="min-h-screen bg-[#0f203e] pb-24">
            {/* 通知彈窗 */}
            {notification.show && (
                <div className={`fixed top-4 left-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg transition-all duration-300 ${notification.type === 'success' ? 'bg-green-600 text-white' :
                    notification.type === 'error' ? 'bg-red-600 text-white' :
                        'bg-blue-600 text-white'
                    }`}>
                    <div className="flex items-center space-x-2">
                        {notification.type === 'success' && (
                            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        )}
                        {notification.type === 'error' && (
                            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        )}
                        <span className="text-sm break-words">{notification.message}</span>
                    </div>
                </div>
            )}

            <div className="container mx-auto px-4 py-6 w-11/12">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-2xl font-bold text-[#AFE1F5]">管理員面板</h1>
                    <button
                        onClick={handleLogout}
                        className="bg-[#7BC2E6] hover:bg-[#6bb0d4] text-black px-4 py-2 rounded-xl transition-colors"
                    >
                        登出
                    </button>
                </div>

                <div className="space-y-6">
                    {/* 發點數 */}
                    <div className="bg-[#1A325F] rounded-xl p-6">
                        <div className="space-y-4">
                            {/* 學員 / 小隊切換 */}
                            <div className="flex space-x-4">
                                <span className="text-[#7BC2E6]">個人</span>
                                <label className="relative inline-flex items-center cursor-pointer">                                    <input
                                    type="checkbox"
                                    checked={givePointsForm.type === 'group'}
                                    onChange={(e) => {
                                        const newType = e.target.checked ? 'group' : 'user';
                                        setGivePointsForm({
                                            ...givePointsForm,
                                            type: newType,
                                            username: ''
                                        });

                                        setShowSuggestions(false);
                                        setSuggestions([]);
                                    }}
                                    className="sr-only peer"
                                />
                                    <div className="w-11 h-6 bg-[#0f203e] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#7BC2E6] border border-gray-600"></div>
                                </label>
                                <span className="text-[#7BC2E6]">群組</span>
                            </div>                            <div className="relative">
                                <label className="block text-[#7BC2E6] text-sm font-medium mb-2">
                                    給誰（搜尋選擇）
                                </label>
                                <input
                                    type="text"
                                    value={givePointsForm.username}
                                    onChange={(e) => handleUsernameChange(e.target.value)}
                                    onFocus={() => {
                                        if (suggestions.length > 0) {
                                            setShowSuggestions(true);
                                        }
                                    }}
                                    onBlur={() => {
                                        setTimeout(() => setShowSuggestions(false), 150);
                                    }}
                                    className="w-full px-3 py-2 bg-[#1A325F] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder={givePointsForm.type === 'user' ? '搜尋學生姓名...' : '搜尋團隊名稱...'}
                                />

                                {/* 搜尋建議下拉 */}
                                {showSuggestions && suggestions.length > 0 && (
                                    <div className="absolute z-10 w-full mt-1 bg-[#0f203e] border border-[#469FD2] rounded-xl shadow-lg max-h-48 overflow-y-auto">
                                        {suggestions.map((suggestion, index) => (
                                            <div
                                                key={index}
                                                onClick={() => selectSuggestion(suggestion)}
                                                className="px-3 py-2 hover:bg-[#1A325F] cursor-pointer text-white text-sm transition-colors border-b border-[#469FD2] last:border-b-0"
                                            >
                                                <div className="flex items-center justify-between">
                                                    <span>{suggestion.label}</span>
                                                    <span className="text-xs text-gray-400">
                                                        {suggestion.type === 'user' ? '個人' : '團隊'}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div>
                                <label className="block text-[#7BC2E6] text-sm font-medium mb-2">
                                    給多少
                                </label>
                                <input
                                    type="number"
                                    value={givePointsForm.amount}
                                    onChange={(e) => setGivePointsForm({
                                        ...givePointsForm,
                                        amount: e.target.value
                                    })}
                                    className="w-full px-3 py-2 bg-[#1A325F] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div className='w-full items-center flex justify-center'>
                                <button
                                    onClick={handleGivePoints}
                                    disabled={givePointsLoading || !givePointsForm.username}
                                    className="mx-auto bg-[#7BC2E6] hover:bg-[#6bb0d4] disabled:bg-[#4a5568] disabled:hover:bg-[#4a5568] disabled:cursor-not-allowed text-black disabled:text-[#a0aec0] font-medium py-2 px-4 rounded-lg transition-colors"
                                >
                                    {givePointsLoading ? '發放中...' : '發點數'}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* 漲跌限制設定 */}
                    <div className="bg-[#1A325F] rounded-xl p-6">
                        <h2 className="text-lg text-[#7BC2E6] mb-4">當日股票漲跌限制</h2>
                        <div className="space-y-4">
                            <div className="relative">
                                <input
                                    type="number"
                                    min="0"
                                    max="100"
                                    step="0.1"
                                    value={tradingLimitPercent}
                                    onChange={(e) => {
                                        const value = e.target.value;
                                        if (value === '' || (!isNaN(value) && parseFloat(value) >= 0 && parseFloat(value) <= 100)) {
                                            setTradingLimitPercent(value);
                                        }
                                    }}
                                    placeholder="輸入百分比數字 (0-100)"
                                    className="w-full px-3 py-2 pr-8 bg-[#1A325F] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <span className="absolute right-3 top-2 text-[#7BC2E6] pointer-events-none">%</span>
                            </div>
                            <div className='w-full items-center flex justify-center'>
                                <button
                                    onClick={handleSetTradingLimit}
                                    disabled={tradingLimitLoading}
                                    className="mx-auto bg-[#7BC2E6] hover:bg-[#6bb0d4] disabled:bg-[#4a5568] disabled:hover:bg-[#4a5568] disabled:cursor-not-allowed text-black disabled:text-[#a0aec0] font-medium py-2 px-4 rounded-lg transition-colors"
                                >
                                    {tradingLimitLoading ? '設定中...' : '設定'}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* 交易時間管理 */}
                    <div className="bg-[#1A325F] rounded-xl p-6">
                        <div className="flex justify-between items-center mb-4 border-b-1 border-[#469FD2] pb-3">
                            <h2 className="text-lg text-[#7BC2E6]">允許交易時間</h2>
                            <div className="flex space-x-2">
                                <button
                                    onClick={openAddTimeModal}
                                    className="bg-[#7BC2E6] text-black p-1 rounded-full transition-colors text-xs"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <div className="space-y-3">
                            {marketTimes.map((time, index) => (
                                <div key={index} className="flex items-center justify-between bg-[#0f203e] p-3 rounded-xl">
                                    <div className="flex items-center space-x-3 flex-1">
                                        <div className="text-yellow-400">
                                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                                <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                                            </svg>
                                        </div>

                                        <div className="flex items-center space-x-2 flex-1">
                                            <span className="text-white text-sm">{time.start}</span>
                                            <span className="text-[#7BC2E6]">-</span>
                                            <span className="text-white text-sm">{time.end}</span>
                                        </div>
                                    </div>

                                    <button
                                        onClick={() => removeMarketTime(index)}
                                        className="text-red-400 p-1 ml-2 hover:text-red-300 transition-colors"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                    </button>
                                </div>
                            ))}
                        </div>

                        <div className='w-full items-center flex justify-center mt-4'>
                            <button
                                onClick={saveMarketTimes}
                                disabled={marketTimesLoading}
                                className="mx-auto bg-[#7BC2E6] hover:bg-[#6bb0d4] disabled:bg-[#4a5568] disabled:hover:bg-[#4a5568] disabled:cursor-not-allowed text-black disabled:text-[#a0aec0] font-medium py-2 px-4 rounded-lg transition-colors"
                            >
                                {marketTimesLoading ? '保存中...' : '保存交易時間'}
                            </button>
                        </div>
                    </div>

                    {/* 發布公告 */}
                    <div className="bg-[#1A325F] rounded-xl p-6">
                        <h2 className="text-xl font-bold text-white mb-4">發布公告</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-[#7BC2E6] text-sm font-medium mb-2">
                                    公告標題
                                </label>
                                <input
                                    type="text"
                                    value={announcementForm.title}
                                    onChange={(e) => setAnnouncementForm({
                                        ...announcementForm,
                                        title: e.target.value
                                    })}
                                    className="w-full px-3 py-2 bg-[#1A325F] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="輸入公告標題"
                                />
                            </div>

                            <div>
                                <label className="block text-[#7BC2E6] text-sm font-medium mb-2">
                                    公告內容
                                </label>
                                <textarea
                                    value={announcementForm.message}
                                    onChange={(e) => setAnnouncementForm({
                                        ...announcementForm,
                                        message: e.target.value
                                    })}
                                    rows={4}
                                    className="w-full px-3 py-2 bg-[#1A325F] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                                    placeholder="輸入公告內容"
                                />
                            </div>

                            <div className="flex items-center space-x-3">
                                <input
                                    type="checkbox"
                                    id="broadcast"
                                    checked={announcementForm.broadcast}
                                    onChange={(e) => setAnnouncementForm({
                                        ...announcementForm,
                                        broadcast: e.target.checked
                                    })}
                                    className="w-4 h-4 text-blue-600 bg-[#1A325F] border border-[#469FD2] rounded focus:ring-blue-500"
                                />
                                <label htmlFor="broadcast" className="text-[#7BC2E6] text-sm">
                                    廣播到 Telegram Bot
                                </label>
                            </div>

                            <div className='w-full items-center flex justify-center'>
                                <button
                                    onClick={handleCreateAnnouncement}
                                    disabled={announcementLoading || !announcementForm.title.trim() || !announcementForm.message.trim()}
                                    className="mx-auto bg-[#7BC2E6] hover:bg-[#6bb0d4] disabled:bg-[#4a5568] disabled:hover:bg-[#4a5568] disabled:cursor-not-allowed text-black disabled:text-[#a0aec0] font-medium py-2 px-4 rounded-lg transition-colors"
                                >
                                    {announcementLoading ? '發布中...' : '發布公告'}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* 使用者資產 */}
                    <div className="bg-[#1A325F] rounded-xl p-6">
                        <h2 className="text-xl font-bold text-white mb-4">使用者資產明細</h2>

                        <div className="space-y-2 mb-4">
                            <input
                                type="text"
                                value={userSearchTerm}
                                onChange={(e) => setUserSearchTerm(e.target.value)}
                                placeholder="查詢使用者名稱..."
                                className="w-full px-3 py-2 bg-[#0f203e] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                onKeyPress={(e) => e.key === 'Enter' && handleUserSearch()}
                            />
                            <div className="flex space-x-2">
                                <button
                                    onClick={handleUserSearch}
                                    disabled={userAssetsLoading}
                                    className="bg-[#7bc2e6] hover:bg-[#6bb0d4] disabled:bg-[#4a5568] disabled:hover:bg-[#4a5568] disabled:cursor-not-allowed text-black disabled:text-[#a0aec0] px-4 py-2 rounded-xl transition-colors flex-1"
                                >
                                    {userAssetsLoading ? '查詢中...' : '查詢'}
                                </button>
                                <button
                                    onClick={() => {
                                        setUserSearchTerm('');
                                        fetchUserAssets(adminToken);
                                    }}
                                    disabled={userAssetsLoading}
                                    className="bg-gray-600 hover:bg-gray-700 disabled:bg-[#2d3748] disabled:hover:bg-[#2d3748] disabled:cursor-not-allowed text-white disabled:text-[#718096] px-4 py-2 rounded-xl transition-colors flex-1"
                                >
                                    {userAssetsLoading ? '重置中...' : '重置'}
                                </button>
                            </div>
                        </div>

                        {userAssetsLoading ? (
                            // Loading skeleton
                            <div className="space-y-3">
                                {[1, 2, 3].map((index) => (
                                    <div key={index} className="bg-[#0f203e] p-4 rounded-xl animate-pulse">
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <div className="h-5 bg-[#1A325F] rounded w-24 mb-2"></div>
                                                <div className="h-4 bg-[#1A325F] rounded w-16"></div>
                                            </div>
                                            <div className="text-right">
                                                <div className="h-6 bg-[#1A325F] rounded w-20 mb-1"></div>
                                                <div className="h-3 bg-[#1A325F] rounded w-12"></div>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-3 gap-2 text-sm">
                                            <div className="text-center">
                                                <div className="h-5 bg-[#1A325F] rounded w-16 mx-auto mb-1"></div>
                                                <div className="h-3 bg-[#1A325F] rounded w-8 mx-auto"></div>
                                            </div>
                                            <div className="text-center">
                                                <div className="h-5 bg-[#1A325F] rounded w-8 mx-auto mb-1"></div>
                                                <div className="h-3 bg-[#1A325F] rounded w-10 mx-auto"></div>
                                            </div>
                                            <div className="text-center">
                                                <div className="h-5 bg-[#1A325F] rounded w-16 mx-auto mb-1"></div>
                                                <div className="h-3 bg-[#1A325F] rounded w-12 mx-auto"></div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : userAssets.length > 0 ? (
                            <div className="space-y-3">
                                {userAssets.slice(0, 3).map((user, index) => (
                                    <div key={index} className="bg-[#0f203e] p-4 rounded-xl">
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <div className="text-white font-medium">{user.username}</div>
                                                <div className="text-gray-400 text-sm">{user.team}</div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-white font-bold">{Math.round(user.total).toLocaleString()}</div>
                                                <div className="text-gray-400 text-sm">總資產</div>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-3 gap-2 text-sm">
                                            <div className="text-center">
                                                <div className="text-white">{user.points.toLocaleString()}</div>
                                                <div className="text-gray-400 text-xs">點數</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-white">{user.stocks}</div>
                                                <div className="text-gray-400 text-xs">持股數</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-white">{Math.round(user.stockValue).toLocaleString()}</div>
                                                <div className="text-gray-400 text-xs">股票價值</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                                {userAssets.length > 3 && (
                                    <div className="text-center text-gray-400 text-sm mt-4">
                                        顯示前3個使用者，共{userAssets.length}個使用者
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="text-center text-gray-400 py-8">
                                暫無使用者資料
                            </div>
                        )}
                    </div>

                    {/* 系統統計 */}
                    {systemStats && (
                        <div className="bg-[#1A325F] rounded-xl p-6">
                            <h2 className="text-xl font-bold text-white mb-4">統計</h2>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="text-center bg-[#0f203e] p-3 rounded-xl">
                                    <div className="text-2xl font-bold">{systemStats.total_users}</div>
                                    <div className="text-gray-400 text-sm mt-1">個使用者</div>
                                </div>
                                <div className="text-center bg-[#0f203e] p-3 rounded-xl">
                                    <div className="text-2xl font-bold">{systemStats.total_groups}</div>
                                    <div className="text-gray-400 text-sm mt-1">個隊伍</div>
                                </div>
                                <div className="text-center bg-[#0f203e] p-3 rounded-xl">
                                    <div className="text-2xl font-bold">{systemStats.total_points.toLocaleString()}</div>
                                    <div className="text-gray-400 text-sm mt-1">總點數</div>
                                </div>
                                <div className="text-center bg-[#0f203e] p-3 rounded-xl">
                                    <div className="text-2xl font-bold">{systemStats.total_stocks.toLocaleString()}</div>
                                    <div className="text-gray-400 text-sm mt-1">總股票數</div>
                                </div>
                                <div className="text-center bg-[#0f203e] p-3 rounded-xl col-span-2">
                                    <div className="text-2xl font-bold">{systemStats.total_trades}</div>
                                    <div className="text-gray-400 text-sm mt-1">總交易數</div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* IPO 管理 */}
            <div className="max-w-4xl mx-auto px-4 mt-8">
                <div className="bg-[#1A325F] rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-white">IPO 管理</h2>
                        <button
                            onClick={() => fetchIpoStatus(adminToken)}
                            disabled={ipoLoading}
                            className="bg-blue-600 hover:bg-blue-700 disabled:bg-[#2d3748] text-white px-3 py-1 rounded-lg text-sm"
                        >
                            {ipoLoading ? '載入中...' : '重新整理'}
                        </button>
                    </div>
                    
                    {ipoStatus ? (
                        <div className="space-y-4">
                            {/* IPO 狀態顯示 */}
                            <div className="grid grid-cols-3 gap-4 bg-[#0f203e] p-4 rounded-xl">
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-white">{ipoStatus.initialShares?.toLocaleString()}</div>
                                    <div className="text-gray-400 text-sm">初始股數</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-orange-400">{ipoStatus.sharesRemaining?.toLocaleString()}</div>
                                    <div className="text-gray-400 text-sm">剩餘股數</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-green-400">{ipoStatus.initialPrice}</div>
                                    <div className="text-gray-400 text-sm">每股價格 (點)</div>
                                </div>
                            </div>
                            
                            {/* 操作按鈕 */}
                            <div className="grid grid-cols-2 gap-3 mb-3">
                                <button
                                    onClick={() => setShowIpoUpdateModal(true)}
                                    disabled={ipoLoading}
                                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-[#2d3748] text-white px-4 py-2 rounded-xl font-medium transition-colors"
                                >
                                    更新參數
                                </button>
                                <button
                                    onClick={handleIpoReset}
                                    disabled={ipoLoading}
                                    className="bg-orange-600 hover:bg-orange-700 disabled:bg-[#2d3748] text-white px-4 py-2 rounded-xl font-medium transition-colors"
                                >
                                    {ipoLoading ? '重置中...' : '重置IPO'}
                                </button>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    onClick={handleCallAuction}
                                    disabled={callAuctionLoading}
                                    className="bg-purple-600 hover:bg-purple-700 disabled:bg-[#2d3748] text-white px-4 py-2 rounded-xl font-medium transition-colors"
                                >
                                    {callAuctionLoading ? '撮合中...' : '集合競價'}
                                </button>
                                <button
                                    onClick={() => setShowIpoDefaultsModal(true)}
                                    disabled={ipoDefaultsLoading}
                                    className="bg-green-600 hover:bg-green-700 disabled:bg-[#2d3748] text-white px-4 py-2 rounded-xl font-medium transition-colors"
                                >
                                    管理預設值
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center text-gray-400 py-4">
                            {ipoLoading ? '載入IPO狀態中...' : '無法載入IPO狀態'}
                        </div>
                    )}
                </div>
            </div>

            {/* Danger Zone */}
            <div className="max-w-4xl mx-auto px-4 mt-8">
                <div className="bg-[#1A325F] rounded-xl p-6 border-2 border-red-500">
                    <div className="flex items-center mb-4">
                        <svg className="w-6 h-6 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                        <h2 className="text-xl font-bold text-red-500">Danger Zone</h2>
                    </div>
                    <div className="pt-2">
                        <div className="flex flex-col gap-5 w-full justify-between">
                            <div>
                                <h3 className="text-white font-medium">強制結算</h3>
                                <p className="text-gray-400 text-sm">將所有使用者的持股以固定價格轉換為點數，並清除其股票</p>
                            </div>
                            <button
                                onClick={openSettlementConfirmModal}
                                disabled={forceSettlementLoading}
                                className="bg-red-600 hover:bg-red-700 disabled:bg-[#2d3748] disabled:hover:bg-[#2d3748] disabled:cursor-not-allowed text-white disabled:text-[#718096] px-4 py-2 rounded-xl font-medium transition-colors w-full"
                            >
                                {forceSettlementLoading ? '結算中...' : '強制結算'}
                            </button>
                        </div>
                        
                        <div className="flex flex-col gap-5 w-full justify-between mt-6 pt-6 border-t border-red-500">
                            <div>
                                <h3 className="text-white font-medium">重置所有資料 (Dev)</h3>
                                <p className="text-gray-400 text-sm">永久刪除所有使用者資料、交易記錄和系統設定</p>
                            </div>
                            <button
                                onClick={openResetConfirmModal}
                                disabled={resetLoading}
                                className="bg-red-600 hover:bg-red-700 disabled:bg-[#2d3748] disabled:hover:bg-[#2d3748] disabled:cursor-not-allowed text-white disabled:text-[#718096] px-4 py-2 rounded-xl font-medium transition-colors w-full"
                            >
                                {resetLoading ? '處理中...' : '重置所有資料'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* 新增時間 Modal */}
            {showAddTimeModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1A325F] rounded-xl p-6 w-full max-w-md">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-[#7BC2E6]">新增交易時間</h3>
                            <button
                                onClick={closeAddTimeModal}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-[#7BC2E6] text-sm font-medium mb-2">
                                    開始時間
                                </label>
                                <input
                                    type="time"
                                    value={newTimeForm.start}
                                    onChange={(e) => setNewTimeForm({ ...newTimeForm, start: e.target.value })}
                                    className="w-full px-3 py-2 bg-[#0f203e] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-[#7BC2E6] text-sm font-medium mb-2">
                                    結束時間
                                </label>
                                <input
                                    type="time"
                                    value={newTimeForm.end}
                                    onChange={(e) => setNewTimeForm({ ...newTimeForm, end: e.target.value })}
                                    className="w-full px-3 py-2 bg-[#0f203e] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div className="flex space-x-3 mt-6">
                                <button
                                    onClick={closeAddTimeModal}
                                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-xl transition-colors"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleAddNewTime}
                                    className="flex-1 bg-[#7BC2E6] hover:bg-[#6bb0d4] text-black py-2 px-4 rounded-xl transition-colors"
                                >
                                    新增
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 重置確認 Modal */}
            {showResetConfirmModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1A325F] rounded-xl p-6 w-full max-w-md border-2 border-red-500">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-red-500">危險操作確認</h3>
                            <button
                                onClick={closeResetConfirmModal}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="bg-red-900 border border-red-600 rounded-lg p-4">
                                <p className="text-white font-medium mb-2">您即將重置所有系統資料！</p>
                                <p className="text-red-200 text-sm">
                                    這個操作將會把系統資料全部刪光，你要確定欸？
                                </p>
                            </div>

                            <div className="flex space-x-3 mt-6">
                                <button
                                    onClick={closeResetConfirmModal}
                                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-xl transition-colors"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleResetAllData}
                                    disabled={resetLoading}
                                    className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-[#2d3748] disabled:hover:bg-[#2d3748] disabled:cursor-not-allowed text-white disabled:text-[#718096] py-2 px-4 rounded-xl transition-colors font-medium"
                                >
                                    {resetLoading ? '重置中...' : '確認重置'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 強制結算確認 Modal */}
            {showSettlementConfirmModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1A325F] rounded-xl p-6 w-full max-w-md border-2 border-red-500">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-red-500">強制結算確認</h3>
                            <button
                                onClick={closeSettlementConfirmModal}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="bg-orange-900 border border-orange-600 rounded-lg p-4">
                                <p className="text-white font-medium mb-2">您即將執行強制結算！</p>
                                <p className="text-orange-200 text-sm">
                                    這個操作將會把所有使用者的持股以固定價格轉換為點數，並清除其股票。此操作無法復原！
                                </p>
                            </div>

                            <div className="flex space-x-3 mt-6">
                                <button
                                    onClick={closeSettlementConfirmModal}
                                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-xl transition-colors"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleForceSettlement}
                                    disabled={forceSettlementLoading}
                                    className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-[#2d3748] disabled:hover:bg-[#2d3748] disabled:cursor-not-allowed text-white disabled:text-[#718096] py-2 px-4 rounded-xl transition-colors font-medium"
                                >
                                    {forceSettlementLoading ? '結算中...' : '確認結算'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 強制結算結果 Modal */}
            {showSettlementResultModal && settlementResult && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1A325F] rounded-xl p-6 w-full max-w-md">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-green-500">強制結算完成</h3>
                            <button
                                onClick={closeSettlementResultModal}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="bg-[#0f203e] border border-[#469FD2] rounded-lg p-4">
                                <h4 className="text-[#7BC2E6] font-medium mb-3">後端回應：</h4>
                                <div className="bg-gray-900 rounded p-3 font-mono text-sm text-gray-300 whitespace-pre-wrap overflow-auto max-h-96">
                                    {JSON.stringify(settlementResult, null, 2)}
                                </div>
                            </div>

                            <div className="flex justify-end mt-6">
                                <button
                                    onClick={closeSettlementResultModal}
                                    className="bg-[#7BC2E6] hover:bg-[#6bb0d4] text-black py-2 px-6 rounded-xl transition-colors font-medium"
                                >
                                    關閉
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 重置結果 Modal */}
            {showResetResultModal && resetResult && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1A325F] rounded-xl p-6 w-full max-w-md">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-green-500">重置完成</h3>
                            <button
                                onClick={closeResetResultModal}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="bg-[#0f203e] border border-[#469FD2] rounded-lg p-4">
                                <h4 className="text-[#7BC2E6] font-medium mb-3">後端回應：</h4>
                                <div className="bg-gray-900 rounded p-3 font-mono text-sm text-gray-300 whitespace-pre-wrap overflow-auto max-h-96">
                                    {JSON.stringify(resetResult, null, 2)}
                                </div>
                            </div>

                            <div className="flex justify-end mt-6">
                                <button
                                    onClick={closeResetResultModal}
                                    className="bg-[#7BC2E6] hover:bg-[#6bb0d4] text-black py-2 px-6 rounded-xl transition-colors font-medium"
                                >
                                    關閉
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* IPO 更新 Modal */}
            {showIpoUpdateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1A325F] rounded-xl p-6 w-full max-w-md">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-[#7BC2E6]">更新 IPO 參數</h3>
                            <button
                                onClick={() => setShowIpoUpdateModal(false)}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-[#7BC2E6] text-sm font-medium mb-2">
                                    剩餘股數 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    value={ipoUpdateForm.sharesRemaining}
                                    onChange={(e) => setIpoUpdateForm({ ...ipoUpdateForm, sharesRemaining: e.target.value })}
                                    placeholder="例如: 0"
                                    className="w-full px-3 py-2 bg-[#0f203e] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="text-gray-400 text-xs mt-1">
                                    目前: {ipoStatus?.sharesRemaining?.toLocaleString()} 股
                                </p>
                            </div>

                            <div>
                                <label className="block text-[#7BC2E6] text-sm font-medium mb-2">
                                    IPO 價格 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    value={ipoUpdateForm.initialPrice}
                                    onChange={(e) => setIpoUpdateForm({ ...ipoUpdateForm, initialPrice: e.target.value })}
                                    placeholder="例如: 25"
                                    className="w-full px-3 py-2 bg-[#0f203e] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="text-gray-400 text-xs mt-1">
                                    目前: {ipoStatus?.initialPrice} 點/股
                                </p>
                            </div>

                            <div className="bg-blue-900 border border-blue-600 rounded-lg p-3">
                                <p className="text-blue-200 text-sm">
                                    💡 提示：設定剩餘股數為 0 可以強制市價單使用限價單撮合，實現價格發現機制
                                </p>
                            </div>

                            <div className="flex space-x-3 mt-6">
                                <button
                                    onClick={() => setShowIpoUpdateModal(false)}
                                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-xl transition-colors"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleIpoUpdate}
                                    disabled={ipoLoading}
                                    className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-[#2d3748] text-white py-2 px-4 rounded-xl transition-colors"
                                >
                                    {ipoLoading ? '更新中...' : '更新'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 集合競價結果 Modal */}
            {showCallAuctionModal && callAuctionResult && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1A325F] rounded-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-[#7BC2E6]">集合競價結果</h3>
                            <button
                                onClick={() => setShowCallAuctionModal(false)}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            {/* 結果總結 */}
                            <div className={`rounded-lg p-4 ${callAuctionResult.ok ? 'bg-green-900 border border-green-600' : 'bg-red-900 border border-red-600'}`}>
                                <h4 className={`font-medium mb-2 ${callAuctionResult.ok ? 'text-green-200' : 'text-red-200'}`}>
                                    {callAuctionResult.ok ? '✅ 集合競價成功' : '❌ 集合競價失敗'}
                                </h4>
                                <p className={`text-sm ${callAuctionResult.ok ? 'text-green-300' : 'text-red-300'}`}>
                                    {callAuctionResult.message}
                                </p>
                                {callAuctionResult.ok && (
                                    <div className="mt-2 text-green-200 text-sm">
                                        <p>撮合價格: {callAuctionResult.auction_price} 元</p>
                                        <p>成交量: {callAuctionResult.matched_volume} 股</p>
                                    </div>
                                )}
                            </div>

                            {/* 訂單統計 */}
                            {callAuctionResult.order_stats && (
                                <div className="bg-[#0f203e] border border-[#469FD2] rounded-lg p-4">
                                    <h4 className="text-[#7BC2E6] font-medium mb-3">訂單統計</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <h5 className="text-white font-medium mb-2">買單</h5>
                                            <p className="text-sm text-gray-300">待撮合: {callAuctionResult.order_stats.pending_buy || 0} 張</p>
                                            <p className="text-sm text-gray-300">限制等待: {callAuctionResult.order_stats.limit_buy || 0} 張</p>
                                            <p className="text-sm text-yellow-300">總計: {callAuctionResult.order_stats.total_buy_orders || 0} 張</p>
                                        </div>
                                        <div>
                                            <h5 className="text-white font-medium mb-2">賣單</h5>
                                            <p className="text-sm text-gray-300">待撮合: {callAuctionResult.order_stats.pending_sell || 0} 張</p>
                                            <p className="text-sm text-gray-300">限制等待: {callAuctionResult.order_stats.limit_sell || 0} 張</p>
                                            <p className="text-sm text-yellow-300">總計: {callAuctionResult.order_stats.total_sell_orders || 0} 張</p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* 訂單詳細列表 */}
                            {callAuctionResult.order_details && (
                                <div className="space-y-4">
                                    {/* 買單列表 */}
                                    <div className="bg-[#0f203e] border border-[#469FD2] rounded-lg p-4">
                                        <h4 className="text-green-400 font-medium mb-3">買單列表 ({callAuctionResult.order_details.buy_orders?.length || 0} 筆)</h4>
                                        {callAuctionResult.order_details.buy_orders?.length > 0 ? (
                                            <div className="space-y-2 max-h-40 overflow-y-auto">
                                                {callAuctionResult.order_details.buy_orders.map((order, index) => (
                                                    <div key={index} className="flex justify-between items-center bg-[#1A325F] p-2 rounded text-sm">
                                                        <div>
                                                            <span className="text-white font-medium">{order.username}</span>
                                                            <span className={`ml-2 px-2 py-1 rounded text-xs ${order.status === 'pending' ? 'bg-yellow-600 text-yellow-100' : 'bg-orange-600 text-orange-100'}`}>
                                                                {order.status === 'pending' ? '待撮合' : '限制等待'}
                                                            </span>
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="text-green-400 font-medium">{order.price} 元 x {order.quantity} 股</div>
                                                            <div className="text-gray-400 text-xs">{new Date(order.created_at).toLocaleString()}</div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-gray-400 text-sm">無買單</p>
                                        )}
                                    </div>

                                    {/* 賣單列表 */}
                                    <div className="bg-[#0f203e] border border-[#469FD2] rounded-lg p-4">
                                        <h4 className="text-red-400 font-medium mb-3">賣單列表 ({callAuctionResult.order_details.sell_orders?.length || 0} 筆)</h4>
                                        {callAuctionResult.order_details.sell_orders?.length > 0 ? (
                                            <div className="space-y-2 max-h-40 overflow-y-auto">
                                                {callAuctionResult.order_details.sell_orders.map((order, index) => (
                                                    <div key={index} className="flex justify-between items-center bg-[#1A325F] p-2 rounded text-sm">
                                                        <div>
                                                            <span className="text-white font-medium">{order.username}</span>
                                                            <span className={`ml-2 px-2 py-1 rounded text-xs ${order.status === 'pending' ? 'bg-yellow-600 text-yellow-100' : 'bg-orange-600 text-orange-100'}`}>
                                                                {order.status === 'pending' ? '待撮合' : '限制等待'}
                                                            </span>
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="text-red-400 font-medium">{order.price} 元 x {order.quantity} 股</div>
                                                            <div className="text-gray-400 text-xs">{new Date(order.created_at).toLocaleString()}</div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-gray-400 text-sm">無賣單</p>
                                        )}
                                    </div>
                                </div>
                            )}

                            <div className="flex justify-end mt-6">
                                <button
                                    onClick={() => setShowCallAuctionModal(false)}
                                    className="bg-[#7BC2E6] hover:bg-[#6bb0d4] text-black py-2 px-6 rounded-xl transition-colors font-medium"
                                >
                                    關閉
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* IPO 預設配置 Modal */}
            {showIpoDefaultsModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1A325F] rounded-xl p-6 w-full max-w-md">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-[#7BC2E6]">IPO 預設配置管理</h3>
                            <button
                                onClick={() => setShowIpoDefaultsModal(false)}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-[#7BC2E6] text-sm font-medium mb-2">
                                    預設初始股數 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    value={ipoDefaultsForm.defaultInitialShares}
                                    onChange={(e) => setIpoDefaultsForm({ ...ipoDefaultsForm, defaultInitialShares: e.target.value })}
                                    placeholder="例如: 1000"
                                    className="w-full px-3 py-2 bg-[#0f203e] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="text-gray-400 text-xs mt-1">
                                    目前: {ipoDefaults?.defaultInitialShares?.toLocaleString()} 股
                                </p>
                            </div>

                            <div>
                                <label className="block text-[#7BC2E6] text-sm font-medium mb-2">
                                    預設IPO價格 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    value={ipoDefaultsForm.defaultInitialPrice}
                                    onChange={(e) => setIpoDefaultsForm({ ...ipoDefaultsForm, defaultInitialPrice: e.target.value })}
                                    placeholder="例如: 20"
                                    className="w-full px-3 py-2 bg-[#0f203e] border border-[#469FD2] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="text-gray-400 text-xs mt-1">
                                    目前: {ipoDefaults?.defaultInitialPrice} 點/股
                                </p>
                            </div>

                            <div className="bg-green-900 border border-green-600 rounded-lg p-3">
                                <p className="text-green-200 text-sm">
                                    ⚙️ 這些設定將用於未來的IPO重置操作，不會影響當前的IPO狀態
                                </p>
                            </div>

                            <div className="flex space-x-3 mt-6">
                                <button
                                    onClick={() => setShowIpoDefaultsModal(false)}
                                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-xl transition-colors"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleIpoDefaultsUpdate}
                                    disabled={ipoDefaultsLoading}
                                    className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-[#2d3748] text-white py-2 px-4 rounded-xl transition-colors"
                                >
                                    {ipoDefaultsLoading ? '更新中...' : '更新配置'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
