// 模擬股票資料
export const mockStockData = {
  symbol: 'SITC',
  name: 'SITCON Camp 專屬',
  currentPrice: 70,
  change: 5,
  changePercent: 20,
  openPrice: 40,
  highPrice: 10,
  lowPrice: 300,
  volume: 1500,
  lastUpdate: '2025-05-25 08:59:10'
};

// 模擬交易紀錄
export const mockTransactions = [
  { id: 1, time: '5/25 8:59:10', price: 20, quantity: 35, change: -5, type: 'sell' },
  { id: 2, time: '5/25 8:59:10', price: 20, quantity: 30, change: 5, type: 'buy' },
  { id: 3, time: '5/25 8:58:45', price: 20, quantity: 35, change: -5, type: 'sell' },
  { id: 4, time: '5/25 8:58:30', price: 20, quantity: 30, change: 5, type: 'buy' },
  { id: 5, time: '5/25 8:58:15', price: 20, quantity: 35, change: -5, type: 'sell' },
];

// 模擬五檔報價
export const mockOrderBook = {
  bids: [
    { price: 35, quantity: 20, level: 1 },
    { price: 34, quantity: 15, level: 2 },
    { price: 33, quantity: 25, level: 3 },
    { price: 32, quantity: 30, level: 4 },
    { price: 31, quantity: 18, level: 5 },
  ],
  asks: [
    { price: 36, quantity: 22, level: 1 },
    { price: 37, quantity: 17, level: 2 },
    { price: 38, quantity: 28, level: 3 },
    { price: 39, quantity: 33, level: 4 },
    { price: 40, quantity: 20, level: 5 },
  ]
};

// 模擬排行榜資料
export const mockRankings = {
  group: [
    { rank: 1, name: '第一組', score: 2500, change: '+15%' },
    { rank: 2, name: '第二組', score: 2350, change: '+12%' },
    { rank: 3, name: '第三組', score: 2200, change: '+8%' },
    { rank: 4, name: '第四組', score: 2100, change: '+5%' },
  ],
  individual: [
    { rank: 1, name: '張三', group: '第一組', score: 850, change: '+20%' },
    { rank: 2, name: '李四', group: '第二組', score: 820, change: '+18%' },
    { rank: 3, name: '王五', group: '第一組', score: 800, change: '+15%' },
  ]
};

// 模擬管理員資料
export const mockAdminData = {
  currentUser: {
    name: '庫曄',
    role: 'admin',
    permissions: ['manage_users', 'manage_trades', 'system_settings']
  },
  tradingSessions: [
    { id: 1, name: '早盤', startTime: '7:00', endTime: '9:00', active: true },
    { id: 2, name: '午盤', startTime: '13:30', endTime: '15:30', active: true },
    { id: 3, name: '夜盤', startTime: '19:00', endTime: '21:00', active: false },
  ],
  systemSettings: {
    dailyDividendRate: 10,
    tradingEnabled: true,
    maxPositionSize: 1000,
  }
};
