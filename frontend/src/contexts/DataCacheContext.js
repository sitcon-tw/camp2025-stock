'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';

const DataCacheContext = createContext();

export const useDataCache = () => {
    const context = useContext(DataCacheContext);
    if (!context) {
        throw new Error('useDataCache must be used within DataCacheProvider');
    }
    return context;
};

export const DataCacheProvider = ({ children }) => {
    const [cache, setCache] = useState({});
    const [loadingStates, setLoadingStates] = useState({});

    const getCachedData = useCallback((key, maxAge = 30000) => {
        const cachedItem = cache[key];
        if (cachedItem) {
            const isExpired = Date.now() - cachedItem.timestamp > maxAge;
            if (!isExpired) {
                return cachedItem.data;
            }
        }
        return null;
    }, [cache]);

    const setCachedData = useCallback((key, data) => {
        setCache(prev => ({
            ...prev,
            [key]: {
                data,
                timestamp: Date.now()
            }
        }));
    }, []);

    const isLoading = useCallback((key) => {
        return loadingStates[key] || false;
    }, [loadingStates]);

    const setLoadingState = useCallback((key, isLoading) => {
        setLoadingStates(prev => ({
            ...prev,
            [key]: isLoading
        }));
    }, []);

    const fetchWithCache = useCallback(async (key, fetchFunction, maxAge = 30000) => {
        // 檢查 cache
        const cachedData = getCachedData(key, maxAge);

        if (cachedData) {
            return cachedData;
        }

        if (isLoading(key)) {
            return null;
        }

        try {
            const data = await fetchFunction();
            setLoadingState(key, true);
            setCachedData(key, data);
            return data;
        } finally {
            setLoadingState(key, false);
        }
    }, [getCachedData, setCachedData, isLoading, setLoadingState]);

    const value = {
        getCachedData,
        setCachedData,
        isLoading,
        fetchWithCache,
        clearCache: () => setCache({})
    };

    return (
        <DataCacheContext.Provider value={value}>
            {children}
        </DataCacheContext.Provider>
    );
};
