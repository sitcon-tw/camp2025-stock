import { QrCode, Camera } from "lucide-react";

export default function PointTransfer({ 
    userPermissions, 
    onOpenQRCode, 
    onStartQRScanner, 
    onOpenTransferModal 
}) {
    // 檢查是否有轉帳權限
    const hasTransferPermission = userPermissions && 
        userPermissions.permissions && 
        userPermissions.permissions.includes('transfer_points');
    
    // 暫時的資訊
    console.log('PointTransfer - userPermissions:', userPermissions);
    console.log('PointTransfer - hasTransferPermission:', hasTransferPermission);
    
    if (!hasTransferPermission) {
        return null;
    }

    return (
        <div className="mx-auto max-w-2xl rounded-xl border border-[#294565] bg-[#1A325F] p-6">
            <h3 className="mb-4 text-lg font-semibold text-[#92cbf4]">
                點數轉帳
            </h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="text-center">
                    <button
                        onClick={onOpenQRCode}
                        className="w-full rounded-xl bg-[#3483b0] px-6 py-4 text-white transition-colors hover:bg-[#357AB8] focus:outline-none focus:ring-2 focus:ring-[#469FD2]/50"
                    >
                        <QrCode className="mx-auto mb-2 h-8 w-8" />
                        <div className="text-lg font-bold">顯示我的 QR Code</div>
                        <div className="text-sm text-blue-100">讓別人掃描轉帳給你</div>
                    </button>
                </div>
                <div className="text-center">
                    <button
                        onClick={onStartQRScanner}
                        className="w-full rounded-xl bg-green-600 px-6 py-4 text-white transition-colors hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-600/50"
                    >
                        <Camera className="mx-auto mb-2 h-8 w-8" />
                        <div className="text-lg font-bold">掃描 QR Code</div>
                        <div className="text-sm text-green-100">掃描轉帳或兌換點數</div>
                    </button>
                </div>
            </div>
            
            <div className="mt-4 text-center">
                <button
                    onClick={onOpenTransferModal}
                    className="inline-flex items-center rounded-xl border border-[#294565] bg-transparent px-4 py-2 text-sm text-[#92cbf4] transition-colors hover:bg-[#294565]/30"
                >
                    手動輸入轉帳
                </button>
            </div>
        </div>
    );
}