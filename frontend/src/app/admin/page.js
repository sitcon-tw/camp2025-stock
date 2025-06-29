"use client";

import {
    closeMarket,
    createAnnouncement,
    executeCallAuction,
    forceSettlement,
    getAdminMarketStatus,
    getIpoDefaults,
    getIpoStatus,
    getSystemStats,
    getTeams,
    getTradingHours,
    getTransferFeeConfig,
    getUserAssets,
    givePoints,
    openMarket,
    resetAllData,
    resetIpo,
    setTradingLimit,
    updateIpo,
    updateIpoDefaults,
    updateMarketTimes,
    updateTransferFeeConfig,
} from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { twMerge } from "tailwind-merge";

export default function AdminPage() {
    const router = useRouter();

    const [adminToken, setAdminToken] = useState(null);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [notification, setNotification] = useState({
        show: false,
        message: "",
        type: "info",
    });

    // loading state
    const [givePointsLoading, setGivePointsLoading] = useState(false);
    const [tradingLimitLoading, setTradingLimitLoading] =
        useState(false);
    const [marketTimesLoading, setMarketTimesLoading] =
        useState(false);
    const [announcementLoading, setAnnouncementLoading] =
        useState(false);
    const [resetLoading, setResetLoading] = useState(false);
    const [userAssetsLoading, setUserAssetsLoading] = useState(false);
    const [forceSettlementLoading, setForceSettlementLoading] =
        useState(false);

    const [givePointsForm, setGivePointsForm] = useState({
        type: "user", // 'user', 'group', 'all_users', 'all_groups', 'multi_users', 'multi_groups'
        username: "",
        amount: "",
        multiTargets: [], // 多選目標列表
    });

    const [tradingLimitPercent, setTradingLimitPercent] =
        useState(10);
    const [marketTimes, setMarketTimes] = useState([]);
    const [userAssets, setUserAssets] = useState([]);
    const [systemStats, setSystemStats] = useState(null);
    const [userSearchTerm, setUserSearchTerm] = useState("");
    const [announcementForm, setAnnouncementForm] = useState({
        title: "",
        message: "",
        broadcast: true,
    });

    // 學員跟小隊列表
    const [students, setStudents] = useState([]);
    const [teams, setTeams] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [studentsLoading, setStudentsLoading] = useState(true); // 新增學員資料載入狀態

    // 市場狀態
    const [marketStatus, setMarketStatus] = useState(null);

    // IPO 管理狀態
    const [ipoStatus, setIpoStatus] = useState(null);
    const [ipoLoading, setIpoLoading] = useState(false);
    const [showIpoUpdateModal, setShowIpoUpdateModal] =
        useState(false);
    const [ipoUpdateForm, setIpoUpdateForm] = useState({
        sharesRemaining: "",
        initialPrice: "",
    });

    //隊伍相關
    const [teamNumber, setTeamNumber] = useState(0);

    // 集合競價狀態
    const [callAuctionLoading, setCallAuctionLoading] =
        useState(false);
    const [showCallAuctionModal, setShowCallAuctionModal] =
        useState(false);
    const [callAuctionResult, setCallAuctionResult] = useState(null);

    // IPO 預設設定狀態
    const [ipoDefaults, setIpoDefaults] = useState(null);
    const [showIpoDefaultsModal, setShowIpoDefaultsModal] =
        useState(false);
    const [ipoDefaultsForm, setIpoDefaultsForm] = useState({
        defaultInitialShares: "",
        defaultInitialPrice: "",
    });
    const [ipoDefaultsLoading, setIpoDefaultsLoading] =
        useState(false);

    // 市場開關控制狀態
    const [marketControlLoading, setMarketControlLoading] =
        useState(false);

    // 轉點數手續費設定狀態
    const [transferFeeConfig, setTransferFeeConfig] = useState(null);
    const [transferFeeLoading, setTransferFeeLoading] =
        useState(false);
    const [showTransferFeeModal, setShowTransferFeeModal] =
        useState(false);
    const [transferFeeForm, setTransferFeeForm] = useState({
        feeRate: "",
        minFee: "",
    });

    // 新增時間 Modal
    const [showAddTimeModal, setShowAddTimeModal] = useState(false);
    const [newTimeForm, setNewTimeForm] = useState({
        start: "7:00",
        end: "9:00",
    });

    // Danger Zone
    const [showResetConfirmModal, setShowResetConfirmModal] =
        useState(false);
    const [showResetResultModal, setShowResetResultModal] =
        useState(false);
    const [resetResult, setResetResult] = useState(null);
    const [
        showSettlementConfirmModal,
        setShowSettlementConfirmModal,
    ] = useState(false);
    const [showSettlementResultModal, setShowSettlementResultModal] =
        useState(false);
    const [settlementResult, setSettlementResult] = useState(null);

    const showNotification = (message, type = "info") => {
        setNotification({ show: true, message, type });
        setTimeout(() => {
            setNotification({
                show: false,
                message: "",
                type: "info",
            });
        }, 3000);
    };

    // 處理 401 錯誤的統一函數
    const handle401Error = () => {
        localStorage.removeItem("isAdmin");
        localStorage.removeItem("adminToken");
        localStorage.removeItem("adminCode");
        setIsLoggedIn(false);
        setAdminToken(null);
        router.push("/login");
    };

    // 統一的錯誤處理函數
    const handleApiError = (error, context = "") => {
        console.error(`${context}錯誤:`, error);
        if (error.status === 401) {
            handle401Error();
            showNotification("登入已過期，請重新登入", "error");
        } else {
            showNotification(
                `${context}失敗: ${error.message}`,
                "error",
            );
        }
    };

    // 檢查登入狀態
    useEffect(() => {
        let isMounted = true;

        const checkAuthAndInitialize = async () => {
            const isAdmin = localStorage.getItem("isAdmin");
            const token = localStorage.getItem("adminToken");

            if (!isAdmin || !token) {
                router.push("/login");
                return;
            }

            if (!isMounted) return;

            try {
                // 先測試 token 是否有效
                await getSystemStats(token);

                // Token 有效，設置狀態並初始化資料
                setAdminToken(token);
                setIsLoggedIn(true);

                if (isMounted) {
                    // 並行執行不相依的 API 調用，避免重複調用
                    await Promise.all([
                        fetchSystemStats(token),
                        fetchTradingHours(),
                        fetchIpoStatus(token),
                        fetchIpoDefaults(token),
                        fetchMarketStatus(token),
                        fetchTransferFeeConfig(token),
                    ]);

                    // 獲取使用者資料（包含學生列表）
                    const userData = await getUserAssets(token);
                    if (isMounted && Array.isArray(userData)) {
                        setStudents(userData);
                        setUserAssets(userData);
                        setStudentsLoading(false);
                        setUserAssetsLoading(false);
                    }

                    // 獲取團隊資料
                    const teamData = await getTeams(token);
                    if (isMounted && Array.isArray(teamData)) {
                        setTeams(teamData);
                        setTeamNumber(teamData.length);
                    }
                }
            } catch (error) {
                if (error.status === 401) {
                    handle401Error();
                } else {
                    console.error("初始化失敗:", error);
                    router.push("/login");
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
        localStorage.removeItem("isAdmin");
        localStorage.removeItem("adminToken");
        localStorage.removeItem("adminCode");
        setUserAssets([]);
        setSystemStats(null);
        router.push("/login");
    };

    // 撈學員的資料
    const fetchUserAssets = async (token, searchUser = null) => {
        try {
            setUserAssetsLoading(true);
            const data = await getUserAssets(token, searchUser);
            setUserAssets(data);
            // 如果沒有搜尋條件，同時更新學生列表
            if (!searchUser && Array.isArray(data)) {
                setStudents(data);
                setStudentsLoading(false);
            }
        } catch (error) {
            handleApiError(error, "獲取使用者資產");
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
            handleApiError(error, "獲取系統統計");
        }
    };

    // 撈學員列表 - 移除重複調用，改為使用已有的資料
    const fetchStudents = async (token) => {
        try {
            setStudentsLoading(true);
            // 檢查是否已經有資料，避免重複調用
            if (students.length > 0) {
                setStudentsLoading(false);
                return;
            }

            const data = await getUserAssets(token);
            console.log("學生資料:", data);
            if (Array.isArray(data)) {
                setStudents(data);
                // 同時更新使用者資產，避免重複調用
                setUserAssets(data);
            } else {
                console.error("學生資料格式錯誤:", data);
                setStudents([]);
            }
        } catch (error) {
            console.error("獲取學生列表錯誤:", error);
            setStudents([]);
            handleApiError(error, "獲取學生列表");
        } finally {
            setStudentsLoading(false);
        }
    };

    // 撈交易時間
    const fetchTradingHours = async () => {
        try {
            const data = await getTradingHours();
            if (data.tradingHours && data.tradingHours.length > 0) {
                const formattedTimes = data.tradingHours.map(
                    (slot) => {
                        const startDate = new Date(slot.start * 1000);
                        const endDate = new Date(slot.end * 1000);
                        return {
                            start: startDate
                                .toTimeString()
                                .slice(0, 5), // 轉 HH:MM Format
                            end: endDate.toTimeString().slice(0, 5),
                            favorite: false,
                        };
                    },
                );
                setMarketTimes(formattedTimes);
            }
        } catch (error) {
            console.error("獲取交易時間失敗:", error);
        }
    };

    // 撈IPO狀態
    const fetchIpoStatus = async (token) => {
        try {
            setIpoLoading(true);
            const data = await getIpoStatus(token);
            setIpoStatus(data);
        } catch (error) {
            handleApiError(error, "獲取IPO狀態");
        } finally {
            setIpoLoading(false);
        }
    };

    // 撈IPO預設設定
    const fetchIpoDefaults = async (token) => {
        try {
            setIpoDefaultsLoading(true);
            const data = await getIpoDefaults(token);
            setIpoDefaults(data);
        } catch (error) {
            handleApiError(error, "獲取IPO預設設定");
        } finally {
            setIpoDefaultsLoading(false);
        }
    };

    // 撈轉點數手續費設定
    const fetchTransferFeeConfig = async (token) => {
        try {
            setTransferFeeLoading(true);
            const data = await getTransferFeeConfig(token);
            setTransferFeeConfig(data);
        } catch (error) {
            handleApiError(error, "獲取轉點數手續費設定");
        } finally {
            setTransferFeeLoading(false);
        }
    };

    // 更新IPO
    const handleIpoUpdate = async () => {
        try {
            setIpoLoading(true);

            const sharesRemaining =
                ipoUpdateForm.sharesRemaining !== ""
                    ? parseInt(ipoUpdateForm.sharesRemaining)
                    : null;
            const initialPrice =
                ipoUpdateForm.initialPrice !== ""
                    ? parseInt(ipoUpdateForm.initialPrice)
                    : null;

            const result = await updateIpo(
                adminToken,
                sharesRemaining,
                initialPrice,
            );

            showNotification(result.message, "success");
            setShowIpoUpdateModal(false);
            setIpoUpdateForm({
                sharesRemaining: "",
                initialPrice: "",
            });

            // 重新取得IPO狀態
            await fetchIpoStatus(adminToken);
        } catch (error) {
            handleApiError(error, "IPO更新");
        } finally {
            setIpoLoading(false);
        }
    };

    // 重置IPO
    const handleIpoReset = async () => {
        try {
            setIpoLoading(true);
            const result = await resetIpo(adminToken);
            showNotification(result.message, "success");
            await fetchIpoStatus(adminToken);
        } catch (error) {
            handleApiError(error, "IPO重置");
        } finally {
            setIpoLoading(false);
        }
    };

    // 更新IPO預設設定
    const handleIpoDefaultsUpdate = async () => {
        try {
            setIpoDefaultsLoading(true);

            const defaultShares =
                ipoDefaultsForm.defaultInitialShares !== ""
                    ? parseInt(ipoDefaultsForm.defaultInitialShares)
                    : null;
            const defaultPrice =
                ipoDefaultsForm.defaultInitialPrice !== ""
                    ? parseInt(ipoDefaultsForm.defaultInitialPrice)
                    : null;

            const result = await updateIpoDefaults(
                adminToken,
                defaultShares,
                defaultPrice,
            );

            showNotification(result.message, "success");
            setShowIpoDefaultsModal(false);
            setIpoDefaultsForm({
                defaultInitialShares: "",
                defaultInitialPrice: "",
            });

            // 重新取得IPO預設設定
            await fetchIpoDefaults(adminToken);
        } catch (error) {
            handleApiError(error, "IPO預設設定更新");
        } finally {
            setIpoDefaultsLoading(false);
        }
    };

    // 更新轉點數手續費設定
    const handleTransferFeeUpdate = async () => {
        try {
            setTransferFeeLoading(true);

            const feeRate =
                transferFeeForm.feeRate !== ""
                    ? parseFloat(transferFeeForm.feeRate)
                    : null;
            const minFee =
                transferFeeForm.minFee !== ""
                    ? parseFloat(transferFeeForm.minFee)
                    : null;

            const result = await updateTransferFeeConfig(
                adminToken,
                feeRate,
                minFee,
            );

            showNotification(result.message, "success");
            setShowTransferFeeModal(false);
            setTransferFeeForm({ feeRate: "", minFee: "" });

            // 重新取得手續費設定
            await fetchTransferFeeConfig(adminToken);
        } catch (error) {
            handleApiError(error, "轉點數手續費設定更新");
        } finally {
            setTransferFeeLoading(false);
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

            if (result.success) {
                let message = result.message;

                // 如果有詳細統計，新增到通知中
                if (result.order_stats) {
                    const stats = result.order_stats;
                    const totalBuy =
                        (stats.pending_buy || 0) +
                        (stats.limit_buy || 0);
                    const totalSell =
                        (stats.pending_sell || 0) +
                        (stats.limit_sell || 0);
                    message += ` (處理了 ${totalBuy} 張買單、${totalSell} 張賣單)`;
                }

                showNotification(message, "success");
            } else {
                let errorMessage =
                    result.message || "集合競價執行失敗";

                // 如果有統計訊息，新增到錯誤消息中
                if (result.order_stats) {
                    const stats = result.order_stats;
                    const totalPending =
                        (stats.pending_buy || 0) +
                        (stats.pending_sell || 0);
                    const totalLimit =
                        (stats.limit_buy || 0) +
                        (stats.limit_sell || 0);
                    if (totalPending > 0 || totalLimit > 0) {
                        errorMessage += ` (目前有 ${totalPending} 張待撮合訂單、${totalLimit} 張限制等待訂單)`;
                    }
                }

                showNotification(errorMessage, "error");
            }
        } catch (error) {
            handleApiError(error, "集合競價執行");
        } finally {
            setCallAuctionLoading(false);
        }
    };
    const fetchMarketStatus = async (token = adminToken) => {
        try {
            const status = await getAdminMarketStatus(token);
            setMarketStatus(status);
        } catch (error) {
            console.error("取得市場狀態失敗:", error);
        }
    };

    const handleOpenMarket = async () => {
        try {
            setMarketControlLoading(true);
            const result = await openMarket(adminToken);
            if (result.success) {
                showNotification(result.message, "success");
                await fetchMarketStatus(adminToken);

                // 如果有集合競價結果就顯示詳細訊息
                if (
                    result.call_auction_result &&
                    result.call_auction_result.success
                ) {
                    const auctionResult = result.call_auction_result;
                    const auctionMessage = `集合競價完成：${auctionResult.matched_volume} 股於 ${auctionResult.auction_price} 元成交`;
                    setTimeout(
                        () =>
                            showNotification(auctionMessage, "info"),
                        3000,
                    );
                }
            } else {
                showNotification(
                    result.message || "開盤失敗",
                    "error",
                );
            }
        } catch (error) {
            handleApiError(error, "市場開盤");
        } finally {
            setMarketControlLoading(false);
        }
    };

    const handleCloseMarket = async () => {
        try {
            setMarketControlLoading(true);
            const result = await closeMarket(adminToken);
            if (result.success) {
                showNotification(result.message, "success");

                await fetchMarketStatus(adminToken);
            } else {
                showNotification(
                    result.message || "收盤失敗",
                    "error",
                );
            }
        } catch (error) {
            handleApiError(error, "市場收盤");
        } finally {
            setMarketControlLoading(false);
        }
    };

    // 搜尋建議
    const handleUsernameChange = (value) => {
        setGivePointsForm({
            ...givePointsForm,
            username: value,
        });

        if (value.trim() === "" || studentsLoading) {
            setSuggestions([]);
            setShowSuggestions(false);
            return;
        }

        let filteredSuggestions = [];

        if (
            givePointsForm.type === "user" ||
            givePointsForm.type === "multi_users"
        ) {
            // 查學員 - 加強錯誤檢查
            console.log(
                "搜尋學生:",
                value,
                "學生列表長度:",
                students.length,
            ); // Debug用
            if (Array.isArray(students)) {
                filteredSuggestions = students
                    .filter(
                        (student) =>
                            student &&
                            typeof student.username === "string" &&
                            student.username
                                .toLowerCase()
                                .includes(value.toLowerCase()),
                    )
                    .map((student) => ({
                        value: student.username,
                        label: `${student.username}${student.team ? ` (${student.team})` : ""}`,
                        type: "user",
                    }));
            } else {
                console.warn("學生資料不是陣列:", students);
            }
        } else if (
            givePointsForm.type === "group" ||
            givePointsForm.type === "multi_groups"
        ) {
            // 查小隊 - 加強錯誤檢查
            console.log(
                "搜尋團隊:",
                value,
                "團隊列表長度:",
                teams.length,
            ); // Debug用
            if (Array.isArray(teams)) {
                filteredSuggestions = teams
                    .filter(
                        (team) =>
                            team &&
                            typeof team.name === "string" &&
                            team.name
                                .toLowerCase()
                                .includes(value.toLowerCase()),
                    )
                    .map((team) => ({
                        value: team.name,
                        label: `${team.name}${team.member_count ? ` (${team.member_count}人)` : ""}`,
                        type: "group",
                    }));
            } else {
                console.warn("團隊資料不是陣列:", teams);
            }
        }

        console.log("過濾後的建議:", filteredSuggestions); // Debug用
        setSuggestions(filteredSuggestions.slice(0, 5));
        setShowSuggestions(filteredSuggestions.length > 0);
    };

    const selectSuggestion = (suggestion) => {
        setGivePointsForm({
            ...givePointsForm,
            username: suggestion.value,
        });
        setShowSuggestions(false);
        setSuggestions([]);
    };

    // 多選功能：新增目標到列表
    const addMultiTarget = (suggestion) => {
        if (
            !givePointsForm.multiTargets.find(
                (target) => target.value === suggestion.value,
            )
        ) {
            setGivePointsForm({
                ...givePointsForm,
                multiTargets: [
                    ...givePointsForm.multiTargets,
                    suggestion,
                ],
                username: "",
            });
        }
        setShowSuggestions(false);
        setSuggestions([]);
    };

    // 多選功能：從列表移除目標
    const removeMultiTarget = (targetValue) => {
        setGivePointsForm({
            ...givePointsForm,
            multiTargets: givePointsForm.multiTargets.filter(
                (target) => target.value !== targetValue,
            ),
        });
    };

    const handleGivePoints = async () => {
        setGivePointsLoading(true);
        try {
            const amount = parseInt(givePointsForm.amount);

            if (givePointsForm.type === "all_users") {
                // 發放給全部使用者
                const promises = students.map((student) =>
                    givePoints(
                        adminToken,
                        student.username,
                        "user",
                        amount,
                    ),
                );
                await Promise.all(promises);
                showNotification(
                    `成功發放 ${amount} 點給 ${students.length} 位使用者！`,
                    "success",
                );
            } else if (givePointsForm.type === "all_groups") {
                // 發放給全部團隊全部團隊
                const promises = teams.map((team) =>
                    givePoints(
                        adminToken,
                        team.name,
                        "group",
                        amount,
                    ),
                );
                await Promise.all(promises);
                showNotification(
                    `成功發放 ${amount} 點給 ${teams.length} 個團隊！`,
                    "success",
                );
            } else if (
                givePointsForm.type === "multi_users" ||
                givePointsForm.type === "multi_groups"
            ) {
                // 多選模式
                const targetType =
                    givePointsForm.type === "multi_users"
                        ? "user"
                        : "group";
                const promises = givePointsForm.multiTargets.map(
                    (target) =>
                        givePoints(
                            adminToken,
                            target.value,
                            targetType,
                            amount,
                        ),
                );
                await Promise.all(promises);
                showNotification(
                    `成功發放 ${amount} 點給 ${givePointsForm.multiTargets.length} 個目標！`,
                    "success",
                );
            } else {
                // 單一目標模式
                await givePoints(
                    adminToken,
                    givePointsForm.username,
                    givePointsForm.type,
                    amount,
                );
                showNotification("點數發放成功！", "success");
            }

            await fetchSystemStats(adminToken);
            setGivePointsForm({
                type: givePointsForm.type,
                username: "",
                amount: "",
                multiTargets: [],
            });

            setSuggestions([]);
            setShowSuggestions(false);
        } catch (error) {
            handleApiError(error, "發放點數");
        }
        setGivePointsLoading(false);
    };

    const handleSetTradingLimit = async () => {
        setTradingLimitLoading(true);
        try {
            await setTradingLimit(
                adminToken,
                parseFloat(tradingLimitPercent),
            );
            showNotification("交易限制設定成功！", "success");
        } catch (error) {
            handleApiError(error, "設定交易限制");
        }
        setTradingLimitLoading(false);
    };

    // 時間管理 Modal
    const openAddTimeModal = () => {
        setNewTimeForm({ start: "7:00", end: "9:00" });
        setShowAddTimeModal(true);
    };

    const closeAddTimeModal = () => {
        setShowAddTimeModal(false);
        setNewTimeForm({ start: "7:00", end: "9:00" });
    };

    const handleAddNewTime = () => {
        setMarketTimes([
            ...marketTimes,
            { ...newTimeForm, favorite: false },
        ]);
        closeAddTimeModal();
    };

    const removeMarketTime = (index) => {
        const newTimes = marketTimes.filter((_, i) => i !== index);
        setMarketTimes(newTimes);
    };
    const saveMarketTimes = async () => {
        setMarketTimesLoading(true);
        try {
            const openTime = marketTimes.map((time) => {
                const today = new Date();
                const startTime = new Date(
                    today.toDateString() + " " + time.start,
                );
                const endTime = new Date(
                    today.toDateString() + " " + time.end,
                );

                return {
                    start: Math.floor(startTime.getTime() / 1000),
                    end: Math.floor(endTime.getTime() / 1000),
                };
            });

            await updateMarketTimes(adminToken, openTime);
            showNotification("市場時間設定成功！", "success");
        } catch (error) {
            handleApiError(error, "設定市場時間");
        }
        setMarketTimesLoading(false);
    };

    // 查學員
    const handleUserSearch = () => {
        if (adminToken) {
            fetchUserAssets(
                adminToken,
                userSearchTerm.trim() || null,
            );
        }
    };

    // 發布公告
    const handleCreateAnnouncement = async () => {
        if (
            !announcementForm.title.trim() ||
            !announcementForm.message.trim()
        ) {
            showNotification("請填寫公告標題和內容", "error");
            return;
        }

        setAnnouncementLoading(true);
        try {
            await createAnnouncement(
                adminToken,
                announcementForm.title,
                announcementForm.message,
                announcementForm.broadcast,
            );

            showNotification("公告發布成功！", "success");
            setAnnouncementForm({
                title: "",
                message: "",
                broadcast: true,
            });
        } catch (error) {
            handleApiError(error, "發布公告");
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
            showNotification("資料重置完成", "success");
        } catch (error) {
            handleApiError(error, "重置資料");
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
            showNotification("強制結算完成！", "success");

            // 重新獲取統計資料
            await fetchSystemStats(adminToken);
            await fetchUserAssets(adminToken);
        } catch (error) {
            handleApiError(error, "強制結算");
        }
        setForceSettlementLoading(false);
    };

    // 未登入時顯示載入畫面
    if (!isLoggedIn) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-white border-t-transparent"></div>
                    <p className="text-white">正在檢查登入狀態...</p>
                </div>
            </div>
        );
    }
    return (
        <div className="min-h-screen bg-[#0f203e] pb-24">
            {/* 通知彈窗 */}
            {notification.show && (
                <div
                    className={twMerge(
                        "fixed top-4 right-4 left-4 z-50 rounded-xl px-4 py-3 shadow-lg transition-all duration-300",
                        notification.type === "success"
                            ? "bg-green-600 text-white"
                            : notification.type === "error"
                              ? "bg-red-600 text-white"
                              : "bg-blue-600 text-white",
                    )}
                >
                    <div className="flex items-center space-x-2">
                        {notification.type === "success" && (
                            <svg
                                className="h-5 w-5 flex-shrink-0"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M5 13l4 4L19 7"
                                />
                            </svg>
                        )}
                        {notification.type === "error" && (
                            <svg
                                className="h-5 w-5 flex-shrink-0"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M6 18L18 6M6 6l12 12"
                                />
                            </svg>
                        )}
                        <span className="text-sm break-words">
                            {notification.message}
                        </span>
                    </div>
                </div>
            )}

            <div className="mx-auto max-w-xl space-y-6 px-4 py-8">
                <div className="mb-6 flex items-center justify-between">
                    <div>
                        <h1 className="mb-1 text-2xl font-bold text-[#AFE1F5]">
                           歡迎，{"康喔"}！
                        </h1>
                        <p className="text-sm text-[#7BC2E6]">
                            權限：點數發放、傳送公告、系統管理
                        </p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="rounded-xl bg-[#7BC2E6] px-4 py-2 text-black transition-colors hover:bg-[#6bb0d4]"
                    >
                        登出
                    </button>
                </div>

                {/* 系統統計 */}
                {systemStats && (
                    <div className="rounded-xl bg-[#1A325F] p-6">
                        <h2 className="mb-4 text-xl font-bold text-white">
                            統計
                        </h2>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="rounded-xl bg-[#0f203e] p-3 text-center">
                                <div className="text-2xl font-bold">
                                    {systemStats.total_users}
                                </div>
                                <div className="mt-1 text-sm text-gray-400">
                                    個使用者
                                </div>
                            </div>
                            <div className="rounded-xl bg-[#0f203e] p-3 text-center">
                                <div className="text-2xl font-bold">
                                    {teamNumber}
                                </div>
                                <div className="mt-1 text-sm text-gray-400">
                                    個隊伍
                                </div>
                            </div>
                            <div className="rounded-xl bg-[#0f203e] p-3 text-center">
                                <div className="text-2xl font-bold">
                                    {systemStats.total_points.toLocaleString()}
                                </div>
                                <div className="mt-1 text-sm text-gray-400">
                                    總點數
                                </div>
                            </div>
                            <div className="rounded-xl bg-[#0f203e] p-3 text-center">
                                <div className="text-2xl font-bold">
                                    {systemStats.total_stocks.toLocaleString()}
                                </div>
                                <div className="mt-1 text-sm text-gray-400">
                                    總股票數(單位:股)
                                </div>
                            </div>
                            <div className="col-span-2 rounded-xl bg-[#0f203e] p-3 text-center">
                                <div className="text-2xl font-bold">
                                    {systemStats.total_trades}
                                </div>
                                <div className="mt-1 text-sm text-gray-400">
                                    總交易數
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* 發點數 */}
                <div className="rounded-xl bg-[#1A325F] p-6">
                    <div className="space-y-4">
                        {/* 發放模式選擇 */}
                        <div className="space-y-4">
                            <label className="block text-sm font-medium text-[#7BC2E6]">
                                發放模式
                            </label>

                            {/* 個人/團隊切換 */}
                            <div className="flex items-center space-x-4">
                                <span className="text-[#7BC2E6]">
                                    個人
                                </span>
                                <label className="relative inline-flex cursor-pointer items-center">
                                    <input
                                        type="checkbox"
                                        checked={
                                            givePointsForm.type ===
                                                "group" ||
                                            givePointsForm.type ===
                                                "multi_groups"
                                        }
                                        onChange={(e) => {
                                            const isMulti =
                                                givePointsForm.type.startsWith(
                                                    "multi_",
                                                );
                                            let newType;

                                            if (isMulti) {
                                                newType = e.target
                                                    .checked
                                                    ? "multi_groups"
                                                    : "multi_users";
                                            } else {
                                                newType = e.target
                                                    .checked
                                                    ? "group"
                                                    : "user";
                                            }

                                            setGivePointsForm({
                                                ...givePointsForm,
                                                type: newType,
                                                username: "",
                                                multiTargets: [],
                                            });
                                            setShowSuggestions(false);
                                            setSuggestions([]);
                                        }}
                                        className="peer sr-only"
                                    />
                                    <div className="peer h-6 w-11 rounded-full border border-gray-600 bg-[#0f203e] peer-checked:bg-[#7BC2E6] peer-focus:outline-none after:absolute after:top-[2px] after:left-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
                                </label>
                                <span className="text-[#7BC2E6]">
                                    團隊
                                </span>
                            </div>

                            {/* 多選開關 */}
                            <div className="flex items-center space-x-4">
                                <span className="text-[#7BC2E6]">
                                    單選
                                </span>
                                <label className="relative inline-flex cursor-pointer items-center">
                                    <input
                                        type="checkbox"
                                        checked={givePointsForm.type.startsWith(
                                            "multi_",
                                        )}
                                        onChange={(e) => {
                                            const isGroup =
                                                givePointsForm.type ===
                                                    "group" ||
                                                givePointsForm.type ===
                                                    "multi_groups";
                                            const newType = e.target
                                                .checked
                                                ? isGroup
                                                    ? "multi_groups"
                                                    : "multi_users"
                                                : isGroup
                                                  ? "group"
                                                  : "user";

                                            setGivePointsForm({
                                                ...givePointsForm,
                                                type: newType,
                                                username: "",
                                                multiTargets: [],
                                            });
                                            setShowSuggestions(false);
                                            setSuggestions([]);
                                        }}
                                        className="peer sr-only"
                                    />
                                    <div className="peer h-6 w-11 rounded-full border border-gray-600 bg-[#0f203e] peer-checked:bg-[#7BC2E6] peer-focus:outline-none after:absolute after:top-[2px] after:left-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
                                </label>
                                <span className="text-[#7BC2E6]">
                                    多選
                                </span>
                            </div>

                            {/* 全選按鈕 - 只在多選模式下顯示 */}
                            {givePointsForm.type.startsWith(
                                "multi_",
                            ) && (
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        type="button"
                                        onClick={() => {
                                            const targetList =
                                                givePointsForm.type ===
                                                "multi_users"
                                                    ? students
                                                    : teams;
                                            const allTargets =
                                                targetList.map(
                                                    (item) => ({
                                                        value:
                                                            givePointsForm.type ===
                                                            "multi_users"
                                                                ? item.username
                                                                : item.name,
                                                        label:
                                                            givePointsForm.type ===
                                                            "multi_users"
                                                                ? `${item.username}${item.team ? ` (${item.team})` : ""}`
                                                                : `${item.name}${item.member_count ? ` (${item.member_count}人)` : ""}`,
                                                        type:
                                                            givePointsForm.type ===
                                                            "multi_users"
                                                                ? "user"
                                                                : "group",
                                                    }),
                                                );

                                            setGivePointsForm({
                                                ...givePointsForm,
                                                multiTargets:
                                                    allTargets,
                                                username: "",
                                            });
                                            setShowSuggestions(false);
                                            setSuggestions([]);
                                        }}
                                        className="rounded-lg bg-[#7BC2E6] px-4 py-2 text-sm text-black transition-colors hover:bg-[#6bb0d4]"
                                    >
                                        全選{" "}
                                        {givePointsForm.type ===
                                        "multi_users"
                                            ? `所有個人 (${students.length})`
                                            : `所有團隊 (${teams.length})`}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setGivePointsForm({
                                                ...givePointsForm,
                                                multiTargets: [],
                                                username: "",
                                            });
                                            setShowSuggestions(false);
                                            setSuggestions([]);
                                        }}
                                        disabled={
                                            givePointsForm
                                                .multiTargets
                                                .length === 0
                                        }
                                        className="rounded-lg bg-red-700/80 px-4 py-2 text-sm text-white transition-colors hover:bg-red-700/70 disabled:cursor-not-allowed disabled:bg-gray-600"
                                    >
                                        全部移除 (
                                        {
                                            givePointsForm
                                                .multiTargets.length
                                        }
                                        )
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* 條件顯示搜尋框 */}
                        {givePointsForm.type.startsWith("multi_") ||
                        ["user", "group"].includes(
                            givePointsForm.type,
                        ) ? (
                            <div className="relative">
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    {givePointsForm.type.startsWith(
                                        "multi_",
                                    )
                                        ? "新增目標（搜尋選擇）"
                                        : "給誰（搜尋選擇）"}
                                </label>
                                <input
                                    type="text"
                                    value={givePointsForm.username}
                                    onChange={(e) =>
                                        handleUsernameChange(
                                            e.target.value,
                                        )
                                    }
                                    onFocus={() => {
                                        // 重新觸發搜尋以顯示建議
                                        if (
                                            givePointsForm.username.trim() !==
                                            ""
                                        ) {
                                            handleUsernameChange(
                                                givePointsForm.username,
                                            );
                                        }
                                    }}
                                    onBlur={() => {
                                        // 延遲隱藏建議，讓點選事件能夠觸發
                                        setTimeout(
                                            () =>
                                                setShowSuggestions(
                                                    false,
                                                ),
                                            200,
                                        );
                                    }}
                                    disabled={studentsLoading}
                                    className="w-full rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:bg-[#0f203e] disabled:opacity-50"
                                    placeholder={
                                        studentsLoading
                                            ? "正在載入使用者資料..."
                                            : givePointsForm.type ===
                                                    "user" ||
                                                givePointsForm.type ===
                                                    "multi_users"
                                              ? "搜尋學生姓名..."
                                              : "搜尋團隊名稱..."
                                    }
                                />

                                {/* 搜尋建議下拉 */}
                                {showSuggestions &&
                                    suggestions.length > 0 && (
                                        <div className="absolute z-10 mt-1 max-h-48 w-full overflow-y-auto rounded-xl border border-[#469FD2] bg-[#0f203e] shadow-lg">
                                            {suggestions.map(
                                                (
                                                    suggestion,
                                                    index,
                                                ) => (
                                                    <div
                                                        key={index}
                                                        onMouseDown={(
                                                            e,
                                                        ) => {
                                                            e.preventDefault(); // 防止blur事件影響點選
                                                            if (
                                                                givePointsForm.type.startsWith(
                                                                    "multi_",
                                                                )
                                                            ) {
                                                                addMultiTarget(
                                                                    suggestion,
                                                                );
                                                            } else {
                                                                selectSuggestion(
                                                                    suggestion,
                                                                );
                                                            }
                                                        }}
                                                        className="cursor-pointer border-b border-[#469FD2] px-3 py-2 text-sm text-white transition-colors last:border-b-0 hover:bg-[#1A325F]"
                                                    >
                                                        <div className="flex items-center justify-between">
                                                            <span>
                                                                {
                                                                    suggestion.label
                                                                }
                                                            </span>
                                                            <span className="text-xs text-gray-400">
                                                                {suggestion.type ===
                                                                "user"
                                                                    ? "個人"
                                                                    : "團隊"}
                                                            </span>
                                                        </div>
                                                    </div>
                                                ),
                                            )}
                                        </div>
                                    )}
                            </div>
                        ) : null}

                        {/* 多選模式的已選目標列表 */}
                        {givePointsForm.type.startsWith("multi_") &&
                            givePointsForm.multiTargets.length >
                                0 && (
                                <div>
                                    <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                        已選擇的目標 (
                                        {
                                            givePointsForm
                                                .multiTargets.length
                                        }
                                        )
                                    </label>
                                    <div className="max-h-32 space-y-2 overflow-y-auto">
                                        {givePointsForm.multiTargets.map(
                                            (target, index) => (
                                                <div
                                                    key={index}
                                                    className="flex items-center justify-between rounded-lg bg-[#0f203e] px-3 py-2"
                                                >
                                                    <span className="text-sm text-white">
                                                        {target.label}
                                                    </span>
                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            removeMultiTarget(
                                                                target.value,
                                                            )
                                                        }
                                                        className="text-sm text-red-400 hover:text-red-300"
                                                    >
                                                        移除
                                                    </button>
                                                </div>
                                            ),
                                        )}
                                    </div>
                                </div>
                            )}

                        {/* 全部模式的說明 */}
                        {["all_users", "all_groups"].includes(
                            givePointsForm.type,
                        ) && (
                            <div className="rounded-lg border border-[#469FD2] bg-[#0f203e] p-3">
                                <p className="text-sm text-[#7BC2E6]">
                                    {givePointsForm.type ===
                                    "all_users"
                                        ? `將發放給所有 ${students.length} 位使用者`
                                        : `將發放給所有 ${teams.length} 個團隊`}
                                </p>
                            </div>
                        )}

                        <div>
                            <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                給多少
                            </label>
                            <input
                                type="number"
                                value={givePointsForm.amount}
                                onChange={(e) =>
                                    setGivePointsForm({
                                        ...givePointsForm,
                                        amount: e.target.value,
                                    })
                                }
                                className="w-full rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                        </div>

                        <div className="flex w-full items-center justify-center">
                            <button
                                onClick={handleGivePoints}
                                disabled={
                                    givePointsLoading ||
                                    !givePointsForm.amount ||
                                    (["user", "group"].includes(
                                        givePointsForm.type,
                                    ) &&
                                        !givePointsForm.username) ||
                                    (givePointsForm.type.startsWith(
                                        "multi_",
                                    ) &&
                                        givePointsForm.multiTargets
                                            .length === 0)
                                }
                                className="mx-auto rounded-lg bg-[#7BC2E6] px-4 py-2 font-medium text-black transition-colors hover:bg-[#6bb0d4] disabled:cursor-not-allowed disabled:bg-[#4a5568] disabled:text-[#a0aec0] disabled:hover:bg-[#4a5568]"
                            >
                                {givePointsLoading
                                    ? "發放中..."
                                    : "發點數"}
                            </button>
                        </div>
                    </div>
                </div>

                {/* 漲跌限制設定 */}
                <div className="rounded-xl bg-[#1A325F] p-6">
                    <h2 className="mb-4 text-lg text-[#7BC2E6]">
                        當日股票漲跌限制
                    </h2>
                    <div className="space-y-4">
                        <div className="relative">
                            <input
                                type="number"
                                min="0"
                                step="10"
                                value={tradingLimitPercent}
                                onChange={(e) => {
                                    const value = e.target.value;
                                    if (
                                        value === "" ||
                                        (!isNaN(value) &&
                                            parseFloat(value) >= 0)
                                    ) {
                                        setTradingLimitPercent(value);
                                    }
                                }}
                                placeholder="輸入百分比數字 (0-100)"
                                className="w-full rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 pr-8 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                            <span className="pointer-events-none absolute top-2 right-3 text-[#7BC2E6]">
                                %
                            </span>
                        </div>
                        <div className="flex w-full items-center justify-center">
                            <button
                                onClick={handleSetTradingLimit}
                                disabled={tradingLimitLoading}
                                className="mx-auto rounded-lg bg-[#7BC2E6] px-4 py-2 font-medium text-black transition-colors hover:bg-[#6bb0d4] disabled:cursor-not-allowed disabled:bg-[#4a5568] disabled:text-[#a0aec0] disabled:hover:bg-[#4a5568]"
                            >
                                {tradingLimitLoading
                                    ? "設定中..."
                                    : "設定"}
                            </button>
                        </div>
                    </div>
                </div>

                {/* 交易時間管理 */}
                <div className="rounded-xl bg-[#1A325F] p-6">
                    <div className="mb-4 flex items-center justify-between border-b-1 border-[#469FD2] pb-3">
                        <h2 className="text-lg text-[#7BC2E6]">
                            允許交易時間
                        </h2>
                        <div className="flex space-x-2">
                            <button
                                onClick={openAddTimeModal}
                                className="rounded-full bg-[#7BC2E6] p-1 text-xs text-black transition-colors"
                            >
                                <svg
                                    className="h-5 w-5"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                                    />
                                </svg>
                            </button>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {marketTimes.map((time, index) => (
                            <div
                                key={index}
                                className="flex items-center justify-between rounded-xl bg-[#0f203e] p-3"
                            >
                                <div className="flex flex-1 items-center space-x-3">
                                    <div className="text-yellow-400">
                                        <svg
                                            className="h-5 w-5"
                                            fill="currentColor"
                                            viewBox="0 0 24 24"
                                        >
                                            <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                                        </svg>
                                    </div>

                                    <div className="flex flex-1 items-center space-x-2">
                                        <span className="text-sm text-white">
                                            {time.start}
                                        </span>
                                        <span className="text-[#7BC2E6]">
                                            -
                                        </span>
                                        <span className="text-sm text-white">
                                            {time.end}
                                        </span>
                                    </div>
                                </div>

                                <button
                                    onClick={() =>
                                        removeMarketTime(index)
                                    }
                                    className="ml-2 p-1 text-red-400 transition-colors hover:text-red-300"
                                >
                                    <svg
                                        className="h-5 w-5"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                        />
                                    </svg>
                                </button>
                            </div>
                        ))}
                    </div>

                    <div className="mt-4 flex w-full items-center justify-center">
                        <button
                            onClick={saveMarketTimes}
                            disabled={marketTimesLoading}
                            className="mx-auto rounded-lg bg-[#7BC2E6] px-4 py-2 font-medium text-black transition-colors hover:bg-[#6bb0d4] disabled:cursor-not-allowed disabled:bg-[#4a5568] disabled:text-[#a0aec0] disabled:hover:bg-[#4a5568]"
                        >
                            {marketTimesLoading
                                ? "保存中..."
                                : "保存交易時間"}
                        </button>
                    </div>
                </div>

                {/* 發布公告 */}
                <div className="rounded-xl bg-[#1A325F] p-6">
                    <h2 className="mb-4 text-xl font-bold text-white">
                        發布公告
                    </h2>
                    <div className="space-y-4">
                        <div>
                            <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                公告標題
                            </label>
                            <input
                                type="text"
                                value={announcementForm.title}
                                onChange={(e) =>
                                    setAnnouncementForm({
                                        ...announcementForm,
                                        title: e.target.value,
                                    })
                                }
                                className="w-full rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                placeholder="輸入公告標題"
                            />
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                公告內容
                            </label>
                            <textarea
                                value={announcementForm.message}
                                onChange={(e) =>
                                    setAnnouncementForm({
                                        ...announcementForm,
                                        message: e.target.value,
                                    })
                                }
                                rows={4}
                                className="w-full resize-none rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                placeholder="輸入公告內容"
                            />
                        </div>

                        <div className="flex items-center space-x-3">
                            <input
                                type="checkbox"
                                id="broadcast"
                                checked={announcementForm.broadcast}
                                onChange={(e) =>
                                    setAnnouncementForm({
                                        ...announcementForm,
                                        broadcast: e.target.checked,
                                    })
                                }
                                className="h-4 w-4 cursor-pointer rounded border border-[#469FD2] bg-[#1A325F] text-blue-600 focus:ring-blue-500"
                            />
                            <label
                                htmlFor="broadcast"
                                className="cursor-pointer text-sm text-[#7BC2E6]"
                            >
                                廣播到 Telegram Bot
                            </label>
                        </div>

                        <div className="flex w-full items-center justify-center">
                            <button
                                onClick={handleCreateAnnouncement}
                                disabled={
                                    announcementLoading ||
                                    !announcementForm.title.trim() ||
                                    !announcementForm.message.trim()
                                }
                                className="mx-auto rounded-lg bg-[#7BC2E6] px-4 py-2 font-medium text-black transition-colors hover:bg-[#6bb0d4] disabled:cursor-not-allowed disabled:bg-[#4a5568] disabled:text-[#a0aec0] disabled:hover:bg-[#4a5568]"
                            >
                                {announcementLoading
                                    ? "發布中..."
                                    : "發布公告"}
                            </button>
                        </div>
                    </div>
                </div>

                {/* 使用者資產 */}
                <div className="rounded-xl bg-[#1A325F] p-6">
                    <h2 className="mb-4 text-xl font-bold text-white">
                        使用者資產明細
                    </h2>

                    <div className="mb-4 space-y-3">
                        <input
                            type="text"
                            value={userSearchTerm}
                            onChange={(e) =>
                                setUserSearchTerm(e.target.value)
                            }
                            placeholder="查詢使用者名稱..."
                            className="w-full rounded-xl border border-[#469FD2] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            onKeyPress={(e) =>
                                e.key === "Enter" &&
                                handleUserSearch()
                            }
                        />
                        <div className="flex space-x-2">
                            <button
                                onClick={handleUserSearch}
                                disabled={userAssetsLoading}
                                className="flex-1 rounded-xl bg-[#7bc2e6] px-4 py-2 text-black transition-colors hover:bg-[#6bb0d4] disabled:cursor-not-allowed disabled:bg-[#4a5568] disabled:text-[#a0aec0] disabled:hover:bg-[#4a5568]"
                            >
                                {userAssetsLoading
                                    ? "查詢中..."
                                    : "查詢"}
                            </button>
                            <button
                                onClick={() => {
                                    setUserSearchTerm("");
                                    fetchUserAssets(adminToken);
                                }}
                                disabled={userAssetsLoading}
                                className="flex-1 rounded-xl bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700 disabled:cursor-not-allowed disabled:bg-[#2d3748] disabled:text-[#718096] disabled:hover:bg-[#2d3748]"
                            >
                                {userAssetsLoading
                                    ? "返回中..."
                                    : "返回"}
                            </button>
                        </div>
                    </div>

                    {userAssetsLoading ? (
                        // Loading skeleton
                        <div className="space-y-3">
                            {[1, 2, 3].map((index) => (
                                <div
                                    key={index}
                                    className="animate-pulse rounded-xl bg-[#0f203e] p-4"
                                >
                                    <div className="mb-2 flex items-start justify-between">
                                        <div>
                                            <div className="mb-2 h-5 w-24 rounded bg-[#1A325F]"></div>
                                            <div className="h-4 w-16 rounded bg-[#1A325F]"></div>
                                        </div>
                                        <div className="text-right">
                                            <div className="mb-1 h-6 w-20 rounded bg-[#1A325F]"></div>
                                            <div className="h-3 w-12 rounded bg-[#1A325F]"></div>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-3 gap-2 text-sm">
                                        <div className="text-center">
                                            <div className="mx-auto mb-1 h-5 w-16 rounded bg-[#1A325F]"></div>
                                            <div className="mx-auto h-3 w-8 rounded bg-[#1A325F]"></div>
                                        </div>
                                        <div className="text-center">
                                            <div className="mx-auto mb-1 h-5 w-8 rounded bg-[#1A325F]"></div>
                                            <div className="mx-auto h-3 w-10 rounded bg-[#1A325F]"></div>
                                        </div>
                                        <div className="text-center">
                                            <div className="mx-auto mb-1 h-5 w-16 rounded bg-[#1A325F]"></div>
                                            <div className="mx-auto h-3 w-12 rounded bg-[#1A325F]"></div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : userAssets.length > 0 ? (
                        <div className="space-y-3">
                            {userAssets
                                .slice(0, 3)
                                .map((user, index) => (
                                    <div
                                        key={index}
                                        className="rounded-xl bg-[#0f203e] p-4"
                                    >
                                        <div className="mb-2 flex items-start justify-between">
                                            <div>
                                                <div className="font-medium text-white">
                                                    {user.username}
                                                </div>
                                                <div className="text-sm text-gray-400">
                                                    {user.team}
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="font-bold text-white">
                                                    {Math.round(
                                                        user.total,
                                                    ).toLocaleString()}
                                                </div>
                                                <div className="text-sm text-gray-400">
                                                    總資產
                                                </div>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-3 gap-2 text-sm">
                                            <div className="text-center">
                                                <div className="text-white">
                                                    {user.points.toLocaleString()}
                                                </div>
                                                <div className="text-xs text-gray-400">
                                                    點數
                                                </div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-white">
                                                    {user.stocks}
                                                </div>
                                                <div className="text-xs text-gray-400">
                                                    持股數
                                                </div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-white">
                                                    {Math.round(
                                                        user.stockValue,
                                                    ).toLocaleString()}
                                                </div>
                                                <div className="text-xs text-gray-400">
                                                    股票價值
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            {userAssets.length > 3 && (
                                <div className="mt-4 text-center text-sm text-gray-400">
                                    顯示前3位使用者，共
                                    {userAssets.length}位使用者
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="py-8 text-center text-gray-400">
                            暫無使用者資料
                        </div>
                    )}
                </div>

                {/* IPO 管理 */}

                <div className="rounded-xl bg-[#1A325F] p-6">
                    <div className="mb-4 flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white">
                            IPO 管理
                        </h2>
                        <button
                            onClick={() => fetchIpoStatus(adminToken)}
                            disabled={ipoLoading}
                            className="rounded-lg bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:bg-[#2d3748]"
                        >
                            {ipoLoading ? "載入中..." : "重新整理"}
                        </button>
                    </div>

                    {ipoStatus ? (
                        <div className="space-y-4">
                            {/* IPO 狀態顯示 */}
                            <div className="grid grid-cols-3 gap-4 rounded-xl bg-[#0f203e] p-4">
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-white">
                                        {ipoStatus.initialShares?.toLocaleString()}
                                    </div>
                                    <div className="text-sm text-gray-400">
                                        初始股數
                                    </div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-orange-400">
                                        {ipoStatus.sharesRemaining?.toLocaleString()}
                                    </div>
                                    <div className="text-sm text-gray-400">
                                        剩餘股數
                                    </div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-green-400">
                                        {ipoStatus.initialPrice}
                                    </div>
                                    <div className="text-sm text-gray-400">
                                        每股價格 (點)
                                    </div>
                                </div>
                            </div>

                            {/* 操作按鈕 */}
                            <div className="mb-3 grid grid-cols-2 gap-3">
                                <button
                                    onClick={() =>
                                        setShowIpoUpdateModal(true)
                                    }
                                    disabled={ipoLoading}
                                    className="rounded-xl bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700 disabled:bg-[#2d3748]"
                                >
                                    更新參數
                                </button>
                                <button
                                    onClick={handleIpoReset}
                                    disabled={ipoLoading}
                                    className="rounded-xl bg-orange-600 px-4 py-2 font-medium text-white transition-colors hover:bg-orange-700 disabled:bg-[#2d3748]"
                                >
                                    {ipoLoading
                                        ? "重置中..."
                                        : "重置IPO"}
                                </button>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    onClick={handleCallAuction}
                                    disabled={callAuctionLoading}
                                    className="rounded-xl bg-purple-600 px-4 py-2 font-medium text-white transition-colors hover:bg-purple-700 disabled:bg-[#2d3748]"
                                >
                                    {callAuctionLoading
                                        ? "撮合中..."
                                        : "集合競價"}
                                </button>
                                <button
                                    onClick={() =>
                                        setShowIpoDefaultsModal(true)
                                    }
                                    disabled={ipoDefaultsLoading}
                                    className="rounded-xl bg-green-600 px-4 py-2 font-medium text-white transition-colors hover:bg-green-700 disabled:bg-[#2d3748]"
                                >
                                    管理預設值
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="py-4 text-center text-gray-400">
                            {ipoLoading
                                ? "載入IPO狀態中..."
                                : "無法載入IPO狀態"}
                        </div>
                    )}
                </div>

                {/* 轉點數手續費設定 */}
                <div className="rounded-xl bg-[#1A325F] p-6">
                    <div className="mb-4 flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white">
                            轉點數手續費設定
                        </h2>
                        <button
                            onClick={() =>
                                fetchTransferFeeConfig(adminToken)
                            }
                            disabled={transferFeeLoading}
                            className="rounded-lg bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:bg-[#2d3748]"
                        >
                            {transferFeeLoading
                                ? "載入中..."
                                : "重新整理"}
                        </button>
                    </div>

                    {transferFeeConfig ? (
                        <div className="space-y-4">
                            {/* 手續費配置顯示 */}
                            <div className="grid grid-cols-2 gap-4 rounded-xl bg-[#0f203e] p-4">
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-white">
                                        {transferFeeConfig.feeRate.toFixed(
                                            1,
                                        )}
                                        %
                                    </div>
                                    <div className="text-sm text-gray-400">
                                        手續費率
                                    </div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-orange-400">
                                        {transferFeeConfig.minFee}
                                    </div>
                                    <div className="text-sm text-gray-400">
                                        最低手續費 (點)
                                    </div>
                                </div>
                            </div>

                            {/* 操作按鈕 */}
                            <div className="grid grid-cols-1 gap-3">
                                <button
                                    onClick={() => {
                                        setTransferFeeForm({
                                            feeRate:
                                                transferFeeConfig.feeRate.toString(),
                                            minFee: transferFeeConfig.minFee.toString(),
                                        });
                                        setShowTransferFeeModal(true);
                                    }}
                                    disabled={transferFeeLoading}
                                    className="rounded-xl bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700 disabled:bg-[#2d3748]"
                                >
                                    修改設定
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="py-4 text-center text-gray-400">
                            {transferFeeLoading
                                ? "載入手續費設定中..."
                                : "無法載入手續費設定"}
                        </div>
                    )}
                </div>

                {/* 市場開關控制 */}

                <div className="rounded-xl bg-[#1A325F] p-6">
                    <h2 className="mb-4 text-xl font-bold text-white">
                        市場開關控制
                    </h2>

                    {/* 市場狀態顯示 */}
                    {marketStatus && (
                        <div className="mb-6 rounded-lg bg-[#0f203e] p-4">
                            <div className="mb-2 flex items-center justify-between">
                                <span className="text-gray-300">
                                    市場狀態:
                                </span>
                                <span
                                    className={twMerge(
                                        "rounded-full px-3 py-1 text-sm font-medium",
                                        marketStatus.is_open
                                            ? "bg-green-600 text-green-100"
                                            : "bg-red-600 text-red-100",
                                    )}
                                >
                                    {marketStatus.is_open
                                        ? "開盤中"
                                        : "已收盤"}
                                </span>
                            </div>
                            {marketStatus.last_updated && (
                                <div className="text-sm text-gray-400">
                                    最後更新:{" "}
                                    {new Date(
                                        marketStatus.last_updated,
                                    ).toLocaleString("zh-TW")}
                                </div>
                            )}
                            {marketStatus.last_action && (
                                <div className="text-sm text-gray-400">
                                    上次操作:{" "}
                                    {marketStatus.last_action ===
                                    "open"
                                        ? "開盤"
                                        : "收盤"}
                                </div>
                            )}
                        </div>
                    )}

                    {/* 控制按鈕 */}
                    <div className="grid grid-cols-2 gap-4">
                        <button
                            onClick={handleOpenMarket}
                            disabled={
                                marketControlLoading ||
                                (marketStatus && marketStatus.is_open)
                            }
                            className="rounded-xl bg-green-600 px-6 py-3 font-medium text-white transition-colors hover:bg-green-700 disabled:bg-[#2d3748] disabled:text-gray-500"
                        >
                            {marketControlLoading ? (
                                "處理中..."
                            ) : (
                                <p>
                                    開盤
                                    <br />
                                    (含集合競價)
                                </p>
                            )}
                        </button>
                        <button
                            onClick={handleCloseMarket}
                            disabled={
                                marketControlLoading ||
                                (marketStatus &&
                                    !marketStatus.is_open)
                            }
                            className="rounded-xl bg-red-600 px-6 py-3 font-medium text-white transition-colors hover:bg-red-700 disabled:bg-[#2d3748] disabled:text-gray-500"
                        >
                            {marketControlLoading
                                ? "處理中..."
                                : "收盤"}
                        </button>
                    </div>

                    <div className="mt-4 rounded-lg bg-[#0f203e] p-3">
                        <div className="text-sm text-gray-300">
                            <p className="mb-1">
                                <strong>開盤</strong>
                                ：會自動執行集合競價，然後開放市場交易
                            </p>
                            <p>
                                <strong>收盤</strong>
                                ：停止接受新的交易訂單
                            </p>
                        </div>
                    </div>
                </div>

                {/* Danger Zone */}

                <div className="rounded-xl border-2 border-red-500 bg-[#1A325F] p-6">
                    <div className="mb-4 flex items-center">
                        <svg
                            className="mr-2 h-6 w-6 text-red-500"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z"
                            />
                        </svg>
                        <h2 className="text-xl font-bold text-red-500">
                            Danger Zone
                        </h2>
                    </div>
                    <div className="pt-2">
                        <div className="flex w-full flex-col justify-between gap-5">
                            <div>
                                <h3 className="font-medium text-white">
                                    強制結算
                                </h3>
                                <p className="text-sm text-gray-400">
                                    將所有使用者的持股以固定價格轉換為點數，並清除其股票
                                </p>
                            </div>
                            <button
                                onClick={openSettlementConfirmModal}
                                disabled={forceSettlementLoading}
                                className="w-full rounded-xl bg-red-600 px-4 py-2 font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-[#2d3748] disabled:text-[#718096] disabled:hover:bg-[#2d3748]"
                            >
                                {forceSettlementLoading
                                    ? "結算中..."
                                    : "強制結算"}
                            </button>
                        </div>

                        <div className="mt-6 flex w-full flex-col justify-between gap-5 border-t border-red-500 pt-6">
                            <div>
                                <h3 className="font-medium text-white">
                                    重置所有資料 (Dev)
                                </h3>
                                <p className="text-sm text-gray-400">
                                    永久刪除所有使用者資料、交易記錄和系統設定
                                </p>
                            </div>
                            <button
                                onClick={openResetConfirmModal}
                                disabled={resetLoading}
                                className="w-full rounded-xl bg-red-600 px-4 py-2 font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-[#2d3748] disabled:text-[#718096] disabled:hover:bg-[#2d3748]"
                            >
                                {resetLoading
                                    ? "處理中..."
                                    : "重置所有資料"}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* 新增時間 Modal */}
            {showAddTimeModal && (
                <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
                    <div className="w-full max-w-md rounded-xl bg-[#1A325F] p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-[#7BC2E6]">
                                新增交易時間
                            </h3>
                            <button
                                onClick={closeAddTimeModal}
                                className="text-gray-400 transition-colors hover:text-white"
                            >
                                <svg
                                    className="h-6 w-6"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    開始時間
                                </label>
                                <input
                                    type="time"
                                    value={newTimeForm.start}
                                    onChange={(e) =>
                                        setNewTimeForm({
                                            ...newTimeForm,
                                            start: e.target.value,
                                        })
                                    }
                                    className="w-full rounded-xl border border-[#469FD2] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                />
                            </div>

                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    結束時間
                                </label>
                                <input
                                    type="time"
                                    value={newTimeForm.end}
                                    onChange={(e) =>
                                        setNewTimeForm({
                                            ...newTimeForm,
                                            end: e.target.value,
                                        })
                                    }
                                    className="w-full rounded-xl border border-[#469FD2] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                />
                            </div>

                            <div className="mt-6 flex space-x-3">
                                <button
                                    onClick={closeAddTimeModal}
                                    className="flex-1 rounded-xl bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleAddNewTime}
                                    className="flex-1 rounded-xl bg-[#7BC2E6] px-4 py-2 text-black transition-colors hover:bg-[#6bb0d4]"
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
                <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
                    <div className="w-full max-w-md rounded-xl border-2 border-red-500 bg-[#1A325F] p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-red-500">
                                危險操作確認
                            </h3>
                            <button
                                onClick={closeResetConfirmModal}
                                className="text-gray-400 transition-colors hover:text-white"
                            >
                                <svg
                                    className="h-6 w-6"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="rounded-lg border border-red-600 bg-red-900 p-4">
                                <p className="mb-2 font-medium text-white">
                                    您即將重置所有系統資料！
                                </p>
                                <p className="text-sm text-red-200">
                                    這個操作將會把系統資料全部刪光，你要確定欸？
                                </p>
                            </div>

                            <div className="mt-6 flex space-x-3">
                                <button
                                    onClick={closeResetConfirmModal}
                                    className="flex-1 rounded-xl bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleResetAllData}
                                    disabled={resetLoading}
                                    className="flex-1 rounded-xl bg-red-600 px-4 py-2 font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-[#2d3748] disabled:text-[#718096] disabled:hover:bg-[#2d3748]"
                                >
                                    {resetLoading
                                        ? "重置中..."
                                        : "確認重置"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 強制結算確認 Modal */}
            {showSettlementConfirmModal && (
                <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
                    <div className="w-full max-w-md rounded-xl border-2 border-red-500 bg-[#1A325F] p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-red-500">
                                強制結算確認
                            </h3>
                            <button
                                onClick={closeSettlementConfirmModal}
                                className="text-gray-400 transition-colors hover:text-white"
                            >
                                <svg
                                    className="h-6 w-6"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="rounded-lg border border-orange-600 bg-orange-900 p-4">
                                <p className="mb-2 font-medium text-white">
                                    您即將執行強制結算！
                                </p>
                                <p className="text-sm text-orange-200">
                                    這個操作將會把所有使用者的持股以固定價格轉換為點數，並清除其股票。此操作無法復原！
                                </p>
                            </div>

                            <div className="mt-6 flex space-x-3">
                                <button
                                    onClick={
                                        closeSettlementConfirmModal
                                    }
                                    className="flex-1 rounded-xl bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleForceSettlement}
                                    disabled={forceSettlementLoading}
                                    className="flex-1 rounded-xl bg-red-600 px-4 py-2 font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-[#2d3748] disabled:text-[#718096] disabled:hover:bg-[#2d3748]"
                                >
                                    {forceSettlementLoading
                                        ? "結算中..."
                                        : "確認結算"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 強制結算結果 Modal */}
            {showSettlementResultModal && settlementResult && (
                <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
                    <div className="w-full max-w-md rounded-xl bg-[#1A325F] p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-green-500">
                                強制結算完成
                            </h3>
                            <button
                                onClick={closeSettlementResultModal}
                                className="text-gray-400 transition-colors hover:text-white"
                            >
                                <svg
                                    className="h-6 w-6"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="rounded-lg border border-[#469FD2] bg-[#0f203e] p-4">
                                <h4 className="mb-3 font-medium text-[#7BC2E6]">
                                    後端回應：
                                </h4>
                                <div className="max-h-96 overflow-auto rounded bg-gray-900 p-3 font-mono text-sm whitespace-pre-wrap text-gray-300">
                                    {JSON.stringify(
                                        settlementResult,
                                        null,
                                        2,
                                    )}
                                </div>
                            </div>

                            <div className="mt-6 flex justify-end">
                                <button
                                    onClick={
                                        closeSettlementResultModal
                                    }
                                    className="rounded-xl bg-[#7BC2E6] px-6 py-2 font-medium text-black transition-colors hover:bg-[#6bb0d4]"
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
                <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
                    <div className="w-full max-w-md rounded-xl bg-[#1A325F] p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-green-500">
                                重置完成
                            </h3>
                            <button
                                onClick={closeResetResultModal}
                                className="text-gray-400 transition-colors hover:text-white"
                            >
                                <svg
                                    className="h-6 w-6"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="rounded-lg border border-[#469FD2] bg-[#0f203e] p-4">
                                <h4 className="mb-3 font-medium text-[#7BC2E6]">
                                    後端回應：
                                </h4>
                                <div className="max-h-96 overflow-auto rounded bg-gray-900 p-3 font-mono text-sm whitespace-pre-wrap text-gray-300">
                                    {JSON.stringify(
                                        resetResult,
                                        null,
                                        2,
                                    )}
                                </div>
                            </div>

                            <div className="mt-6 flex justify-end">
                                <button
                                    onClick={closeResetResultModal}
                                    className="rounded-xl bg-[#7BC2E6] px-6 py-2 font-medium text-black transition-colors hover:bg-[#6bb0d4]"
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
                <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
                    <div className="w-full max-w-md rounded-xl bg-[#1A325F] p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-[#7BC2E6]">
                                更新 IPO 參數
                            </h3>
                            <button
                                onClick={() =>
                                    setShowIpoUpdateModal(false)
                                }
                                className="text-gray-400 transition-colors hover:text-white"
                            >
                                <svg
                                    className="h-6 w-6"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    剩餘股數 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    value={
                                        ipoUpdateForm.sharesRemaining
                                    }
                                    onChange={(e) =>
                                        setIpoUpdateForm({
                                            ...ipoUpdateForm,
                                            sharesRemaining:
                                                e.target.value,
                                        })
                                    }
                                    placeholder="例如: 0"
                                    className="w-full rounded-xl border border-[#469FD2] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                />
                                <p className="mt-1 text-xs text-gray-400">
                                    目前:{" "}
                                    {ipoStatus?.sharesRemaining?.toLocaleString()}{" "}
                                    股
                                </p>
                            </div>

                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    IPO 價格 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    value={ipoUpdateForm.initialPrice}
                                    onChange={(e) =>
                                        setIpoUpdateForm({
                                            ...ipoUpdateForm,
                                            initialPrice:
                                                e.target.value,
                                        })
                                    }
                                    placeholder="例如: 25"
                                    className="w-full rounded-xl border border-[#469FD2] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                />
                                <p className="mt-1 text-xs text-gray-400">
                                    目前: {ipoStatus?.initialPrice}{" "}
                                    點/股
                                </p>
                            </div>

                            <div className="rounded-lg border border-blue-600 bg-blue-900 p-3">
                                <p className="text-sm text-blue-200">
                                    💡 提示：設定剩餘股數為 0
                                    可以強制市價單使用限價單撮合，實現價格發現機制
                                </p>
                            </div>

                            <div className="mt-6 flex space-x-3">
                                <button
                                    onClick={() =>
                                        setShowIpoUpdateModal(false)
                                    }
                                    className="flex-1 rounded-xl bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleIpoUpdate}
                                    disabled={ipoLoading}
                                    className="flex-1 rounded-xl bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700 disabled:bg-[#2d3748]"
                                >
                                    {ipoLoading
                                        ? "更新中..."
                                        : "更新"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 集合競價結果 Modal */}
            {showCallAuctionModal && callAuctionResult && (
                <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
                    <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-xl bg-[#1A325F] p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-[#7BC2E6]">
                                集合競價結果
                            </h3>
                            <button
                                onClick={() =>
                                    setShowCallAuctionModal(false)
                                }
                                className="text-gray-400 transition-colors hover:text-white"
                            >
                                <svg
                                    className="h-6 w-6"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            {/* 結果總結 */}
                            <div
                                className={twMerge(
                                    "rounded-lg p-4",
                                    callAuctionResult.success
                                        ? "border border-green-600 bg-green-900"
                                        : "border border-red-600 bg-red-900",
                                )}
                            >
                                <h4
                                    className={twMerge(
                                        "mb-2 font-medium",
                                        callAuctionResult.success
                                            ? "text-green-200"
                                            : "text-red-200",
                                    )}
                                >
                                    {callAuctionResult.success
                                        ? "✅ 集合競價成功"
                                        : "❌ 集合競價失敗"}
                                </h4>
                                <p
                                    className={twMerge(
                                        "text-sm",
                                        callAuctionResult.success
                                            ? "text-green-300"
                                            : "text-red-300",
                                    )}
                                >
                                    {callAuctionResult.message}
                                </p>
                                {callAuctionResult.success && (
                                    <div className="mt-2 text-sm text-green-200">
                                        <p>
                                            撮合價格:{" "}
                                            {
                                                callAuctionResult.auction_price
                                            }{" "}
                                            元
                                        </p>
                                        <p>
                                            成交量:{" "}
                                            {
                                                callAuctionResult.matched_volume
                                            }{" "}
                                            股
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* 訂單統計 */}
                            {callAuctionResult.order_stats && (
                                <div className="rounded-lg border border-[#469FD2] bg-[#0f203e] p-4">
                                    <h4 className="mb-3 font-medium text-[#7BC2E6]">
                                        訂單統計
                                    </h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <h5 className="mb-2 font-medium text-white">
                                                買單
                                            </h5>
                                            <p className="text-sm text-gray-300">
                                                待撮合:{" "}
                                                {callAuctionResult
                                                    .order_stats
                                                    .pending_buy ||
                                                    0}{" "}
                                                張
                                            </p>
                                            <p className="text-sm text-gray-300">
                                                限制等待:{" "}
                                                {callAuctionResult
                                                    .order_stats
                                                    .limit_buy ||
                                                    0}{" "}
                                                張
                                            </p>
                                            <p className="text-sm text-yellow-300">
                                                總計:{" "}
                                                {callAuctionResult
                                                    .order_stats
                                                    .total_buy_orders ||
                                                    0}{" "}
                                                張
                                            </p>
                                        </div>
                                        <div>
                                            <h5 className="mb-2 font-medium text-white">
                                                賣單
                                            </h5>
                                            <p className="text-sm text-gray-300">
                                                待撮合:{" "}
                                                {callAuctionResult
                                                    .order_stats
                                                    .pending_sell ||
                                                    0}{" "}
                                                張
                                            </p>
                                            <p className="text-sm text-gray-300">
                                                限制等待:{" "}
                                                {callAuctionResult
                                                    .order_stats
                                                    .limit_sell ||
                                                    0}{" "}
                                                張
                                            </p>
                                            <p className="text-sm text-yellow-300">
                                                總計:{" "}
                                                {callAuctionResult
                                                    .order_stats
                                                    .total_sell_orders ||
                                                    0}{" "}
                                                張
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* 訂單詳細列表 */}
                            {callAuctionResult.order_details && (
                                <div className="space-y-4">
                                    {/* 買單列表 */}
                                    <div className="rounded-lg border border-[#469FD2] bg-[#0f203e] p-4">
                                        <h4 className="mb-3 font-medium text-green-400">
                                            買單列表 (
                                            {callAuctionResult
                                                .order_details
                                                .buy_orders?.length ||
                                                0}{" "}
                                            筆)
                                        </h4>
                                        {callAuctionResult
                                            .order_details.buy_orders
                                            ?.length > 0 ? (
                                            <div className="max-h-40 space-y-2 overflow-y-auto">
                                                {callAuctionResult.order_details.buy_orders.map(
                                                    (
                                                        order,
                                                        index,
                                                    ) => (
                                                        <div
                                                            key={
                                                                index
                                                            }
                                                            className="flex items-center justify-between rounded bg-[#1A325F] p-2 text-sm"
                                                        >
                                                            <div>
                                                                <span className="font-medium text-white">
                                                                    {
                                                                        order.username
                                                                    }
                                                                </span>
                                                                <span
                                                                    className={twMerge(
                                                                        "ml-2 rounded px-2 py-1 text-xs",
                                                                        order.status ===
                                                                            "pending"
                                                                            ? "bg-yellow-600 text-yellow-100"
                                                                            : "bg-orange-600 text-orange-100",
                                                                    )}
                                                                >
                                                                    {order.status ===
                                                                    "pending"
                                                                        ? "待撮合"
                                                                        : "限制等待"}
                                                                </span>
                                                            </div>
                                                            <div className="text-right">
                                                                <div className="font-medium text-green-400">
                                                                    {
                                                                        order.price
                                                                    }{" "}
                                                                    元
                                                                    x{" "}
                                                                    {
                                                                        order.quantity
                                                                    }{" "}
                                                                    股
                                                                </div>
                                                                <div className="text-xs text-gray-400">
                                                                    {new Date(
                                                                        order.created_at,
                                                                    ).toLocaleString()}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ),
                                                )}
                                            </div>
                                        ) : (
                                            <p className="text-sm text-gray-400">
                                                無買單
                                            </p>
                                        )}
                                    </div>

                                    {/* 賣單列表 */}
                                    <div className="rounded-lg border border-[#469FD2] bg-[#0f203e] p-4">
                                        <h4 className="mb-3 font-medium text-red-400">
                                            賣單列表 (
                                            {callAuctionResult
                                                .order_details
                                                .sell_orders
                                                ?.length || 0}{" "}
                                            筆)
                                        </h4>
                                        {callAuctionResult
                                            .order_details.sell_orders
                                            ?.length > 0 ? (
                                            <div className="max-h-40 space-y-2 overflow-y-auto">
                                                {callAuctionResult.order_details.sell_orders.map(
                                                    (
                                                        order,
                                                        index,
                                                    ) => (
                                                        <div
                                                            key={
                                                                index
                                                            }
                                                            className="flex items-center justify-between rounded bg-[#1A325F] p-2 text-sm"
                                                        >
                                                            <div>
                                                                <span className="font-medium text-white">
                                                                    {
                                                                        order.username
                                                                    }
                                                                </span>
                                                                <span
                                                                    className={twMerge(
                                                                        "ml-2 rounded px-2 py-1 text-xs",
                                                                        order.status ===
                                                                            "pending"
                                                                            ? "bg-yellow-600 text-yellow-100"
                                                                            : "bg-orange-600 text-orange-100",
                                                                    )}
                                                                >
                                                                    {order.status ===
                                                                    "pending"
                                                                        ? "待撮合"
                                                                        : "限制等待"}
                                                                </span>
                                                            </div>
                                                            <div className="text-right">
                                                                <div className="font-medium text-red-400">
                                                                    {
                                                                        order.price
                                                                    }{" "}
                                                                    元
                                                                    x{" "}
                                                                    {
                                                                        order.quantity
                                                                    }{" "}
                                                                    股
                                                                </div>
                                                                <div className="text-xs text-gray-400">
                                                                    {new Date(
                                                                        order.created_at,
                                                                    ).toLocaleString()}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ),
                                                )}
                                            </div>
                                        ) : (
                                            <p className="text-sm text-gray-400">
                                                無賣單
                                            </p>
                                        )}
                                    </div>
                                </div>
                            )}

                            <div className="mt-6 flex justify-end">
                                <button
                                    onClick={() =>
                                        setShowCallAuctionModal(false)
                                    }
                                    className="rounded-xl bg-[#7BC2E6] px-6 py-2 font-medium text-black transition-colors hover:bg-[#6bb0d4]"
                                >
                                    關閉
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* IPO 預設設定 Modal */}
            {showIpoDefaultsModal && (
                <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
                    <div className="w-full max-w-md rounded-xl bg-[#1A325F] p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-[#7BC2E6]">
                                IPO 預設設定管理
                            </h3>
                            <button
                                onClick={() =>
                                    setShowIpoDefaultsModal(false)
                                }
                                className="text-gray-400 transition-colors hover:text-white"
                            >
                                <svg
                                    className="h-6 w-6"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    預設初始股數 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    value={
                                        ipoDefaultsForm.defaultInitialShares
                                    }
                                    onChange={(e) =>
                                        setIpoDefaultsForm({
                                            ...ipoDefaultsForm,
                                            defaultInitialShares:
                                                e.target.value,
                                        })
                                    }
                                    placeholder="例如: 1000000"
                                    className="w-full rounded-xl border border-[#469FD2] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                />
                                <p className="mt-1 text-xs text-gray-400">
                                    目前:{" "}
                                    {ipoDefaults?.defaultInitialShares?.toLocaleString()}{" "}
                                    股
                                </p>
                            </div>

                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    預設IPO價格 (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    value={
                                        ipoDefaultsForm.defaultInitialPrice
                                    }
                                    onChange={(e) =>
                                        setIpoDefaultsForm({
                                            ...ipoDefaultsForm,
                                            defaultInitialPrice:
                                                e.target.value,
                                        })
                                    }
                                    placeholder="例如: 20"
                                    className="w-full rounded-xl border border-[#469FD2] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                />
                                <p className="mt-1 text-xs text-gray-400">
                                    目前:{" "}
                                    {ipoDefaults?.defaultInitialPrice}{" "}
                                    點/股
                                </p>
                            </div>

                            <div className="rounded-lg border border-green-600 bg-green-900 p-3">
                                <p className="text-sm text-green-200">
                                    ⚙️
                                    這些設定將用於未來的IPO重置操作，不會影響目前的IPO狀態
                                </p>
                            </div>

                            <div className="mt-6 flex space-x-3">
                                <button
                                    onClick={() =>
                                        setShowIpoDefaultsModal(false)
                                    }
                                    className="flex-1 rounded-xl bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleIpoDefaultsUpdate}
                                    disabled={ipoDefaultsLoading}
                                    className="flex-1 rounded-xl bg-green-600 px-4 py-2 text-white transition-colors hover:bg-green-700 disabled:bg-[#2d3748]"
                                >
                                    {ipoDefaultsLoading
                                        ? "更新中..."
                                        : "更新設定"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 轉點數手續費設定 Modal */}
            {showTransferFeeModal && (
                <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
                    <div className="w-full max-w-md rounded-xl bg-[#1A325F] p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-[#7BC2E6]">
                                轉點數手續費設定
                            </h3>
                            <button
                                onClick={() =>
                                    setShowTransferFeeModal(false)
                                }
                                className="text-gray-400 transition-colors hover:text-white"
                            >
                                <svg
                                    className="h-6 w-6"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    手續費率 (%) (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    max="100"
                                    value={transferFeeForm.feeRate}
                                    onChange={(e) =>
                                        setTransferFeeForm({
                                            ...transferFeeForm,
                                            feeRate: e.target.value,
                                        })
                                    }
                                    placeholder="例如: 10"
                                    className="w-full rounded-xl border border-[#469FD2] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                />
                                <p className="mt-1 text-xs text-gray-400">
                                    目前:{" "}
                                    {transferFeeConfig
                                        ? transferFeeConfig.feeRate.toFixed(
                                              1,
                                          )
                                        : 0}
                                    %
                                </p>
                            </div>

                            <div>
                                <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                    最低手續費 (點) (留空則不更新)
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    value={transferFeeForm.minFee}
                                    onChange={(e) =>
                                        setTransferFeeForm({
                                            ...transferFeeForm,
                                            minFee: e.target.value,
                                        })
                                    }
                                    placeholder="例如: 1"
                                    className="w-full rounded-xl border border-[#469FD2] bg-[#0f203e] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                />
                                <p className="mt-1 text-xs text-gray-400">
                                    目前:{" "}
                                    {transferFeeConfig?.minFee || 0}{" "}
                                    點
                                </p>
                            </div>

                            <div className="rounded-lg border border-blue-600 bg-blue-900 p-3">
                                <p className="text-sm text-blue-200">
                                    💡 提示：手續費 = max(轉帳金額 ×
                                    手續費率, 最低手續費)
                                </p>
                            </div>

                            <div className="mt-6 flex space-x-3">
                                <button
                                    onClick={() =>
                                        setShowTransferFeeModal(false)
                                    }
                                    className="flex-1 rounded-xl bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleTransferFeeUpdate}
                                    disabled={transferFeeLoading}
                                    className="flex-1 rounded-xl bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700 disabled:bg-[#2d3748]"
                                >
                                    {transferFeeLoading
                                        ? "更新中..."
                                        : "更新設定"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
