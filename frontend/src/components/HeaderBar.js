import React, { useState, useEffect } from 'react'

export default function HeaderBar() {
  const [priceData, setPriceData] = useState({
    currentPrice: 20.0,
    changePercent: 0,
    loading: true
  });

  // 獲取價格摘要資料
  const fetchPriceData = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/price/summary`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // 解析 changePercent 字串（移除 % 符號並轉換為數字）
      const changePercentNum = parseFloat(data.changePercent?.replace('%', '') || '0');
      
      setPriceData({
        currentPrice: data.lastPrice || 20.0,
        changePercent: changePercentNum,
        loading: false
      });
    } catch (error) {
      console.error('獲取價格資料失敗:', error);
      // API 失敗時使用預設值
      setPriceData({
        currentPrice: 20.0,
        changePercent: 0,
        loading: false
      });
    }
  };

  // 初始載入和定期更新
  useEffect(() => {
    fetchPriceData();
    
    // 每 30 秒更新一次
    const interval = setInterval(fetchPriceData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const { currentPrice, changePercent, loading } = priceData;
  const isPositive = changePercent > 0;
  const isNegative = changePercent < 0;

  return (
    <div id="header" className="flex justify-between items-center pt-10">
          <div>
            <h1 className="font-bold text-5xl text-[#82bee2] mx-auto mb-5">
              SITC
            </h1>

            <h1 className="font-bold text-2xl text-[#82bee2] mx-auto mb-10">
              SITCON Camp 點
            </h1>
          </div>
          <div className="flex flex-col justify-center items-end">
            {loading ? (
              <div className="animate-pulse">
                <div className="h-8 w-16 bg-[#82bee2]/20 rounded mb-2"></div>
                <div className="h-6 w-12 bg-[#82bee2]/20 rounded mb-2"></div>
              </div>
            ) : (
              <>
                <h1 className="text-[#82bee2] text-3xl font-bold">
                  ${currentPrice.toFixed(2)}
                </h1>
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
                  {Math.abs(changePercent).toFixed(1)}%
                </h1>
              </>
            )}
            <h1 className="text-[#82bee2] text-sm">開放交易</h1>
          </div>
        </div>
  )
}
