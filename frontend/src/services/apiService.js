"use client";

import {
    getHistoricalPrices,
    getLeaderboard,
    getMarketStatus,
    getPriceDepth,
    getPriceSummary,
    getRecentTrades,
    getTradingStats,
} from "@/lib/api";

class ApiService {
    constructor() {
        this.cache = new Map();
        this.pendingRequests = new Map();
        this.defaultCacheTime = 15000;
    }

    async request(
        key,
        apiFunction,
        cacheTime = this.defaultCacheTime,
    ) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < cacheTime) {
            return cached.data;
        }

        if (this.pendingRequests.has(key)) {
            return this.pendingRequests.get(key);
        }

        // 創新請求
        const promise = this._makeRequest(key, apiFunction);
        this.pendingRequests.set(key, promise);

        return promise;
    }

    async _makeRequest(key, apiFunction) {
        try {
            const data = await apiFunction();

            // 緩存結果
            this.cache.set(key, {
                data,
                timestamp: Date.now(),
            });

            return data;
        } catch (error) {
            throw error;
        } finally {
            this.pendingRequests.delete(key);
        }
    }

    // 清除緩存
    clearCache(key) {
        if (key) {
            this.cache.delete(key);
        } else {
            this.cache.clear();
        }
    }

    // 具體的API方法
    async getPriceData() {
        return this.request("price-summary", getPriceSummary, 10000);
    }

    async getMarketData() {
        return this.request("market-status", getMarketStatus, 15000);
    }

    async getOrderBookData() {
        return this.request("price-depth", getPriceDepth, 5000);
    }

    async getTradeHistory(limit = 20) {
        return this.request(
            `trades-${limit}`,
            () => getRecentTrades(limit),
            15000,
        );
    }

    async getHistoricalData(hours = 24) {
        return this.request(
            `historical-${hours}`,
            () => getHistoricalPrices(hours),
            30000,
        );
    }

    async getLeaderboardData() {
        return this.request("leaderboard", getLeaderboard, 15000);
    }

    async getTradingStatsData() {
        return this.request("trading-stats", getTradingStats, 10000);
    }
}

// 建立單例實例
export const apiService = new ApiService();
