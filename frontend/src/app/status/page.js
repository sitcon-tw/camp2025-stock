'use client';

import { useState, useEffect } from 'react';
import HeaderBar from "@/components/HeaderBar";
import StockChart from "@/components/StockChart";
import TradingTabs from "@/components/TradingTabs";
import { getPriceSummary } from "@/lib/api";

export default function Status() {
	const [stockData, setStockData] = useState({
		lastPrice: 70,
		change: 0,
		changePercent: 0,
		high: 75,
		low: 65,
		open: 70,
		volume: 0
	});
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	useEffect(() => {
		const fetchStockData = async () => {
			try {
				setLoading(true);
				const data = await getPriceSummary();
				setStockData(data);
				setError(null);
			} catch (err) {
				console.error('獲取股票資料失敗:', err);
				setError('無法獲取股票資料');
				// 保持默認值
			} finally {
				setLoading(false);
			}
		};

		fetchStockData();

		// 每30秒更新一次資料
		const interval = setInterval(fetchStockData, 30000);

		return () => clearInterval(interval);
	}, []);

	const currentPrice = stockData.lastPrice;
	const changePercent = parseFloat(stockData.changePercent) || 0;

	return (
		<div className="bg-[#0f203e] min-h-screen pb-28">
			<div className="flex flex-col px-8">
				<HeaderBar />

				{/* 錯誤狀態 */}
				{error && (
					<div className="mt-8 p-4 bg-red-900/30 border border-red-600 rounded-lg">
						<div className="text-red-400 text-sm">{error}</div>
					</div>
				)}

				{/* 股市趨勢圖 */}
				<div className="mt-3 mb-2 w-full">
					<StockChart
						currentPrice={currentPrice}
						changePercent={changePercent}
					/>
				</div>

				{/* 開盤價 今日最低 今日最高 */}
				<div>
					<div className="grid grid-cols-3 gap-4 text-center">
						<div className="bg-[#1A325F] px-4 py-2 rounded-lg">
							<h5 className="text-sm text-white">開盤價</h5>
							<p className="text-2xl font-bold">{Math.round(stockData.open)}</p>
						</div>
						<div className="bg-[#1A325F] px-4 py-2 rounded-lg">
							<h5 className="text-sm text-white">今日最低</h5>
							<p className="text-2xl font-bold">{Math.round(stockData.low)}</p>
						</div>
						<div className="bg-[#1A325F] px-4 py-2 rounded-lg">
							<h5 className="text-sm text-white">今日最高</h5>
							<p className="text-2xl font-bold">{Math.round(stockData.high)}</p>
						</div>
					</div>
				</div>

				{/* 五檔股價 和 交易紀錄 的 TAB */}
				<div className="mt-6">
					<TradingTabs currentPrice={currentPrice} />
				</div>
			</div>
		</div>
	);
}
