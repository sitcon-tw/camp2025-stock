export default function Home() {
  // 模擬數據 - 您可以根據實際需求替換
  const currentPrice = 70;
  const changePercent = 20; // 正數表示上漲，負數表示下跌
  const isPositive = changePercent > 0;
  const isNegative = changePercent < 0;

  return (
    <div className="bg-[#0f203e] min-h-screen items-center justify-center pb-36">
      <div className="flex flex-col h-screen px-8">
        <div id="header" className="flex justify-between items-center pt-10">
          <div>
            <h1 className="font-bold text-5xl text-[#82bee2] mx-auto mt-10 mb-5">
              SITC
            </h1>

            <h1 className="font-bold text-2xl text-[#82bee2] mx-auto mb-10">
              SITCON Camp 點
            </h1>
          </div>
          <div className="flex flex-col justify-center">
            <h1 className="text-[#82bee2] text-3xl font-bold">{currentPrice}</h1>
            <h1
              className={`mx-2 font-semibold ${
                isPositive
                  ? "text-red-500"
                  : isNegative
                  ? "text-green-500"
                  : "text-gray-500"
              }`}
            >
              {isPositive ? "▲" : isNegative ? "▼" : ""}
              {Math.abs(changePercent)}%
            </h1>
            <h1 className="text-[#82bee2]">開放交易</h1>
          </div>
        </div>
      </div>
    </div>
  );
}
