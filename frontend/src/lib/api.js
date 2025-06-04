// const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://specs-about-blogging-slovenia.trycloudflare.com';

// API 請求通用函數
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

// 取得股票價格摘要
export async function getPriceSummary() {
  return apiRequest('/api/price/summary');
}

// 取得五檔報價
export async function getPriceDepth() {
  return apiRequest('/api/price/depth');
}

// 取得最近成交記錄
export async function getRecentTrades(limit = 20) {
  return apiRequest(`/api/price/trades?limit=${limit}`);
}

// 取得歷史價格資料
export async function getHistoricalPrices(hours = 24) {
  return apiRequest(`/api/price/history?hours=${hours}`);
}

// 取得排行榜資料
export async function getLeaderboard() {
  return apiRequest('/api/leaderboard');
}

// 取得市場狀態
export async function getMarketStatus() {
  return apiRequest('/api/status');
}

// 取得交易時間列表
export async function getTradingHours() {
  return apiRequest('/api/trading-hours');
}

export async function adminLogin(password) {
  return apiRequest('/api/admin/login', {
    method: 'POST',
    body: JSON.stringify({ password }),
  });
}

export async function getUserAssets(token, searchUser = null) {
  const url = searchUser ? `/api/admin/user?user=${encodeURIComponent(searchUser)}` : '/api/admin/user';
  return apiRequest(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
}

export async function getSystemStats(token) {
  return apiRequest('/api/admin/stats', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
}

export async function givePoints(token, username, type, amount) {
  return apiRequest('/api/admin/users/give-points', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, type, amount }),
  });
}

export async function setTradingLimit(token, limitPercent) {
  return apiRequest('/api/admin/market/set-limit', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ limit_percent: limitPercent }),
  });
}

export async function updateMarketTimes(token, openTime) {
  return apiRequest('/api/admin/market/update', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ openTime }),
  });
}

export async function createAnnouncement(token, title, message, broadcast) {
  return apiRequest('/api/admin/announcement', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title, message, broadcast }),
  });
}

export async function getStudents(token) {
  return apiRequest('/api/admin/students', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
}

export async function getTeams(token) {
  return apiRequest('/api/admin/teams', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
}

export { API_BASE_URL };
