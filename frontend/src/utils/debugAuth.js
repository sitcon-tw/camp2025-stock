/**
 * 認證調試工具
 * 幫助診斷登入和權限問題
 */

/**
 * 解析 JWT Token 內容（不驗證簽名）
 * @param {string} token - JWT Token
 * @returns {Object|null} - 解析後的 payload
 */
export const decodeJWT = (token) => {
    try {
        if (!token) return null;
        
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        
        const payload = parts[1];
        const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
        return JSON.parse(decoded);
    } catch (error) {
        console.error('Failed to decode JWT:', error);
        return null;
    }
};

/**
 * 檢查當前認證狀態
 * @returns {Object} - 認證狀態資訊
 */
export const checkAuthStatus = () => {
    const adminToken = localStorage.getItem("adminToken");
    const userToken = localStorage.getItem("userToken");
    const isAdmin = localStorage.getItem("isAdmin");
    const isUser = localStorage.getItem("isUser");
    
    const adminPayload = decodeJWT(adminToken);
    const userPayload = decodeJWT(userToken);
    
    return {
        localStorage: {
            adminToken: adminToken ? `${adminToken.substring(0, 20)}...` : null,
            userToken: userToken ? `${userToken.substring(0, 20)}...` : null,
            isAdmin,
            isUser,
        },
        tokenPayloads: {
            admin: adminPayload,
            user: userPayload,
        },
        tokenExpiry: {
            admin: adminPayload?.exp ? new Date(adminPayload.exp * 1000) : null,
            user: userPayload?.exp ? new Date(userPayload.exp * 1000) : null,
        },
        isExpired: {
            admin: adminPayload?.exp ? Date.now() > adminPayload.exp * 1000 : false,
            user: userPayload?.exp ? Date.now() > userPayload.exp * 1000 : false,
        }
    };
};

/**
 * 清理所有認證資料
 */
export const clearAllAuth = () => {
    localStorage.removeItem("adminToken");
    localStorage.removeItem("userToken");
    localStorage.removeItem("isAdmin");
    localStorage.removeItem("isUser");
    localStorage.removeItem("adminCode");
    console.log("All authentication data cleared");
};

/**
 * 在控制台顯示認證狀態
 */
export const debugAuth = () => {
    const status = checkAuthStatus();
    
    console.group("🔍 Authentication Debug Info");
    console.log("📱 LocalStorage:", status.localStorage);
    console.log("🎫 Token Payloads:", status.tokenPayloads);
    console.log("⏰ Token Expiry:", status.tokenExpiry);
    console.log("❌ Is Expired:", status.isExpired);
    console.groupEnd();
    
    return status;
};

// 在開發環境中將 debugAuth 添加到 window 對象
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    window.debugAuth = debugAuth;
    window.clearAllAuth = clearAllAuth;
    console.log("🛠️  Debug tools available: debugAuth(), clearAllAuth()");
}

export default {
    decodeJWT,
    checkAuthStatus,
    clearAllAuth,
    debugAuth,
};