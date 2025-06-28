"use client";

import { useEffect, useRef } from "react";

const KLineChart = ({
    data,
    width = 1000,
    height = 400,
}) => {
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        let mounted = true;

        const initChart = async () => {
            if (!mounted || !chartRef.current || !data || data.length === 0) return;

            try {
                const { init, dispose } = await import('klinecharts');
                
                if (chartInstance.current) {
                    dispose(chartRef.current);
                    chartInstance.current = null;
                }

                const chart = init(chartRef.current);
                chartInstance.current = chart;

                chart.setSymbol({ ticker: 'TestSymbol' });
                chart.setPeriod({ span: 1, type: 'minute' });

                const klineData = data.map(item => ({
                    timestamp: item.timestamp,
                    open: parseFloat(item.open) || 0,
                    high: parseFloat(item.high) || 0,
                    low: parseFloat(item.low) || 0,
                    close: parseFloat(item.close) || 0,
                    volume: parseFloat(item.volume) || 0
                }));

                chart.setDataLoader({
                    getBars: ({ callback }) => {
                        callback(klineData);
                    }
                });

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
                            showRule: 'follow_cross',
                            showType: 'rect',
                            rect: {
                                position: isMobile ? 'fixed' : 'pointer',
                                paddingLeft: 6,
                                paddingRight: 6,
                                paddingTop: 6,
                                paddingBottom: 6,
                                offsetLeft: 4,
                                offsetTop: isMobile ? 20 : 4,
                                offsetRight: 4,
                                offsetBottom: isMobile ? 20 : 4,
                                borderRadius: 6,
                                borderSize: 1,
                                borderColor: '#CCCCCC',
                                backgroundColor: '#FFFFFF'
                            },
                            title: {
                                show: false
                            },
                            legend: {
                                size: isMobile ? 11 : 13,
                                family: 'Helvetica Neue',
                                weight: 'normal',
                                color: '#000000',
                                marginLeft: 6,
                                marginTop: 4,
                                marginRight: 6,
                                marginBottom: 4,
                                defaultValue: 'n/a',
                                template: [
                                    { title: { text: '時間', color: '#666666' }, value: { text: '{time}', color: '#000000' } },
                                    { title: { text: '開', color: '#666666' }, value: { text: '{open}', color: '#000000' } },
                                    { title: { text: '高', color: '#666666' }, value: { text: '{high}', color: '#000000' } },
                                    { title: { text: '低', color: '#666666' }, value: { text: '{low}', color: '#000000' } },
                                    { title: { text: '收', color: '#666666' }, value: { text: '{close}', color: '#000000' } }
                                ]
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
                            size: isMobile ? 8 : 10,
                            family: 'Helvetica Neue',
                            weight: 'normal',
                            marginStart: 2,
                            marginEnd: 2
                        },
                        tickLine: {
                            show: true,
                            size: 1,
                            length: 2,
                            color: '#82bee2'
                        }
                    },
                    yAxis: {
                        show: true,
                        width: isMobile ? 40 : null,
                        position: 'right',
                        type: 'normal',
                        inside: false,
                        reverse: false,
                        axisLine: {
                            show: true,
                            color: '#82bee2',
                            size: 1
                        },
                        tickText: {
                            show: true,
                            color: '#82bee2',
                            size: isMobile ? 8 : 10,
                            family: 'Helvetica Neue',
                            weight: 'normal',
                            marginStart: 2,
                            marginEnd: 2
                        },
                        tickLine: {
                            show: true,
                            size: 1,
                            length: 2,
                            color: '#82bee2'
                        }
                    },
                    separator: {
                        size: 1,
                        color: '#82bee2',
                        fill: true,
                        activeBackgroundColor: 'rgba(130, 190, 226, 0.08)'
                    },
                    crosshair: {
                        show: true,
                        horizontal: {
                            show: true,
                            line: {
                                show: true,
                                style: 'dash',
                                dashValue: [4, 2],
                                size: 1,
                                color: '#82bee2'
                            },
                            text: {
                                show: true,
                                color: '#000000',
                                size: isMobile ? 8 : 10,
                                family: 'Helvetica Neue',
                                weight: 'normal',
                                paddingLeft: 4,
                                paddingRight: 4,
                                paddingTop: 3,
                                paddingBottom: 3,
                                borderSize: 1,
                                borderColor: '#CCCCCC',
                                borderRadius: 3,
                                backgroundColor: '#FFFFFF'
                            }
                        },
                        vertical: {
                            show: true,
                            line: {
                                show: true,
                                style: 'dash',
                                dashValue: [4, 2],
                                size: 1,
                                color: '#82bee2'
                            },
                            text: {
                                show: true,
                                color: '#000000',
                                size: isMobile ? 8 : 10,
                                family: 'Helvetica Neue',
                                weight: 'normal',
                                paddingLeft: 4,
                                paddingRight: 4,
                                paddingTop: 3,
                                paddingBottom: 3,
                                borderSize: 1,
                                borderColor: '#CCCCCC',
                                borderRadius: 3,
                                backgroundColor: '#FFFFFF'
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
            if (chartInstance.current && chartRef.current) {
                try {
                    const { dispose } = require('klinecharts');
                    dispose(chartRef.current);
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
        <div className="flex h-full w-full items-center justify-center overflow-hidden rounded-lg bg-[#0f203e]">
            <div
                ref={chartRef}
                style={{ width: '100%', height: height }}
                className="kline-chart"
            />
        </div>
    );
};

export default KLineChart;