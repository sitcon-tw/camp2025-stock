'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import HeaderBar from '@/components/HeaderBar';

export default function AdminPage() {
  const router = useRouter();
  
  // 狀態管理
  const [adminToken, setAdminToken] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ show: false, message: '', type: 'info' });
  
  // 表單狀態
  const [givePointsForm, setGivePointsForm] = useState({
    type: 'user',
    username: '',
    amount: -200,
    reason: '-200'
  });
  const [tradingLimitPercent, setTradingLimitPercent] = useState(10);
  const [marketTimes, setMarketTimes] = useState([
    { start: '7:00', end: '9:00', favorite: false }
  ]);
  const [announcementForm, setAnnouncementForm] = useState({
    title: '',
    message: '',
    broadcast: true
  });
  
  // 使用者資產資料
  const [userAssets, setUserAssets] = useState([]);
  const [systemStats, setSystemStats] = useState(null);
  const [userSearchTerm, setUserSearchTerm] = useState('');

  // 顯示通知
  const showNotification = (message, type = 'info') => {
    setNotification({ show: true, message, type });
    setTimeout(() => {
      setNotification({ show: false, message: '', type: 'info' });
    }, 3000);
  };

  // 檢查登入狀態
  useEffect(() => {
    const isAdmin = localStorage.getItem('isAdmin');
    const token = localStorage.getItem('adminToken');
    
    if (!isAdmin || !token) {
      router.push('/login');
      return;
    }

    setAdminToken(token);
    setIsLoggedIn(true);
    fetchUserAssets(token);
    fetchSystemStats(token);
  }, [router]);

  // 登出
  const handleLogout = () => {
    setIsLoggedIn(false);
    setAdminToken(null);
    localStorage.removeItem('adminToken');
    setUserAssets([]);
    setSystemStats(null);
    router.push('/'); // Redirect to home or login page
  };

  // 獲取使用者資產
  const fetchUserAssets = async (token, searchUser = null) => {
    try {
      const url = searchUser ? `/api/admin/user?user=${encodeURIComponent(searchUser)}` : '/api/admin/user';
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setUserAssets(data);
      } else {
        console.warn('無法獲取使用者資產，可能是權限問題');
      }
    } catch (error) {
      console.error('獲取使用者資產失敗:', error);
    }
  };

  // 獲取系統統計
  const fetchSystemStats = async (token) => {
    try {
      const response = await fetch('/api/admin/stats', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setSystemStats(data);
      } else {
        console.warn('無法獲取系統統計，可能是權限問題');
      }
    } catch (error) {
      console.error('獲取系統統計失敗:', error);
    }
  };

  // 給予點數
  const handleGivePoints = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/admin/users/give-points', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`,
        },
        body: JSON.stringify({
          username: givePointsForm.username,
          type: givePointsForm.type,
          amount: parseInt(givePointsForm.amount),
        }),
      });

      if (response.ok) {
        showNotification('點數發放成功！', 'success');
        await fetchUserAssets(adminToken);
        await fetchSystemStats(adminToken);
        // 重置表單
        setGivePointsForm({
          type: 'user',
          username: '',
          amount: -200,
          reason: '-200'
        });
      } else {
        const error = await response.json();
        showNotification(`發放失敗: ${error.detail}`, 'error');
      }
    } catch (error) {
      console.error('發放點數錯誤:', error);
      showNotification('發放點數時發生錯誤', 'error');
    }
    setLoading(false);
  };

  // 設定交易限制
  const handleSetTradingLimit = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/admin/market/set-limit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`,
        },
        body: JSON.stringify({
          limitPercent: parseFloat(tradingLimitPercent),
        }),
      });

      if (response.ok) {
        showNotification('交易限制設定成功！', 'success');
      } else {
        showNotification('設定失敗', 'error');
      }
    } catch (error) {
      console.error('設定交易限制錯誤:', error);
      showNotification('設定時發生錯誤', 'error');
    }
    setLoading(false);
  };

  // 新增交易時間
  const addMarketTime = () => {
    setMarketTimes([...marketTimes, { start: '7:00', end: '9:00', favorite: false }]);
  };

  // 移除交易時間
  const removeMarketTime = (index) => {
    const newTimes = marketTimes.filter((_, i) => i !== index);
    setMarketTimes(newTimes);
  };

  // 切換最愛
  const toggleFavorite = (index) => {
    const newTimes = [...marketTimes];
    newTimes[index].favorite = !newTimes[index].favorite;
    setMarketTimes(newTimes);
  };

  // 更新交易時間
  const updateMarketTime = (index, field, value) => {
    const newTimes = [...marketTimes];
    newTimes[index][field] = value;
    setMarketTimes(newTimes);
  };

  // 儲存市場時間
  const saveMarketTimes = async () => {
    setLoading(true);
    try {
      // 轉換時間格式為時間戳
      const openTime = marketTimes.map(time => {
        const today = new Date();
        const startTime = new Date(today.toDateString() + ' ' + time.start);
        const endTime = new Date(today.toDateString() + ' ' + time.end);
        
        return {
          start: Math.floor(startTime.getTime() / 1000),
          end: Math.floor(endTime.getTime() / 1000)
        };
      });

      const response = await fetch('/api/admin/market/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`,
        },
        body: JSON.stringify({ openTime }),
      });

      if (response.ok) {
        showNotification('市場時間設定成功！', 'success');
      } else {
        showNotification('設定失敗', 'error');
      }
    } catch (error) {
      console.error('設定市場時間錯誤:', error);
      showNotification('設定時發生錯誤', 'error');
    }
    setLoading(false);
  };

  // 搜索使用者
  const handleUserSearch = () => {
    if (adminToken) {
      fetchUserAssets(adminToken, userSearchTerm.trim() || null);
    }
  };

  // 發布公告
  const handleCreateAnnouncement = async () => {
    if (!announcementForm.title.trim() || !announcementForm.message.trim()) {
      showNotification('請填寫公告標題和內容', 'error');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/admin/announcement', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`,
        },
        body: JSON.stringify(announcementForm),
      });

      if (response.ok) {
        showNotification('公告發布成功！', 'success');
        setAnnouncementForm({
          title: '',
          message: '',
          broadcast: true
        });
      } else {
        const error = await response.json();
        showNotification(`發布失敗: ${error.detail}`, 'error');
      }
    } catch (error) {
      console.error('發布公告錯誤:', error);
      showNotification('發布公告時發生錯誤', 'error');
    }
    setLoading(false);
  };

  // 如果未登入，重定向到登入頁面
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white">正在檢查登入狀態...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* 通知元件 */}
      {notification.show && (
        <div className={`fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg transition-all duration-300 ${
          notification.type === 'success' ? 'bg-green-600 text-white' :
          notification.type === 'error' ? 'bg-red-600 text-white' :
          'bg-blue-600 text-white'
        }`}>
          <div className="flex items-center space-x-2">
            {notification.type === 'success' && (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
            {notification.type === 'error' && (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <span>{notification.message}</span>
          </div>
        </div>
      )}
      
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">管理頁面</h1>
          <button
            onClick={handleLogout}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md transition-colors"
          >
            登出
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 康堤橙名 - 給予點數功能 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white">康堤橙名</h2>
            </div>

            <div className="space-y-4">
              {/* 個人/群組切換 */}
              <div className="flex items-center space-x-4">
                <span className="text-gray-300">個人</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={givePointsForm.type === 'group'}
                    onChange={(e) => setGivePointsForm({
                      ...givePointsForm,
                      type: e.target.checked ? 'group' : 'user'
                    })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
                <span className="text-gray-300">群組</span>
              </div>

              {/* 給誰 */}
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  給誰（操尋選擇）
                </label>
                <input
                  type="text"
                  value={givePointsForm.username}
                  onChange={(e) => setGivePointsForm({
                    ...givePointsForm,
                    username: e.target.value
                  })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="輸入使用者名稱或群組名稱"
                />
              </div>

              {/* 給多少 */}
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  給多少
                </label>
                <input
                  type="number"
                  value={givePointsForm.amount}
                  onChange={(e) => setGivePointsForm({
                    ...givePointsForm,
                    amount: e.target.value
                  })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* 理由 */}
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  理由
                </label>
                <input
                  type="text"
                  value={givePointsForm.reason}
                  onChange={(e) => setGivePointsForm({
                    ...givePointsForm,
                    reason: e.target.value
                  })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                onClick={handleGivePoints}
                disabled={loading || !givePointsForm.username}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
              >
                {loading ? '發放中...' : '發放'}
              </button>
            </div>
          </div>

          {/* 發布公告 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">發布公告</h2>
            <div className="space-y-4">
              {/* 公告標題 */}
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  公告標題
                </label>
                <input
                  type="text"
                  value={announcementForm.title}
                  onChange={(e) => setAnnouncementForm({
                    ...announcementForm,
                    title: e.target.value
                  })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="輸入公告標題"
                />
              </div>

              {/* 公告內容 */}
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  公告內容
                </label>
                <textarea
                  value={announcementForm.message}
                  onChange={(e) => setAnnouncementForm({
                    ...announcementForm,
                    message: e.target.value
                  })}
                  rows={4}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="輸入公告內容"
                />
              </div>

              {/* 廣播選項 */}
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="broadcast"
                  checked={announcementForm.broadcast}
                  onChange={(e) => setAnnouncementForm({
                    ...announcementForm,
                    broadcast: e.target.checked
                  })}
                  className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="broadcast" className="text-gray-300 text-sm">
                  廣播到 Telegram Bot
                </label>
              </div>

              <button
                onClick={handleCreateAnnouncement}
                disabled={loading || !announcementForm.title.trim() || !announcementForm.message.trim()}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
              >
                {loading ? '發布中...' : '發布公告'}
              </button>
            </div>
          </div>

          {/* 當日股票漲跌限制 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">當日股票漲跌限制</h2>
            <div className="space-y-4">
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={tradingLimitPercent}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value === '' || (!isNaN(value) && parseFloat(value) >= 0 && parseFloat(value) <= 100)) {
                      setTradingLimitPercent(value);
                    }
                  }}
                  placeholder="輸入百分比數字 (0-100)"
                  className="w-full px-3 py-2 pr-8 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <span className="absolute right-3 top-2 text-gray-400 pointer-events-none">%</span>
              </div>
              <button
                onClick={handleSetTradingLimit}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
              >
                {loading ? '設定中...' : '設定'}
              </button>
            </div>
          </div>

          {/* 允許交易時間 */}
          <div className="bg-gray-800 rounded-lg p-6 lg:col-span-2">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white">允許交易時間</h2>
              <div className="flex space-x-2">
                <button
                  onClick={saveMarketTimes}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-md text-sm transition-colors"
                >
                  {loading ? '儲存中...' : '儲存時間'}
                </button>
                <button
                  onClick={addMarketTime}
                  className="bg-green-600 hover:bg-green-700 text-white p-2 rounded-full transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="space-y-3">
              {marketTimes.map((time, index) => (
                <div key={index} className="flex items-center space-x-4 bg-gray-700 p-3 rounded-md">
                  <button
                    onClick={() => toggleFavorite(index)}
                    className={`p-1 rounded ${time.favorite ? 'text-yellow-400' : 'text-gray-400'}`}
                  >
                    <svg className="w-5 h-5" fill={time.favorite ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                    </svg>
                  </button>
                  
                  <div className="flex items-center space-x-2 flex-1">
                    <input
                      type="time"
                      value={time.start}
                      onChange={(e) => updateMarketTime(index, 'start', e.target.value)}
                      className="bg-gray-600 border border-gray-500 rounded px-2 py-1 text-white text-sm"
                    />
                    <span className="text-gray-300">-</span>
                    <input
                      type="time"
                      value={time.end}
                      onChange={(e) => updateMarketTime(index, 'end', e.target.value)}
                      className="bg-gray-600 border border-gray-500 rounded px-2 py-1 text-white text-sm"
                    />
                    <span className="text-gray-400 text-sm">早晨</span>
                  </div>
                  
                  <button
                    onClick={() => removeMarketTime(index)}
                    className="text-red-400 hover:text-red-300 p-1"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* 系統統計 */}
          {systemStats && (
            <div className="bg-gray-800 rounded-lg p-6 lg:col-span-2">
              <h2 className="text-xl font-bold text-white mb-4">系統統計</h2>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{systemStats.total_users}</div>
                  <div className="text-gray-400 text-sm">總使用者數</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">{systemStats.total_groups}</div>
                  <div className="text-gray-400 text-sm">總群組數</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-400">{systemStats.total_points.toLocaleString()}</div>
                  <div className="text-gray-400 text-sm">總點數</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-400">{systemStats.total_stocks.toLocaleString()}</div>
                  <div className="text-gray-400 text-sm">總股票數</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-400">{systemStats.total_trades}</div>
                  <div className="text-gray-400 text-sm">總交易數</div>
                </div>
              </div>
            </div>
          )}

          {/* 使用者資產列表 */}
          {userAssets.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6 lg:col-span-2">
              <h2 className="text-xl font-bold text-white mb-4">使用者資產明細</h2>
              
              {/* 搜索框 */}
              <div className="flex space-x-2 mb-4">
                <input
                  type="text"
                  value={userSearchTerm}
                  onChange={(e) => setUserSearchTerm(e.target.value)}
                  placeholder="搜索使用者名稱..."
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleUserSearch()}
                />
                <button
                  onClick={handleUserSearch}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
                >
                  搜索
                </button>
                <button
                  onClick={() => {
                    setUserSearchTerm('');
                    fetchUserAssets(adminToken);
                  }}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md transition-colors"
                >
                  重置
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-600">
                      <th className="text-left text-gray-300 py-3 px-2">使用者名</th>
                      <th className="text-left text-gray-300 py-3 px-2">隊伍</th>
                      <th className="text-right text-gray-300 py-3 px-2">點數</th>
                      <th className="text-right text-gray-300 py-3 px-2">持股數</th>
                      <th className="text-right text-gray-300 py-3 px-2">股票價值</th>
                      <th className="text-right text-gray-300 py-3 px-2">總資產</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userAssets.slice(0, 20).map((user, index) => (
                      <tr key={index} className="border-b border-gray-700 hover:bg-gray-700 transition-colors">
                        <td className="text-white py-3 px-2 font-medium">{user.username}</td>
                        <td className="text-gray-300 py-3 px-2">{user.team}</td>
                        <td className="text-right text-white py-3 px-2">{user.points.toLocaleString()}</td>
                        <td className="text-right text-white py-3 px-2">{user.stocks}</td>
                        <td className="text-right text-white py-3 px-2">{user.stockValue.toFixed(2)}</td>
                        <td className="text-right text-white py-3 px-2 font-medium">{user.total.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {userAssets.length > 20 && (
                  <div className="text-center text-gray-400 text-sm mt-4">
                    顯示前20個使用者，共{userAssets.length}個使用者
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
