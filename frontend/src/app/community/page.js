"use client";

import { useState, useRef, useEffect } from "react";
import { Camera, Eye, EyeOff } from "lucide-react";
import { Modal } from "@/components/ui";
import { verifyCommunityPassword, communityGivePoints, getStudentInfo, getCommunityGivingLogs, clearCommunityGivingLogs, checkStudentReward } from "@/lib/api";
import QrScanner from "qr-scanner";


export default function CommunityPage() {
    // 獲取當前社群的密碼
    const getCommunityPassword = () => {
        try {
            const communityLogin = localStorage.getItem('communityLogin');
            if (communityLogin) {
                const loginData = JSON.parse(communityLogin);
                return loginData.password; // 需要在登入時儲存密碼
            }
        } catch (e) {
            console.error('無法獲取社群密碼:', e);
        }
        return null;
    };
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [currentCommunity, setCurrentCommunity] = useState("");
    const [showLoginForm, setShowLoginForm] = useState(false);
    const [loginForm, setLoginForm] = useState({ password: "" });
    const [loginError, setLoginError] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [showQRScanner, setShowQRScanner] = useState(false);
    const [scanError, setScanError] = useState("");
    const [scanSuccess, setScanSuccess] = useState("");
    const [isScanning, setIsScanning] = useState(false);
    const videoRef = useRef(null);
    const qrScannerRef = useRef(null);
    const [showQuickTransfer, setShowQuickTransfer] = useState(false);
    const [quickTransferData, setQuickTransferData] = useState(null);
    const [transferLoading, setTransferLoading] = useState(false);
    const [transferError, setTransferError] = useState("");
    const [transferSuccess, setTransferSuccess] = useState("");
    const [givingLogs, setGivingLogs] = useState([]);
    const [logsLoading, setLogsLoading] = useState(false);
    const [logsError, setLogsError] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [filteredLogs, setFilteredLogs] = useState([]);
    const [showSuccessModal, setShowSuccessModal] = useState(false);
    const [successData, setSuccessData] = useState(null);
    const [deleteLoading, setDeleteLoading] = useState(false);
    const [deleteError, setDeleteError] = useState("");

    // 載入社群發放紀錄
    const loadGivingLogs = async () => {
        if (!isLoggedIn || !currentCommunity) return;
        
        setLogsLoading(true);
        setLogsError("");
        
        try {
            const communityPassword = getCommunityPassword();
            if (communityPassword) {
                const result = await getCommunityGivingLogs(communityPassword, 20);
                console.log('發放紀錄結果:', result);
                
                if (result && result.success) {
                    const logs = result.logs || [];
                    setGivingLogs(logs);
                    setFilteredLogs(logs);
                } else {
                    setLogsError(result?.message || '載入發放紀錄失敗');
                }
            }
        } catch (error) {
            console.error('載入發放紀錄失敗:', error);
            setLogsError('載入發放紀錄時發生錯誤');
        } finally {
            setLogsLoading(false);
        }
    };

    // 檢查登入狀態
    useEffect(() => {
        const savedLogin = localStorage.getItem('communityLogin');
        if (savedLogin) {
            try {
                const loginData = JSON.parse(savedLogin);
                // 檢查是否在24小時內
                const loginTime = new Date(loginData.timestamp);
                const now = new Date();
                const timeDiff = now - loginTime;
                const hoursDiff = timeDiff / (1000 * 60 * 60);
                
                if (hoursDiff < 24 && loginData.community && loginData.password) {
                    setIsLoggedIn(true);
                    setCurrentCommunity(loginData.community);
                } else {
                    // 如果超過 24 小時或缺少必要資料，清除登入狀態
                    localStorage.removeItem('communityLogin');
                }
            } catch (e) {
                localStorage.removeItem('communityLogin');
            }
        }
    }, []);

    // 當登入狀態或社群變更時載入發放紀錄
    useEffect(() => {
        if (isLoggedIn && currentCommunity) {
            loadGivingLogs();
        }
    }, [isLoggedIn, currentCommunity]);

    // 搜尋過濾邏輯
    useEffect(() => {
        if (!searchQuery.trim()) {
            setFilteredLogs(givingLogs);
        } else {
            const query = searchQuery.toLowerCase().trim();
            const filtered = givingLogs.filter(log => {
                const displayName = (log.student_display_name || '').toLowerCase();
                const username = (log.student_username || '').toLowerCase();
                const note = (log.note || '').toLowerCase();
                const amount = (log.amount || '').toString();
                
                return displayName.includes(query) || 
                       username.includes(query) || 
                       note.includes(query) || 
                       amount.includes(query);
            });
            setFilteredLogs(filtered);
        }
    }, [searchQuery, givingLogs]);

    // 處理登入
    const handleLogin = async (e) => {
        e.preventDefault();
        setLoginError("");
        
        const { password } = loginForm;
        
        if (!password) {
            setLoginError("請輸入密碼");
            return;
        }
        
        try {
            // 首先嘗試 API 驗證
            const result = await verifyCommunityPassword(password);
            
            if (result.success) {
                const loginData = {
                    community: result.community,
                    password: password, // 儲存密碼以供後續 API 使用
                    timestamp: new Date().toISOString(),
                    source: 'api'
                };
                localStorage.setItem('communityLogin', JSON.stringify(loginData));
                setIsLoggedIn(true);
                setCurrentCommunity(result.community);
                setShowLoginForm(false);
                setLoginForm({ password: "" });
                return;
            } else {
                setLoginError(result.message || "API驗證失敗");
            }
        } catch (error) {
            console.warn("API驗證失敗:", error);
            
            // API 失敗時，顯示錯誤訊息
            setLoginError("密碼驗證失敗，請檢查密碼是否正確或稍後再試");
        }
    };

    // 登出
    const handleLogout = () => {
        localStorage.removeItem('communityLogin');
        setIsLoggedIn(false);
        setCurrentCommunity("");
        setShowLoginForm(false);
        setLoginForm({ password: "" });
    };

    // 啟動 QR Scanner
    const startQRScanner = async () => {
        setShowQRScanner(true);
        setScanError("");
        setIsScanning(true);
        
        try {
            await new Promise(resolve => setTimeout(resolve, 100));
            
            if (videoRef.current) {
                qrScannerRef.current = new QrScanner(
                    videoRef.current,
                    result => {
                        console.log('QR Code 掃描結果:', result.data);
                        handleQRResult(result.data);
                    },
                    {
                        returnDetailedScanResult: true,
                        highlightScanRegion: true,
                        highlightCodeOutline: true,
                    }
                );
                
                await qrScannerRef.current.start();
                setIsScanning(false);
            }
        } catch (error) {
            console.error('啟動相機失敗:', error);
            setScanError('無法啟動相機，請檢查權限設定');
            setShowQRScanner(false);
            setIsScanning(false);
        }
    };

    // 處理 QR Code 掃描結果
    const handleQRResult = async (qrData) => {
        console.log('=== QR Code 掃描Debug ===');
        console.log('原始 QR Data:', qrData);
        console.log('資料類型:', typeof qrData);
        console.log('資料長度:', qrData ? qrData.length : 0);
        
        try {
            if (!qrData || qrData.trim() === '') {
                setScanError('QR Code 資料為空，請重新掃描');
                return;
            }

            // 先嘗試解析 JSON
            let parsedData;
            try {
                parsedData = JSON.parse(qrData);
                console.log('JSON 解析成功:', parsedData);
            } catch (jsonError) {
                console.log('JSON 解析失敗:', jsonError);
                
                // 如果不是 JSON，嘗試其他常見格式
                console.log('嘗試直接處理為純文字或其他格式...');
                
                // 檢查是否為簡單的文字格式
                if (qrData.includes('points') || qrData.includes('redeem')) {
                    console.log('檢測到可能的點數兌換相關文字');
                    setScanError('QR Code 格式不正確，請確認為有效的點數兌換 QR Code');
                } else {
                    console.log('無法辨識的 QR Code 格式');
                    setScanError(`無法解析的 QR Code 格式。資料內容: ${qrData.substring(0, 50)}...`);
                }
                setTimeout(() => setScanError(''), 5000);
                return;
            }
            
            console.log('解析後的 QR Data:', parsedData);
            console.log('類型檢查:', {
                type: parsedData.type,
                hasId: !!parsedData.id,
                hasPoints: !!parsedData.points,
                points: parsedData.points
            });
            
            // 檢查是否為學員轉帳 QR Code
            if (parsedData.type === 'transfer' && parsedData.id) {
                console.log('符合學員轉帳 QR Code 格式，開始處理...');
                // 停止掃描器
                if (qrScannerRef.current) {
                    qrScannerRef.current.stop();
                }
                stopQRScanner();
                // 獲取學員資訊並開啟快速轉帳模式
                await fetchStudentInfo(parsedData);
            } else {
                console.log('不符合預期格式');
                console.log('預期格式: {type: "transfer", id: "telegram_id"}');
                console.log('實際格式:', parsedData);
                
                let errorMsg = '無效的 QR Code 格式。';
                if (!parsedData.type) {
                    errorMsg += ' 缺少 type 欄位。';
                } else if (parsedData.type !== 'transfer') {
                    errorMsg += ` type 應為 "transfer"，實際為 "${parsedData.type}"。`;
                }
                if (!parsedData.id) {
                    errorMsg += ' 缺少 id 欄位。';
                }
                
                setScanError(errorMsg);
                setTimeout(() => setScanError(''), 5000);
            }
        } catch (error) {
            console.error('QR Code 處理失敗:', error);
            setScanError(`QR Code 處理錯誤: ${error.message}`);
            setTimeout(() => setScanError(''), 5000);
        }
        
        console.log('=== QR Code Debug 結束 ===');
    };

    // 獲取學員資訊
    const fetchStudentInfo = async (qrData) => {
        try {
            console.log('開始處理學員資訊:', qrData);
            
            // 設定基本資料（作為fallback）
            const preferredIdentifier = qrData.id;
            console.log('使用學員ID:', preferredIdentifier);
            
            const basicStudentData = {
                username: `學員 ${preferredIdentifier}`,
                id: String(qrData.id),
                photo_url: null
            };

            console.log('設定基本學員資料:', basicStudentData);
            setQuickTransferData(basicStudentData);
            setShowQuickTransfer(true);
            setTransferError("");
            setTransferSuccess("");
            
            // 立即檢查是否已經領取過獎勵（基本資料情況）
            const communityPassword = getCommunityPassword();
            if (communityPassword) {
                try {
                    const rewardCheck = await checkStudentReward(communityPassword, preferredIdentifier);
                    console.log('基本資料獎勵檢查結果:', rewardCheck);
                    
                    if (rewardCheck && rewardCheck.success && rewardCheck.already_given) {
                        // 已經領取過，直接顯示警告
                        setTransferError(
                            `${rewardCheck.message}\n` +
                            `上次發放：${rewardCheck.previous_amount} 點`
                        );
                        console.log('基本資料檢測到重複發放，已設定警告訊息');
                    }
                } catch (rewardCheckError) {
                    console.log('基本資料獎勵檢查失敗:', rewardCheckError);
                    // 檢查失敗不影響正常流程
                }
            }

            // 使用新的學員資訊 API 獲取完整資訊（包括頭像）
            try {
                // 從 localStorage 獲取社群密碼
                const communityLogin = localStorage.getItem('communityLogin');
                if (communityLogin) {
                    const communityPassword = getCommunityPassword();
                    
                    if (communityPassword) {
                        console.log('嘗試獲取學員完整資訊...');
                        const studentInfo = await getStudentInfo(communityPassword, preferredIdentifier);
                        console.log('學員資訊 API 返回結果:', studentInfo);
                        
                        if (studentInfo && studentInfo.success) {
                            const updatedData = {
                                username: studentInfo.student_display_name || basicStudentData.username,
                                id: studentInfo.student_id || String(qrData.id),
                                photo_url: studentInfo.student_photo_url,
                                team: studentInfo.student_team,
                                points: studentInfo.student_points
                            };
                            console.log('更新學員完整資料:', updatedData);
                            setQuickTransferData(updatedData);
                            
                            // 立即檢查是否已經領取過獎勵
                            try {
                                const rewardCheck = await checkStudentReward(communityPassword, preferredIdentifier);
                                console.log('獎勵檢查結果:', rewardCheck);
                                
                                if (rewardCheck && rewardCheck.success && rewardCheck.already_given) {
                                    // 已經領取過，直接顯示警告
                                    setTransferError(
                                        `${rewardCheck.message}\n` +
                                        `上次發放：${rewardCheck.previous_amount} 點`
                                    );
                                    console.log('檢測到重複發放，已設定警告訊息');
                                } else {
                                    // 未領取過，清除可能的錯誤訊息
                                    setTransferError("");
                                }
                            } catch (rewardCheckError) {
                                console.log('獎勵檢查失敗:', rewardCheckError);
                                // 檢查失敗不影響正常流程，讓後端在實際發放時檢查
                            }
                            
                            console.log('成功獲取學員完整資訊:', {
                                display_name: studentInfo.student_display_name,
                                photo_url: studentInfo.student_photo_url,
                                team: studentInfo.student_team,
                                points: studentInfo.student_points
                            });
                        } else {
                            console.log('學員資訊 API 失敗，使用基本資料:', studentInfo?.message || '未知錯誤');
                        }
                    }
                }
            } catch (userInfoError) {
                console.log('獲取學員資訊失敗:', userInfoError);
                // 如果是 404 錯誤，說明 API 還沒部署，嘗試使用排行榜 API 作為 fallback
                if (userInfoError.message && userInfoError.message.includes('404')) {
                    console.log('新 API 未部署，嘗試使用排行榜 fallback...');
                    try {
                        const { getUserDisplayNameFromLeaderboard } = await import("@/lib/api");
                        const userInfo = await getUserDisplayNameFromLeaderboard(preferredIdentifier);
                        if (userInfo && userInfo.display_name) {
                            const updatedData = {
                                ...basicStudentData,
                                username: userInfo.display_name,
                                team: userInfo.team,
                                photo_url: null // 排行榜不提供頭像
                            };
                            console.log('Fallback: 更新學員資料:', updatedData);
                            setQuickTransferData(updatedData);
                        }
                    } catch (fallbackError) {
                        console.log('Fallback 也失敗:', fallbackError);
                    }
                }
                // 保持使用基本資料，不顯示錯誤給使用者
                console.log('將使用基本資料繼續:', basicStudentData);
            }
            
        } catch (error) {
            console.error('處理學員資訊失敗:', error);
            setScanError(`處理失敗: ${error.message}`);
            setTimeout(() => setScanError(''), 5000);
        }
    };

    // 關閉快速轉帳 Modal
    const closeQuickTransfer = () => {
        setShowQuickTransfer(false);
        setQuickTransferData(null);
        setTransferError("");
        setTransferSuccess("");
    };

    // 關閉成功 Modal
    const closeSuccessModal = () => {
        setShowSuccessModal(false);
        setSuccessData(null);
    };

    // 清除發放紀錄（開發測試用）
    const handleClearLogs = async () => {
        if (!confirm('⚠️ 確定要清除所有發放紀錄嗎？\n這個操作無法復原！（僅限開發測試）')) {
            return;
        }

        setDeleteLoading(true);
        setDeleteError("");

        try {
            const communityPassword = getCommunityPassword();
            if (!communityPassword) {
                throw new Error('無法獲取社群密碼，請重新登入');
            }

            const result = await clearCommunityGivingLogs(communityPassword);
            console.log('清除紀錄結果:', result);

            if (result.success) {
                alert(`✅ 成功清除 ${result.deleted_count} 筆發放紀錄`);
                // 重新載入發放紀錄
                loadGivingLogs();
            } else {
                setDeleteError(result.message || '清除紀錄失敗');
            }
        } catch (error) {
            console.error('清除紀錄失敗:', error);
            setDeleteError(`清除失敗: ${error.message}`);
        } finally {
            setDeleteLoading(false);
        }
    };

    // 處理快速轉帳提交
    const handleQuickTransferSubmit = async (e) => {
        e.preventDefault();
        
        // 檢查是否已經有重複發放的錯誤
        if (transferError && (transferError.includes('已經領取過') || transferError.includes('領取過'))) {
            console.log('已有重複發放警告，阻止提交');
            return;
        }
        
        setTransferError("");
        setTransferSuccess("");
        setTransferLoading(true);
        
        try {
            const formData = new FormData(e.target);
            const note = formData.get('note') || `${currentCommunity} 攤位獎勵`;
            
            // 從 localStorage 獲取社群密碼
            const communityLogin = localStorage.getItem('communityLogin');
            if (!communityLogin) {
                throw new Error('未找到社群登入資訊，請重新登入');
            }
            
            // 獲取社群密碼
            const communityPassword = getCommunityPassword();
            if (!communityPassword) {
                throw new Error('無法獲取社群密碼，請重新登入');
            }
            
            // 使用 telegram_id 作為 username（暫時方案）
            const studentUsername = quickTransferData.id.toString();
            
            console.log('發放點數參數:', {
                communityPassword: communityPassword.substring(0, 5) + '...',
                studentUsername,
                note,
                fixedAmount: 1000
            });
            
            // 呼叫 API 發放點數 (固定1000點)
            const result = await communityGivePoints(communityPassword, studentUsername, note);
            
            console.log('發放結果:', result);
            
            if (result.success) {
                // 如果 API 返回了學員的詳細資訊，先更新 Modal 顯示
                if (result.student_display_name || result.student_photo_url) {
                    const updatedData = {
                        ...quickTransferData,
                        username: result.student_display_name || quickTransferData.username,
                        photo_url: result.student_photo_url || quickTransferData.photo_url,
                        team: result.student_team || quickTransferData.team
                    };
                    console.log('從發放結果更新學員資料:', updatedData);
                    setQuickTransferData(updatedData);
                    
                    // 短暫延遲讓用戶看到更新的資訊
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
                
                // 關閉快速轉帳 Modal 並顯示成功 Modal
                closeQuickTransfer();
                const displayName = result.student_display_name || result.student || quickTransferData.username;
                
                // 設置成功 Modal 的資料
                setSuccessData({
                    studentName: displayName,
                    studentPhoto: result.student_photo_url || quickTransferData.photo_url,
                    studentTeam: result.student_team || quickTransferData.team,
                    points: result.points,
                    community: currentCommunity,
                    newBalance: result.new_balance
                });
                setShowSuccessModal(true);
                
                // 重新載入發放紀錄
                loadGivingLogs();
                
                // 播放成功音效
                try {
                    const AudioContext = window.AudioContext;
                    const audioContext = new AudioContext();
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
            } else {
                // 檢查是否為重複發放錯誤
                if (result.already_given) {
                    setTransferError(
                        `${result.message}\n` +
                        `上次發放：${result.previous_amount} 點`
                    );
                } else {
                    setTransferError(result.message || '發放點數失敗');
                }
            }
            
        } catch (error) {
            console.error('發放點數失敗:', error);
            setTransferError(`發放失敗: ${error.message}`);
        } finally {
            setTransferLoading(false);
        }
    };

    // 停止 QR Scanner
    const stopQRScanner = () => {
        try {
            if (qrScannerRef.current) {
                qrScannerRef.current.stop();
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
        setIsScanning(false);
    };

    // 清理 QR Scanner
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
        };
    }, []);

    // 如果未登入，顯示登入頁面
    if (!isLoggedIn) {
        return (
            <div className="flex min-h-screen w-full bg-[#0f203e] pt-10 pb-20 md:items-center">
                <div className="w-full space-y-6 p-4">
                    {/* 社群攤位標題 */}
                    <div className="mx-auto max-w-2xl text-center">
                        <h1 className="text-3xl font-bold text-[#92cbf4] mb-2">
                            社群攤位
                        </h1>
                        <p className="text-[#557797]">
                            請先登入您的社群帳號
                        </p>
                    </div>

                    {/* 社群 Logo */}
                    <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-8">
                        <div className="text-center">
                            <div className="mb-6">
                                <img 
                                    src="/withname-white.svg" 
                                    alt="SITCON Logo" 
                                    className="mx-auto h-32 w-auto"
                                    onError={(e) => {
                                        e.target.style.display = 'none';
                                        e.target.nextElementSibling.style.display = 'block';
                                    }}
                                />
                                <div className="rounded-xl bg-gradient-to-br from-[#469FD2] to-[#357AB8] p-8 text-white" style={{display: 'none'}}>
                                    <div className="text-4xl font-bold mb-2">SITCON</div>
                                    <div className="text-lg">Students' Information Technology Conference</div>
                                </div>
                            </div>
                            <h2 className="text-2xl font-semibold text-[#92cbf4] mb-2">
                                SITCON Camp 2025
                            </h2>
                            <p className="text-[#557797]">
                                學生計算機年會夏令營
                            </p>
                        </div>
                    </div>

                    {/* 登入區域 */}
                    <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                        <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                            社群登入
                        </h3>
                        
                        <div className="text-center">
                            <p className="mb-6 text-sm text-[#557797]">
                                請選擇您的社群並輸入密碼以開始使用
                            </p>
                            
                            <button
                                onClick={() => setShowLoginForm(true)}
                                className="w-full rounded-xl bg-gradient-to-r from-[#469FD2] to-[#357AB8] px-6 py-4 text-white transition-all duration-200 hover:from-[#357AB8] hover:to-[#2B5A8B] hover:shadow-lg active:scale-95"
                            >
                                <div className="text-lg font-bold">
                                    社群登入
                                </div>
                                <div className="text-sm text-blue-100">
                                    點選進入登入頁面
                                </div>
                            </button>
                        </div>
                    </div>
                </div>

                {/* 登入表單 Modal */}
                <Modal
                    isOpen={showLoginForm}
                    onClose={() => setShowLoginForm(false)}
                    title="社群登入"
                    size="md"
                >
                    <form onSubmit={handleLogin} className="space-y-4">
                        {loginError && (
                            <div className="rounded-xl border border-red-500/30 bg-red-600/20 p-3">
                                <p className="text-sm text-red-400">
                                    ❌ {loginError}
                                </p>
                            </div>
                        )}
                        
                        <div className="text-center mb-4">
                            <p className="text-sm text-[#92cbf4]">
                                請輸入您的社群專屬密碼，系統將自動辨識對應的社群
                            </p>
                        </div>
                        
                        <div>
                            <label className="block text-sm font-medium text-[#92cbf4] mb-2">
                                社群專屬密碼
                            </label>
                            <div className="relative">
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={loginForm.password}
                                    onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                                    className="w-full rounded-xl border border-[#294565] bg-[#0f203e] px-3 py-2 pr-10 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="請輸入社群專屬密碼"
                                    required
                                    autoFocus
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#557797] hover:text-[#92cbf4]"
                                >
                                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                            <p className="mt-1 text-xs text-[#557797]">
                                輸入密碼後系統將自動辨識您的社群身份
                            </p>
                        </div>
                        
                        <div className="flex gap-3 pt-2">
                            <button
                                type="button"
                                onClick={() => setShowLoginForm(false)}
                                className="flex-1 rounded-xl border border-[#294565] bg-[#1A325F] px-4 py-2 text-[#92cbf4] transition-colors hover:bg-[#294565]"
                            >
                                取消
                            </button>
                            <button
                                type="submit"
                                className="flex-1 rounded-xl bg-[#469FD2] px-4 py-2 text-white transition-colors hover:bg-[#357AB8]"
                            >
                                登入
                            </button>
                        </div>
                    </form>
                </Modal>
            </div>
        );
    }

    // 已登入，顯示主要功能
    return (
        <div className="flex min-h-screen w-full bg-[#0f203e] pt-10 pb-20 md:items-center">
            <div className="w-full space-y-6 p-4">
                {/* 社群攤位標題 */}
                <div className="mx-auto max-w-2xl text-center">
                    <h1 className="text-3xl font-bold text-[#92cbf4] mb-2">
                        社群攤位
                    </h1>
                    <p className="text-[#557797]">
                        歡迎 {currentCommunity}
                    </p>
                </div>

                {/* 社群資訊 */}
                <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-[#92cbf4]">
                            目前登入社群
                        </h3>
                        <button
                            onClick={handleLogout}
                            className="rounded-xl border border-red-500/30 bg-red-600/20 px-3 py-1 text-sm text-red-400 transition-colors hover:bg-red-600/30"
                        >
                            登出
                        </button>
                    </div>
                    <div className="text-center">
                        <div className="mb-4">
                            <div className="mx-auto w-16 h-16 rounded-full bg-gradient-to-br from-[#469FD2] to-[#357AB8] flex items-center justify-center text-white font-bold text-xl">
                                {currentCommunity.substring(0, 2)}
                            </div>
                        </div>
                        <h2 className="text-xl font-semibold text-white mb-2">
                            {currentCommunity}
                        </h2>
                        <p className="text-[#557797] text-sm">
                            登入時間：{(() => {
                                try {
                                    const loginData = JSON.parse(localStorage.getItem('communityLogin'));
                                    return new Date(loginData.timestamp).toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' });
                                } catch (e) {
                                    return '未知';
                                }
                            })()}
                        </p>
                        <p className="text-[#557797] text-xs mt-1">
                            驗證方式：{(() => {
                                try {
                                    const loginData = JSON.parse(localStorage.getItem('communityLogin'));
                                    return loginData.source === 'api' ? 'API 驗證' : 'Fallback 驗證';
                                } catch (e) {
                                    return '未知';
                                }
                            })()}
                        </p>
                    </div>
                </div>

                {/* QR Code Scanner */}
                <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                    <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                        QR Code 掃描器
                    </h3>
                    
                    <div className="text-center">
                        <p className="mb-6 text-sm text-[#557797]">
                            點選下方按鈕開始掃描，兌換專屬點數獎勵
                        </p>
                        
                        <button
                            onClick={startQRScanner}
                            disabled={isScanning}
                            className="w-full rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 px-6 py-4 text-white transition-all duration-200 hover:from-green-700 hover:to-emerald-700 hover:shadow-lg active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            <Camera className="mx-auto mb-2 h-8 w-8" />
                            <div className="text-lg font-bold">
                                {isScanning ? '啟動中...' : '開始掃描 QR Code'}
                            </div>
                            <div className="text-sm text-green-100">
                                掃描兌換點數
                            </div>
                        </button>
                    </div>
                </div>

                {/* 成功/錯誤訊息 */}
                {scanSuccess && (
                    <div className="mx-auto max-w-2xl rounded-xl border border-green-500/30 bg-green-600/20 p-4">
                        <p className="text-center text-green-400">
                            {scanSuccess}
                        </p>
                    </div>
                )}
                
                {scanError && (
                    <div className="mx-auto max-w-2xl rounded-xl border border-red-500/30 bg-red-600/20 p-4">
                        <p className="text-center text-red-400">
                            ❌ {scanError}
                        </p>
                    </div>
                )}

                {/* 發放紀錄 */}
                <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-[#92cbf4]">
                            發放紀錄
                        </h3>
                        <button
                            onClick={loadGivingLogs}
                            disabled={logsLoading}
                            className="rounded-lg border border-[#469FD2]/30 bg-[#469FD2]/10 px-3 py-1 text-sm text-[#92cbf4] transition-colors hover:bg-[#469FD2]/20 disabled:opacity-50"
                        >
                            {logsLoading ? '載入中...' : '重新整理'}
                        </button>
                    </div>

                    {/* 搜尋欄 */}
                    <div className="mb-4">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="搜尋學員名稱、ID、備註或點數..."
                            className="w-full rounded-xl border border-[#294565] bg-[#0f203e] px-4 py-2 text-white placeholder-[#557797] focus:border-[#469FD2] focus:outline-none"
                        />
                        {searchQuery && (
                            <p className="mt-2 text-xs text-[#557797]">
                                找到 {filteredLogs.length} 筆紀錄
                            </p>
                        )}
                    </div>

                    {logsError && (
                        <div className="mb-4 rounded-xl border border-red-500/30 bg-red-600/20 p-3">
                            <p className="text-sm text-red-400">
                                ❌ {logsError}
                            </p>
                        </div>
                    )}

                    {logsLoading ? (
                        <div className="text-center py-8">
                            <p className="text-[#557797]">載入中...</p>
                        </div>
                    ) : filteredLogs.length === 0 ? (
                        <div className="text-center py-8">
                            <p className="text-[#557797]">
                                {searchQuery ? '沒有符合搜尋條件的紀錄' : '尚無發放紀錄'}
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-3 max-h-96 overflow-y-auto">
                            {filteredLogs.map((log, index) => (
                                <div key={log.id || index} className="rounded-lg border border-[#294565] bg-[#0f203e] p-3 relative">
                                    <div className="flex items-center justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <div className="flex flex-col">
                                                    <span className="font-medium text-white">
                                                        {log.student_display_name || log.student_username}
                                                    </span>
                                                    {log.student_display_name && log.student_display_name !== log.student_username && (
                                                        <span className="text-xs text-[#557797]">
                                                            ID: {log.student_username}
                                                        </span>
                                                    )}
                                                </div>
                                                <span className="text-lg font-bold text-green-400 ml-auto">
                                                    +{log.amount?.toLocaleString() || 0} 點
                                                </span>
                                            </div>
                                            {log.note && (
                                                <p className="text-xs text-[#557797] mb-1">
                                                    {log.note}
                                                </p>
                                            )}
                                            <div className="flex items-center gap-4 text-xs text-[#557797]">
                                                <span>
                                                    {log.created_at ? new Date(log.created_at).toLocaleString('zh-TW', {
                                                        timeZone: 'Asia/Taipei',
                                                        year: 'numeric',
                                                        month: '2-digit',
                                                        day: '2-digit',
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    }) : '時間未知'}
                                                </span>
                                                <span>
                                                    餘額：{log.balance_after?.toLocaleString() || 0} 點
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                
            </div>

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
                            請對準學員的轉帳 QR Code 進行掃描
                        </p>
                        <p className="text-xs text-[#557797]">
                            掃描後可選擇發放點數給該學員
                        </p>
                    </div>
                    
                    {scanError && (
                        <div className="rounded-xl border border-red-500/30 bg-red-600/20 p-3">
                            <p className="text-sm text-red-400">
                                ❌ {scanError}
                            </p>
                        </div>
                    )}
                </div>
            </Modal>

            {/* 快速轉帳 Modal */}
            <Modal
                isOpen={showQuickTransfer}
                onClose={closeQuickTransfer}
                title={`${currentCommunity} 快速贈點`}
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
                            <div className={`rounded-xl border p-3 ${
                                transferError.includes('已經領取過') || transferError.includes('領取過')
                                    ? 'border-yellow-500/30 bg-yellow-600/20'
                                    : 'border-red-500/30 bg-red-600/20'
                            }`}>
                                <p className={`text-sm whitespace-pre-line ${
                                    transferError.includes('已經領取過') || transferError.includes('領取過')
                                        ? 'text-yellow-400'
                                        : 'text-red-400'
                                }`}>
                                    {transferError.includes('已經領取過') || transferError.includes('領取過') ? '⚠️ ' : '❌ '}{transferError}
                                </p>
                            </div>
                        )}

                        {/* 收款人資訊確認 */}
                        <div className="rounded-xl border border-[#469FD2]/30 bg-[#469FD2]/10 p-4">
                            <div className="flex items-center gap-3">
                                {quickTransferData.photo_url ? (
                                    <img
                                        src={quickTransferData.photo_url}
                                        alt="學員大頭照"
                                        className="h-12 w-12 shrink-0 rounded-full object-cover shadow-lg ring-2 ring-[#469FD2]/50"
                                        onError={(e) => {
                                            e.target.style.display = 'none';
                                            e.target.nextElementSibling.style.display = 'flex';
                                        }}
                                    />
                                ) : null}
                                <div 
                                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#469FD2] to-[#357AB8] text-lg font-bold text-white shadow-lg ring-2 ring-white/20 border-2 border-white/10 ${quickTransferData.photo_url ? 'hidden' : 'flex'}`}
                                >
                                    {String(quickTransferData.username || '').substring(0, 1).toUpperCase() || "學"}
                                </div>
                                <div className="flex-1">
                                    <p className="text-xl font-bold text-white">
                                        {quickTransferData.username}
                                    </p>
                                    {quickTransferData.id && (
                                        <p className="text-xs text-[#557797]">
                                            ID: {quickTransferData.id}
                                        </p>
                                    )}
                                    {quickTransferData.team && (
                                        <p className="text-xs text-[#557797]">
                                            隊伍：{quickTransferData.team}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* 檢查是否有重複發放警告 */}
                        {transferError && (transferError.includes('已經領取過') || transferError.includes('領取過')) ? (
                            // 已有發放紀錄時，只顯示關閉按鈕
                            <div className="pt-4">
                                <button
                                    type="button"
                                    onClick={closeQuickTransfer}
                                    className="w-full rounded-xl bg-[#469FD2] px-4 py-3 text-white transition-colors hover:bg-[#357AB8]"
                                >
                                    關閉
                                </button>
                            </div>
                        ) : (
                            // 正常發放表單
                            <form onSubmit={handleQuickTransferSubmit} className="space-y-4">
                                <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-4 text-center">
                                    <div className="text-2xl font-bold text-green-400 mb-2">
                                        固定發放：1000 點
                                    </div>
                                    <p className="text-sm text-green-300">
                                        社群攤位統一發放獎勵點數
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
                                        placeholder={`${currentCommunity} 攤位獎勵`}
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
                                        {transferLoading ? '發放中...' : '確認發放'}
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                )}
            </Modal>

            {/* 成功發放 Modal */}
            <Modal
                isOpen={showSuccessModal}
                onClose={closeSuccessModal}
                title="🎉 發放成功"
            >
                {successData && (
                    <div className="space-y-6">
                        {/* 成功訊息 */}
                        <div className="text-center">
                            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-500/20">
                                <div className="text-3xl">✅</div>
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">
                                點數發放成功！
                            </h3>
                            <p className="text-[#92cbf4]">
                                已成功給學員發放點數獎勵
                            </p>
                        </div>

                        {/* 學員資訊 */}
                        <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-4">
                            <div className="flex items-center gap-3 mx-auto">
                                {successData.studentPhoto ? (
                                    <img
                                        src={successData.studentPhoto}
                                        alt="學員大頭照"
                                        className="h-12 w-12 shrink-0 rounded-full object-cover shadow-lg ring-2 ring-green-500/50 ml-1"
                                        onError={(e) => {
                                            e.target.style.display = 'none';
                                            e.target.nextElementSibling.style.display = 'flex';
                                        }}
                                    />
                                ) : null}
                                <div 
                                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-green-500 to-green-600 text-lg font-bold text-white shadow-lg ring-2 ring-white/20 border-2 border-white/10 ${successData.studentPhoto ? 'hidden' : 'flex'}`}
                                >
                                    {String(successData.studentName || '').substring(0, 1).toUpperCase() || "學"}
                                </div>
                                <div className="flex-1 ml-2">
                                    <p className="text-xl font-bold text-white">
                                        {successData.studentName}
                                    </p>
                                    {successData.studentTeam && (
                                        <p className="text-sm text-green-400">
                                            隊伍：{successData.studentTeam}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* 發放詳情 */}
                        <div className="space-y-3">
                            <div className="flex justify-between items-center py-2 border-b border-[#294565]">
                                <span className="text-[#92cbf4]">社群攤位</span>
                                <span className="text-white font-medium">{successData.community}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-[#294565]">
                                <span className="text-[#92cbf4]">發放點數</span>
                                <span className="text-green-400 font-bold text-lg">+{successData.points} 點</span>
                            </div>
                            {successData.newBalance && (
                                <div className="flex justify-between items-center py-2">
                                    <span className="text-[#92cbf4]">學員餘額</span>
                                    <span className="text-white font-medium">{successData.newBalance} 點</span>
                                </div>
                            )}
                        </div>

                        {/* 關閉按鈕 */}
                        <div className="pt-4">
                            <button
                                type="button"
                                onClick={closeSuccessModal}
                                className="w-full rounded-xl bg-green-500 px-4 py-3 text-white font-medium transition-colors hover:bg-green-600"
                            >
                                完成
                            </button>
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    );
}