"use client";

import { useEffect, useRef } from "react";

const KLineChart = ({
    data,
    height = 500,
}) => {
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        let mounted = true;

        const initChart = async () => {
            if (!mounted || !chartRef.current || !data || data.length === 0) return;

            try {
                const { init } = await import('klinecharts');

                if (chartInstance.current) {
                    try {
                        if (typeof chartInstance.current.dispose === 'function') {
                            chartInstance.current.dispose();
                        } else if (typeof chartInstance.current.destroy === 'function') {
                            chartInstance.current.destroy();
                        }
                    } catch (e) {
                        console.warn('Error disposing previous chart:', e);
                    }
                    chartInstance.current = null;
                }

                chartRef.current.innerHTML = '';

                const chart = init(chartRef.current);
                chartInstance.current = chart;

                const klineData = data.map(item => {
                    // Convert timestamp to UTC+8 timezone
                    const utcDate = new Date(item.timestamp);
                    const utc8Date = new Date(utcDate.getTime() + (8 * 60 * 60 * 1000));
                    return {
                        timestamp: utc8Date.getTime(),
                        open: parseFloat(item.open) || 0,
                        high: parseFloat(item.high) || 0,
                        low: parseFloat(item.low) || 0,
                        close: parseFloat(item.close) || 0,
                        volume: parseFloat(item.volume) || 0
                    };
                });

                chart.applyNewData(klineData);

                const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

                chart.setStyles({
                    grid: {
                        show: true,
                        horizontal: {
                            show: true,
                            size: 1,
                            color: 'rgba(130, 190, 226, 0.1)',
                            style: 'solid'
                        },
                        vertical: {
                            show: false
                        }
                    },
                    candle: {
                        type: 'candle_solid',
                        bar: {
                            upColor: '#22c55e',
                            downColor: '#ef4444',
                            noChangeColor: '#22c55e'
                        },
                        tooltip: {
                            showRule: 'always',
                            showType: 'standard',
                            title: {
                                show: true,
                                template: '{ticker} · {period}'
                            }
                        }
                    },
                    xAxis: {
                        show: true,
                        height: isMobile ? 25 : null,
                        axisLine: {
                            show: true,
                            color: '#82bee2',
                            size: 1
                        },
                        tickText: {
                            show: true,
                            color: '#82bee2',
                            size: isMobile ? 8 : 10
                        }
                    },
                    yAxis: {
                        show: true,
                        width: isMobile ? 40 : null,
                        position: 'right',
                        axisLine: {
                            show: true,
                            color: '#82bee2',
                            size: 1
                        },
                        tickText: {
                            show: true,
                            color: '#82bee2',
                            size: isMobile ? 8 : 10
                        }
                    },
                    crosshair: {
                        show: true,
                        horizontal: {
                            show: true,
                            line: {
                                show: true,
                                style: 'dash',
                                size: 1,
                                color: '#82bee2'
                            }
                        },
                        vertical: {
                            show: true,
                            line: {
                                show: true,
                                style: 'dash',
                                size: 1,
                                color: '#82bee2'
                            }
                        }
                    }
                });

                chart.resize();

            } catch (error) {
                console.error('KLineChart initialization error:', error);
            }
        };

        initChart();

        return () => {
            mounted = false;
            if (chartInstance.current) {
                try {
                    if (typeof chartInstance.current.dispose === 'function') {
                        chartInstance.current.dispose();
                    } else if (typeof chartInstance.current.destroy === 'function') {
                        chartInstance.current.destroy();
                    }
                } catch (error) {
                    console.error('Error disposing chart:', error);
                }
                chartInstance.current = null;
            }
        };
    }, [data]);

    useEffect(() => {
        const handleResize = () => {
            if (chartInstance.current) {
                chartInstance.current.resize();
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    if (!data || data.length === 0) {
        return (
            <div
                className="flex items-center justify-center rounded-lg bg-[#0f203e]"
                style={{ height: height }}
            >
                <div className="text-sm text-[#82bee2]">
                    無資料可顯示
                </div>
            </div>
        );
    }

    return (
        <div className="h-full w-full overflow-hidden rounded-lg bg-[#0f203e]">
            <div
                ref={chartRef}
                style={{ width: '100%', height: height }}
                className="kline-chart"
            />
        </div>
    );
};

export default KLineChart;