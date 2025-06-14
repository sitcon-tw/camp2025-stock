import { useCallback, useRef } from "react";

export const useApiRequest = (minInterval = 5000) => {
    const fetchingRef = useRef(false);
    const lastFetchTimeRef = useRef(0);
    const abortControllerRef = useRef(null);

    const makeRequest = useCallback(
        async (apiFunction, ...args) => {
            const now = Date.now();

            // 檢查現在有沒有正在 request
            if (
                fetchingRef.current ||
                now - lastFetchTimeRef.current < minInterval
            ) {
                return null;
            }

            // 取消請求
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }

            // 新建 AbortController
            abortControllerRef.current = new AbortController();

            try {
                fetchingRef.current = true;
                lastFetchTimeRef.current = now;

                const result = await apiFunction(...args, {
                    signal: abortControllerRef.current.signal,
                });

                return result;
            } catch (error) {
                if (error.name === "AbortError") {
                    console.log("請求已取消");
                    return null;
                }
                throw error;
            } finally {
                fetchingRef.current = false;
                abortControllerRef.current = null;
            }
        },
        [minInterval],
    );

    // 清理函數
    const cleanup = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        fetchingRef.current = false;
    }, []);

    return { makeRequest, cleanup };
};

export const useMountedState = () => {
    const isMountedRef = useRef(true);

    const cleanup = useCallback(() => {
        isMountedRef.current = false;
    }, []);

    return { isMountedRef, cleanup };
};
