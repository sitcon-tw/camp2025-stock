"use client";

import { Modal } from "@/components/ui";
import {
    cancelWebStockOrder,
    getMyPermissions,
    getWebPointHistory,
    getWebPortfolio,
    getWebStockOrders,
    webTransferPoints,
    getUserAvatar,
    redeemQRCode,
} from "@/lib/api";
import dayjs from "dayjs";
import { LogOut, QrCode, Camera, X, DollarSign, CheckCircle2, Send, ArrowRight, Sparkles, Clock, ChevronDown } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { twMerge } from "tailwind-merge";
import QRCode from "react-qr-code";
import QrScanner from "qr-scanner";

export default function Dashboard() {
    const [isLoading, setIsLoading] = useState(true);
    const [user, setUser] = useState(null);
    const [studentList, setStudentList] = useState([]);
    const [pointHistory, setPointHistory] = useState([]);
    const [pointHistoryPage, setPointHistoryPage] = useState(0);
    const [orderHistory, setOrderHistory] = useState([]);
    const [orderHistoryPage, setOrderHistoryPage] = useState(0);
    const [authData, setAuthData] = useState(null);
    const [activeTab, setActiveTab] = useState("portfolio");
    const [error, setError] = useState("");
    const [cancelingOrders, setCancelingOrders] = useState(new Set());
    const [cancelSuccess, setCancelSuccess] = useState("");
    const [cancelError, setCancelError] = useState("");
    const [showCancelModal, setShowCancelModal] = useState(false);
    const [pendingCancelOrder, setPendingCancelOrder] =
        useState(null);
    const [userPermissions, setUserPermissions] = useState(null);
    const [useAvatarFallback, setUseAvatarFallback] = useState(false);
    const [showQRCode, setShowQRCode] = useState(false);
    const [showTransferModal, setShowTransferModal] = useState(false);
    const [showQRScanner, setShowQRScanner] = useState(false);
    const [showQuickTransfer, setShowQuickTransfer] = useState(false);
    const [quickTransferData, setQuickTransferData] = useState(null);
    const [transferForm, setTransferForm] = useState({
        to_username: "",
        amount: "",
        note: ""
    });
    const [transferLoading, setTransferLoading] = useState(false);
    const [transferError, setTransferError] = useState("");
    const [transferSuccess, setTransferSuccess] = useState("");
    const [receivedPayment, setReceivedPayment] = useState(null);
    const [showPaymentNotification, setShowPaymentNotification] = useState(false);
    const [lastPointHistory, setLastPointHistory] = useState([]);
    const [transferSuccessData, setTransferSuccessData] = useState(null);
    const [showTransferSuccess, setShowTransferSuccess] = useState(false);
    const [pointHistoryLimit, setPointHistoryLimit] = useState(10);
    const [pointHistoryLoading, setPointHistoryLoading] = useState(false);
    const [showLimitDropdown, setShowLimitDropdown] = useState(false);
    const videoRef = useRef(null);
    const qrScannerRef = useRef(null);
    const pollingIntervalRef = useRef(null);
    const limitDropdownRef = useRef(null);
    const router = useRouter();

    // 檢查大頭照圖片是否太小（Telegram 隱私設定導致的 1-4 像素圖片）
    const handleAvatarLoad = (event) => {
        const img = event.target;

        // 如果圖片太小，使用文字大頭照
        if (img.naturalWidth <= 10 || img.naturalHeight <= 10) {
            setUseAvatarFallback(true);
        } else {
            setUseAvatarFallback(false);
        }
    };

    // 登出功能
    const handleLogout = () => {
        // 清除所有認證相關的 localStorage
        localStorage.removeItem("isUser");
        localStorage.removeItem("userToken");
        localStorage.removeItem("userData");
        localStorage.removeItem("telegramData");
        localStorage.removeItem("isAdmin");
        localStorage.removeItem("adminToken");

        // 觸發自定義事件通知其他設定登入狀態已變更
        window.dispatchEvent(new Event("authStateChanged"));

        // 強制重新載入頁面以清除所有狀態
        window.location.href = "/telegram-login";
    };

    // 開啟取消訂單 Modal
    const openCancelModal = (orderData, orderType, quantity) => {
        // 從訂單物件中提取正確的 ID - 嘗試更多可能的字段
        const orderId =
            orderData._id ||
            orderData.id ||
            orderData.order_id ||
            orderData.orderId ||
            orderData["$oid"];

        console.log("=== 取消訂單Debug訊息 ===");
        console.log("完整訂單資料:", orderData);
        console.log("訂單物件的所有 keys:", Object.keys(orderData));
        console.log("嘗試提取的 ID:", orderId);
        console.log("ID 類型:", typeof orderId);
        console.log("訂單的使用者ID:", orderData.user_id);
        console.log("目前使用者資料:", user);

        // 從 localStorage 獲取真正的 telegram ID
        const telegramDataStr = localStorage.getItem("telegramData");
        const userDataStr = localStorage.getItem("userData");
        let telegramData = null;
        let userData = null;

        try {
            telegramData = JSON.parse(telegramDataStr);
            userData = JSON.parse(userDataStr);
        } catch (e) {
            console.error("無法解析 localStorage 資料:", e);
        }

        console.log("解析後的 telegramData:", telegramData);
        console.log("解析後的 userData:", userData);
        console.log("真正的 Telegram ID:", telegramData?.id);
        console.log("內部 User ID:", userData?.id);
        console.log("========================");

        if (!orderId) {
            console.error("無法從訂單物件中找到有效的 ID 字段");
            setCancelError("無法取得訂單 ID - 請檢查控制台Debug訊息");
            return;
        }

        setPendingCancelOrder({
            orderData,
            orderType,
            quantity,
            orderId,
        });
        setShowCancelModal(true);
    };

    // 確認取消訂單
    const confirmCancelOrder = async () => {
        if (!pendingCancelOrder) return;

        const { orderData, orderType, quantity, orderId } =
            pendingCancelOrder;

        const token = localStorage.getItem("userToken");
        if (!token) {
            setCancelError("認證已過期，請重新登入");
            setShowCancelModal(false);
            setPendingCancelOrder(null);
            return;
        }

        // 關閉 Modal
        setShowCancelModal(false);

        // 添加到取消中的訂單集合
        setCancelingOrders((prev) => new Set(prev).add(orderId));
        setCancelError("");
        setCancelSuccess("");

        try {
            const result = await cancelWebStockOrder(
                token,
                orderId,
                "使用者主動取消",
            );

            if (result.success) {
                setCancelSuccess("訂單已成功取消");

                // 重新載入訂單歷史
                try {
                    const updatedOrders =
                        await getWebStockOrders(token);
                    setOrderHistory(updatedOrders);
                } catch (refreshError) {
                    console.error("重新載入訂單失敗:", refreshError);
                }

                // 3秒後清除成功訊息
                setTimeout(() => setCancelSuccess(""), 3000);
            } else {
                setCancelError(result.message || "取消訂單失敗");
            }
        } catch (error) {
            console.error("取消訂單失敗:", error);
            setCancelError(error.message || "取消訂單時發生錯誤");
        } finally {
            // 從取消中的訂單集合移除
            setCancelingOrders((prev) => {
                const newSet = new Set(prev);
                newSet.delete(orderId);
                return newSet;
            });
            setPendingCancelOrder(null);
        }
    };

    // 關閉取消 Modal
    const closeCancelModal = () => {
        setShowCancelModal(false);
        setPendingCancelOrder(null);
    };

    // QR Code 和轉帳相關函數
    const openQRCode = () => {
        setShowQRCode(true);
    };

    const closeQRCode = () => {
        setShowQRCode(false);
    };

    const openTransferModal = () => {
        setTransferForm({ to_username: "", amount: "", note: "" });
        setTransferError("");
        setTransferSuccess("");
        setShowTransferModal(true);
    };

    const closeTransferModal = () => {
        setShowTransferModal(false);
        setTransferForm({ to_username: "", amount: "", note: "" });
        setTransferError("");
        setTransferSuccess("");
    };

    const startQRScanner = async () => {
        setShowQRScanner(true);
        setTransferError("");
        
        try {
            await new Promise(resolve => setTimeout(resolve, 100)); // 等待DOM更新
            
            if (videoRef.current) {
                qrScannerRef.current = new QrScanner(
                    videoRef.current,
                    result => {
                        console.log('QR Code 掃描結果:', result.data);
                        console.log('QR Code 數據長度:', result.data.length);
                        console.log('QR Code 數據類型:', typeof result.data);
                        
                        // 檢查是否為空字符串或無效數據
                        if (!result.data || result.data.trim() === '') {
                            console.error('QR Code 掃描到空數據');
                            setTransferError('QR Code 數據為空，請重新掃描');
                            return;
                        }
                        
                        try {
                            const qrData = JSON.parse(result.data);
                            console.log('解析後的 QR Data:', qrData);
                            console.log('Type:', qrData.type);
                            console.log('ID:', qrData.id);
                            console.log('Username:', qrData.username);
                            
                            if (qrData.type === 'transfer' && (qrData.id || qrData.username)) {
                                console.log('匹配到 transfer 類型，ID 或 username 存在');
                                // 嘗試獲取收款人的完整資訊（包括大頭照）
                                fetchRecipientInfo(qrData);
                            } else if (qrData.type === 'points_redeem' && qrData.id && qrData.points) {
                                console.log('匹配到 points_redeem 類型');
                                // 處理點數兌換 QR Code
                                handlePointsRedemption(result.data);
                            } else {
                                console.log('QR Code 不符合任何預期格式');
                                console.log('條件檢查結果:', {
                                    isTransfer: qrData.type === 'transfer',
                                    hasIdOrUsername: !!(qrData.id || qrData.username),
                                    isPointsRedeem: qrData.type === 'points_redeem',
                                    hasRequiredFields: !!(qrData.id && qrData.points)
                                });
                                setTransferError('無效的 QR Code');
                            }
                        } catch (e) {
                            console.error('QR Code 解析失敗:', e);
                            console.error('原始數據:', result.data);
                            console.error('原始數據編碼:', encodeURIComponent(result.data));
                            
                            // 嘗試不同的解析方式
                            if (result.data.includes('{"')) {
                                console.log('數據似乎包含 JSON，嘗試修復...');
                                // 嘗試找到 JSON 開始和結束位置
                                const jsonStart = result.data.indexOf('{');
                                const jsonEnd = result.data.lastIndexOf('}');
                                if (jsonStart !== -1 && jsonEnd !== -1 && jsonEnd > jsonStart) {
                                    const extractedJson = result.data.substring(jsonStart, jsonEnd + 1);
                                    console.log('提取的 JSON:', extractedJson);
                                    try {
                                        const qrData = JSON.parse(extractedJson);
                                        console.log('修復後解析成功:', qrData);
                                        if (qrData.type === 'transfer' && (qrData.id || qrData.username)) {
                                            fetchRecipientInfo(qrData);
                                            return;
                                        }
                                    } catch (fixError) {
                                        console.error('修復解析也失敗:', fixError);
                                    }
                                }
                            }
                            
                            setTransferError('QR Code 格式錯誤或數據損壞');
                        }
                    },
                    {
                        returnDetailedScanResult: true,
                        highlightScanRegion: true,
                        highlightCodeOutline: true,
                    }
                );
                
                await qrScannerRef.current.start();
            }
        } catch (error) {
            console.error('啟動相機失敗:', error);
            setTransferError('無法啟動相機，請檢查權限設定');
            setShowQRScanner(false);
        }
    };

    const stopQRScanner = () => {
        try {
            if (qrScannerRef.current) {
                qrScannerRef.current.stop();
                // 延遲銷毀以避免 document 訪問錯誤
                setTimeout(() => {
                    if (qrScannerRef.current) {
                        qrScannerRef.current.destroy();
                        qrScannerRef.current = null;
                    }
                }, 100);
            }
        } catch (error) {
            console.error('停止 QR Scanner 失敗:', error);
            qrScannerRef.current = null;
        }
        setShowQRScanner(false);
    };

    // 處理點數兌換 QR Code
    const handlePointsRedemption = async (qrData) => {
        try {
            const token = localStorage.getItem('userToken');
            if (!token) {
                throw new Error('未找到認證令牌');
            }

            // 呼叫兌換 API
            const result = await redeemQRCode(token, qrData);
            
            if (result.ok) {
                // 兌換成功，停止掃描器
                stopQRScanner();
                
                const qrInfo = JSON.parse(qrData);
                setTransferSuccess(`🎉 QR Code 兌換成功！獲得 ${result.points} 點數！`);
                
                // 觸發收款通知動畫
                const redemptionData = {
                    amount: result.points,
                    from: 'QR Code 兌換',
                    note: `QR Code 兌換 (${qrInfo.id})`,
                    timestamp: new Date().toISOString()
                };
                
                setReceivedPayment(redemptionData);
                setShowPaymentNotification(true);
                
                // 播放收款音效
                try {
                    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    
                    oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                    oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
                    oscillator.frequency.setValueAtTime(1200, audioContext.currentTime + 0.2);
                    
                    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                    
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.3);
                } catch (e) {
                    console.log('音效播放失敗:', e);
                }
                
                // 重新載入使用者資料
                try {
                    const [portfolio, points] = await Promise.all([
                        getWebPortfolio(token),
                        getWebPointHistory(token, pointHistoryLimit)
                    ]);
                    setUser(portfolio);
                    setPointHistory(points);
                    setLastPointHistory(points);
                } catch (refreshError) {
                    console.error('重新載入資料失敗:', refreshError);
                }
            } else {
                // 兌換失敗，保持掃描器開啟，只顯示錯誤訊息
                setTransferError(result.message || '兌換失敗');
                
                // 3秒後清除錯誤訊息，繼續掃描
                setTimeout(() => {
                    setTransferError('');
                }, 3000);
            }
        } catch (error) {
            console.error('兌換 QR Code 失敗:', error);
            // 兌換失敗，保持掃描器開啟，只顯示錯誤訊息
            setTransferError(error.message || '兌換失敗，請稍後再試');
            
            // 3秒後清除錯誤訊息，繼續掃描
            setTimeout(() => {
                setTransferError('');
            }, 3000);
        }
    };

    // 獲取收款人資訊
    const fetchRecipientInfo = async (qrData) => {
        try {
            console.log('開始處理收款人資訊:', qrData);
            const token = localStorage.getItem('userToken');
            if (!token) {
                throw new Error('未找到認證令牌');
            }

            // 先停止掃描器
            stopQRScanner();

            // 設定基本資料（作為fallback）
            // 優先使用 ID，如果 ID 不存在或無效，則使用 username
            const preferredIdentifier = qrData.id || qrData.username;
            console.log('使用識別符:', preferredIdentifier);
            
            const basicRecipientData = {
                username: String(preferredIdentifier),
                id: qrData.id ? String(qrData.id) : '',
                photo_url: null
            };

            console.log('設定基本收款人資料:', basicRecipientData);
            setQuickTransferData(basicRecipientData);
            setShowQuickTransfer(true);

            // 嘗試獲取收款人的大頭照和顯示名稱
            try {
                console.log('正在通過 API 獲取收款人詳細資訊...');
                const avatarResult = await getUserAvatar(token, preferredIdentifier);
                console.log('API 返回結果:', avatarResult);
                
                if (avatarResult) {
                    const updatedData = {
                        ...basicRecipientData,
                        username: avatarResult.display_name || basicRecipientData.username, // 使用 API 返回的顯示名稱
                        photo_url: avatarResult.photo_url
                    };
                    console.log('更新收款人資料:', updatedData);
                    setQuickTransferData(updatedData);
                    
                    console.log('成功獲取收款人資訊:', {
                        display_name: avatarResult.display_name,
                        photo_url: avatarResult.photo_url
                    });
                }
            } catch (avatarError) {
                console.log('獲取收款人資訊失敗:', avatarError);
                // 保持使用基本資料，不顯示錯誤給使用者
                console.log('將使用基本資料繼續:', basicRecipientData);
            }

        } catch (error) {
            console.error('設定收款人資訊失敗:', error);
            setTransferError('無法獲取收款人資訊');
        }
    };

    // 快速轉帳相關函數
    const closeQuickTransfer = () => {
        setShowQuickTransfer(false);
        setQuickTransferData(null);
        setTransferError("");
        setTransferSuccess("");
    };

    const handleQuickTransferSubmit = async (e) => {
        e.preventDefault();
        setTransferError("");
        setTransferSuccess("");
        
        const formData = new FormData(e.target);
        const amount = parseInt(formData.get('amount'));
        const note = formData.get('note') || `轉帳給 ${quickTransferData.username}`;
        
        if (isNaN(amount) || amount <= 0) {
            setTransferError('請輸入有效的轉帳金額');
            return;
        }
        
        if (amount > user.points) {
            setTransferError('點數不足，無法完成轉帳');
            return;
        }
        
        setTransferLoading(true);
        
        try {
            const token = localStorage.getItem('userToken');
            const result = await webTransferPoints(token, {
                to_username: quickTransferData.username,
                amount: amount,
                note: note
            });
            
            if (result.success) {
                // 準備轉帳成功的資料
                const successData = {
                    recipient: quickTransferData.username,
                    recipientPhoto: quickTransferData.photo_url,
                    amount: amount,
                    fee: result.fee,
                    note: note,
                    timestamp: new Date().toISOString(),
                    transactionId: result.transaction_id || `TXN-${Date.now()}`
                };
                
                // 重新載入使用者資料
                try {
                    const [portfolio, points] = await Promise.all([
                        getWebPortfolio(token),
                        getWebPointHistory(token, pointHistoryLimit)
                    ]);
                    setUser(portfolio);
                    setPointHistory(points);
                } catch (refreshError) {
                    console.error('重新載入資料失敗:', refreshError);
                }
                
                // 關閉快速轉帳 Modal 並顯示成功 Modal
                closeQuickTransfer();
                setTransferSuccessData(successData);
                setShowTransferSuccess(true);
            } else {
                setTransferError(result.message || '轉帳失敗');
            }
        } catch (error) {
            console.error('轉帳失敗:', error);
            setTransferError(error.message || '轉帳時發生錯誤');
        } finally {
            setTransferLoading(false);
        }
    };

    const handleTransferSubmit = async (e) => {
        e.preventDefault();
        setTransferError("");
        setTransferSuccess("");
        
        if (!transferForm.to_username || !transferForm.amount) {
            setTransferError('請填寫收款人和轉帳金額');
            return;
        }
        
        const amount = parseInt(transferForm.amount);
        if (isNaN(amount) || amount <= 0) {
            setTransferError('請輸入有效的轉帳金額');
            return;
        }
        
        if (amount > user.points) {
            setTransferError('點數不足，無法完成轉帳');
            return;
        }
        
        setTransferLoading(true);
        
        try {
            const token = localStorage.getItem('userToken');
            const result = await webTransferPoints(token, {
                to_username: transferForm.to_username,
                amount: amount,
                note: transferForm.note || `轉帳給 ${transferForm.to_username}`
            });
            
            if (result.success) {
                // 準備轉帳成功的資料
                const successData = {
                    recipient: transferForm.to_username,
                    recipientPhoto: null, // 手動輸入的沒有照片
                    amount: amount,
                    fee: result.fee,
                    note: transferForm.note || `轉帳給 ${transferForm.to_username}`,
                    timestamp: new Date().toISOString(),
                    transactionId: result.transaction_id || `TXN-${Date.now()}`
                };
                
                // 重新載入使用者資料
                try {
                    const [portfolio, points] = await Promise.all([
                        getWebPortfolio(token),
                        getWebPointHistory(token, pointHistoryLimit)
                    ]);
                    setUser(portfolio);
                    setPointHistory(points);
                    setLastPointHistory(points);
                } catch (refreshError) {
                    console.error('重新載入資料失敗:', refreshError);
                }
                
                // 關閉轉帳 Modal 並顯示成功 Modal
                closeTransferModal();
                setTransferSuccessData(successData);
                setShowTransferSuccess(true);
            } else {
                setTransferError(result.message || '轉帳失敗');
            }
        } catch (error) {
            console.error('轉帳失敗:', error);
            setTransferError(error.message || '轉帳時發生錯誤');
        } finally {
            setTransferLoading(false);
        }
    };


    // 輪詢檢查新的收款
    const checkForNewPayments = async () => {
        try {
            const token = localStorage.getItem('userToken');
            if (!token) return;

            const newPointHistory = await getWebPointHistory(token, pointHistoryLimit);
            
            if (newPointHistory.length > 0 && lastPointHistory.length > 0) {
                const newTransactions = newPointHistory.filter(newTransaction => {
                    return !lastPointHistory.some(oldTransaction => 
                        oldTransaction.created_at === newTransaction.created_at &&
                        oldTransaction.amount === newTransaction.amount &&
                        oldTransaction.note === newTransaction.note
                    );
                });
                
                console.log('檢查新交易:', {
                    newHistoryLength: newPointHistory.length,
                    lastHistoryLength: lastPointHistory.length,
                    newTransactionsCount: newTransactions.length,
                    newTransactions: newTransactions
                });
                
                for (const transaction of newTransactions) {
                    // 檢查是否為轉帳收入或 QR Code 兌換
                    const isTransferIn = transaction.amount > 0 && transaction.note && 
                        (transaction.type === 'transfer_in' || 
                         transaction.note.includes('收到來自') || 
                         transaction.note.includes('的轉帳'));
                         
                    const isQRCodeRedemption = transaction.amount > 0 && transaction.note && 
                        transaction.note.includes('QR Code 兌換');
                    
                    console.log('檢查交易:', {
                        amount: transaction.amount,
                        type: transaction.type,
                        note: transaction.note,
                        isTransferIn: isTransferIn,
                        isQRCodeRedemption: isQRCodeRedemption
                    });
                    
                    if (isTransferIn || isQRCodeRedemption) {
                        
                        // 提取轉帳人名稱或標示為 QR Code 兌換
                        let fromUser = '未知使用者';
                        if (isQRCodeRedemption) {
                            fromUser = 'QR Code 兌換';
                        } else if (transaction.note.includes('收到來自') && transaction.note.includes('的轉帳')) {
                            const match = transaction.note.match(/收到來自\s*(.+?)\s*的轉帳/);
                            fromUser = match?.[1]?.trim() || '未知使用者';
                        }
                        
                        // 找到新的收款
                        const paymentData = {
                            amount: transaction.amount,
                            from: fromUser,
                            note: transaction.note,
                            timestamp: transaction.created_at
                        };
                        
                        console.log('觸發收款通知:', paymentData);
                        setReceivedPayment(paymentData);
                        setShowPaymentNotification(true);
                        
                        // 播放收款音效（使用簡單的音頻音效）
                        try {
                            // 使用 Web Audio API 生成簡單的提示音
                            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                            const oscillator = audioContext.createOscillator();
                            const gainNode = audioContext.createGain();
                            
                            oscillator.connect(gainNode);
                            gainNode.connect(audioContext.destination);
                            
                            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                            oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
                            oscillator.frequency.setValueAtTime(1200, audioContext.currentTime + 0.2);
                            
                            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                            
                            oscillator.start(audioContext.currentTime);
                            oscillator.stop(audioContext.currentTime + 0.3);
                        } catch (e) {
                            console.log('音效播放失敗:', e);
                        }
                        
                        break; // 只顯示最新一筆收款
                    }
                }
            }
            
            setLastPointHistory(newPointHistory);
            setPointHistory(newPointHistory);
            
        } catch (error) {
            console.error('檢查新收款失敗:', error);
        }
    };

    // 開始輪詢
    const startPolling = () => {
        if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = setInterval(checkForNewPayments, 3000); // 每3秒檢查一次
        
    };

    // 停止輪詢
    const stopPolling = () => {
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
        }
    };

    // 關閉收款通知
    const closePaymentNotification = () => {
        setShowPaymentNotification(false);
        setReceivedPayment(null);
    };

    // 關閉轉帳成功通知
    const closeTransferSuccess = () => {
        setShowTransferSuccess(false);
        setTransferSuccessData(null);
    };

    // 更改點數記錄顯示筆數
    const changePointHistoryLimit = async (newLimit) => {
        setPointHistoryLimit(newLimit);
        setShowLimitDropdown(false);
        setPointHistoryLoading(true);
        
        try {
            const token = localStorage.getItem('userToken');
            if (!token) return;
            
            const newPointHistory = await getWebPointHistory(token, newLimit);
            setPointHistory(newPointHistory);
            setLastPointHistory(newPointHistory);
        } catch (error) {
            console.error('載入點數記錄失敗:', error);
        } finally {
            setPointHistoryLoading(false);
        }
    };

    // 清理 QR Scanner 和輪詢
    useEffect(() => {
        return () => {
            try {
                if (qrScannerRef.current) {
                    qrScannerRef.current.stop();
                    qrScannerRef.current.destroy();
                }
            } catch (error) {
                console.error('清理 QR Scanner 失敗:', error);
            }
            stopPolling();
        };
    }, []);

    // 點選外部關閉下拉選單
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (limitDropdownRef.current && !limitDropdownRef.current.contains(event.target)) {
                setShowLimitDropdown(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // 當頁面可見時開始輪詢，隱藏時停止
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.hidden) {
                stopPolling();
            } else if (user && authData) {
                startPolling();
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        
        // 如果使用者數據已載入，開始輪詢
        if (user && authData) {
            startPolling();
        }

        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            stopPolling();
        };
    }, [user, authData, lastPointHistory]);

    // 初始化歷史記錄
    useEffect(() => {
        if (pointHistory.length > 0 && lastPointHistory.length === 0) {
            setLastPointHistory(pointHistory);
        }
    }, [pointHistory, lastPointHistory]);

    // 檢查訂單是否可以取消
    const canCancelOrder = (order) => {
        const cancellableStatuses = [
            "pending",
            "partial",
            "pending_limit",
        ];
        return (
            cancellableStatuses.includes(order.status) &&
            order.quantity > 0
        );
    };

    // 檢查登入狀態並載入使用者資料
    useEffect(() => {
        const checkAuthAndLoadData = async () => {
            // 檢查必要的認證資料
            const isUser = localStorage.getItem("isUser");
            const token = localStorage.getItem("userToken");
            const telegramData = localStorage.getItem("telegramData");

            console.log("認證檢查:", {
                isUser,
                hasToken: !!token,
                hasTelegramData: !!telegramData,
            });

            // 如果缺少任何必要的認證資料，重新導向到登入頁
            if (!isUser || !token || !telegramData) {
                console.log("缺少認證資料，重新導向到登入頁");
                handleLogout(); // 清理可能不完整的資料
                return;
            }

            // 檢查 token 格式是否正確
            try {
                const tokenParts = token.split(".");
                if (tokenParts.length !== 3) {
                    console.log("Token 格式無效");
                    handleLogout();
                    return;
                }
            } catch (e) {
                console.log("Token 驗證失敗");
                handleLogout();
                return;
            }

            try {
                // 設定 Telegram 資料
                let parsedTelegramData = null;
                try {
                    parsedTelegramData = JSON.parse(telegramData);
                    // 檢查是否為有效的 Telegram 登入資料
                    if (
                        !parsedTelegramData ||
                        typeof parsedTelegramData !== "object"
                    ) {
                        throw new Error(
                            "Invalid telegram data structure",
                        );
                    }
                } catch (parseError) {
                    console.log(
                        "Telegram 資料無效，可能未使用 Telegram 登入:",
                        parseError,
                    );
                    // 如果是無效的 Telegram 資料，引導重新登入
                    setError("請使用 Telegram 登入以獲得完整功能");
                    setTimeout(() => {
                        handleLogout();
                    }, 3000);
                    return;
                }
                setAuthData(parsedTelegramData);
                setUseAvatarFallback(false);

                console.log("開始載入使用者資料...");

                // 載入使用者資料，添加超時處理
                const loadWithTimeout = (promise, name, timeout = 10000) => {
                    return Promise.race([
                        promise,
                        new Promise((_, reject) => 
                            setTimeout(() => reject(new Error(`${name} 請求超時`)), timeout)
                        )
                    ]);
                };

                console.log("正在載入 Portfolio...");
                const portfolio = await loadWithTimeout(getWebPortfolio(token), "Portfolio");
                console.log("Portfolio 載入完成:", portfolio);

                console.log("正在載入 Point History...");
                const points = await loadWithTimeout(getWebPointHistory(token, pointHistoryLimit), "Point History");
                console.log("Point History 載入完成:", points?.length, "筆記錄");

                console.log("正在載入 Stock Orders...");
                const stocks = await loadWithTimeout(getWebStockOrders(token), "Stock Orders");
                console.log("Stock Orders 載入完成:", stocks?.length, "筆記錄");

                console.log("正在載入 Permissions...");
                const permissions = await loadWithTimeout(
                    getMyPermissions(token).catch((error) => {
                        console.warn("無法載入權限資訊:", error);
                        return null;
                    }),
                    "Permissions"
                );
                console.log("Permissions 載入完成:", permissions);

                console.log("資料載入成功:", {
                    portfolio,
                    pointsCount: points?.length || 0,
                    stocksCount: stocks?.length || 0,
                    permissions,
                });

                setUser(portfolio);
                setPointHistory(points);
                setOrderHistory(stocks);
                setUserPermissions(permissions);
                setIsLoading(false);
            } catch (error) {
                console.error("載入使用者資料失敗:", error);

                // 處理不同類型的錯誤
                if (error.status === 401 || error.status === 403) {
                    console.log("認證失敗，重新登入");
                    handleLogout();
                } else if (error.status === 404) {
                    console.log("使用者未註冊或資料不存在");
                    setError(
                        "使用者帳號未完成註冊，或需要使用 Telegram 登入。將重新導向到登入頁面...",
                    );
                    setTimeout(() => {
                        handleLogout();
                    }, 3000);
                    setIsLoading(false);
                } else if (error.status >= 500) {
                    console.log("伺服器錯誤");
                    setError("伺服器暫時無法使用，請稍後再試");
                    setIsLoading(false);
                } else {
                    console.log("其他錯誤:", error);
                    setError("載入資料失敗，請重新整理頁面");
                    setIsLoading(false);
                }
            }
        };

        checkAuthAndLoadData();
    }, [router]);

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">載入中...</p>
                </div>
            </div>
        );
    }

    // 如果有錯誤且不是載入中，顯示錯誤頁面
    if (error && !isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="max-w-md p-6 text-center">
                    <div className="mb-4 text-6xl">⚠️</div>
                    <h2 className="mb-4 text-xl font-bold text-red-400">
                        載入失敗
                    </h2>
                    <p className="mb-6 text-[#92cbf4]">{error}</p>
                    <div className="space-y-3">
                        <button
                            onClick={() => window.location.reload()}
                            className="w-full rounded-xl bg-[#469FD2] px-4 py-2 text-white transition-colors hover:bg-[#357AB8]"
                        >
                            重新載入
                        </button>
                        <button
                            onClick={handleLogout}
                            className="w-full rounded-xl border border-[#294565] px-4 py-2 text-[#92cbf4] transition-colors hover:bg-[#1A325F]"
                        >
                            重新登入
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // 確保必要資料存在才渲染主要內容
    if (!user || !authData) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0f203e]">
                <div className="text-center">
                    <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-[#92cbf4] border-t-transparent"></div>
                    <p className="text-[#92cbf4]">準備資料中...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen w-full bg-[#0f203e] pt-10 pb-20 md:items-center">
            <div className="w-full space-y-4 p-4">
                <div className="mx-auto flex max-w-2xl space-x-8 rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                    {authData?.photo_url && !useAvatarFallback ? (
                        <img
                            src={authData.photo_url}
                            alt="Telegram 頭貼"
                            className="h-20 w-20 rounded-full"
                            onLoad={handleAvatarLoad}
                            onError={() => {
                                setUseAvatarFallback(true);
                            }}
                        />
                    ) : (
                        <div className="inline-flex h-20 w-20 items-center justify-center rounded-full bg-[#264173] text-xl font-bold text-[#92cbf4]">
                            {String(user?.username || '').substring(0, 1).toUpperCase() || "U"}
                        </div>
                    )}
                    <div>
                        <p className="mb-2 text-xl">
                            早安，
                            <b>{user?.username || "使用者"}</b>
                        </p>
                        <p className="mb-1 text-[#92cbf4]">
                            你現在擁有的總資產為{" "}
                            <span className="text-white">
                                {user?.totalValue?.toLocaleString() ||
                                    "0"}
                            </span>{" "}
                            點
                        </p>
                        <p className="text-sm text-[#92cbf4]">
                            可動用點數共{" "}
                            <span className="text-white">
                                {user?.points?.toLocaleString() ||
                                    "0"}
                            </span>{" "}
                            點
                        </p>
                    </div>
                    <div className="ml-auto">
                        <button onClick={handleLogout}>
                            <LogOut className="h-5 w-5 text-[#92cbf4] transition-colors hover:text-red-700" />
                        </button>
                    </div>
                </div>

                <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                    <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                        資產總覽
                    </h3>
                    <div className="grid grid-cols-2 place-items-center gap-4 md:grid-cols-4">
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                現金點數
                            </p>
                            <p className="text-center text-xl font-bold text-white">
                                {user?.points?.toLocaleString() ||
                                    "0"}
                            </p>
                        </div>
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                股票數量
                            </p>
                            <p className="text-center text-xl font-bold text-white">
                                {user?.stocks?.toLocaleString() ||
                                    "0"}
                            </p>
                        </div>
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                股票價值
                            </p>
                            <p className="text-center text-xl font-bold text-white">
                                {user?.stockValue?.toLocaleString() ||
                                    "0"}
                            </p>
                        </div>
                        <div>
                            <p className="mb-1 text-center text-sm text-[#557797]">
                                總資產
                            </p>
                            <p className="text-center text-xl font-bold text-[#92cbf4]">
                                {user?.totalValue?.toLocaleString() ||
                                    "0"}
                            </p>
                        </div>
                    </div>
                    {user?.avgCost !== undefined && (
                        <div className="mt-4 border-t border-[#294565] pt-4">
                            <p className="text-sm text-[#557797]">
                                購買股票平均成本:{" "}
                                <span className="font-semibold text-white">
                                    {user.avgCost}
                                </span>
                            </p>
                        </div>
                    )}
                </div>

                {/* 點數轉帳功能 */}
                {userPermissions && userPermissions.permissions && userPermissions.permissions.includes('transfer_points') && (
                    <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                        <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                            點數轉帳
                        </h3>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <div className="text-center">
                                <button
                                    onClick={openQRCode}
                                    className="w-full rounded-xl bg-[#3483b0] px-6 py-4 text-white transition-colors hover:bg-[#357AB8] focus:outline-none focus:ring-2 focus:ring-[#469FD2]/50"
                                >
                                    <QrCode className="mx-auto mb-2 h-8 w-8" />
                                    <div className="text-lg font-bold">顯示我的 QR Code</div>
                                    <div className="text-sm text-blue-100">讓別人掃描轉帳給你</div>
                                </button>
                            </div>
                            <div className="text-center">
                                <button
                                    onClick={startQRScanner}
                                    className="w-full rounded-xl bg-green-600 px-6 py-4 text-white transition-colors hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-600/50"
                                >
                                    <Camera className="mx-auto mb-2 h-8 w-8" />
                                    <div className="text-lg font-bold">掃描 QR Code</div>
                                    <div className="text-sm text-green-100">掃描轉帳或兌換點數</div>
                                </button>
                            </div>
                        </div>
                        
                        {/* 手動輸入選項 */}
                        <div className="mt-4 text-center">
                            <button
                                onClick={() => openTransferModal()}
                                className="inline-flex items-center rounded-xl border border-[#294565] bg-transparent px-4 py-2 text-sm text-[#92cbf4] transition-colors hover:bg-[#294565]/30"
                            >
                                手動輸入轉帳
                            </button>
                        </div>
                    </div>
                )}

                {/* 管理員後台入口 */}
                {userPermissions && 
                 userPermissions.permissions && 
                 (userPermissions.role === "admin" || 
                  userPermissions.role === "qrcode_manager" ||
                  userPermissions.role === "point_manager" || 
                  userPermissions.role === "announcer" ||
                  userPermissions.permissions.includes("manage_users") ||
                  userPermissions.permissions.includes("manage_market") ||
                  userPermissions.permissions.includes("system_admin") ||
                  userPermissions.permissions.includes("give_points") ||
                  userPermissions.permissions.includes("create_announcement") ||
                  userPermissions.permissions.includes("generate_qrcode") ||
                  userPermissions.can_give_points ||
                  userPermissions.can_create_announcement ||
                  userPermissions.can_view_all_users ||
                  userPermissions.can_manage_system ||
                  userPermissions.can_generate_qrcode) && (
                    <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                        <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                            管理功能
                        </h3>
                        <div className="text-center">
                            <p className="mb-4 text-sm text-[#557797]">
                                您擁有管理權限，可以進入管理員後台
                            </p>
                            <button
                                onClick={() => router.push("/admin")}
                                className="inline-flex items-center rounded-xl bg-gradient-to-r from-[#469FD2] to-[#357AB8] px-6 py-3 font-medium text-white transition-all duration-200 hover:from-[#357AB8] hover:to-[#2B5A8B] hover:shadow-lg active:scale-95"
                            >
                                <svg
                                    className="mr-2 h-5 w-5"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                    xmlns="http://www.w3.org/2000/svg"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                                    />
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                                    />
                                </svg>
                                進入管理員後台
                            </button>
                        </div>
                    </div>
                )}

                <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                    <div className="mb-4 flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-[#92cbf4]">
                            點數紀錄
                        </h3>
                        
                        {/* 筆數選擇器 */}
                        <div className="relative" ref={limitDropdownRef}>
                            <button
                                onClick={() => setShowLimitDropdown(!showLimitDropdown)}
                                className="flex items-center gap-2 rounded-lg border border-[#294565] bg-[#0f203e] px-3 py-2 text-sm text-[#92cbf4] transition-colors hover:bg-[#294565]/30"
                            >
                                <span>顯示 {pointHistoryLimit} 筆</span>
                                <ChevronDown className={`h-4 w-4 transition-transform ${showLimitDropdown ? 'rotate-180' : ''}`} />
                            </button>
                            
                            {/* 下拉選單 */}
                            {showLimitDropdown && (
                                <div className="absolute right-0 top-12 z-10 w-32 rounded-lg border border-[#294565] bg-[#1A325F] py-2 shadow-lg">
                                    {[10, 50, 100, 500, 1000].map((limit) => (
                                        <button
                                            key={limit}
                                            onClick={() => changePointHistoryLimit(limit)}
                                            className={`w-full px-4 py-2 text-left text-sm transition-colors hover:bg-[#294565]/30 ${
                                                pointHistoryLimit === limit 
                                                    ? 'bg-[#469FD2]/20 text-[#469FD2]' 
                                                    : 'text-[#92cbf4]'
                                            }`}
                                        >
                                            {limit} 筆
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="grid grid-flow-row gap-4">
                        {pointHistoryLoading ? (
                            <div className="flex items-center justify-center py-8">
                                <div className="flex items-center gap-3">
                                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-[#92cbf4] border-t-transparent"></div>
                                    <span className="text-[#92cbf4]">載入中...</span>
                                </div>
                            </div>
                        ) : pointHistory && pointHistory.length > 0 ? (
                            pointHistory.map((i) => {
                                return (
                                    <div
                                        className="grid grid-cols-5 space-y-1 md:space-y-0 md:space-x-4"
                                        key={i.created_at}
                                    >
                                        <p className="col-span-5 font-mono text-sm md:col-span-1 md:text-base">
                                            {dayjs(i.created_at)
                                                .add(8, "hour")
                                                .format(
                                                    "MM/DD HH:mm",
                                                )}
                                        </p>
                                        <div className="col-span-5 md:col-span-4 md:flex">
                                            <p className="font-bold text-[#92cbf4]">
                                                {i.note}
                                            </p>

                                            <p className="ml-auto w-fit font-mono">
                                                {i.balance_after}{" "}
                                                <span
                                                    className={
                                                        i.amount < 0
                                                            ? "text-red-400"
                                                            : "text-green-400"
                                                    }
                                                >
                                                    (
                                                    {i.amount > 0 &&
                                                        "+"}
                                                    {i.amount})
                                                </span>
                                            </p>
                                        </div>
                                    </div>
                                );
                            })
                        ) : (
                            <div className="py-4 text-center text-[#557797]">
                                暫無點數記錄
                            </div>
                        )}
                    </div>
                </div>

                <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                    <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                        股票購買紀錄
                    </h3>

                    {/* 取消訂單的通知訊息 */}
                    {cancelSuccess && (
                        <div className="mb-4 rounded-xl border border-green-500/30 bg-green-600/20 p-3">
                            <p className="text-sm text-green-400">
                                ✅ {cancelSuccess}
                            </p>
                        </div>
                    )}
                    {cancelError && (
                        <div className="mb-4 rounded-xl border border-red-500/30 bg-red-600/20 p-3">
                            <p className="text-sm text-red-400">
                                ❌ {cancelError}
                            </p>
                        </div>
                    )}

                    <div className="grid grid-flow-row gap-4">
                        {orderHistory && orderHistory.length > 0 ? (
                            orderHistory.map((i) => {
                                const isCancellable =
                                    canCancelOrder(i);
                                const orderId =
                                    i._id ||
                                    i.id ||
                                    i.order_id ||
                                    i.orderId ||
                                    i["$oid"];
                                const isCancelling =
                                    cancelingOrders.has(orderId);

                                return (
                                    <div
                                        className="rounded-xl border border-[#294565] bg-[#0f203e] p-4"
                                        key={orderId || i.created_at}
                                    >
                                        {/* 訂單基本資訊 */}
                                        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                                            <p className="font-mono text-sm text-[#92cbf4]">
                                                {dayjs(i.created_at)
                                                    .add(8, "hour")
                                                    .format(
                                                        "MM/DD HH:mm",
                                                    )}
                                            </p>
                                            <div className="flex items-center gap-2">
                                                <span
                                                    className={twMerge(
                                                        "rounded px-2 py-1 text-xs font-semibold",
                                                        i.side ===
                                                            "sell"
                                                            ? "bg-green-600/20 text-green-400"
                                                            : "bg-red-600/20 text-red-400",
                                                    )}
                                                >
                                                    {i.side === "sell"
                                                        ? "賣出"
                                                        : "買入"}
                                                </span>
                                                <span className="rounded bg-[#294565] px-2 py-1 text-xs text-[#92cbf4]">
                                                    {i.order_type ===
                                                    "market"
                                                        ? "市價單"
                                                        : "限價單"}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Debug訊息 - 可以在生產環境中移除 */}
                                        {process.env.NODE_ENV ===
                                            "development" && (
                                            <div className="mb-2 rounded bg-gray-800 p-2 text-xs">
                                                <details>
                                                    <summary className="cursor-pointer text-gray-400">
                                                        Debug：訂單物件結構
                                                    </summary>
                                                    <pre className="mt-1 overflow-auto text-gray-300">
                                                        {JSON.stringify(
                                                            i,
                                                            null,
                                                            2,
                                                        )}
                                                    </pre>
                                                </details>
                                            </div>
                                        )}

                                        {/* 訂單狀態和詳情 */}
                                        <div className="mb-3">
                                            <p className="font-bold text-[#92cbf4]">
                                                {i.status === "filled"
                                                    ? `✅ 已成交${i.price ? ` → ${i.price}元` : ""}`
                                                    : i.status ===
                                                        "cancelled"
                                                      ? "❌ 已取消"
                                                      : i.status ===
                                                          "pending_limit"
                                                        ? "⏳ 等待中 (限制)"
                                                        : i.status ===
                                                                "partial" ||
                                                            i.status ===
                                                                "pending"
                                                          ? i.filled_quantity >
                                                            0
                                                              ? `🔄 部分成交 (${i.filled_quantity}/${i.quantity} 股已成交@${i.filled_price ?? i.price}元，剩餘${i.quantity - i.filled_quantity}股等待)`
                                                              : "⏳ 等待成交"
                                                          : i.status}
                                            </p>

                                            {/* 訂單詳情 */}
                                            <div className="mt-2 grid grid-cols-2 gap-4 text-sm text-[#557797] md:grid-cols-3">
                                                <div>
                                                    <span>
                                                        數量：
                                                    </span>
                                                    <span className="text-white">
                                                        {i.quantity}{" "}
                                                        股
                                                    </span>
                                                </div>
                                                {i.price && (
                                                    <div>
                                                        <span>
                                                            價格：
                                                        </span>
                                                        <span className="text-white">
                                                            {i.price}{" "}
                                                            元
                                                        </span>
                                                    </div>
                                                )}
                                                {i.filled_quantity >
                                                    0 && (
                                                    <div>
                                                        <span>
                                                            已成交：
                                                        </span>
                                                        <span className="text-green-400">
                                                            {
                                                                i.filled_quantity
                                                            }{" "}
                                                            股
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* 取消按鈕 */}
                                        {isCancellable && (
                                            <div className="flex justify-end">
                                                <button
                                                    onClick={() =>
                                                        openCancelModal(
                                                            i,
                                                            i.order_type,
                                                            i.quantity -
                                                                (i.filled_quantity || 0),
                                                        )
                                                    }
                                                    disabled={
                                                        isCancelling
                                                    }
                                                    className={twMerge(
                                                        "rounded-xl px-3 py-1 text-sm font-medium transition-colors",
                                                        isCancelling
                                                            ? "cursor-not-allowed bg-gray-600/50 text-gray-400"
                                                            : "border border-red-500/30 bg-red-600/20 text-red-400 hover:bg-red-600/30",
                                                    )}
                                                >
                                                    {isCancelling
                                                        ? "取消中..."
                                                        : "取消訂單"}
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                );
                            })
                        ) : (
                            <div className="py-4 text-center text-[#557797]">
                                暫無股票交易記錄
                            </div>
                        )}
                    </div>
                </div>

                {/* 權限資訊 */}
                {userPermissions && (
                    <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                        <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                            帳號權限資訊
                        </h3>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-[#557797]">
                                    角色
                                </span>
                                <span className="rounded bg-[#294565] px-2 py-1 text-sm font-medium text-[#92cbf4]">
                                    {userPermissions.role ===
                                        "student" && "一般學員"}
                                    {userPermissions.role ===
                                        "qrcode_manager" && "QR Code管理員"}
                                    {userPermissions.role ===
                                        "point_manager" &&
                                        "點數管理員"}
                                    {userPermissions.role ===
                                        "announcer" && "公告員"}
                                    {userPermissions.role ===
                                        "admin" && "系統管理員"}
                                    {![
                                        "student",
                                        "qrcode_manager",
                                        "point_manager",
                                        "announcer",
                                        "admin",
                                    ].includes(
                                        userPermissions.role,
                                    ) && userPermissions.role}
                                </span>
                            </div>

                            <div>
                                <p className="mb-2 text-sm text-[#557797]">
                                    可用權限
                                </p>
                                <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                                    {userPermissions.permissions &&
                                    userPermissions.permissions
                                        .length > 0 ? (
                                        userPermissions.permissions.map(
                                            (permission, index) => (
                                                <div
                                                    key={index}
                                                    className="flex items-center space-x-2"
                                                >
                                                    <span className="text-green-400">
                                                        ✓
                                                    </span>
                                                    <span className="text-xs text-white">
                                                        {permission ===
                                                            "view_own_data" &&
                                                            "查看自己的資料"}
                                                        {permission ===
                                                            "trade_stocks" &&
                                                            "股票交易"}
                                                        {permission ===
                                                            "transfer_points" &&
                                                            "轉帳點數"}
                                                        {permission ===
                                                            "view_all_users" &&
                                                            "查看所有使用者"}
                                                        {permission ===
                                                            "give_points" &&
                                                            "發放點數"}
                                                        {permission ===
                                                            "create_announcement" &&
                                                            "發布公告"}
                                                        {permission ===
                                                            "manage_users" &&
                                                            "管理使用者"}
                                                        {permission ===
                                                            "manage_market" &&
                                                            "管理市場"}
                                                        {permission ===
                                                            "system_admin" &&
                                                            "系統管理"}
                                                        {![
                                                            "view_own_data",
                                                            "trade_stocks",
                                                            "transfer_points",
                                                            "view_all_users",
                                                            "give_points",
                                                            "create_announcement",
                                                            "manage_users",
                                                            "manage_market",
                                                            "system_admin",
                                                        ].includes(
                                                            permission,
                                                        ) &&
                                                            permission}
                                                    </span>
                                                </div>
                                            ),
                                        )
                                    ) : (
                                        <p className="text-xs text-[#557797]">
                                            暫無特殊權限
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* 取消訂單確認 Modal */}
            <Modal
                isOpen={showCancelModal}
                onClose={closeCancelModal}
                title="確認取消訂單"
                size="md"
            >
                {pendingCancelOrder && (
                    <div className="space-y-4">
                        <div className="rounded-xl border border-orange-500/30 bg-orange-600/10 p-4">
                            <div className="mb-3 flex items-center gap-2">
                                <h3 className="text-lg font-semibold text-orange-400">
                                    你確定要取消這張訂單？
                                </h3>
                            </div>

                            <div className="space-y-2 text-sm text-[#92cbf4]">
                                <div className="flex justify-between">
                                    <span>訂單類型：</span>
                                    <span className="text-white">
                                        {pendingCancelOrder.orderType ===
                                        "market"
                                            ? "市價單"
                                            : "限價單"}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span>數量：</span>
                                    <span className="text-white">
                                        {pendingCancelOrder.quantity}{" "}
                                        股
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span>訂單 ID：</span>
                                    <span className="font-mono text-xs text-white">
                                        {pendingCancelOrder.orderId}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <p className="text-sm text-[#557797]">
                            謹慎操作，按錯不能幫你復原喔
                        </p>

                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={closeCancelModal}
                                className="flex-1 rounded-xl border border-[#294565] bg-[#1A325F] px-4 py-2 text-[#92cbf4] transition-colors hover:bg-[#294565]"
                            >
                                保留訂單
                            </button>
                            <button
                                onClick={confirmCancelOrder}
                                className="flex-1 rounded-xl bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
                            >
                                確認取消
                            </button>
                        </div>
                    </div>
                )}
            </Modal>

            {/* QR Code 顯示 Modal */}
            <Modal
                isOpen={showQRCode}
                onClose={closeQRCode}
                title="我的收款 QR Code"
                size="md"
            >
                <div className="space-y-4 text-center">
                    <div className="relative mx-auto bg-white p-4 rounded-xl" style={{ width: 'fit-content' }}>
                        <QRCode
                            level="M"
                            value={(() => {
                                const qrData = {
                                    type: 'transfer',
                                    // username: user?.username || user?.name || 'unknown',
                                    id: authData?.id || user?.id || 'unknown'
                                };
                                const qrString = JSON.stringify(qrData);
                                console.log('生成 QR Code 數據:', qrData);
                                console.log('QR Code 字符串:', qrString);
                                console.log('QR Code 字符串長度:', qrString.length);
                                console.log('user 對象:', user);
                                console.log('authData 對象:', authData);
                                return qrString;
                            })()}
                            size={200}
                            bgColor="#ffffff"
                            fgColor="#000000"
                        />
                        <img src="/SITQR.svg" alt="QR Code Icon" className="absolute w-12 bg-white py-2 px-1 top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                    </div>
                    <div className="space-y-3">
                        <p className="text-sm text-[#92cbf4]">
                            讓別人掃描這個 QR Code 來轉帳給你
                        </p>
                        <div className="flex items-center justify-center gap-3">
                            {authData?.photo_url && !useAvatarFallback ? (
                                <img
                                    src={authData.photo_url}
                                    alt="大頭照"
                                    className="h-8 w-8 rounded-full"
                                    onError={() => setUseAvatarFallback(true)}
                                />
                            ) : (
                                <div className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#264173] text-sm font-bold text-[#92cbf4]">
                                    {String(user?.username || '').substring(0, 1).toUpperCase() || "U"}
                                </div>
                            )}
                            <span className="text-sm font-medium text-white">
                                {user?.username || ''}
                            </span>
                        </div>
                    </div>
                </div>
            </Modal>

            {/* 轉帳 Modal */}
            <Modal
                isOpen={showTransferModal}
                onClose={closeTransferModal}
                title="點數轉帳"
                size="md"
            >
                <div className="space-y-4">
                    {/* 成功和錯誤訊息 */}
                    {transferSuccess && (
                        <div className="rounded-xl border border-green-500/30 bg-green-600/20 p-3">
                            <p className="text-sm text-green-400">
                                ✅ {transferSuccess}
                            </p>
                        </div>
                    )}
                    {transferError && (
                        <div className="rounded-xl border border-red-500/30 bg-red-600/20 p-3">
                            <p className="text-sm text-red-400">
                                ❌ {transferError}
                            </p>
                        </div>
                    )}

                    <form onSubmit={handleTransferSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-2">
                                收款人使用者名
                            </label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={transferForm.to_username}
                                    onChange={(e) => setTransferForm(prev => ({ ...prev, to_username: e.target.value }))}
                                    className="flex-1 rounded-xl border border-[#294565] bg-[#0f203e] px-3 py-2 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="輸入收款人使用者名"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={startQRScanner}
                                    className="rounded-xl bg-[#469FD2] px-3 py-2 text-white transition-colors hover:bg-[#357AB8]"
                                >
                                    <QrCode className="h-4 w-4" />
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-2">
                                轉帳金額
                            </label>
                            <input
                                type="number"
                                value={transferForm.amount}
                                onChange={(e) => setTransferForm(prev => ({ ...prev, amount: e.target.value }))}
                                className="w-full rounded-xl border border-[#294565] bg-[#0f203e] px-3 py-2 text-white focus:border-[#469FD2] focus:outline-none"
                                placeholder="輸入轉帳金額"
                                min="1"
                                max={user?.points || 0}
                                required
                            />
                            <p className="mt-1 text-xs text-[#557797]">
                                可用點數：{user?.points?.toLocaleString() || '0'} 點
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-2">
                                備註（可選）
                            </label>
                            <input
                                type="text"
                                value={transferForm.note}
                                onChange={(e) => setTransferForm(prev => ({ ...prev, note: e.target.value }))}
                                className="w-full rounded-xl border border-[#294565] bg-[#0f203e] px-3 py-2 text-white focus:border-[#469FD2] focus:outline-none"
                                placeholder="輸入備註訊息"
                                maxLength="200"
                            />
                        </div>

                        <div className="flex gap-3 pt-2">
                            <button
                                type="button"
                                onClick={closeTransferModal}
                                className="flex-1 rounded-xl border border-[#294565] bg-[#1A325F] px-4 py-2 text-[#92cbf4] transition-colors hover:bg-[#294565]"
                            >
                                取消
                            </button>
                            <button
                                type="submit"
                                disabled={transferLoading}
                                className="flex-1 rounded-xl bg-green-600 px-4 py-2 text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-gray-600"
                            >
                                {transferLoading ? '轉帳中...' : '確認轉帳'}
                            </button>
                        </div>
                    </form>
                </div>
            </Modal>

            {/* QR Scanner Modal */}
            <Modal
                isOpen={showQRScanner}
                onClose={stopQRScanner}
                title="掃描 QR Code"
                size="md"
            >
                <div className="space-y-4">
                    <div className="relative">
                        <video
                            ref={videoRef}
                            className="w-full rounded-xl bg-black"
                            style={{ 
                                width: '100%', 
                                height: '300px', 
                                objectFit: 'cover' 
                            }}
                            autoPlay
                            playsInline
                            muted
                        />
                    </div>
                    
                    <div className="text-center space-y-2">
                        <p className="text-sm text-[#92cbf4]">
                            請對準 QR Code 進行掃描
                        </p>
                        <p className="text-xs text-[#557797]">
                            支援轉帳 QR Code 和點數兌換 QR Code
                        </p>
                        
                        {/* 測試相機按鈕 */}
                        <div className="flex gap-2 justify-center">
                            <button
                                onClick={startQRScanner}
                                className="px-3 py-1 bg-[#469FD2] text-white rounded hover:bg-[#3A8BC0] transition-colors text-sm"
                            >
                                重新啟動掃描
                            </button>
                            <button
                                onClick={async () => {
                                    try {
                                        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                                        if (videoRef.current) {
                                            videoRef.current.srcObject = stream;
                                            videoRef.current.play();
                                        }
                                        console.log('直接相機測試成功');
                                    } catch (e) {
                                        console.error('直接相機測試失敗:', e);
                                        setTransferError('相機測試失敗: ' + e.message);
                                    }
                                }}
                                className="px-3 py-1 bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors text-sm"
                            >
                                測試相機
                            </button>
                        </div>
                    </div>
                    
                    {transferError && (
                        <div className="rounded-xl border border-red-500/30 bg-red-600/20 p-3">
                            <p className="text-sm text-red-400">
                                ❌ {transferError}
                            </p>
                        </div>
                    )}
                </div>
            </Modal>

            {/* 快速轉帳 Modal */}
            <Modal
                isOpen={showQuickTransfer}
                onClose={closeQuickTransfer}
                title="快速轉帳"
                size="md"
            >
                {quickTransferData && (
                    <div className="space-y-4">
                        {/* 成功和錯誤訊息 */}
                        {transferSuccess && (
                            <div className="rounded-xl border border-green-500/30 bg-green-600/20 p-3">
                                <p className="text-sm text-green-400">
                                    ✅ {transferSuccess}
                                </p>
                            </div>
                        )}
                        {transferError && (
                            <div className="rounded-xl border border-red-500/30 bg-red-600/20 p-3">
                                <p className="text-sm text-red-400">
                                    ❌ {transferError}
                                </p>
                            </div>
                        )}

                        {/* 收款人資訊確認 */}
                        <div className="rounded-xl border border-[#469FD2]/30 bg-[#469FD2]/10 p-4">
                            <div className="flex items-center gap-3">
                                {quickTransferData.photo_url ? (
                                    <img
                                        src={quickTransferData.photo_url}
                                        alt="收款人大頭照"
                                        className="h-12 w-12 shrink-0 rounded-full object-cover shadow-lg ring-2 ring-[#469FD2]/50"
                                        onError={(e) => {
                                            // 如果大頭照載入失敗，改為顯示字母圓形圖標
                                            e.target.style.display = 'none';
                                            e.target.nextElementSibling.style.display = 'flex';
                                        }}
                                    />
                                ) : null}
                                <div 
                                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 via-indigo-500 to-blue-500 text-lg font-bold text-white shadow-lg ring-2 ring-white/20 border-2 border-white/10 ${quickTransferData.photo_url ? 'hidden' : 'flex'}`}
                                >
                                    {String(quickTransferData.username || '').substring(0, 1).toUpperCase() || "U"}
                                </div>
                                <div className="flex-1">
                                    <p className="font-medium text-[#92cbf4]">轉帳給</p>
                                    <p className="text-xl font-bold text-white">
                                        {quickTransferData.username}
                                    </p>
                                    {quickTransferData.id && (
                                        <p className="text-xs text-[#557797]">
                                            ID: {quickTransferData.id}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>

                        <form onSubmit={handleQuickTransferSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-[#92cbf4] mb-2">
                                    轉帳金額 <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="number"
                                    name="amount"
                                    className="w-full rounded-xl border border-[#294565] bg-[#0f203e] px-3 py-2 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="輸入轉帳金額"
                                    min="1"
                                    max={user?.points || 0}
                                    required
                                    autoFocus
                                />
                                <p className="mt-1 text-xs text-[#557797]">
                                    可用點數：{user?.points?.toLocaleString() || '0'} 點
                                </p>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-[#92cbf4] mb-2">
                                    備註（可選）
                                </label>
                                <input
                                    type="text"
                                    name="note"
                                    className="w-full rounded-xl border border-[#294565] bg-[#0f203e] px-3 py-2 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder={`轉帳給 ${quickTransferData.username}`}
                                    maxLength="200"
                                />
                            </div>

                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={closeQuickTransfer}
                                    className="flex-1 rounded-xl border border-[#294565] bg-[#1A325F] px-4 py-2 text-[#92cbf4] transition-colors hover:bg-[#294565]"
                                >
                                    取消
                                </button>
                                <button
                                    type="submit"
                                    disabled={transferLoading}
                                    className="flex-1 rounded-xl bg-[#469FD2] px-4 py-2 text-white transition-colors hover:bg-[#357AB8] disabled:cursor-not-allowed disabled:bg-gray-600"
                                >
                                    {transferLoading ? '轉帳中...' : '確認轉帳'}
                                </button>
                            </div>
                        </form>
                    </div>
                )}
            </Modal>


            {/* 收款通知彈出視窗 */}
            {showPaymentNotification && receivedPayment && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="relative mx-4 w-full max-w-md payment-notification">
                        {/* 成功動畫背景 */}
                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-green-500/20 via-emerald-500/20 to-teal-500/20 blur-xl payment-glow" />
                        
                        {/* 主要內容 */}
                        <div className="relative rounded-2xl border border-green-500/30 bg-gradient-to-br from-green-900/90 via-emerald-900/90 to-teal-900/90 p-6 shadow-2xl backdrop-blur-md">
                            {/* 關閉按鈕 */}
                            <button
                                onClick={closePaymentNotification}
                                className="absolute right-4 top-4 rounded-full p-1 text-green-300 hover:bg-green-800/50 hover:text-white transition-colors"
                            >
                                <X className="h-5 w-5" />
                            </button>

                            {/* 成功圖示 */}
                            <div className="mb-4 flex justify-center">
                                <div className="rounded-full bg-green-600/20 p-3 ring-2 ring-green-500/30 success-pulse">
                                    <CheckCircle2 className="h-12 w-12 text-green-400" />
                                </div>
                            </div>

                            {/* 標題 */}
                            <div className="mb-4 text-center">
                                <h3 className="text-xl font-bold text-green-100 mb-1">
                                    收款成功！
                                </h3>
                                <p className="text-sm text-green-300">
                                    您有一筆新的轉帳收入
                                </p>
                            </div>

                            {/* 金額顯示 */}
                            <div className="mb-6 text-center">
                                <div className="flex items-center justify-center gap-2 mb-2 money-float">
                                    <DollarSign className="h-6 w-6 text-green-400" />
                                    <span className="text-3xl font-bold text-white">
                                        +{receivedPayment.amount.toLocaleString()}
                                    </span>
                                    <span className="text-lg text-green-300">點</span>
                                </div>
                                <div className="h-px bg-gradient-to-r from-transparent via-green-500/50 to-transparent" />
                            </div>

                            {/* 轉帳詳情 */}
                            <div className="space-y-3 mb-6">
                                <div className="flex items-center justify-between rounded-xl bg-green-800/30 p-3">
                                    <span className="text-sm text-green-300">轉帳人</span>
                                    <span className="font-medium text-green-100">
                                        {receivedPayment.from}
                                    </span>
                                </div>
                                
                                <div className="flex items-center justify-between rounded-xl bg-green-800/30 p-3">
                                    <span className="text-sm text-green-300">時間</span>
                                    <span className="font-medium text-green-100">
                                        {dayjs(receivedPayment.timestamp)
                                            .add(8, 'hour')
                                            .format('MM/DD HH:mm:ss')}
                                    </span>
                                </div>
                                
                                {receivedPayment.note && (
                                    <div className="rounded-xl bg-green-800/30 p-3">
                                        <span className="text-sm text-green-300 block mb-1">備註</span>
                                        <span className="text-green-100">
                                            {receivedPayment.note}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* 確認按鈕 */}
                            <button
                                onClick={closePaymentNotification}
                                className="w-full rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 py-3 font-medium text-white transition-all duration-300 hover:from-green-700 hover:to-emerald-700 hover:shadow-lg active:scale-95"
                            >
                                知道了
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 轉帳成功彈出視窗 */}
            {showTransferSuccess && transferSuccessData && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="relative mx-4 w-full max-w-md transfer-success-modal">
                        {/* 成功動畫背景 */}
                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 blur-xl transfer-glow" />
                        
                        {/* 主要內容 */}
                        <div className="relative rounded-2xl border border-blue-500/30 bg-gradient-to-br from-blue-900/90 via-purple-900/90 to-pink-900/90 p-6 shadow-2xl backdrop-blur-md">
                            {/* 關閉按鈕 */}
                            <button
                                onClick={closeTransferSuccess}
                                className="absolute right-4 top-4 rounded-full p-1 text-blue-300 hover:bg-blue-800/50 hover:text-white transition-colors"
                            >
                                <X className="h-5 w-5" />
                            </button>

                            {/* 成功圖示動畫 */}
                            <div className="mb-6 flex justify-center">
                                <div className="relative">
                                    <div className="rounded-full bg-gradient-to-r from-blue-500 to-purple-500 p-4 shadow-lg success-pulse">
                                        <Send className="h-12 w-12 text-white" />
                                    </div>
                                </div>
                            </div>

                            {/* 標題 */}
                            <div className="mb-6 text-center">
                                <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-2">
                                    轉帳成功！
                                </h3>
                                <p className="text-sm text-blue-300">
                                    您的轉帳已成功送達
                                </p>
                            </div>

                            {/* 轉帳流程視覺化 */}
                            <div className="mb-6 flex items-center justify-center gap-4">
                                {/* 發送者 */}
                                <div className="flex flex-col items-center">
                                    {authData?.photo_url && !useAvatarFallback ? (
                                        <img
                                            src={authData.photo_url}
                                            alt="我的頭像"
                                            className="h-12 w-12 rounded-full border-2 border-blue-400 shadow-lg"
                                            onError={() => setUseAvatarFallback(true)}
                                        />
                                    ) : (
                                        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center border-2 border-blue-400 shadow-lg">
                                            <span className="text-white font-bold">
                                                {String(user?.username || '').substring(0, 1).toUpperCase() || "U"}
                                            </span>
                                        </div>
                                    )}
                                    <span className="text-xs text-blue-300 mt-2">你</span>
                                </div>

                                {/* 箭頭動畫 */}
                                <div className="flex flex-col items-center">
                                    <div className="relative transfer-arrow-flow mx-2">
                                        <ArrowRight className="h-8 w-8 text-blue-400" />
                                        <div className="absolute inset-0 rounded-full bg-blue-400/20 animate-ping" />
                                    </div>
                                </div>

                                {/* 接收者 */}
                                <div className="flex flex-col items-center">
                                    {transferSuccessData.recipientPhoto ? (
                                        <img
                                            src={transferSuccessData.recipientPhoto}
                                            className="h-12 w-12 rounded-full border-2 border-purple-400 shadow-lg"
                                        />
                                    ) : (
                                        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center border-2 border-purple-400 shadow-lg">
                                            <span className="text-white font-bold">
                                                {String(transferSuccessData.recipient || '').substring(0, 1).toUpperCase() || "R"}
                                            </span>
                                        </div>
                                    )}
                                    <span className="text-xs text-purple-300 mt-2 max-w-16">
                                        {transferSuccessData.recipient}
                                    </span>
                                </div>
                            </div>

                            {/* 交易詳情 */}
                            <div className="space-y-3 mb-6">
                                <div className="rounded-xl bg-gradient-to-r from-blue-800/30 to-purple-800/30 p-4 border border-blue-500/20">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div className="flex items-center gap-2">
                                            <DollarSign className="h-4 w-4 text-green-400" />
                                            <span className="text-blue-300">轉帳金額</span>
                                        </div>
                                        <div className="text-right font-bold text-white">
                                            {transferSuccessData.amount.toLocaleString()} 點
                                        </div>
                                        
                                        <div className="flex items-center gap-2">
                                            <DollarSign className="h-4 w-4 text-orange-300" />
                                            <span className="text-blue-300">手續費</span>
                                        </div>
                                        <div className="text-right font-bold text-orange-300">
                                            {transferSuccessData.fee.toLocaleString()} 點
                                        </div>
                                        
                                        <div className="flex items-center gap-2">
                                            <Clock className="h-4 w-4 text-blue-200" />
                                            <span className="text-blue-300">時間</span>
                                        </div>
                                        <div className="text-right font-bold text-white">
                                            {dayjs(transferSuccessData.timestamp)
                                                .add(8, 'hour')
                                                .format('MM/DD HH:mm:ss')}
                                        </div>
                                    </div>
                                </div>
                                
                                {transferSuccessData.note && (
                                    <div className="rounded-xl bg-gradient-to-r from-purple-800/30 to-pink-800/30 p-3 border border-purple-500/20">
                                        <span className="text-sm text-purple-300 block mb-1">備註</span>
                                        <span className="text-white text-sm break-words">
                                            {transferSuccessData.note}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* 確認按鈕 */}
                            <button
                                onClick={closeTransferSuccess}
                                className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 py-3 font-medium text-white transition-all duration-300 hover:from-blue-700 hover:to-purple-700 hover:shadow-lg active:scale-95 flex items-center justify-center gap-2"
                            >
                                OK
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
