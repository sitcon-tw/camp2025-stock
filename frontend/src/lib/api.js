const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://camp.sitcon.party';

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
            // 如果是 401 錯誤，拋出特殊錯誤
            if (response.status === 401) {
                const error = new Error(`API 請求失敗: ${response.status} ${response.statusText}`);
                error.status = 401;
                throw error;
            }
            throw new Error(`API 請求失敗: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw error;
        }
        console.error(`API 請求錯誤 (${endpoint}):`, error);
        throw error;
    }
}

// 取得股票價格摘要
export async function getPriceSummary(options = {}) {
    return apiRequest('/api/price/summary', options);
}

// 取得五檔報價
export async function getPriceDepth(options = {}) {
    return apiRequest('/api/price/depth', options);
}

// 取得最近成交記錄
export async function getRecentTrades(limit = 20, options = {}) {
    return apiRequest(`/api/price/trades?limit=${limit}`, options);
}

// 取得歷史價格資料
export async function getHistoricalPrices(hours = 24, options = {}) {
    return apiRequest(`/api/price/history?hours=${hours}`, options);
}

// 取得排行榜資料
export async function getLeaderboard(options = {}) {
    return apiRequest('/api/leaderboard', options);
}

// 取得市場狀態
export async function getMarketStatus(options = {}) {
    return apiRequest('/api/status', options);
}

// 取得交易時間列表
export async function getTradingHours(options = {}) {
    return apiRequest('/api/trading-hours', options);
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

// 取得公告列表
export async function getAnnouncements(limit = 10, options = {}) {
    return apiRequest(`/api/announcements?limit=${limit}`, options);
}

// 取得交易統計
export async function getTradingStats(options = {}) {
    return apiRequest('/api/trading/stats', options);
}

// 重置所有資料 (Danger Zone)
export async function resetAllData(token) {
    return apiRequest('/api/admin/reset/alldata', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });
}

export { API_BASE_URL };
