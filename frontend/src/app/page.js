import HeaderBar from "@/components/HeaderBar";
import StockChart from "@/components/StockChart";
import TradingTabs from "@/components/TradingTabs";

export default function Home() {

  const currentPrice = 70;
  const changePercent = 20; // 正數表示上漲，負數表示下跌
  const isPositive = changePercent > 0;
  const isNegative = changePercent < 0;

  return (
    <div className="bg-[#0f203e] min-h-screen items-center justify-center pb-36">
      <div className="flex flex-col h-screen px-8 mb-10">
        <HeaderBar
          currentPrice={currentPrice}
          changePercent={changePercent}
          isPositive={isPositive}
          Negative={isNegative}
        />
        {/* 股市趨勢圖 */}
        <div className="mt-8">
          <StockChart 
            currentPrice={currentPrice}
            changePercent={changePercent}
          />
        </div>
        {/* 開盤價 今日最低 今日最高 */}
        <div className="mt-4">
          <h4 className="text-[#82bee2] text-lg font-semibold mb-2">今日股市資訊</h4>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-[#1a2e4a] p-4 rounded-lg">
              <h5 className="text-sm text-[#82bee2]">開盤價</h5>
              <p className="text-xl font-bold">${currentPrice}</p>
            </div>
            <div className="bg-[#1a2e4a] p-4 rounded-lg">
              <h5 className="text-sm text-[#82bee2]">今日最低</h5>
              <p className="text-xl font-bold">${currentPrice - 5}</p>
            </div>
            <div className="bg-[#1a2e4a] p-4 rounded-lg">
              <h5 className="text-sm text-[#82bee2]">今日最高</h5>
              <p className="text-xl font-bold">${currentPrice + 5}</p>
            </div>
          </div>
        </div>        
        {/* 五檔股價 和 交易紀錄 的 TAB */}
        <div className="mt-6">
          <TradingTabs currentPrice={currentPrice} />
        </div></div>
    </div>
  );
}
