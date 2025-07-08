import { useState } from "react";
import { PermissionButton } from "./PermissionGuard";
import { PERMISSIONS } from "@/contexts/PermissionContext";
import { givePoints } from "@/lib/api";
import QRCode from "react-qr-code";

/**
 * QR Code 生成器組件
 * 用於生成一次性的點數加點 QR Code
 */
export const QRCodeGenerator = ({ token, showNotification }) => {
    const [pointsPerQR, setPointsPerQR] = useState(50);
    const [qrCodes, setQrCodes] = useState([]);
    const [generateCount, setGenerateCount] = useState(10);
    const [isGenerating, setIsGenerating] = useState(false);

    // 生成QR Code
    const generateQRCodes = async () => {
        if (!pointsPerQR || pointsPerQR <= 0) {
            showNotification("請輸入有效的點數數量", "error");
            return;
        }

        if (!generateCount || generateCount <= 0 || generateCount > 100) {
            showNotification("請輸入有效的生成數量（1-100）", "error");
            return;
        }

        setIsGenerating(true);
        try {
            const newQRCodes = [];
            
            for (let i = 0; i < generateCount; i++) {
                // 生成唯一的QR Code ID
                const qrId = `qr_${Date.now()}_${i}_${Math.random().toString(36).substr(2, 9)}`;
                
                // QR Code 數據結構
                const qrData = {
                    type: 'points_redeem',
                    id: qrId,
                    points: pointsPerQR,
                    created_at: new Date().toISOString(),
                    used: false
                };

                newQRCodes.push({
                    id: qrId,
                    data: JSON.stringify(qrData),
                    points: pointsPerQR,
                    created_at: new Date().toISOString(),
                    used: false
                });
            }

            setQrCodes(prev => [...prev, ...newQRCodes]);
            showNotification(`成功生成 ${generateCount} 個 QR Code，每個 ${pointsPerQR} 點`, "success");
        } catch (error) {
            showNotification(`生成 QR Code 失敗: ${error.message}`, "error");
        } finally {
            setIsGenerating(false);
        }
    };

    // 清空所有QR Code
    const clearAllQRCodes = () => {
        if (confirm("確定要清空所有 QR Code 嗎？")) {
            setQrCodes([]);
            showNotification("已清空所有 QR Code", "info");
        }
    };

    // 刪除單個QR Code
    const deleteQRCode = (id) => {
        setQrCodes(prev => prev.filter(qr => qr.id !== id));
        showNotification("QR Code 已刪除", "info");
    };

    // 列印功能
    const printQRCodes = async () => {
        if (qrCodes.length === 0) {
            showNotification("沒有可列印的 QR Code", "error");
            return;
        }

        // 先在主視窗中產生 QR Code 的 base64 圖片
        const qrImages = [];
        
        // 動態導入 QRCode 庫
        const QRCodeLib = await import('qrcode');
        
        for (const qr of qrCodes) {
            try {
                const qrImageUrl = await QRCodeLib.default.toDataURL(qr.data, {
                    width: 120,
                    height: 120,
                    margin: 1,
                    color: { dark: '#000000', light: '#ffffff' }
                });
                qrImages.push({
                    id: qr.id,
                    points: qr.points,
                    imageUrl: qrImageUrl
                });
            } catch (error) {
                console.error('Failed to generate QR code for', qr.id, error);
            }
        }

        const printWindow = window.open('', '_blank');
        const printContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>QR Code 列印</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: white;
                    }
                    .qr-grid {
                        display: grid;
                        grid-template-columns: repeat(4, 1fr);
                        gap: 15px;
                        margin-bottom: 20px;
                    }
                    .qr-item {
                        border: 2px dashed #ccc;
                        padding: 15px;
                        text-align: center;
                        background: #f9f9f9;
                        border-radius: 10px;
                        page-break-inside: avoid;
                    }
                    .qr-code {
                        margin: 10px 0;
                    }
                    .qr-info {
                        margin-top: 10px;
                        font-size: 14px;
                        color: #333;
                    }
                    .qr-points {
                        font-size: 18px;
                        font-weight: bold;
                        color: #2563eb;
                        margin: 5px 0;
                    }
                    .qr-id {
                        font-size: 10px;
                        color: #666;
                        font-family: monospace;
                        word-break: break-all;
                    }
                    .print-header {
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 2px solid #333;
                        padding-bottom: 10px;
                    }
                    @media print {
                        body { margin: 0; padding: 10px; }
                        .qr-grid { gap: 12px; }
                        .qr-item { 
                            break-inside: avoid; 
                            padding: 10px;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="print-header">
                    <h1>SITCON Camp 2025 點數兌換 QR Code</h1>
                    <p>生成時間: ${new Date().toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' })}</p>
                    <p>總數量: ${qrImages.length} 個</p>
                </div>
                <div class="qr-grid">
                    ${qrImages.map(qr => `
                        <div class="qr-item">
                            <div class="qr-code">
                                <div style="background: white; padding: 10px; display: inline-block; border-radius: 8px;">
                                    <img src="${qr.imageUrl}" width="120" height="120" alt="QR Code" style="display: block;" />
                                </div>
                            </div>
                            <div class="qr-info">
                                <div class="qr-points">${qr.points} 點</div>
                                <div class="qr-id">${qr.id}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <script>
                    // 等待圖片載入完成後自動列印
                    window.addEventListener('load', function() {
                        setTimeout(() => {
                            window.print();
                        }, 500);
                    });
                </script>
            </body>
            </html>
        `;

        printWindow.document.write(printContent);
        printWindow.document.close();
    };

    return (
        <div className="rounded-lg border border-[#294565] bg-[#1A325F] p-6 shadow">
            <h2 className="mb-4 text-xl font-bold text-yellow-400">
                QR Code 生成器
            </h2>
            
            <div className="space-y-6">
                {/* 設定區 */}
                <div className="rounded-lg border border-[#294565] bg-[#0f203e] p-4">
                    <h3 className="mb-3 text-lg font-semibold text-[#7BC2E6]">生成設定</h3>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div>
                            <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                每個 QR Code 點數
                            </label>
                            <input
                                type="number"
                                value={pointsPerQR}
                                onChange={(e) => setPointsPerQR(parseInt(e.target.value) || 0)}
                                min="1"
                                max="1000"
                                className="w-full rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                placeholder="例如: 50"
                            />
                        </div>
                        <div>
                            <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                生成數量
                            </label>
                            <input
                                type="number"
                                value={generateCount}
                                onChange={(e) => setGenerateCount(parseInt(e.target.value) || 0)}
                                min="1"
                                max="100"
                                className="w-full rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                placeholder="例如: 10"
                            />
                        </div>
                    </div>
                    <div className="mt-4 flex gap-3">
                        <PermissionButton
                            requiredPermission={PERMISSIONS.GIVE_POINTS}
                            token={token}
                            onClick={generateQRCodes}
                            disabled={isGenerating || !pointsPerQR || !generateCount}
                            className="flex-1 rounded-xl bg-yellow-600 px-4 py-2 text-white transition-colors hover:bg-yellow-700 disabled:cursor-not-allowed disabled:bg-gray-600"
                        >
                            {isGenerating ? "生成中..." : "生成 QR Code"}
                        </PermissionButton>
                        {qrCodes.length > 0 && (
                            <>
                                <button
                                    onClick={printQRCodes}
                                    className="rounded-xl bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
                                >
                                    列印全部
                                </button>
                                <button
                                    onClick={clearAllQRCodes}
                                    className="rounded-xl bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
                                >
                                    清空全部
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {/* 統計區 */}
                {qrCodes.length > 0 && (
                    <div className="rounded-lg border border-[#294565] bg-[#0f203e] p-4">
                        <h3 className="mb-3 text-lg font-semibold text-[#7BC2E6]">統計資訊</h3>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-white">{qrCodes.length}</div>
                                <div className="text-sm text-gray-400">總QR Code數</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-green-400">
                                    {qrCodes.filter(qr => !qr.used).length}
                                </div>
                                <div className="text-sm text-gray-400">未使用</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-400">
                                    {qrCodes.reduce((total, qr) => total + qr.points, 0)}
                                </div>
                                <div className="text-sm text-gray-400">總點數價值</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* QR Code 列表 */}
                {qrCodes.length > 0 && (
                    <div className="rounded-lg border border-[#294565] bg-[#0f203e] p-4">
                        <h3 className="mb-3 text-lg font-semibold text-[#7BC2E6]">
                            已生成的 QR Code ({qrCodes.length})
                        </h3>
                        <div className="max-h-96 overflow-y-auto">
                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                                {qrCodes.map((qr) => (
                                    <div key={qr.id} className="rounded-lg border border-[#469FD2] bg-[#1A325F] p-4">
                                        <div className="text-center">
                                            <div className="mb-2 inline-block rounded-lg bg-white p-2">
                                                <QRCode
                                                    value={qr.data}
                                                    size={100}
                                                    bgColor="#ffffff"
                                                    fgColor="#000000"
                                                />
                                            </div>
                                            <div className="space-y-1">
                                                <div className="text-lg font-bold text-yellow-400">
                                                    {qr.points} 點
                                                </div>
                                                <div className="text-xs text-gray-400 font-mono">
                                                    {qr.id}
                                                </div>
                                                <div className="text-xs text-gray-400">
                                                    {new Date(qr.created_at).toLocaleString('zh-TW', { 
                                                        timeZone: 'Asia/Taipei' 
                                                    })}
                                                </div>
                                                <div className="flex gap-2 mt-2">
                                                    <button
                                                        onClick={() => deleteQRCode(qr.id)}
                                                        className="text-xs bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700"
                                                    >
                                                        刪除
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* 使用說明 */}
                <div className="rounded-lg border border-green-500/30 bg-green-600/10 p-4">
                    <h3 className="mb-2 text-lg font-semibold text-green-400">使用說明</h3>
                    <ul className="space-y-1 text-sm text-green-300">
                        <li>• 設定每個 QR Code 要給的點數量</li>
                        <li>• 設定要生成的 QR Code 數量</li>
                        <li>• 點擊「生成 QR Code」按鈕</li>
                        <li>• 使用「列印全部」功能可以列印所有 QR Code</li>
                        <li>• 學生可以在個人面板掃描 QR Code 來獲得點數</li>
                        <li>• 每個 QR Code 只能使用一次</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default QRCodeGenerator;