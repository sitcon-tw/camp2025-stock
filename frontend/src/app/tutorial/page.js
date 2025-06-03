import React from 'react'

export default function TutorialPage() {
  return (<div className="bg-[#0f203e] min-h-screen pb-24">
    <div className="container mx-auto px-8 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold text-center mb-8 text-[#82bee2]">🚀 SITC 交易平台教學</h1>

      <div className="bg-[#1a2e4a] p-4 rounded-lg mb-8">
        <p className="text-md text-white">歡迎使用 SITC 股票交易系統！這裡將教你如何使用平台進行股票買賣，讓你快速上手投資世界。</p>
      </div>

      <h2 className="text-2xl font-bold mb-4 text-[#82bee2]">快速入門</h2>
      <ul className="list-disc pl-6 mb-8 text-white">
        <li>註冊帳號並獲得初始資金</li>
        <li>學會看盤和下單</li>
        <li>掌握買低賣高的基本原則</li>
      </ul>

      <h2 className="text-2xl font-bold mb-4 text-[#82bee2]">🎯 平台功能介紹</h2>
      <div className="overflow-x-auto mb-8">
        <table className="w-full border-collapse border border-[#82bee2] bg-[#1a2e4a] overflow-hidden rounded-xl">
          <thead>
            <tr className="bg-[#19325e]">
              <th className="border border-[#82bee2] px-4 py-2 text-left text-[#82bee2]">功能</th>
              <th className="border border-[#82bee2] px-4 py-2 text-left text-[#82bee2]">描述</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="border border-[#82bee2] px-4 py-2 text-white">即時報價</td>
              <td className="border border-[#82bee2] px-4 py-2 text-white">查看股票即時價格和走勢圖表</td>
            </tr>
            <tr>
              <td className="border border-[#82bee2] px-4 py-2 text-white">下單交易</td>
              <td className="border border-[#82bee2] px-4 py-2 text-white">透過 Bot 指令進行買賣操作</td>
            </tr>
            <tr>
              <td className="border border-[#82bee2] px-4 py-2 text-white">投資組合</td>
              <td className="border border-[#82bee2] px-4 py-2 text-white">查看持股狀況和損益表現</td>
            </tr>
            <tr>
              <td className="border border-[#82bee2] px-4 py-2 text-white">交易紀錄</td>
              <td className="border border-[#82bee2] px-4 py-2 text-white">檢視歷史成交記錄</td>
            </tr>
            <tr>
              <td className="border border-[#82bee2] px-4 py-2 text-white">排行榜</td>
              <td className="border border-[#82bee2] px-4 py-2 text-white">查看個人和團隊投資績效排名</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h2 className="text-2xl font-bold mb-4 text-[#82bee2]">📊 如何開始交易</h2>
      <div className="bg-[#1a2e4a] p-4 rounded-lg mb-6">
        <p className="font-semibold text-[#82bee2]">所有交易操作都透過 Telegram Bot 完成</p>
      </div>

      <h3 className="text-xl font-semibold mb-3 text-[#82bee2]">📈 買入股票</h3>
      <div className="bg-[#1a2e4a] p-4 rounded-lg mb-4">
        <p className="font-semibold mb-2 text-[#82bee2]">市價買入：</p>
        <code className="bg-black text-green-400 px-2 py-1 rounded">/buy [數量]</code>
        <p className="mt-2 text-white">以當前市場價格立即買入</p>
      </div>

      <div className="bg-[#1a2e4a] p-4 rounded-lg mb-6">
        <p className="font-semibold mb-2 text-[#82bee2]">限價買入：</p>
        <code className="bg-black text-green-400 px-2 py-1 rounded">/bid [價格] [數量]</code>
        <p className="mt-2 text-white">設定價格等待成交</p>
      </div>

      <h3 className="text-xl font-semibold mb-3 text-[#82bee2]">📉 賣出股票</h3>
      <div className="bg-[#1a2e4a] p-4 rounded-lg mb-4">
        <p className="font-semibold mb-2 text-[#82bee2]">市價賣出：</p>
        <code className="bg-black text-green-400 px-2 py-1 rounded">/sell [數量]</code>
        <p className="mt-2 text-white">以當前市場價格立即賣出</p>
      </div>

      <div className="bg-[#1a2e4a] p-4 rounded-lg mb-8">
        <p className="font-semibold mb-2 text-[#82bee2]">限價賣出：</p>
        <code className="bg-black text-green-400 px-2 py-1 rounded">/ask [價格] [數量]</code>
        <p className="mt-2 text-white">設定價格等待買家</p>
      </div>

      <h2 className="text-2xl font-bold mb-4 text-[#82bee2]">🔧 其他功能</h2>

      <h3 className="text-xl font-semibold mb-3 text-[#82bee2]">取消訂單</h3>
      <div className="bg-[#1a2e4a] p-4 rounded-lg mb-6">
        <code className="bg-black text-green-400 px-2 py-1 rounded">/cancel</code>
        <p className="mt-2 text-white">取消未成交的掛單</p>
      </div>

      <h3 className="text-xl font-semibold mb-3 text-[#82bee2]">查詢資訊</h3>
      <div className="bg-[#1a2e4a] p-4 rounded-lg mb-8">
        <code className="bg-black text-green-400 px-2 py-1 rounded">/status</code>
        <p className="mt-2 text-white">查看帳戶餘額和持股</p>
      </div>

      <h2 className="text-2xl font-bold mb-4 text-[#82bee2]">💡 投資小技巧</h2>
      <div className="space-y-4 mb-8">
        <div className="bg-[#1a2e4a] p-4 rounded-lg">
          <h4 className="font-semibold text-[#82bee2] mb-2">觀察市場趨勢</h4>
          <p className="text-white">留意價格走勢和成交量變化</p>
        </div>
        <div className="bg-[#1a2e4a] p-4 rounded-lg">
          <h4 className="font-semibold text-[#82bee2] mb-2">分散風險</h4>
          <p className="text-white">不要把所有資金投入單一標的</p>
        </div>
        <div className="bg-[#1a2e4a] p-4 rounded-lg">
          <h4 className="font-semibold text-[#82bee2] mb-2">設定停損</h4>
          <p className="text-white">預先規劃虧損時的退場策略</p>
        </div>
      </div>

      <h2 className="text-2xl font-bold mb-4 text-[#82bee2]">❓ 常見問題</h2>
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-2 text-[#82bee2]">如何查看目前股價？</h3>
          <p className="text-white">可在首頁查看即時股價和技術指標。</p>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-2 text-[#82bee2]">交易時間是什麼時候？</h3>
          <p className="text-white">平台會在首頁顯示開放交易的時段。</p>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-2 text-[#82bee2]">如何提升排行榜名次？</h3>
          <p className="text-white">增加總資產價值，包含現金和股票市值。</p>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-2 text-[#82bee2]">訂單沒有成交怎麼辦？</h3>
          <p className="text-white">可以調整價格或改用市價單立即成交。</p>
        </div>
      </div>

      <div className="bg-[#1a2e4a] p-3 overflow-hidden rounded-xl mt-8">
        <blockquote className="text-lg italic text-center text-[#82bee2]">
          "投資成功的關鍵在於耐心和紀律" - 投資大師
        </blockquote>
      </div>
    </div>
  </div>
  )
}
