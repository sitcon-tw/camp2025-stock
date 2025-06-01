export const generateCandlestickData = (days = 60, basePrice = 20.0) => {
  const data = [];
  let currentPrice = basePrice * 0.9; // 從較低價格開始
  
  for (let i = 0; i < days; i++) {
    const date = new Date();
    date.setDate(date.getDate() - (days - i));
    
    // 產生開盤價
    const open = currentPrice;
    
    // 產生隨機波動 (-5% 到 +5%)
    const volatility = (Math.random() - 0.5) * 0.1;
    const trend = i < days * 0.3 ? -0.002 : i < days * 0.7 ? 0.003 : 0.001; // 前期下跌，中期上漲，後期穩定
    
    // 計算收盤價
    const close = open * (1 + volatility + trend);
    
    // 產生最高價和最低價
    const range = Math.abs(close - open) * (1 + Math.random());
    const high = Math.max(open, close) + range * Math.random();
    const low = Math.min(open, close) - range * Math.random();
    
    // 產生成交量 (隨機)
    const volume = Math.floor(Math.random() * 1000000) + 500000;
    
    data.push({
      date,
      open: Math.max(open, 15), // 確保價格不會太低
      high: Math.max(high, 15),
      low: Math.max(low, 10),
      close: Math.max(close, 15),
      volume
    });
    
    currentPrice = close;
  }
  
  // 確保最後一天的收盤價接近目標價格
  const lastDay = data[data.length - 1];
  const adjustment = basePrice / lastDay.close;
  
  // 調整所有資料
  return data.map(d => ({
    ...d,
    open: d.open * adjustment,
    high: d.high * adjustment,
    low: d.low * adjustment,
    close: d.close * adjustment
  }));
};
