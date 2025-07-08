const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
// const API_BASE_URL = 'https://camp.sitcon.party';

// API 請求通用函數
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const defaultOptions = {
        headers: {
            "Content-Type": "application/json",
        },
    };

    const config = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            let errorMessage = `API 請求失敗: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                } else if (errorData.message) {
                    errorMessage = errorData.message;
                }
            } catch (parseError) {
                // 如果無法解析 JSON，使用預設錯誤訊息
                if (response.status === 422) {
                    errorMessage = "請求資料格式錯誤或缺少必要資訊";
                }
            }

            const error = new Error(errorMessage);
            error.status = response.status;
            throw error;
        }

        return await response.json();
    } catch (error) {
        if (error.name === "AbortError") {
            throw error;
        }
        console.error(`API 請求錯誤 (${endpoint}):`, error);
        throw error;
    }
}

// 取得股票價格摘要
export async function getPriceSummary(options = {}) {
    return apiRequest("/api/price/summary", options);
}

// 取得五檔報價
export async function getPriceDepth(options = {}) {
    return apiRequest("/api/price/depth", options);
}

// 取得最近成交記錄
export async function getRecentTrades(limit = 20, options = {}) {
    return apiRequest(`/api/price/trades?limit=${limit}`, options);
}

// 取得所有交易紀錄 (需要權限)
export async function getTrades(token, limit = 1000, options = {}) {
    return apiRequest(`/api/admin/trades?limit=${limit}`, {
        ...options,
        headers: {
            ...options.headers,
            Authorization: `Bearer ${token}`,
        },
    });
}

// 取得所有點數紀錄 (需要權限)
export async function getPointHistory(token, limit = 1000, options = {}) {
    return apiRequest(`/api/admin/points/history?limit=${limit}`, {
        ...options,
        headers: {
            ...options.headers,
            Authorization: `Bearer ${token}`,
        },
    });
}

// 取得歷史價格資料
export async function getHistoricalPrices(hours = 24, options = {}) {
    return apiRequest(`/api/price/history?hours=${hours}`, options);
}

// 取得排行榜資料
export async function getLeaderboard(options = {}) {
    return apiRequest("/api/leaderboard", options);
}

// 取得市場狀態
export async function getMarketStatus(options = {}) {
    return apiRequest("/api/status", options);
}

// 取得交易時間列表
export async function getTradingHours(options = {}) {
    return apiRequest("/api/trading-hours", options);
}

export async function adminLogin(password) {
    return apiRequest("/api/admin/login", {
        method: "POST",
        body: JSON.stringify({ password }),
    });
}

export async function getUserAssets(token, searchUser = null) {
    const url = searchUser
        ? `/api/admin/user?user=${encodeURIComponent(searchUser)}`
        : "/api/admin/user";
    return apiRequest(url, {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

export async function getSystemStats(token) {
    return apiRequest("/api/admin/stats", {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

export async function getAllStudents(token) {
    return apiRequest("/api/admin/students", {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 取得所有隊伍的基本資料，包括隊伍名稱、成員數量等
export async function getTeams(token) {
    return apiRequest("/api/admin/teams", {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

export async function givePoints(token, username, type, amount) {
    return apiRequest("/api/admin/users/give-points", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, type, amount }),
    });
}

export async function setTradingLimit(token, limitPercent) {
    return apiRequest("/api/admin/market/set-limit", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ limit_percent: limitPercent }),
    });
}

export async function updateMarketTimes(token, openTime) {
    return apiRequest("/api/admin/market/update", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ openTime }),
    });
}

export async function createAnnouncement(
    token,
    title,
    message,
    broadcast,
) {
    return apiRequest("/api/admin/announcement", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ title, message, broadcast }),
    });
}

export async function getStudents(token) {
    return apiRequest("/api/admin/students", {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 取得公告列表
export async function getAnnouncements(limit = 10, options = {}) {
    return apiRequest(`/api/announcements?limit=${limit}`, options);
}

// 取得公告列表 (管理員版本)
export async function getAnnouncementsAdmin(token, limit = 50) {
    return apiRequest(`/api/admin/announcements?limit=${limit}`, {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 刪除公告 (軟刪除)
export async function deleteAnnouncement(token, announcementId) {
    return apiRequest(`/api/admin/announcement/${announcementId}`, {
        method: "DELETE",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 取得交易統計
export async function getTradingStats(options = {}) {
    return apiRequest("/api/trading/stats", options);
}

// 重置所有資料 (Danger Zone)
export async function resetAllData(token) {
    return apiRequest("/api/admin/reset/alldata", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 重置所有資料但保留使用者 (Danger Zone)
export async function resetAllDataExceptUsers(token) {
    return apiRequest("/api/admin/reset/except-users", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 強制結算 (Force Settlement)
export async function forceSettlement(token) {
    return apiRequest("/api/admin/final-settlement", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// IPO 管理功能
// 查詢IPO狀態
export async function getIpoStatus(token) {
    return apiRequest("/api/admin/ipo/status", {
        method: "GET",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 重置IPO狀態
export async function resetIpo(
    token,
    initialShares = null,
    initialPrice = null,
) {
    // 如果沒有提供參數，後端會使用資料庫中的預設設定
    const params = new URLSearchParams();
    if (initialShares !== null) params.append("initial_shares", initialShares);
    if (initialPrice !== null) params.append("initial_price", initialPrice);
    
    const queryString = params.toString();
    const url = queryString ? `/api/admin/ipo/reset?${queryString}` : "/api/admin/ipo/reset";
    
    return apiRequest(url, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 更新IPO參數
export async function updateIpo(
    token,
    sharesRemaining = null,
    initialPrice = null,
) {
    const params = new URLSearchParams();
    if (sharesRemaining !== null)
        params.append("shares_remaining", sharesRemaining);
    if (initialPrice !== null)
        params.append("initial_price", initialPrice);

    return apiRequest(`/api/admin/ipo/update?${params.toString()}`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}


// IPO 預設設定管理
// 查詢IPO預設設定
export async function getIpoDefaults(token) {
    return apiRequest("/api/admin/ipo/defaults", {
        method: "GET",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 更新IPO預設設定
export async function updateIpoDefaults(
    token,
    defaultInitialShares = null,
    defaultInitialPrice = null,
) {
    const params = new URLSearchParams();
    if (defaultInitialShares !== null)
        params.append("default_initial_shares", defaultInitialShares);
    if (defaultInitialPrice !== null)
        params.append("default_initial_price", defaultInitialPrice);

    return apiRequest(
        `/api/admin/ipo/defaults?${params.toString()}`,
        {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        },
    );
}


// 轉點數手續費設定
// 查詢手續費設定
export async function getTransferFeeConfig(token) {
    return apiRequest("/api/admin/transfer/fee-config", {
        method: "GET",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 更新手續費設定
export async function updateTransferFeeConfig(
    token,
    feeRate,
    minFee,
) {
    const params = new URLSearchParams();
    if (feeRate !== null && feeRate !== undefined) {
        params.append("fee_rate", feeRate);
    }
    if (minFee !== null && minFee !== undefined) {
        params.append("min_fee", minFee);
    }

    return apiRequest(
        `/api/admin/transfer/fee-config?${params.toString()}`,
        {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        },
    );
}

// 查詢市場價格資訊 (公開API)
export async function getMarketPriceInfo() {
    return apiRequest("/api/market/price-info", {
        method: "GET",
    });
}

// ========== Telegram OAuth 認證 ==========

// Telegram OAuth 登入
export async function telegramOAuth(authData) {
    return apiRequest("/api/auth/telegram", {
        method: "POST",
        body: JSON.stringify(authData),
    });
}

// ========== Web API 功能 (需要 JWT Token) ==========

// 查詢投資組合
export async function getWebPortfolio(token) {
    return apiRequest("/api/web/portfolio", {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 查詢點數記錄
export async function getWebPointHistory(token, limit = 50) {
    return apiRequest(`/api/web/points/history?limit=${limit}`, {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 下股票訂單
export async function placeWebStockOrder(token, orderData) {
    return apiRequest("/api/web/stock/order", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(orderData),
    });
}

// 查詢股票訂單記錄
export async function getWebStockOrders(token, limit = 50) {
    return apiRequest(`/api/web/stock/orders?limit=${limit}`, {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 取消股票訂單
export async function cancelWebStockOrder(token, orderId, reason = "user_cancelled") {
    return apiRequest(`/api/web/stock/orders/${orderId}?reason=${encodeURIComponent(reason)}`, {
        method: "DELETE",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 點數轉帳
export async function webTransferPoints(token, transferData) {
    return apiRequest("/api/web/transfer", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(transferData),
    });
}

// 查詢使用者資料
export async function getWebUserProfile(token) {
    return apiRequest("/api/web/profile", {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 查詢所有等待撮合的訂單
export async function getPendingOrders(token, limit = 100) {
    return apiRequest(`/api/admin/pending-orders?limit=${limit}`, {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 手動觸發訂單撮合
export async function triggerManualMatching(token) {
    return apiRequest("/api/admin/trigger-matching", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 查詢價格限制資訊
export async function getPriceLimitInfo(token, testPrice = 14.0) {
    return apiRequest(`/api/admin/price-limit-info?test_price=${testPrice}`, {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

// 動態價格級距功能已移除，改為固定漲跌限制

// ========== RBAC 權限管理 API ==========

// 取得目前使用者的權限資訊
export async function getMyPermissions(token) {
    return apiRequest("/api/rbac/my-permissions", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

// 檢查 Telegram 使用者是否為管理員
export async function checkTelegramAdminStatus(token) {
    return apiRequest("/api/rbac/my-permissions", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

// 取得使用者角色資訊
export async function getUserRole(token, userId) {
    return apiRequest(`/api/rbac/users/role/${userId}`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

// 檢查特定權限
export async function checkPermission(token, userId, permission) {
    return apiRequest("/api/rbac/check-permission", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_id: userId, permission }),
    });
}

// 取得可用角色列表
export async function getAvailableRoles(token) {
    return apiRequest("/api/rbac/roles", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

// 更新使用者角色
export async function updateUserRole(token, userId, newRole, reason = "") {
    return apiRequest("/api/rbac/users/role", {
        method: "PUT",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            user_id: userId,
            new_role: newRole,
            reason: reason,
        }),
    });
}

// 取得所有使用者權限摘要
export async function getUserPermissionSummaries(token, role = null) {
    const url = role ? `/api/rbac/users?role=${role}` : "/api/rbac/users";
    return apiRequest(url, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
}

// 查詢轉帳手續費設定 (公開API)
export async function getTransferFeeConfigPublic() {
    return apiRequest("/api/transfer/fee-config", {
        method: "GET",
    });
}

// 取得使用者大頭照
export async function getUserAvatar(token, username) {
    return apiRequest(`/api/web/users/${encodeURIComponent(username)}/avatar`, {
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });
}

export { API_BASE_URL };
