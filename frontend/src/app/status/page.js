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

	const [tradingStats, setTradingStats] = useState({
		total_trades: 0,
		total_volume: 0,
		total_amount: 0
	});


	const [error, setError] = useState(null);

	const fetchData = async () => {
		try {
			const [priceData, statsData] = await Promise.all([
				apiService.getPriceData(),
				apiService.getTradingStatsData()
			]);
			setStockData(priceData);
			setTradingStats(statsData);
			setError(null);
		} catch (err) {
			console.error('獲取資料失敗:', err);
			setError('無法獲取資料');
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

	return (<div className="bg-[#0f203e] min-h-screen pb-28 w-full">
		<div className="flex flex-col px-4 lg:px-8 w-full max-w-none">
			<HeaderBar />

			{/* 錯誤狀態 */}
			{error && (
				<div className="mt-8 p-4 bg-red-900/30 border border-red-600 rounded-lg">
					<div className="text-red-400 text-sm">{error}</div>
				</div>
			)}

			{/* 響應式布局：手機版垂直，桌面版左右分欄 */}
			<div className="flex flex-col lg:flex-row lg:gap-8 xl:gap-12">
				{/* 左半邊：圖表 + 價格資訊 */}
				<div className="w-full lg:w-3/5 xl:w-2/3">
					{/* 股市趨勢圖 */}
					<div className="mt-3 mb-2 w-full">
						<StockChart
							currentPrice={currentPrice}
							changePercent={changePercent}
						/>
					</div>

					{/* 價格資訊 */}
					<div className="mb-4">
						<div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-2 lg:gap-4 xl:gap-6 text-center">
							<div className="bg-[#1A325F] p-3 xl:p-4 rounded-lg">
								<h5 className="text-xs lg:text-sm xl:text-base text-white">開盤價</h5>
								<p className="text-lg lg:text-2xl xl:text-3xl font-bold">{Math.round(stockData.open)}</p>
							</div>
							<div className="bg-[#1A325F] p-3 xl:p-4 rounded-lg">
								<h5 className="text-xs lg:text-sm xl:text-base text-white">今日最低</h5>
								<p className="text-lg lg:text-2xl xl:text-3xl font-bold">{Math.round(stockData.low)}</p>
							</div>
							<div className="bg-[#1A325F] p-3 xl:p-4 rounded-lg">
								<h5 className="text-xs lg:text-sm xl:text-base text-white">今日最高</h5>
								<p className="text-lg lg:text-2xl xl:text-3xl font-bold">{Math.round(stockData.high)}</p>
							</div>
							<div className="bg-[#1A325F] p-3 xl:p-4 rounded-lg">
								<h5 className="text-xs lg:text-sm xl:text-base text-white">今日成交量</h5>
								<p className="text-lg lg:text-2xl xl:text-3xl font-bold">{tradingStats.total_volume.toLocaleString()}</p>
								<p className="text-xs lg:text-sm xl:text-base text-white">股</p>
							</div>
							<div className="bg-[#1A325F] p-3 xl:p-4 rounded-lg">
								<h5 className="text-xs lg:text-sm xl:text-base text-white">成交額</h5>
								<p className="text-lg lg:text-2xl xl:text-3xl font-bold">{tradingStats.total_amount.toLocaleString()}</p>
								<p className="text-xs lg:text-sm xl:text-base text-white">點</p>
							</div>
							<div className="bg-[#1A325F] p-3 xl:p-4 rounded-lg">
								<h5 className="text-xs lg:text-sm xl:text-base text-white">成交筆數</h5>
								<p className="text-lg lg:text-2xl xl:text-3xl font-bold">{tradingStats.total_trades.toLocaleString()}</p>
								<p className="text-xs lg:text-sm xl:text-base text-white">筆</p>
							</div>
						</div>
					</div>
				</div>

				{/* 右半邊：五檔報價 + 交易紀錄 (桌面版專用) */}
				<div className="hidden lg:flex lg:flex-col w-full lg:w-2/5 xl:w-1/3">
					{/* 五檔報價 */}
					<div className="mt-3 mb-4 flex-shrink-0">
						<TradingTabs activeTab="orderbook" currentPrice={currentPrice} />
					</div>

					{/* 交易紀錄 */}
					<div className="flex-1 min-h-0">
						<TradingTabs activeTab="history" currentPrice={currentPrice} />
					</div>
				</div>
			</div>

			{/* 手機版的切換式 TAB */}
			<div className="lg:hidden mt-3">
				<TradingTabs currentPrice={currentPrice} />
			</div>
		</div>
	</div>
	);
}