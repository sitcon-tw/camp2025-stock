"use client";

import { useState, useRef, useEffect } from "react";
import { Camera, Eye, EyeOff } from "lucide-react";
import { Modal } from "@/components/ui";
import { verifyCommunityPassword, communityGivePoints } from "@/lib/api";
import QrScanner from "qr-scanner";

// 社群密碼配置 (Fallback用)
const COMMUNITY_PASSWORDS = {
    "SITCON 學生計算機年會": "Tiger9@Vault!Mo0n#42*",
    "OCF 開放文化基金會": "Ocean^CultuR3$Rise!888",
    "Ubuntu 台灣社群": "Ubun2u!Taipei@2025^Rocks",
    "MozTW 社群": "MozTw$Fox_@42Jade*Fire",
    "COSCUP 開源人年會": "COde*0p3n#Sun5et!UP22",
    "Taiwan Security Club": "S3curE@Tree!^Night_CLUB99",
    "SCoML 學生機器學習社群": "M@chin3Zebra_Learn#504*",
    "綠洲計畫 LZGH": "0@si5^L!ght$Grow*Green88",
    "PyCon TW": "PyTh0n#Conf!Luv2TW@2025"
};

export default function CommunityPage() {
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
                
                if (hoursDiff < 24 && Object.keys(COMMUNITY_PASSWORDS).includes(loginData.community)) {
                    setIsLoggedIn(true);
                    setCurrentCommunity(loginData.community);
                } else {
                    localStorage.removeItem('communityLogin');
                }
            } catch (e) {
                localStorage.removeItem('communityLogin');
            }
        }
    }, []);

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
            console.warn("API驗證失敗，使用fallback驗證:", error);
            
            // API 失敗時，使用本地 fallback 驗證
            for (const [communityName, communityPassword] of Object.entries(COMMUNITY_PASSWORDS)) {
                if (communityPassword === password) {
                    const loginData = {
                        community: communityName,
                        timestamp: new Date().toISOString(),
                        source: 'fallback'
                    };
                    localStorage.setItem('communityLogin', JSON.stringify(loginData));
                    setIsLoggedIn(true);
                    setCurrentCommunity(communityName);
                    setShowLoginForm(false);
                    setLoginForm({ password: "" });
                    return;
                }
            }
            
            setLoginError("密碼錯誤或不存在對應的社群");
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
        console.log('數據類型:', typeof qrData);
        console.log('數據長度:', qrData ? qrData.length : 0);
        
        try {
            if (!qrData || qrData.trim() === '') {
                setScanError('QR Code 數據為空，請重新掃描');
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
                    console.log('無法識別的 QR Code 格式');
                    setScanError(`無法解析的 QR Code 格式。數據內容: ${qrData.substring(0, 50)}...`);
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
                // 開啟快速轉帳模式
                setQuickTransferData(parsedData);
                setShowQuickTransfer(true);
                setTransferError("");
                setTransferSuccess("");
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

    // 關閉快速轉帳 Modal
    const closeQuickTransfer = () => {
        setShowQuickTransfer(false);
        setQuickTransferData(null);
        setTransferError("");
        setTransferSuccess("");
    };

    // 處理快速轉帳提交
    const handleQuickTransferSubmit = async (e) => {
        e.preventDefault();
        setTransferError("");
        setTransferSuccess("");
        setTransferLoading(true);
        
        try {
            const formData = new FormData(e.target);
            const amount = parseInt(formData.get('amount'));
            const note = formData.get('note') || `${currentCommunity} 攤位獎勵`;
            
            if (!amount || amount <= 0 || amount > 100) {
                setTransferError('請輸入1-100之間的有效點數');
                setTransferLoading(false);
                return;
            }
            
            // 從 localStorage 獲取社群密碼
            const communityLogin = localStorage.getItem('communityLogin');
            if (!communityLogin) {
                throw new Error('未找到社群登入資訊，請重新登入');
            }
            
            const loginData = JSON.parse(communityLogin);
            const communityName = loginData.community;
            
            // 根據社群名稱獲取密碼
            const communityPassword = COMMUNITY_PASSWORDS[communityName];
            if (!communityPassword) {
                throw new Error('無法獲取社群密碼，請重新登入');
            }
            
            // 使用 telegram_id 作為 username（暫時方案）
            const studentUsername = quickTransferData.id.toString();
            
            console.log('發放點數參數:', {
                communityPassword: communityPassword.substring(0, 5) + '...',
                studentUsername,
                amount,
                note
            });
            
            // 呼叫 API 發放點數
            const result = await communityGivePoints(communityPassword, studentUsername, amount, note);
            
            console.log('發放結果:', result);
            
            if (result.success) {
                // 關閉快速轉帳 Modal 並顯示成功訊息
                closeQuickTransfer();
                setScanSuccess(`🎉 成功發放！給學員 ${result.student} 發放了 ${result.points} 點數`);
                
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
                
                // 5秒後清除成功訊息
                setTimeout(() => {
                    setScanSuccess('');
                }, 5000);
            } else {
                setTransferError(result.message || '發放點數失敗');
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
                                    src="/sitcon-logo.png" 
                                    alt="SITCON Logo" 
                                    className="mx-auto h-32 w-auto"
                                    onError={(e) => {
                                        e.target.style.display = 'none';
                                        e.target.nextElementSibling.style.display = 'block';
                                    }}
                                />
                                <div className="hidden rounded-xl bg-gradient-to-br from-[#469FD2] to-[#357AB8] p-8 text-white">
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
                                請輸入您的社群專屬密碼，系統將自動識別對應的社群
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
                                輸入密碼後系統將自動識別您的社群身份
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
                        <div className="text-xs text-[#557797] bg-[#0f203e] p-2 rounded">
                            <p>✅ 支援格式: {"{"}"type":"transfer","id":"學員ID"{"}"}</p>
                        </div>
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
                                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-[#469FD2] to-[#357AB8] text-white font-bold text-lg">
                                    學
                                </div>
                                <div className="flex-1">
                                    <p className="font-medium text-[#92cbf4]">發放點數給學員</p>
                                    <p className="text-xl font-bold text-white">
                                        ID: {quickTransferData.id}
                                    </p>
                                    <p className="text-xs text-[#557797]">
                                        來自 {currentCommunity} 攤位
                                    </p>
                                </div>
                            </div>
                        </div>

                        <form onSubmit={handleQuickTransferSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-[#92cbf4] mb-2">
                                    發放點數 <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="number"
                                    name="amount"
                                    className="w-full rounded-xl border border-[#294565] bg-[#0f203e] px-3 py-2 text-white focus:border-[#469FD2] focus:outline-none"
                                    placeholder="輸入發放點數"
                                    min="1"
                                    max="100"
                                    defaultValue="10"
                                    required
                                    autoFocus
                                />
                                <p className="mt-1 text-xs text-[#557797]">
                                    可發放點數：1-100 點
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
                    </div>
                )}
            </Modal>
        </div>
    );
}