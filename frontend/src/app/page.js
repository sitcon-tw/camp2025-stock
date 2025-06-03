'use client';

export default function Home() {
    return (
        <div className="min-h-screen bg-[#101f3e] overflow-hidden">
            <div className="flex flex-col items-center h-screen">
                <h1 className="text-4xl font-bold text-[#7BC2E6] mt-14 text-center">SITCON Camp<br />點數系統</h1>

                {/* 公告區塊 */}
                <div className="bg-[#1A325F] p-6 rounded-xl mt-10 w-[90%]">
                    <h2 className="text-2xl font-semibold text-[#AFE1F5] mb-3 text-center">公告</h2>
                    <p className="text-[#AFE1F5] text-md">
                        別墅裡面唱k，水池裡面銀龍魚。我送阿叔茶具，他研墨下筆直接給我四個字，大展鴻圖。
                    </p>
                </div>

                {/* 關閉交易時間表 */}
                <div className="bg-[#1A325F] p-6 rounded-xl mt-10 w-[90%]">
                    <h3 className="text-2xl font-semibold text-[#AFE1F5] mb-4 text-center">關閉交易時間</h3>
                    <div className="space-y-1 text-[#AFE1F5] text-lg font-bold">
                        <p>2025/6/3 9:00~11:00</p>
                        <p>2025/6/3 9:00~11:00</p>
                        <p>2025/6/4 12:00~15:00</p>
                    </div>
                </div>
            </div>
        </div>
    );
}