// API 配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 通用 API 請求函數
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const config = { ...defaultOptions, ...options };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`API 請求失敗: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API 請求錯誤 (${endpoint}):`, error);
    throw error;
  }
}

// 獲取股票價格摘要
export async function getPriceSummary() {
  return apiRequest('/api/price/summary');
}

// 獲取五檔報價
export async function getPriceDepth() {
  return apiRequest('/api/price/depth');
}

// 獲取最近成交記錄
export async function getRecentTrades(limit = 20) {
  return apiRequest(`/api/price/trades?limit=${limit}`);
}

// 獲取歷史價格資料（基於交易記錄）
export async function getHistoricalPrices(hours = 24) {
  return apiRequest(`/api/price/history?hours=${hours}`);
}

// 獲取排行榜
export async function getLeaderboard() {
  return apiRequest('/api/leaderboard');
}

// 獲取市場狀態
export async function getMarketStatus() {
  return apiRequest('/api/status');
}

// 導出 API 基礎 URL 供其他組件使用
export { API_BASE_URL };
