'use client';

import { useState, useEffect } from 'react';
import HeaderBar from "@/components/HeaderBar";
import StockChart from "@/components/StockChart";
import TradingTabs from "@/components/TradingTabs";
import { apiService } from "@/services/apiService";

export default function Status() {
	const [stockData, setStockData] = useState({
		lastPrice: 0,
		change: 0,
		changePercent: 0,
		high: 0,
		low: 0,
		open: 0,
		volume: 0
	});

	const [error, setError] = useState(null);

	const fetchData = async () => {
		try {
			const data = await apiService.getPriceData();
			setStockData(data);
			setError(null);
		} catch (err) {
			console.error('獲取股票資料失敗:', err);
			setError('無法獲取股票資料');
		}
	};
	useEffect(() => {
		let isMounted = true;

		const fetchInitialData = async () => {
			if (isMounted) {
				await fetchData();
			}
		};

		fetchInitialData();

		return () => {
			isMounted = false;
		};
	}, []);

	const currentPrice = stockData.lastPrice;
	const changePercent = parseFloat(stockData.changePercent) || 0;

	return (<div className="bg-[#0f203e] min-h-screen pb-28">
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
			<div className="mt-3">
				<TradingTabs currentPrice={currentPrice} />
			</div>
		</div>
	</div>
	);
}
