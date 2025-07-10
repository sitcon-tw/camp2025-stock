/**
 * 交易時間可視化設定
 * 顯示24小時交易時段的視覺化圖表
 */
const TradingHoursVisualizer = ({ tradingHours, marketTimesForm }) => {
    // 生成24小時的時間點
    const hours = Array.from({ length: 24 }, (_, i) => i);

    // 獲取交易時段資料，處理不同的資料結構
    const getTradingSessions = () => {
        // 優先使用表單資料（即時更新，用於系統設定頁面）
        if (
            marketTimesForm &&
            marketTimesForm.openTime &&
            Array.isArray(marketTimesForm.openTime)
        ) {
            // 過濾出有效的時間段（開始和結束時間都已填入）
            return marketTimesForm.openTime.filter(
                (session) => session.start && session.end,
            );
        }

        // 如果沒有表單資料，則使用已保存的資料
        if (!tradingHours) return [];

        // 檢查是否有 openTime 屬性
        if (
            tradingHours.openTime &&
            Array.isArray(tradingHours.openTime)
        ) {
            return tradingHours.openTime;
        }

        // 檢查是否有 tradingHours 屬性（時間戳格式）
        if (
            tradingHours.tradingHours &&
            Array.isArray(tradingHours.tradingHours)
        ) {
            return tradingHours.tradingHours.map((slot) => {
                const startDate = new Date(slot.start * 1000);
                const endDate = new Date(slot.end * 1000);
                return {
                    start: startDate.toTimeString().slice(0, 5),
                    end: endDate.toTimeString().slice(0, 5),
                };
            });
        }

        return [];
    };

    // 將時間字符串轉換為分鐘數（從0:00開始計算）
    const timeToMinutes = (timeStr) => {
        const [hours, minutes] = timeStr.split(':').map(Number);
        return hours * 60 + minutes;
    };

    // 生成交易時段的視覺化區塊
    const generateTradingSegments = () => {
        const sessions = getTradingSessions();
        if (sessions.length === 0) return [];

        const segments = [];
        
        sessions.forEach((session, index) => {
            if (!session.start || !session.end) return;

            const startMinutes = timeToMinutes(session.start);
            const endMinutes = timeToMinutes(session.end);

            // 處理跨日情況
            if (endMinutes < startMinutes) {
                // 分成兩段：從開始時間到24:00，從0:00到結束時間
                segments.push({
                    key: `${index}-part1`,
                    left: (startMinutes / (24 * 60)) * 100,
                    width: ((24 * 60 - startMinutes) / (24 * 60)) * 100,
                });
                segments.push({
                    key: `${index}-part2`,
                    left: 0,
                    width: (endMinutes / (24 * 60)) * 100,
                });
            } else {
                // 正常情況：同一天內的時間段
                segments.push({
                    key: `${index}`,
                    left: (startMinutes / (24 * 60)) * 100,
                    width: ((endMinutes - startMinutes) / (24 * 60)) * 100,
                });
            }
        });

        return segments;
    };

    // 檢查某個時間是否在交易時段內（保持原邏輯用於其他用途）
    const isMarketOpen = (hour) => {
        const sessions = getTradingSessions();
        if (sessions.length === 0) return false;

        return sessions.some((session) => {
            if (!session.start || !session.end) return false;
            
            const startHour = parseInt(session.start.split(":")[0]);
            const startMinute = parseInt(session.start.split(":")[1]);
            const endHour = parseInt(session.end.split(":")[0]);
            const endMinute = parseInt(session.end.split(":")[1]);

            if (isNaN(startHour) || isNaN(startMinute) || isNaN(endHour) || isNaN(endMinute)) {
                return false;
            }

            const startTime = startHour + startMinute / 60;
            const endTime = endHour + endMinute / 60;

            // 處理跨日情況
            if (endTime < startTime) {
                return hour >= startTime || hour < endTime;
            } else {
                return hour >= startTime && hour < endTime;
            }
        });
    };

    // 獲取現在時間的精確位置（分鐘級別）
    const getCurrentTimePosition = () => {
        const now = new Date();
        const currentMinutes = now.getHours() * 60 + now.getMinutes();
        return (currentMinutes / (24 * 60)) * 100;
    };

    const tradingSegments = generateTradingSegments();

    return (
        <div className="mb-4 rounded-lg border border-[#294565] bg-[#0f203e] p-4">
            {/* 時間軸 */}
            <div className="relative">
                {/* 小時標記 */}
                <div className="mb-2 flex justify-between text-xs text-[#557797]">
                    {[0, 6, 12, 18, 24].map((hour) => (
                        <span key={hour} className="w-8 text-center">
                            {hour.toString().padStart(2, "0")}:00
                        </span>
                    ))}
                </div>

                {/* 時間條 */}
                <div className="relative h-8 overflow-hidden rounded-lg bg-[#1A325F]">
                    {/* 背景網格線 */}
                    <div className="absolute inset-0 flex">
                        {hours.map((hour) => (
                            <div
                                key={hour}
                                className="flex-1 border-r border-[#294565] last:border-r-0"
                            />
                        ))}
                    </div>

                    {/* 交易時段標記 - 精確到分鐘 */}
                    {tradingSegments.map((segment) => (
                        <div
                            key={segment.key}
                            className="absolute top-0 h-full bg-green-500/80 shadow-lg transition-all duration-300"
                            style={{
                                left: `${segment.left}%`,
                                width: `${segment.width}%`,
                            }}
                        />
                    ))}

                    {/* 現在時間指示器 - 精確到分鐘 */}
                    <div
                        className="absolute top-0 h-full w-0.5 bg-yellow-400 shadow-lg"
                        style={{
                            left: `${getCurrentTimePosition()}%`,
                        }}
                    ></div>
                </div>

                {/* 圖例 */}
                <div className="mt-3 flex items-center justify-center space-x-4 text-xs">
                    <div className="flex items-center space-x-2">
                        <div className="h-3 w-3 rounded bg-green-500/80"></div>
                        <span className="text-[#7BC2E6]">
                            交易時段
                        </span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="h-3 w-3 rounded bg-[#1A325F]"></div>
                        <span className="text-[#7BC2E6]">
                            非交易時段
                        </span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="h-3 w-0.5 bg-yellow-400"></div>
                        <span className="text-[#7BC2E6]">
                            現在時間
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TradingHoursVisualizer;