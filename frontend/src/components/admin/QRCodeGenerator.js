import { useState, useEffect } from "react";
import { PermissionButton } from "./PermissionGuard";
import { PERMISSIONS } from "@/contexts/PermissionContext";
import { createQRCode, listQRCodes } from "@/lib/api";
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
    const [isLoading, setIsLoading] = useState(true);
    const [filterUsed, setFilterUsed] = useState(null); // null=全部, true=已使用, false=未使用

    // 載入 QR Code 記錄
    const loadQRCodes = async () => {
        try {
            setIsLoading(true);
            const records = await listQRCodes(token, 100, filterUsed);
            // 轉換後端格式為前端格式
            const formattedQRCodes = records.map(record => ({
                id: record.id,
                data: record.qr_data,
                points: record.points,
                created_at: record.created_at,
                used: record.used,
                used_by: record.used_by,
                used_at: record.used_at
            }));
            setQrCodes(formattedQRCodes);
        } catch (error) {
            console.error('載入 QR Code 記錄失敗:', error);
            showNotification('載入 QR Code 記錄失敗', 'error');
        } finally {
            setIsLoading(false);
        }
    };

    // 初始載入和過濾變更時重新載入
    useEffect(() => {
        if (token) {
            loadQRCodes();
        }
    }, [token, filterUsed]);

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
            const createdQRCodes = [];
            
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

                const qrDataString = JSON.stringify(qrData);

                // 保存到後端
                try {
                    const record = await createQRCode(token, qrDataString, pointsPerQR);
                    createdQRCodes.push({
                        id: record.id,
                        data: qrDataString,
                        points: record.points,
                        created_at: record.created_at,
                        used: record.used,
                        used_by: record.used_by,
                        used_at: record.used_at
                    });
                } catch (saveError) {
                    console.error(`保存 QR Code ${qrId} 失敗:`, saveError);
                    // 繼續生成其他 QR Code
                }
            }

            // 重新載入所有記錄以確保同步
            await loadQRCodes();
            showNotification(`成功生成 ${createdQRCodes.length} 個 QR Code，每個 ${pointsPerQR} 點`, "success");
        } catch (error) {
            showNotification(`生成 QR Code 失敗: ${error.message}`, "error");
        } finally {
            setIsGenerating(false);
        }
    };

    // 重新載入QR Code記錄
    const refreshQRCodes = () => {
        loadQRCodes();
        showNotification("已重新載入 QR Code 記錄", "info");
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
                        break-inside: avoid;
                        display: flex;
                        flex-direction: column;
                        height: auto;
                        min-height: 200px;
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
                        body { 
                            margin: 0; 
                            padding: 10px;
                            -webkit-print-color-adjust: exact;
                            print-color-adjust: exact;
                        }
                        .qr-grid { 
                            gap: 12px;
                            display: grid;
                            grid-template-columns: repeat(4, 1fr);
                        }
                        .qr-item { 
                            break-inside: avoid; 
                            page-break-inside: avoid;
                            -webkit-column-break-inside: avoid;
                            padding: 10px;
                            margin-bottom: 10px;
                            orphans: 1;
                            widows: 1;
                            min-height: 180px;
                            max-height: 220px;
                            overflow: hidden;
                        }
                        .print-header {
                            page-break-after: avoid;
                            break-after: avoid;
                        }
                        @page {
                            margin: 1cm;
                            size: A4;
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
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
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
                        <div>
                            <label className="mb-2 block text-sm font-medium text-[#7BC2E6]">
                                狀態篩選
                            </label>
                            <select
                                value={filterUsed === null ? 'all' : filterUsed ? 'used' : 'unused'}
                                onChange={(e) => {
                                    const value = e.target.value;
                                    setFilterUsed(value === 'all' ? null : value === 'used');
                                }}
                                className="w-full rounded-xl border border-[#469FD2] bg-[#1A325F] px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            >
                                <option value="all">全部</option>
                                <option value="unused">未使用</option>
                                <option value="used">已使用</option>
                            </select>
                        </div>
                    </div>
                    <div className="mt-4 flex gap-3">
                        <PermissionButton
                            requiredPermission={PERMISSIONS.GENERATE_QRCODE}
                            token={token}
                            onClick={generateQRCodes}
                            disabled={isGenerating || !pointsPerQR || !generateCount}
                            className="flex-1 rounded-xl bg-yellow-600 px-4 py-2 text-white transition-colors hover:bg-yellow-700 disabled:cursor-not-allowed disabled:bg-gray-600"
                        >
                            {isGenerating ? "生成中..." : "生成 QR Code"}
                        </PermissionButton>
                        <button
                            onClick={refreshQRCodes}
                            disabled={isLoading}
                            className="rounded-xl bg-green-600 px-4 py-2 text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-gray-600"
                        >
                            {isLoading ? "載入中..." : "重新載入"}
                        </button>
                        {qrCodes.length > 0 && (
                            <button
                                onClick={printQRCodes}
                                className="rounded-xl bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
                            >
                                列印全部
                            </button>
                        )}
                    </div>
                </div>

                {/* 統計區 */}
                {qrCodes.length > 0 && (
                    <div className="rounded-lg border border-[#294565] bg-[#0f203e] p-4">
                        <h3 className="mb-3 text-lg font-semibold text-[#7BC2E6]">統計資訊</h3>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
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
                                <div className="text-2xl font-bold text-red-400">
                                    {qrCodes.filter(qr => qr.used).length}
                                </div>
                                <div className="text-sm text-gray-400">已使用</div>
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
                                    <div key={qr.id} className={`rounded-lg border p-4 ${
                                        qr.used 
                                            ? 'border-red-400 bg-red-900/20' 
                                            : 'border-[#469FD2] bg-[#1A325F]'
                                    }`}>
                                        <div className="text-center">
                                            <div className="mb-2 inline-block rounded-lg bg-white p-2 relative">
                                                <QRCode
                                                    value={qr.data}
                                                    size={100}
                                                    bgColor="#ffffff"
                                                    fgColor="#000000"
                                                />
                                                {qr.used && (
                                                    <div className="absolute inset-0 bg-red-600/60 rounded-lg flex items-center justify-center">
                                                        <span className="text-white font-bold text-sm">已使用</span>
                                                    </div>
                                                )}
                                            </div>
                                            <div className="space-y-1">
                                                <div className="text-lg font-bold text-yellow-400">
                                                    {qr.points} 點
                                                </div>
                                                <div className={`text-sm font-medium ${
                                                    qr.used ? 'text-red-400' : 'text-green-400'
                                                }`}>
                                                    {qr.used ? '已使用' : '未使用'}
                                                </div>
                                                {qr.used && qr.used_by && (
                                                    <div className="text-xs text-red-300">
                                                        使用者: {qr.used_by}
                                                    </div>
                                                )}
                                                {qr.used && qr.used_at && (
                                                    <div className="text-xs text-red-300">
                                                        使用時間: {new Date(qr.used_at).toLocaleString('zh-TW', { 
                                                            timeZone: 'Asia/Taipei' 
                                                        })}
                                                    </div>
                                                )}
                                                <div className="text-xs text-gray-400 font-mono">
                                                    {qr.id}
                                                </div>
                                                <div className="text-xs text-gray-400">
                                                    建立: {new Date(qr.created_at).toLocaleString('zh-TW', { 
                                                        timeZone: 'Asia/Taipei' 
                                                    })}
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
                        <li>• 點選「生成 QR Code」按鈕生成並保存到資料庫</li>
                        <li>• 使用狀態篩選可以查看未使用或已使用的 QR Code</li>
                        <li>• 使用「列印全部」功能可以列印所有 QR Code</li>
                        <li>• 學生可以在個人面板掃描 QR Code 來獲得點數</li>
                        <li>• 每個 QR Code 只能使用一次，使用後會顯示使用者和時間</li>
                        <li>• 重新整理頁面後 QR Code 記錄會保留，不會消失</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default QRCodeGenerator;